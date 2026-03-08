# utils.py
from passlib.hash import pbkdf2_sha256
import uuid
import json
from datetime import datetime
from extensions import db
from models import AuditLog

def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)

def verify_password(password: str, hash_: str) -> bool:
    return pbkdf2_sha256.verify(password, hash_)

def gen_identifier(prefix='ID'):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def audit(user_id, action, details=None):
    if details is None:
        details = {}
    log = AuditLog(user_id=user_id, action=action, details=json.dumps(details))
    db.session.add(log)
    db.session.commit()