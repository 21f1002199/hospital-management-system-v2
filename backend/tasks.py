# tasks.py
from celery import shared_task
from extensions import db, mail
from models import Appointment, Treatment, Patient, Doctor, User, Department 
from flask_mail import Message
from datetime import datetime, timedelta
import csv
import os

# ==========================================
# HELPERS
# ==========================================
def format_ist(utc_dt, time_only=False):
    if not utc_dt: return 'N/A'
    # Force conversion from UTC to IST (+5:30)
    ist_dt = utc_dt + timedelta(hours=5, minutes=30)
    
    # Return just the AM/PM time if requested
    if time_only:
        return ist_dt.strftime('%I:%M %p')
        
    # Otherwise return full date and AM/PM time
    return ist_dt.strftime('%d-%b-%Y at %I:%M %p')

def calculate_age(dob):
    if not dob: return 'N/A'
    today = datetime.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

# ==========================================
# REAL EMAIL SENDER
# ==========================================
def send_email(to_email, subject, body, is_html=False, attachment_path=None):
    try:
        msg = Message(subject=subject, recipients=[to_email])
        
        if is_html:
            msg.html = body
        else:
            msg.body = body

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                msg.attach(
                    filename=os.path.basename(attachment_path),
                    content_type='text/csv',
                    data=f.read()
                )

        mail.send(msg)
        print(f"[{datetime.now()}] ✅ REAL EMAIL SENT TO: {to_email}")

        if attachment_path and os.path.exists(attachment_path):
            os.remove(attachment_path)

    except Exception as e:
        print(f"[{datetime.now()}] ❌ FAILED TO SEND EMAIL TO {to_email}: {e}")

# ==========================================
# A. DAILY SCHEDULED JOB: Patient Reminders
# ==========================================
@shared_task(name="tasks.daily_reminders")
def send_daily_reminders():
    today = datetime.now().date()
    
    today_str = today.strftime('%Y-%m-%d')
    appointments = Appointment.query.filter(
        Appointment.scheduled_at.like(f"{today_str}%"),
        Appointment.status == 'booked'
    ).all()

    for appt in appointments:
        patient_email = appt.patient.user.email
        if patient_email:
            doctor_name = appt.doctor.user.full_name or appt.doctor.user.username
            # FIXED: Apply the IST conversion with AM/PM
            time_ist = format_ist(appt.scheduled_at, time_only=True)
            
            msg = f"Hello {appt.patient.user.full_name},\n\nThis is a reminder for your appointment with Dr. {doctor_name} today at {time_ist}.\n\nPlease arrive a few minutes early. If you have any questions, feel free to contact us.\n\nBest regards,\nHospital Management System"
            send_email(patient_email, "Hospital Visit Reminder", msg)

    return f"Sent {len(appointments)} reminders for {today_str}"

# ==========================================
# B. MONTHLY SCHEDULED JOB: Doctor Report
# ==========================================
@shared_task(name="tasks.monthly_doctor_report")
def generate_monthly_reports():
    first_day_of_this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    last_month = first_day_of_this_month - timedelta(days=1)
    target_month_str = last_month.strftime('%Y-%m') 

    doctors = Doctor.query.all()
    
    for doc in doctors:
        if not doc.user.email: continue

        treatments = Treatment.query.join(Appointment).filter(
            Treatment.treating_doctor_id == doc.id,
            Appointment.scheduled_at.like(f"{target_month_str}%")
        ).all()

        if not treatments: continue

        html_content = f"""
        <html><body>
            <h2>Monthly Activity Report: {last_month.strftime('%B %Y')}</h2>
            <p>Dear Dr. {doc.user.full_name},</p>
            <p>You completed {len(treatments)} appointments this month.</p>
            <table border="1" cellpadding="5">
                <tr>
                    <th>Appointment ID</th>
                    <th>Patient Name</th>
                    <th>Date & Time</th>
                    <th>Reason</th>
                    <th>Diagnosis</th>
                    <th>Prescription</th>
                </tr>
        """
        for t in treatments:
            patient_name = t.appointment.patient.user.full_name if t.appointment.patient and t.appointment.patient.user else 'Unknown Patient'
            reason = t.appointment.reason if t.appointment.reason else 'None Provided'
            
            # Output the exact IST time with AM/PM
            formatted_date = format_ist(t.appointment.scheduled_at)
            
            html_content += f"""
                <tr>
                    <td>{t.appointment.id}</td>
                    <td>{patient_name}</td>
                    <td>{formatted_date}</td>
                    <td>{reason}</td>
                    <td>{t.diagnosis}</td>
                    <td>{t.prescription}</td>
                </tr>
            """
        
        html_content += "</table></body></html>"

        send_email(doc.user.email, f"Monthly Report - {last_month.strftime('%B')}", html_content, is_html=True)
        
    return "Monthly reports generated."

# ==========================================
# C. USER TRIGGERED ASYNC JOBS: CSV Exports
# ==========================================
@shared_task(name="tasks.export_doctors_csv")
def export_doctors_csv(search_query):
    query = Doctor.query.join(User).outerjoin(Department)
    
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(db.or_(
            User.full_name.ilike(search_term),
            Department.name.ilike(search_term)
        ))
    
    doctors = query.all()
    filename = f"doctors_export_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Name', 'Email', 'Specialization', 'Department', 'Qualifications', 'Contact'])
        
        for doc in doctors:
            writer.writerow([
                doc.id,
                doc.user.full_name if doc.user else 'Unknown',
                doc.user.email if doc.user else 'N/A',
                doc.specialization,
                doc.department.name if doc.department else 'N/A',
                doc.qualifications,
                doc.contact
            ])

    return filepath


@shared_task(name="tasks.export_patients_csv")
def export_patients_csv(search_query):
    query = Patient.query.join(User)
    
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(db.or_(
            User.full_name.ilike(search_term),
            Patient.contact.ilike(search_term)
        ))
        
    patients = query.all()
    filename = f"patients_export_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['ID', 'Name', 'Email', 'Contact', 'Gender', 'DOB', 'Age', 'Joined Date'])
        
        for pat in patients:
            writer.writerow([
                pat.id,
                pat.user.full_name if pat.user else 'Unknown',
                pat.user.email if pat.user else 'N/A',
                pat.contact,
                pat.gender,
                pat.dob.strftime('%Y-%m-%d') if pat.dob else 'N/A',
                calculate_age(pat.dob),
                pat.created_at.strftime('%Y-%m-%d') if pat.created_at else 'N/A'
            ])

    return filepath


@shared_task(name="tasks.export_past_appointments_csv")
def export_past_appointments_csv():
    now = datetime.utcnow()
    appts = Appointment.query.filter(
        db.or_(Appointment.scheduled_at < now, Appointment.status != 'booked')
    ).order_by(Appointment.scheduled_at.desc()).all()

    filename = f"past_appointments_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Appointment ID', 'Date & Time (IST)', 'Patient Name', 'Doctor Name', 'Status', 'Reason'])
        
        for a in appts:
            pat_name = a.patient.user.full_name if a.patient and a.patient.user else 'Unknown'
            doc_name = a.doctor.user.full_name if a.doctor and a.doctor.user else 'Unknown'
            writer.writerow([
                a.id,
                format_ist(a.scheduled_at), # This was already using the helper correctly
                pat_name,
                doc_name,
                (a.status or '').upper(),
                a.reason or 'None provided'
            ])

    return filepath


@shared_task(name="tasks.export_patient_history")
def export_patient_history_csv(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient: return "Patient not found"

    treatments = Treatment.query.join(Appointment).filter(
        Appointment.patient_id == patient_id
    ).order_by(Treatment.created_at.desc()).all()

    filename = f"medical_history_{patient_id}_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Patient ID', 'Patient Name', 'Consulting Doctor', 'Appointment Date', 'Diagnosis', 'Prescription', 'Notes'])
        
        for t in treatments:
            doc_name = t.treating_doctor.user.full_name if t.treating_doctor else 'Unknown'
            writer.writerow([
                patient.id, # FIXED: Uses the accurate integer ID
                patient.user.full_name,
                doc_name,
                format_ist(t.appointment.scheduled_at), # FIXED: IST conversion with AM/PM
                t.diagnosis,
                t.prescription,
                t.notes
            ])

    return filepath

@shared_task(name="tasks.export_doctor_patients_csv")
def export_doctor_patients_csv(doctor_id, search_query):
    query = Patient.query.join(Appointment).filter(Appointment.doctor_id == doctor_id).distinct()
    
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(db.or_(
            Patient.user.has(User.full_name.ilike(search_term)),
            Patient.contact.ilike(search_term)
        ))
        
    patients = query.all()
    filename = f"my_patients_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Patient Name', 'DOB', 'Age', 'Contact Number', 'Gender'])
        
        for pat in patients:
            writer.writerow([
                pat.user.full_name if pat.user else 'Unknown',
                pat.dob.strftime('%Y-%m-%d') if pat.dob else 'N/A',
                calculate_age(pat.dob),
                pat.contact or 'N/A',
                pat.gender or 'N/A'
            ])

    return filepath