import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from background_task import background

from conf.settings import (
    EMAIL_USER,
    NOTIFY_USERS,
)
from mail.libraries.mailbox_service import send_email
from mail.servers import MailServer

NOTIFY_USERS_TASK_QUEUE = "notify_users_queue"


@background(queue=NOTIFY_USERS_TASK_QUEUE, schedule=0)
def notify_users_of_rejected_mail(mail_id, mail_response_date):
    logging.info(f"Notifying users of rejected Mail [{mail_id}, {mail_response_date}]")

    try:
        multipart_msg = MIMEMultipart()
        multipart_msg["From"] = EMAIL_USER
        multipart_msg["To"] = ",".join(NOTIFY_USERS)
        multipart_msg["Subject"] = f"Mail rejected"
        body = MIMEText(f"Mail [{mail_id}] received at [{mail_response_date}] was rejected")
        multipart_msg.attach(body)

        server = MailServer()
        smtp_connection = server.connect_to_smtp()
        send_email(smtp_connection, multipart_msg)
        server.quit_smtp_connection()
    except Exception as exc:  # noqa
        error_message = (
            f"An unexpected error occurred when notifying users of rejected Mail "
            f"[{mail_id}, {mail_response_date}] -> {type(exc).__name__}: {exc}"
        )

        # Raise an exception
        # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
        raise Exception(error_message)
    else:
        logging.info(f"Successfully notified users of rejected Mail [{mail_id}, {mail_response_date}]")
