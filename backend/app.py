# app.py
from flask import Flask, jsonify
from config import Config
from extensions import db, migrate, jwt, cache, mail
from auth import bp as auth_bp
from routes.admin import bp as admin_bp
from routes.doctor import bp as doctor_bp
from routes.patient import bp as patient_bp
from flask_cors import CORS
import logging

import os
from celery import Celery 

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Give Flask the direct map to the Redis Backend ---
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    flask_celery = Celery(app.name, broker=redis_url, backend=redis_url)
    flask_celery.set_default()
    # --------------------------------------------------------------------

    # extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    CORS(app)

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)

    @app.route('/health')
    def health():
        return jsonify({'status':'ok'})

    # simple logging
    logging.basicConfig(level=logging.INFO)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(port=5000, debug=True)