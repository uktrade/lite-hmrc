import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import shared_task
from django.conf import settings

from mail.servers import smtp_send

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


# Notify Users of Rejected Mail
@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def notify_users_of_rejected_mail(mail_id, mail_response_date):
    """If a rejected email is found, this task notifies users of the rejection"""

    logger.info("Notifying users of rejected Mail [%s, %s]", mail_id, mail_response_date)

    try:
        multipart_msg = MIMEMultipart()
        multipart_msg["From"] = settings.EMAIL_USER
        multipart_msg["To"] = ",".join(settings.NOTIFY_USERS)
        multipart_msg["Subject"] = "Mail rejected"
        body = MIMEText(f"Mail [{mail_id}] received at [{mail_response_date}] was rejected")
        multipart_msg.attach(body)

        smtp_send(multipart_msg)
    except Exception as exc:  # noqa
        error_message = (
            f"An unexpected error occurred when notifying users of rejected Mail "
            f"[{mail_id}, {mail_response_date}] -> {type(exc).__name__}: {exc}"
        )

        # Raise an exception
        # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
        raise Exception(error_message)
    else:
        logger.info("Successfully notified users of rejected Mail [%s, %s]", mail_id, mail_response_date)
