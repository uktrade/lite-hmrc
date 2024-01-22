import os
import pytest

from celery import Celery


@pytest.fixture(autouse=True)
def celery_app():
    # Setup the celery worker to run in process for tests
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")
    celeryapp = Celery("lite-hmrc")
    celeryapp.autodiscover_tasks(related_name="celery_tasks")
    celeryapp.conf.update(CELERY_ALWAYS_EAGER=True)
    celeryapp.conf.update(CELERY_TASK_STORE_EAGER_RESULT=True)
    return celeryapp
