# models.py
from datetime import datetime
from extensions import db
import enum
import json

class RoleEnum:
    ADMIN = 'admin'
    DOCTOR = 'doctor'
    PATIENT = 'patient'

class AppointmentStatus:
    BOOKED = 'booked'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    full_name = db.Column(db.String(200))
    email = db.Column(db.String(200), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('Doctor', backref='user', uselist=False)
    patient = db.relationship('Patient', backref='user', uselist=False)

class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    doctors_registered = db.Column(db.Integer, default=0)
    extra_meta = db.Column(db.Text)  # JSON string

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    doctor_identifier = db.Column(db.String(64), unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    specialization = db.Column(db.String(200))
    qualifications = db.Column(db.String(400))
    contact = db.Column(db.String(100))
    available_slots = db.Column(db.Text)  # JSON string: {"2026-02-08": ["09:00","10:00"], ...}
    blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', backref='doctors')

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    patient_identifier = db.Column(db.String(64), unique=True)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(100))
    medical_history = db.Column(db.Text)  # JSON string
    blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_identifier = db.Column(db.String(64), unique=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default=AppointmentStatus.BOOKED)
    reason = db.Column(db.String(400))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = db.relationship('Doctor', backref='appointments')
    patient = db.relationship('Patient', backref='appointments')

class Treatment(db.Model):
    __tablename__ = 'treatments'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)  # JSON string
    notes = db.Column(db.Text)
    treating_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointment = db.relationship('Appointment', backref='treatment')
    treating_doctor = db.relationship('Doctor')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    action = db.Column(db.String(200))
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)