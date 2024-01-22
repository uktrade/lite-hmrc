import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

app = Celery("lite-hmrc")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load celery_tasks.py modules from all registered Django apps.
app.autodiscover_tasks(related_name="celery_tasks")
app.autodiscover_tasks(["core"], related_name="celery_tasks")

# Define any regular scheduled tasks
app.conf.beat_schedule = {
    "send licence details to hmrc, periodic task every 10min": {
        "task": "mail.celery_tasks.send_licence_details_to_hmrc",
        "schedule": crontab(minute="*/10"),
    },
}
