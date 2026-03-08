# routes/admin.py
from flask import Blueprint, request, jsonify, g, send_file
from flask_jwt_extended import jwt_required, get_jwt
from extensions import db, cache
from sqlalchemy.exc import IntegrityError
from models import User, Doctor, Patient, Appointment, Department, Treatment
from utils import gen_identifier, audit, hash_password
import json, os, io
from datetime import datetime
import tasks

bp = Blueprint('admin', __name__, url_prefix='/routes/admin')

def require_admin():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return False
    return True

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix='admin:dashboard') # CACHED for 60 seconds
def dashboard():
    if not require_admin():
        return jsonify({'msg':'forbidden'}), 403
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    return jsonify({
        'doctors': total_doctors,
        'patients': total_patients,
        'appointments': total_appointments
    })

# ==========================================
# ADMIN DOCTOR ROUTES
# ==========================================

@bp.route('/doctors', methods=['GET'])
@jwt_required()
def get_doctors():
    if not require_admin():
        return jsonify({'msg':'forbidden'}), 403
        
    # 1. Explicit Manual Caching
    cache_key = 'admin:doctors:list'
    cached_data = cache.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    doctors = Doctor.query.all()
    output = []
    
    for d in doctors:
        output.append({
            'id': d.id,
            'name': d.user.full_name or d.user.username,
            'email': d.user.email,
            'contact': d.contact,
            'specialization': d.specialization,
            'department': d.department.name if d.department else 'N/A',
            'qualifications': d.qualifications
        })
    
    # Save the exact key explicitly
    cache.set(cache_key, output, timeout=300)
    return jsonify(output)

@bp.route('/doctors', methods=['POST'])
@jwt_required()
def create_doctor():
    if not require_admin():
        return jsonify({'msg':'forbidden'}), 403
        
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password', 'DoctorPass123!')
    full_name = data.get('full_name')
    email = data.get('email') or None 
    specialization = data.get('specialization')
    department_name = data.get('department')
    contact = data.get('contact')
    qualifications = data.get('qualifications')

    if User.query.filter_by(username=username).first():
        return jsonify({'msg':'Username already exists. Please choose a different one.'}), 400
        
    if email and User.query.filter_by(email=email).first():
        return jsonify({'msg': 'Email already exists. Please choose a different one.'}), 400

    try:
        user = User(username=username, password_hash=hash_password(password), role='doctor', full_name=full_name, email=email)
        db.session.add(user)
        db.session.flush() 

        dept = None
        if department_name:
            dept = Department.query.filter_by(name=department_name).first()
            if not dept:
                dept = Department(name=department_name)
                db.session.add(dept)
                db.session.flush()

        doctor = Doctor(
            user_id=user.id, 
            doctor_identifier=gen_identifier('DOC'), 
            specialization=specialization, 
            qualifications=qualifications,
            department_id=(dept.id if dept else None),
            contact=contact
        )
        db.session.add(doctor)
        db.session.commit()
        
        # --- WIPE EXPLICIT CACHE KEYS ---
        cache.delete('admin:doctors:list')
        cache.delete('admin:dashboard')
        cache.delete('patient:doctors:list') # Keep patient side updated

        return jsonify({'msg':'doctor created', 'doctor_id': doctor.id}), 201

    except IntegrityError as e:
        db.session.rollback() 
        return jsonify({'msg': 'A database error occurred. This user ID or email might already be linked to a doctor.'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'An unexpected error occurred while creating the doctor.'}), 500

@bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
@jwt_required()
def update_doctor(doctor_id):
    if not require_admin():
        return jsonify({'msg':'forbidden'}), 403
        
    data = request.get_json() or {}
    doctor = Doctor.query.get_or_404(doctor_id)
    
    doctor.specialization = data.get('specialization', doctor.specialization)
    doctor.qualifications = data.get('qualifications', doctor.qualifications)
    doctor.contact = data.get('contact', doctor.contact)

    dept_name = data.get('department_name')
    if dept_name:
        dept = Department.query.filter(Department.name.ilike(dept_name)).first()
        if not dept:
            dept = Department(name=dept_name)
            db.session.add(dept)
            db.session.flush()
        else:
            if dept.name != dept_name:
                dept.name = dept_name
                db.session.add(dept)
                
        doctor.department_id = dept.id

    if doctor.user:
        doctor.user.full_name = data.get('name', doctor.user.full_name)
        doctor.user.email = data.get('email', doctor.user.email)

    if 'available_slots' in data:
        doctor.available_slots = json.dumps(data.get('available_slots'))
        cache.delete(f'doctor:{doctor.id}:slots')
        
    try:
        db.session.commit()
        
        # --- WIPE EXPLICIT CACHE KEYS ---
        cache.delete('admin:doctors:list')
        cache.delete('patient:doctors:list')
        
        audit(None, 'update_doctor', {'doctor_id': doctor.id})
        return jsonify({'msg':'updated'})
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({'msg': 'Update failed: That email address is already in use.'}), 400

@bp.route('/doctors/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_doctor(id):
    if get_jwt().get('role') != 'admin':
        return jsonify({'msg': 'forbidden'}), 403

    doctor = Doctor.query.get_or_404(id)
    user_record = doctor.user 
    
    # Find all appointments assigned to this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()
    
    for appt in appointments:
        # 2. Delete any treatments tied to this specific appointment
        Treatment.query.filter_by(appointment_id=appt.id).delete()
        # 3. Delete the appointment itself
        db.session.delete(appt)
        
    # 4. Just to be completely safe, remove any stray treatments where they were the treating doctor
    Treatment.query.filter_by(treating_doctor_id=doctor.id).delete()
    
    # 5. Now that the child records are gone, it is safe to delete the parent profiles!
    db.session.delete(doctor)
    if user_record:
        db.session.delete(user_record)
        
    db.session.commit()
    
    # --- WIPE EXPLICIT CACHE KEYS ---
    cache.delete('admin:doctors:list')
    cache.delete('admin:dashboard')
    cache.delete('patient:doctors:list')
    
    return jsonify({'msg': 'Doctor, user account, and all associated history completely removed.'})
@bp.route('/appointments', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, key_prefix='admin:appointments') # CACHED
def list_appointments():
    if not require_admin():
        return jsonify({'msg':'forbidden'}), 403
        
    appts = Appointment.query.order_by(Appointment.scheduled_at.desc()).limit(200).all()
    out = []
    
    for a in appts:
        doctor_name = a.doctor.user.full_name if a.doctor and a.doctor.user else 'Unknown'
        patient_name = a.patient.user.full_name if a.patient and a.patient.user else 'Unknown'
        
        out.append({
            'id': a.id,
            'doctor_name': doctor_name, 
            'patient_name': patient_name, 
            'scheduled_at': a.scheduled_at.isoformat(),
            'status': a.status
        })
    return jsonify(out)

@bp.route('/patients', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix='admin:patients') # CACHED
def get_patients():
    if not require_admin():
        return jsonify({'msg': 'forbidden'}), 403
    
    patients = Patient.query.all()
    out = []
    for p in patients:
        out.append({
            'id': p.id,
            'name': p.user.full_name or p.user.username,
            'email': p.user.email,
            'contact': p.contact,
            'gender': p.gender,
            'dob': str(p.dob) if p.dob else None,
            'created_at': p.created_at.isoformat() if p.created_at else None
        })
    return jsonify(out)

@bp.route('/patients/<int:patient_id>/history', methods=['GET'])
@jwt_required()
# Intentionally NOT caching history directly to ensure live updates for specific patients
def patient_history(patient_id):
    if not require_admin():
        return jsonify({'msg': 'forbidden'}), 403
        
    treatments = Treatment.query.join(Appointment).filter(Appointment.patient_id==patient_id).order_by(Treatment.created_at.desc()).all()
    out = []
    for t in treatments:
        doctor_name = t.treating_doctor.user.full_name if t.treating_doctor else 'Unknown'
        out.append({
            'id': t.id,
            'date': t.appointment.scheduled_at.isoformat(),
            'doctor_name': doctor_name,
            'specialization': t.treating_doctor.specialization if t.treating_doctor else 'N/A',
            'reason': t.appointment.reason,
            'diagnosis': t.diagnosis,
            'prescription': json.loads(t.prescription or '{}'),
            'notes': t.notes
        })
    return jsonify(out)

@bp.route('/patients/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_patient(id):
    if get_jwt().get('role') != 'admin':
        return jsonify({'msg': 'forbidden'}), 403

    patient = Patient.query.get_or_404(id)
    user_record = patient.user 
    
    # FIX: Delete all their appointments and treatments first!
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()
    for appt in appointments:
        # Delete any treatments tied to this appointment
        Treatment.query.filter_by(appointment_id=appt.id).delete()
        db.session.delete(appt)
    
    # Now it is safe to delete the patient and user
    db.session.delete(patient)
    if user_record:
        db.session.delete(user_record)
        
    db.session.commit()
    
    cache.delete('admin:patients')
    cache.delete('admin:dashboard')
    
    return jsonify({'msg': 'Patient, user account, and all history removed.'})

@bp.route('/export', methods=['POST'])
@jwt_required()
def trigger_export():
    if get_jwt().get('role') != 'admin':
        return jsonify({'msg': 'forbidden'}), 403

    data = request.get_json() or {}
    export_type = data.get('type')
    search_query = data.get('query', '')

    # Notice we removed the admin email from the .delay() calls
    if export_type == 'doctors':
        task = tasks.export_doctors_csv.delay(search_query)
    elif export_type == 'patients':
        task = tasks.export_patients_csv.delay(search_query)
    elif export_type == 'patient_history':
        patient_id = data.get('patient_id')
        task = tasks.export_patient_history_csv.delay(patient_id)
    elif export_type == 'past_appointments':
        task = tasks.export_past_appointments_csv.delay()
    else:
        return jsonify({'msg': 'Invalid export type'}), 400

    return jsonify({'msg': 'Export started', 'task_id': task.id}), 202

@bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(task_id):
    # We can use any task function to access the AsyncResult for this Celery app
    task = tasks.export_doctors_csv.AsyncResult(task_id) 
    if task.state == 'SUCCESS':
        return jsonify({'state': task.state, 'filepath': task.result})
    elif task.state == 'FAILURE':
        return jsonify({'state': task.state, 'error': str(task.info)})
    return jsonify({'state': task.state})

@bp.route('/export/download/<task_id>', methods=['GET'])
@jwt_required()
def download_export(task_id):
    task = tasks.export_doctors_csv.AsyncResult(task_id) 
    if task.state == 'SUCCESS' and task.result and os.path.exists(task.result):
        filepath = task.result
        
        # 1. Read the file into server memory
        return_data = io.BytesIO()
        with open(filepath, 'rb') as fo:
            return_data.write(fo.read())
        return_data.seek(0)
        
        # 2. Delete the physical file from your VS Code folder!
        os.remove(filepath)
        
        # 3. Send the memory version to Chrome
        filename = os.path.basename(filepath)
        return send_file(return_data, mimetype='text/csv', as_attachment=True, download_name=filename)
        
    return jsonify({'msg': 'Download failed or expired'}), 404