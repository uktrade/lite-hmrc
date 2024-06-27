import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

from dbt_copilot_python.celery_health_check import healthcheck

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

# Also allow messages that are serialized/deserialized using pickle
app.conf.accept_content = ["json", "pickle"]

# Define any regular scheduled tasks

manage_inbox_interval = int(settings.INBOX_POLL_INTERVAL // 60)
licence_update_task_interval_min = int(settings.LITE_LICENCE_DATA_POLL_INTERVAL // 60)
app.conf.beat_schedule = {
    # send licence details to hmrc, periodic task every 10min
    "mail.celery_tasks.send_licence_details_to_hmrc": {
        "task": "mail.celery_tasks.send_licence_details_to_hmrc",
        "schedule": crontab(minute=f"*/{licence_update_task_interval_min}"),
    },
    "mail.celery_tasks.manage_inbox": {
        "task": "mail.celery_tasks.manage_inbox",
        "schedule": crontab(minute=f"*/{manage_inbox_interval}"),
    },
}

if settings.IS_ENV_DBT_PLATFORM:
    celery_app = healthcheck.setup(app)
