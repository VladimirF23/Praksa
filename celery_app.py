# celery_app.py
from gevent import monkey
monkey.patch_all()

#u principu broker za poruke tj za koje user_id-eve treba uzme je reddis a ne rabitmq, ili kafka sto je normalno
from celery import Celery
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()
redis_password = os.getenv("REDIS_PASSWORD")

celery = Celery(
    "Backend.Service.tasks",  # full module path
    broker=f"redis://:{redis_password}@redis-praksa:6379/0",
    backend=f"redis://:{redis_password}@redis-praksa:6379/0"
)

#  ADD CELERY_IMPORTS TO EXPLICITLY LOAD THE TASK MODULE
celery.conf.update(
    # Specify the module where your tasks are defined
    imports=('Backend.Service.tasks',), 
)

celery.conf.beat_schedule = {
    "live_metering_job": {
        # Ensure this task name matches the one registered by the import
        "task": "Backend.Service.tasks.update_all_users_live_data", 
        "schedule": timedelta(seconds=5),
    },
}
celery.conf.timezone = 'UTC'
