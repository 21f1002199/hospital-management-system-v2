# routes/doctor.py
from flask import Blueprint, request, jsonify, g, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, cache
from models import Doctor, Appointment, Treatment, Patient, User
from utils import audit, gen_identifier
from datetime import datetime, timedelta
import json, os, io
import tasks

bp = Blueprint('doctor', __name__, url_prefix='/routes/doctor')

def require_doctor():
    claims = get_jwt()
    return claims.get('role') == 'doctor'

def get_current_doctor():
    claims = get_jwt()
    uid = claims.get('uid')
    return Doctor.query.filter_by(user_id=uid).first()

@bp.route('/appointments', methods=['GET'])
@jwt_required()
def my_appointments():
    if not require_doctor():
        return jsonify({'msg':'forbidden'}), 403
    
    doctor = get_current_doctor()
    if not doctor:
        return jsonify({'msg':'doctor profile not found'}), 404

    rng = request.args.get('range', 'day')
    
    # --- CACHE CHECK ---
    cache_key = f'doctor:{doctor.id}:appointments:{rng}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    # 1. Get the current time, but roll it back to the START of today (Midnight)
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 2. Determine the end of our search window
    if rng == 'day':
        end_date = today_start + timedelta(days=1)
    else: # 'week'
        end_date = today_start + timedelta(days=7)

    # 3. The Magic Fix: Fetch appointments that are either in our date window, 
    # OR are still marked as 'booked' from the past!
    appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        db.or_(
            Appointment.scheduled_at.between(today_start, end_date),
            db.and_(Appointment.status == 'booked', Appointment.scheduled_at < today_start)
        )
    ).order_by(Appointment.scheduled_at.asc()).all()
    
    out = []
    for a in appts:
        patient_name = a.patient.user.full_name if a.patient and a.patient.user else 'Unknown Patient'
        out.append({
            'id': a.id,
            'patient_id': a.patient_id,
            'patient_name': patient_name,
            'scheduled_at': a.scheduled_at.isoformat(),
            'status': a.status,
            'reason': a.reason
        })
        
    # --- SAVE TO CACHE --- (Cache for 60 seconds)
    cache.set(cache_key, out, timeout=60)
    return jsonify(out)

@bp.route('/appointments/<int:appointment_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_appointment(appointment_id):
    if not require_doctor():
        return jsonify({'msg':'forbidden'}), 403
    
    doctor = get_current_doctor()
    appt = Appointment.query.get_or_404(appointment_id)
    
    if appt.doctor_id != doctor.id:
        return jsonify({'msg':'not your appointment'}), 403

    appt.status = 'cancelled'
    db.session.commit()
    
    # --- WIPE CACHES ---
    cache.delete(f'doctor:{doctor.id}:appointments:day')
    cache.delete(f'doctor:{doctor.id}:appointments:week')
    cache.delete('admin:appointments')
    
    return jsonify({'msg':'appointment cancelled'})

@bp.route('/appointments/<int:appointment_id>/complete', methods=['PUT'])
@jwt_required()
def complete_appointment(appointment_id):
    if not require_doctor():
        return jsonify({'msg':'forbidden'}), 403
    
    doctor = get_current_doctor()
    appt = Appointment.query.get_or_404(appointment_id)
    
    if appt.doctor_id != doctor.id:
        return jsonify({'msg':'not your appointment'}), 403

    data = request.get_json() or {}
    diagnosis = data.get('diagnosis')
    prescription = data.get('prescription')  
    notes = data.get('notes')

    appt.status = 'completed'
    db.session.add(appt)
    
    treat = Treatment(appointment_id=appt.id, diagnosis=diagnosis, prescription=json.dumps(prescription or {}), notes=notes, treating_doctor_id=doctor.id)
    db.session.add(treat)
    db.session.commit()

    # --- WIPE CACHES ---
    cache.delete(f'doctor:{doctor.id}:appointments:day')
    cache.delete(f'doctor:{doctor.id}:appointments:week')
    cache.delete(f'doctor:{doctor.id}:patients') # Patient list might have updated
    cache.delete('admin:appointments')

    return jsonify({'msg':'appointment completed'})

@bp.route('/patients', methods=['GET'])
@jwt_required()
def my_patients():
    if not require_doctor():
        return jsonify({'msg':'forbidden'}), 403
        
    doctor = get_current_doctor()
    
    # --- CACHE CHECK ---
    cache_key = f'doctor:{doctor.id}:patients'
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    # Get unique patients who have booked this doctor
    patients = Patient.query.join(Appointment).filter(Appointment.doctor_id == doctor.id).distinct().all()
    
    out = []
    for p in patients:
        out.append({
            'id': p.id,
            'name': p.user.full_name or p.user.username,
            'contact': p.contact,
            'gender': p.gender,
            'dob': p.dob.strftime('%Y-%m-%d') if p.dob else None
        })
        
    # --- SAVE TO CACHE --- (Cache for 5 minutes)
    cache.set(cache_key, out, timeout=300)
    return jsonify(out)

@bp.route('/availability', methods=['GET', 'PUT'])
@jwt_required()
def availability():
    if not require_doctor():
        return jsonify({'msg':'forbidden'}), 403
        
    doctor = get_current_doctor()
    cache_key = f'doctor:{doctor.id}:slots'
    
    if request.method == 'GET':
        # --- CACHE CHECK ---
        cached_slots = cache.get(cache_key)
        if cached_slots:
            return jsonify({'available_slots': cached_slots})
            
        slots = json.loads(doctor.available_slots or '{}')
        cache.set(cache_key, slots, timeout=300)
        return jsonify({'available_slots': slots})
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        slots = data.get('slots', {})
        
        # --- STRICT BACKEND VALIDATION ---
        # Get the current time in IST to ensure accuracy regardless of server config
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        today_str = ist_now.strftime('%Y-%m-%d')
        
        # Grab the old slots to compare against
        old_slots = json.loads(doctor.available_slots or '{}')

        # Check for any new slots being added to today
        if today_str in slots:
            for t in slots[today_str]:
                # If it's a new addition
                if t not in old_slots.get(today_str, []):
                    try:
                        hour, minute = map(int, t.split(':'))
                        # Verify the time hasn't passed in IST
                        if hour < ist_now.hour or (hour == ist_now.hour and minute < ist_now.minute):
                            return jsonify({'msg': f'Invalid action: {t} on {today_str} has already passed.'}), 400
                    except ValueError:
                        return jsonify({'msg': 'Invalid time format provided.'}), 400
        
        doctor.available_slots = json.dumps(slots)
        db.session.commit()
        
        # --- WIPE CACHES ---
        cache.delete(cache_key)
        cache.delete('doctors:list') # Crucial: Update the public directory so patients see the new slots!
        
        return jsonify({'msg': 'Availability updated successfully'})

@bp.route('/patients/<int:patient_id>/history', methods=['GET'])
@jwt_required()
def patient_history(patient_id):
    claims = get_jwt()
    if claims.get('role') != 'doctor':
        return jsonify({'msg': 'forbidden'}), 403
        
    # We do NOT cache history here to ensure the doctor always sees the 
    # absolute most recent real-time data when treating a patient.
    treatments = Treatment.query.join(Appointment).filter(Appointment.patient_id==patient_id).order_by(Treatment.created_at.desc()).all()
    out = []
    for t in treatments:
        doc_name = t.treating_doctor.user.full_name if t.treating_doctor else 'Unknown'
        out.append({
            'id': t.id,
            'date': t.appointment.scheduled_at.isoformat(),
            'doctor_name': doc_name,
            'specialization': t.treating_doctor.specialization if t.treating_doctor else 'N/A',
            'reason': t.appointment.reason,
            'diagnosis': t.diagnosis,
            'prescription': json.loads(t.prescription or '{}'),
            'notes': t.notes
        })
    return jsonify(out)

@bp.route('/export', methods=['POST'])
@jwt_required()
def trigger_export():
    if not require_doctor():
        return jsonify({'msg': 'forbidden'}), 403

    doctor = get_current_doctor()
    data = request.get_json() or {}
    export_type = data.get('type')

    if export_type == 'patient_history':
        patient_id = data.get('patient_id')
        task = tasks.export_patient_history_csv.delay(patient_id)
    elif export_type == 'assigned_patients':
        search_query = data.get('query', '')
        task = tasks.export_doctor_patients_csv.delay(doctor.id, search_query)
    else:
        return jsonify({'msg': 'Invalid export type'}), 400

    return jsonify({'msg': 'Export started', 'task_id': task.id}), 202

@bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(task_id):
    task = tasks.export_doctor_patients_csv.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        return jsonify({'state': task.state, 'filepath': task.result})
    elif task.state == 'FAILURE':
        return jsonify({'state': task.state, 'error': str(task.info)})
    return jsonify({'state': task.state})

@bp.route('/export/download/<task_id>', methods=['GET'])
@jwt_required()
def download_export(task_id):
    task = tasks.export_doctor_patients_csv.AsyncResult(task_id) 
    if task.state == 'SUCCESS' and task.result and os.path.exists(task.result):
        filepath = task.result
        
        return_data = io.BytesIO()
        with open(filepath, 'rb') as fo:
            return_data.write(fo.read())
        return_data.seek(0)
        
        os.remove(filepath) # Delete from VS Code
        
        filename = os.path.basename(filepath)
        return send_file(return_data, mimetype='text/csv', as_attachment=True, download_name=filename)
        
    return jsonify({'msg': 'Download failed or expired'}), 404