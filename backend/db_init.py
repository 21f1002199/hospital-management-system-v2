# db_init.py
from app import create_app
from extensions import db
from models import User
from utils import hash_password
import os

def init_db():
    app = create_app()
    with app.app_context():
        # 1. NUKE THE EXISTING TABLES (Clears all ghost data and old structures)
        db.drop_all() 
        print("Old database tables dropped.")

        # 2. REBUILD THEM FRESH (Now includes your new contact column)
        db.create_all()
        print("New database tables created.")

        # Create default admin if not exists
        admin_username = os.environ.get('HMS_ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('HMS_ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('HMS_ADMIN_PASSWORD', 'AdminPass123!')

        existing = User.query.filter_by(username=admin_username).first()
        if not existing:
            admin = User(
                username=admin_username,
                password_hash=hash_password(admin_password),
                role='admin',
                full_name='Hospital Admin',
                email=admin_email
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Created admin user: {admin_username} / {admin_password}")
        else:
            print("Admin already exists:", admin_username)

if __name__ == '__main__':
    init_db()