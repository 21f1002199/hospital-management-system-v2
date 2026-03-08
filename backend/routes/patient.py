# routes/patient.py
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db, cache
from models import User, Patient, Doctor, Appointment, Treatment
from utils import gen_identifier, audit
from datetime import datetime
import os, json, tasks, io
from tasks import export_patient_history_csv # NEW: Import the Celery task

bp = Blueprint('patient', __name__, url_prefix='/routes/patient')

def require_patient():
    claims = get_jwt()
    return claims.get('role') == 'patient'

def get_current_patient():
    uid = get_jwt().get('uid')
    return Patient.query.filter_by(user_id=uid).first()

@bp.route('/profile', methods=['GET','PUT'])
@jwt_required()
def profile():
    if not require_patient():
        return jsonify({'msg':'forbidden'}), 403
    uid = get_jwt().get('uid')
    user = User.query.get(uid)
    
    # --- CACHE CHECK ---
    cache_key = f'patient:{uid}:profile'
    
    if request.method == 'GET':
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data)

        patient = Patient.query.filter_by(user_id=uid).first()
        dob_string = patient.dob.isoformat() if patient and patient.dob else ''

        out = {
            'id': user.id, 
            'username': user.username, 
            'full_name': user.full_name, 
            'email': user.email,
            'contact': patient.contact if patient else '',
            'gender': patient.gender if patient else '',
            'dob': dob_string
        }
        # Save to cache for 5 minutes
        cache.set(cache_key, out, timeout=300)
        return jsonify(out)
        
    # --- PUT: UPDATE PROFILE ---
    data = request.get_json() or {}
    user.full_name = data.get('full_name', user.full_name)
    user.email = data.get('email', user.email)
    
    patient = Patient.query.filter_by(user_id=uid).first()
    if patient:
        patient.contact = data.get('contact', patient.contact)
        patient.gender = data.get('gender', patient.gender)
        
        dob_str = data.get('dob')
        if dob_str:
            patient.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        elif dob_str == '':
            patient.dob = None
            
    db.session.commit()
    
    # --- WIPE CACHES ---
    cache.delete(cache_key)
    cache.delete('admin:patients') # Update the admin view as well
    audit(uid, 'update_profile', {})
    return jsonify({'msg':'updated'})

@bp.route('/doctors', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix='patient:doctors:list') # GLOBAL CACHE
def get_doctors():
    if not require_patient():
        return jsonify({'msg':'forbidden'}), 403
    
    doctors = Doctor.query.all()
    out = []
    for d in doctors:
        active_appts = Appointment.query.filter_by(doctor_id=d.id, status='booked').all()
        booked_slots = [a.scheduled_at.isoformat() for a in active_appts]
        out.append({
            'id': d.id,
            'name': d.user.full_name or d.user.username,
            'specialization': d.specialization or 'General',
            'department': d.department.name if d.department else 'General',
            'qualifications': d.qualifications or 'Not specified',
            'available_slots': json.loads(d.available_slots or '{}'),
            'booked_slots': booked_slots 
        })
    return jsonify(out)

@bp.route('/appointments', methods=['GET','POST'])
@jwt_required()
def appointments():
    if not require_patient():
        return jsonify({'msg':'forbidden'}), 403
        
    uid = get_jwt().get('uid')
    patient = get_current_patient()
    cache_key = f'patient:{patient.id}:appointments'
    
    if request.method == 'GET':
        cached_data = cache.get(cache_key)
        if cached_data:
            return jsonify(cached_data)

        appts = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.scheduled_at.desc()).all()
        out = []
        for a in appts:
            doctor_name = a.doctor.user.full_name if a.doctor and a.doctor.user else 'Unknown Doctor'
            out.append({
                'id': a.id,
                'doctor_name': doctor_name,
                'specialization': a.doctor.specialization if a.doctor else '',
                'scheduled_at': a.scheduled_at.isoformat(),
                'status': a.status,
                'reason': a.reason
            })
            
        cache.set(cache_key, out, timeout=120)
        return jsonify(out)

    # --- POST: BOOK APPOINTMENT ---
    data = request.get_json() or {}
    doctor_id = data.get('doctor_id')
    scheduled_at = data.get('scheduled_at')  
    reason = data.get('reason')

    if not doctor_id or not scheduled_at:
        return jsonify({'msg':'doctor_id and scheduled_at required'}), 400
        
    dt = datetime.fromisoformat(scheduled_at)
    
    patient_conflict = Appointment.query.filter_by(
        patient_id=patient.id, 
        scheduled_at=dt, 
        status='booked'
    ).first()
    
    if patient_conflict:
        return jsonify({'msg': 'You already have an appointment booked with another doctor at this exact time.'}), 409

    try:
        doctor = Doctor.query.with_for_update().get_or_404(doctor_id)
        
        doctor_conflict = Appointment.query.filter_by(
            doctor_id=doctor.id, 
            scheduled_at=dt, 
            status='booked'
        ).first()
        
        if doctor_conflict:
            db.session.rollback()
            return jsonify({'msg':'Sorry, this slot was just taken by someone else. Please choose another.'}), 409

        appt = Appointment(
            appointment_identifier=gen_identifier('APT'), 
            doctor_id=doctor.id, 
            patient_id=patient.id, 
            scheduled_at=dt, 
            status='booked',
            reason=reason
        )
        db.session.add(appt)
        db.session.commit()
        
        # --- WIPE CACHES SO EVERYTHING UPDATES INSTANTLY ---
        cache.delete(cache_key) # My Appointments tab
        cache.delete('patient:doctors:list') # Doctor Directory slots
        cache.delete('admin:appointments')
        cache.delete(f'doctor:{doctor.id}:appointments:day')
        cache.delete(f'doctor:{doctor.id}:appointments:week')
        cache.delete(f'doctor:{doctor.id}:patients')
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An error occurred while booking. Please try again.'}), 500
    
    try:
        audit(uid, 'book_appointment', {'appointment_id': appt.id})
    except Exception: pass
        
    return jsonify({'msg':'booked', 'appointment_id': appt.id}), 201

@bp.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_appointment(appointment_id):
    if not require_patient():
        return jsonify({'msg':'forbidden'}), 403
        
    uid = get_jwt().get('uid')
    patient = get_current_patient()
    appt = Appointment.query.get_or_404(appointment_id)
    
    if appt.patient_id != patient.id:
        return jsonify({'msg':'not your appointment'}), 403

    appt.status = 'cancelled'
    db.session.commit()
    
    # --- WIPE CACHES ---
    cache.delete(f'patient:{patient.id}:appointments')
    cache.delete('patient:doctors:list') 
    cache.delete('admin:appointments')
    cache.delete(f'doctor:{appt.doctor_id}:appointments:day')
    cache.delete(f'doctor:{appt.doctor_id}:appointments:week')
    
    try: audit(uid, 'cancel_appointment', {'appointment_id': appt.id})
    except Exception: pass
        
    return jsonify({'msg':'cancelled'})

@bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    if not require_patient():
        return jsonify({'msg':'forbidden'}), 403
        
    patient = get_current_patient()
    cache_key = f'patient:{patient.id}:history'
    
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    treatments = Treatment.query.join(Appointment).filter(Appointment.patient_id==patient.id).order_by(Treatment.created_at.desc()).all()
    out = []
    for t in treatments:
        doctor_name = t.treating_doctor.user.full_name if t.treating_doctor else 'Unknown'
        out.append({
            'id': t.id,
            'date': t.appointment.scheduled_at.isoformat(),
            'doctor_name': doctor_name,
            'diagnosis': t.diagnosis,
            'prescription': json.loads(t.prescription or '{}'),
            'notes': t.notes
        })
        
    cache.set(cache_key, out, timeout=300)
    return jsonify(out)

# ==========================================
# ASYNC JOB TRIGGER: CSV EXPORT
# ==========================================
# 1. THE TRIGGER
@bp.route('/export', methods=['POST'])
@jwt_required()
def trigger_export():
    uid = get_jwt().get('uid')
    patient = Patient.query.filter_by(user_id=uid).first()
    
    if not patient:
        return jsonify({'msg': 'Patient profile not found'}), 404

    # Trigger the task and get the task object back
    task = tasks.export_patient_history_csv.delay(patient.id)

    # Return the task.id so the frontend knows what to listen for
    return jsonify({'msg': 'Export started', 'task_id': task.id}), 202

# 2. THE STATUS CHECKER
@bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(task_id):
    # Ask Celery for the status of this specific task
    task = tasks.export_patient_history_csv.AsyncResult(task_id)
    
    if task.state == 'SUCCESS':
        # task.result contains the filepath we returned from the task!
        return jsonify({'state': task.state, 'filepath': task.result})
    elif task.state == 'FAILURE':
        return jsonify({'state': task.state, 'error': str(task.info)})
        
    return jsonify({'state': task.state})

# 3. THE DOWNLOADER
@bp.route('/export/download/<task_id>', methods=['GET'])
@jwt_required()
def download_export(task_id):
    task = tasks.export_patient_history_csv.AsyncResult(task_id) 
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