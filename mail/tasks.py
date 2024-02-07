import time

from smtplib import SMTPException
from contextlib import contextmanager
from django.core.cache import cache
from celery import shared_task
from celery.utils.log import get_task_logger

from mail.servers import smtp_send
from mail.libraries.builders import build_email_rejected_licence_message, build_email_message

logger = get_task_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180
LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


@contextmanager
def memcache_lock(lock_id, oid=None):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    status = cache.add(lock_id, "locked", LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.delete(lock_id)


@shared_task(bind=True, autoretry_for=(SMTPException,), max_retries=MAX_ATTEMPTS, retry_backoff=RETRY_BACKOFF)
def send_email_task(self, **kwargs):
    global_lock_id = "global_send_email_lock"

    with memcache_lock(global_lock_id) as acquired:
        if acquired:
            logger.info("Global lock acquired, sending email")
            try:
                if "message" in kwargs:
                    multipart_msg = build_email_message(kwargs["message"])
                elif "mail_response_subject" in kwargs and "mail_id" in kwargs:
                    multipart_msg = build_email_rejected_licence_message(
                        kwargs["mail_id"], kwargs["mail_response_subject"]
                    )
                else:
                    raise ValueError("Insufficient parameters to build email.")
                smtp_send(multipart_msg)
                logger.info("Successfully sent email.")
            except SMTPException as e:
                logger.error(f"Failed to send email: {e}")
                raise
        else:
            logger.info("Another send_email_task is currently in progress, will retry...")

            retry_delay = RETRY_BACKOFF * (2**self.request.retries)
            raise self.retry(countdown=retry_delay)
