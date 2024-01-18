from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException

from mail.servers import smtp_send

logger = get_task_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


# Notify Users of Rejected Mail
@shared_task(
    autoretry_for=(SMTPException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def notify_users_of_rejected_mail(mail_id, mail_response_subject):
    """If a reply is received with rejected licences this task notifies users of the rejection"""

    logger.info("Notifying users of rejected licences found in mail with subject %s", mail_response_subject)

    try:
        multipart_msg = MIMEMultipart()
        multipart_msg["From"] = settings.EMAIL_USER
        multipart_msg["To"] = ",".join(settings.NOTIFY_USERS)
        multipart_msg["Subject"] = "Mail rejected"
        body = MIMEText(f"Mail [{mail_id}] with subject [{mail_response_subject}] has rejected licences")
        multipart_msg.attach(body)

        smtp_send(multipart_msg)
    except SMTPException as exc:  # noqa
        error_message = (
            f"An unexpected error occurred when notifying users of rejected licences "
            f"[Id: {mail_id}, subject: {mail_response_subject}] -> {type(exc).__name__}: {exc}"
        )

        # Raise an exception
        # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
        raise exc(error_message)

    logger.info("Successfully notified users of rejected licences found in mail with subject %s", mail_response_subject)
