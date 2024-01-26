from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTPException

from mail.enums import ReceptionStatusEnum, SourceEnum
from mail.libraries.builders import build_licence_data_mail
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.routing_controller import send, update_mail
from mail.models import LicencePayload, Mail
from mail.servers import smtp_send


logger = get_task_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180
CELERY_SEND_LICENCE_UPDATES_TASK_NAME = "mail.celery_tasks.send_licence_details_to_hmrc"


# Notify Users of Rejected Mail
@shared_task(
    autoretry_for=(SMTPException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def notify_users_of_rejected_licences(mail_id, mail_response_subject):
    """If a reply is received with rejected licences this task notifies users of the rejection"""

    logger.info("Notifying users of rejected licences found in mail with subject %s", mail_response_subject)

    try:
        multipart_msg = MIMEMultipart()
        multipart_msg["From"] = settings.EMAIL_USER
        multipart_msg["To"] = ",".join(settings.NOTIFY_USERS)
        multipart_msg["Subject"] = "Licence rejected by HMRC"
        body = MIMEText(f"Mail (Id: {mail_id}) with subject {mail_response_subject} has rejected licences")
        multipart_msg.attach(body)

        smtp_send(multipart_msg)

    except SMTPException:  # noqa
        logger.exception(
            "An unexpected error occurred when notifying users of rejected licences, Mail Id: %s, subject: %s",
            mail_id,
            mail_response_subject,
        )
        raise

    logger.info("Successfully notified users of rejected licences found in mail with subject %s", mail_response_subject)


@shared_task(
    autoretry_for=(SMTPException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def send_licence_details_to_hmrc():
    """Sends LITE issued licence details to HMRC"""

    logger.info(f"Sending LITE issued licence updates to HMRC")

    # We can only send next message after current message is fully processed.
    # Once it is fully processed it's status is marked as 'reply_sent'.
    #
    # So check if there are any in-progress messages before we proceed.
    if Mail.objects.exclude(status=ReceptionStatusEnum.REPLY_SENT).count():
        logger.info(
            "Currently we are either waiting for a reply or next one is ready to be sent out,\n"
            "so we cannot send this update yet and need to wait till that is completed."
        )
        return

    try:
        with transaction.atomic():
            # It is unlikely LicencePayload is being updated concurrently so even though it
            # blocking it is not going to be an issue to acquire lock
            licences = LicencePayload.objects.filter(is_processed=False).select_for_update()
            if not licences.exists():
                logger.info("There are currently no licences in the payload to send to HMRC")
                return

            mail = build_licence_data_mail(licences, SourceEnum.LITE)
            mail_dto = build_request_mail_message_dto(mail)
            licence_references = [licence.reference for licence in licences]
            logger.info(
                "Created licenceData mail with subject %s for licences [%s]", mail_dto.subject, licence_references
            )

            send(mail_dto)
            update_mail(mail, mail_dto)

            # Mark the payloads as processed
            licences.update(is_processed=True)
            logger.info("Licence references [%s] marked as processed", licence_references)

    except SMTPException:
        logger.exception("An unexpected error occurred when sending LITE licence updates to HMRC -> %s")
        raise

    logger.info(
        "Successfully sent LITE issued licence (%s) updates in mail (%s) to HMRC", licence_references, mail.edi_filename
    )
    return True
