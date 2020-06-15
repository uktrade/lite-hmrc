import logging

from background_task import background
from django.db import transaction

from mail.enums import ReceptionStatusEnum, ReplyStatusEnum
from mail.libraries.builders import build_update_mail
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.routing_controller import update_mail, check_and_route_emails, send
from mail.models import LicencePayload, Mail

LICENCE_UPDATES_TASK_QUEUE = "licences_updates_queue"
MANAGE_INBOX_TASK_QUEUE = "manage_inbox_queue"


@background(queue=LICENCE_UPDATES_TASK_QUEUE, schedule=0)
def email_lite_licence_updates():
    if not _is_email_slot_free:
        logging.info("There is currently an update in progress or an email in flight")
        return

    with transaction.atomic():
        try:
            licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

            if not licences.exists():
                logging.info("There are currently no licences to send")
                return

            mail = build_update_mail(licences)
            mail_dto = build_request_mail_message_dto(mail)
            send(mail_dto)
            update_mail(mail, mail_dto)

            licences.update(is_processed=True)
            logging.info("Email successfully sent to HMRC")
        except Exception as exc:  # noqa
            logging.error(f"An unexpected error occurred when sending email to HMRC -> {type(exc).__name__}: {exc}")


@background(queue=MANAGE_INBOX_TASK_QUEUE, schedule=0)
def manage_inbox_queue():
    try:
        check_and_route_emails()
    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when managing inbox -> {type(exc).__name__}: {exc}")


def _is_email_slot_free() -> bool:
    last_email = Mail.objects.last()
    if last_email and (
        last_email.status != ReceptionStatusEnum.REPLY_SENT or ReplyStatusEnum.REJECTED in last_email.response_data
    ):
        return False
    return True
