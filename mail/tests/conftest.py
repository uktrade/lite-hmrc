import os
import pytest

from celery import Celery
from celery.schedules import crontab

from mail.celery_tasks import CELERY_SEND_LICENCE_UPDATES_TASK_NAME


@pytest.fixture(autouse=True)
def celery_app():
    # Setup the celery worker to run in process for tests
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
    celeryapp = Celery("lite-hmrc")
    celeryapp.config_from_object("django.conf:settings", namespace="CELERY_TEST")

    celeryapp.autodiscover_tasks(related_name="celery_tasks")
    celeryapp.conf["CELERY_ALWAYS_EAGER"] = True
    celeryapp.conf["CELERY_TASK_STORE_EAGER_RESULT"] = True

    celeryapp.conf["beat_schedule"] = {
        # send licence details to hmrc, periodic task every 10min
        CELERY_SEND_LICENCE_UPDATES_TASK_NAME: {
            "task": CELERY_SEND_LICENCE_UPDATES_TASK_NAME,
            "schedule": crontab(minute="*/10"),
        },
    }

    # Make this the default app for all threads
    celeryapp.set_default()

    return celeryapp
