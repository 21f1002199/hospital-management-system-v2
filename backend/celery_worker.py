# celery_worker.py
import os
from celery import Celery
from celery.schedules import crontab
from app import create_app

# 1. Create an instance of the Flask app for Celery to use
app = create_app()

# 2. Define Redis URL
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# 3. Define the factory
def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=redis_url,
        backend=redis_url
    )
    
    # This ensures tasks run inside the Flask App Context so they can talk to the Database
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# 4. Initialize Celery and set it as the boss
celery_app = make_celery(app)
celery_app.set_default()

# 5. Import the tasks AFTER creating and setting the default celery app
import tasks 

# ==========================================
# SCHEDULED JOBS (CELERY BEAT CONFIG)
# ==========================================
celery_app.conf.timezone = 'Asia/Kolkata' # Locked to IST

celery_app.conf.beat_schedule = {
    'send-daily-reminders-every-morning': {
        'task': 'tasks.daily_reminders',
        # Triggers every day exactly at 8:00 AM IST
        'schedule': crontab(hour=8, minute=00), 
    },
    'send-monthly-doctor-reports': {
        'task': 'tasks.monthly_doctor_report',
        # Triggers at 12:00 AM on the 1st day of every month
        'schedule': crontab(day_of_month='1', hour=00, minute=00), 
    },
}