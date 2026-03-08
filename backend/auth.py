# auth.py
from flask import Blueprint, request, jsonify
from extensions import db
from models import User, Patient, Doctor
from utils import hash_password, verify_password, gen_identifier, audit
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta # UPDATED: Added datetime for parsing the DOB
import json

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    full_name = data.get('full_name')
    email = data.get('email')
    
    # NEW: Catch the extra patient fields sent from Vue
    contact = data.get('contact')
    gender = data.get('gender')
    dob_str = data.get('dob')

    if not username or not password:
        return jsonify({'msg':'username and password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'msg':'username already exists'}), 400

    try:
        # 1. Create the User account
        user = User(
            username=username,
            password_hash=hash_password(password),
            role='patient',
            full_name=full_name,
            email=email
        )
        db.session.add(user)
        db.session.flush() # Flushes to the database to grab the new user.id

        # 2. Parse the Date of Birth string into a Python Date object safely
        parsed_dob = None
        if dob_str:
            parsed_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

        # 3. Create patient profile mapping all the new fields
        patient = Patient(
            user_id=user.id, 
            patient_identifier=gen_identifier('PAT'),
            contact=contact,
            gender=gender,
            dob=parsed_dob
        )
        db.session.add(patient)
        
        # Finalize the save
        db.session.commit()

        # Non-critical audit log
        try:
            audit(user.id, 'register', {'username': username})
        except Exception:
            pass
            
        return jsonify({'msg':'registered'}), 201

    except Exception as e:
        db.session.rollback() # Undo the registration if something fails!
        print(f"Registration Error: {e}")
        return jsonify({'msg':'An error occurred during registration'}), 500


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'msg':'username and password required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({'msg':'invalid credentials'}), 401

    additional_claims = {'role': user.role, 'uid': user.id}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    return jsonify({'access_token': access_token, 'role': user.role, 'user_id': user.id})