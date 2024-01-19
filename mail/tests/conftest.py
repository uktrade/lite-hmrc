import pytest


@pytest.fixture(autouse=True)
def celery_sync(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_STORE_EAGER_RESULT = True
