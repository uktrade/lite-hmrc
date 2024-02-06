import os
import time

from hashlib import md5
from smtplib import SMTPException
from contextlib import contextmanager
from background_task import background
from django.conf import settings
from django.core.cache import cache
from celery import shared_task
from celery.utils.log import get_task_logger

from mail.servers import smtp_send
from mail.libraries.builders import build_email_rejected_licence_message, build_email_message

logger = get_task_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180
NOTIFY_USERS_TASK_QUEUE = "notify_users_queue"
LICENCE_DATA_TASK_QUEUE = "licences_updates_queue"


@background(queue="test_queue", schedule=0)
def emit_test_file():
    test_file_path = os.path.join(settings.BASE_DIR, ".background-tasks-is-ready")
    with open(test_file_path, "w") as test_file:
        test_file.write("OK")


LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def memcache_lock(lock_id, oid):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    status = cache.add(lock_id, oid, LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.delete(lock_id)


@shared_task(bind=True, autoretry_for=(SMTPException,), max_retries=MAX_ATTEMPTS, retry_backoff=RETRY_BACKOFF)
def send_email_task(self, **kwargs):
    if "message" in kwargs:
        multipart_msg = build_email_message(kwargs["message"])

    if "mail_response_subject" in kwargs:
        multipart_msg = build_email_rejected_licence_message(kwargs["mail_id"], kwargs["mail_response_subject"])

    hexdigest = md5(str(kwargs["mail_id"]).encode("utf-8")).hexdigest()
    lock_id = f"send_email-{hexdigest}"  # Construct a unique lock ID

    with memcache_lock(lock_id, "email_send_operation") as acquired:
        if acquired:
            logger.info("Lock acquired, sending email")
            try:
                smtp_send(multipart_msg)
                logger.info("Successfully notified users.")
            except SMTPException as e:
                logger.error(f"Failed to send email: {e}")
                raise
        else:
            logger.info("Another send_email_task is currently in progress")
