from celery import shared_task
from mail.models import Mail

@shared_task
def debug_add(x, y):
    """
    Simple debug celery task to add two numbers.
    """
    return x + y


@shared_task
def debug_count_mail():
    """
    Simple debug celery task to count the number of mail in the app.
    """
    return Mail.objects.count()


@shared_task
def debug_exception():
    """
    Debug task which raises an exception.
    """
    raise Exception("debug_exception task")