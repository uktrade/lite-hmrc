import logging

from background_task import background
from django.db import transaction
from django.utils import timezone

from conf.settings import HMRC_ADDRESS, EMAIL_USER
from mail.builders import build_mail_message_dto
from mail.dtos import EmailMessageDto
from mail.enums import ReceptionStatusEnum, ReplyStatusEnum, SourceEnum
from mail.models import LicencePayload, Mail, LicenceUpdate
from mail.routing_controller import update_mail_status, check_and_route_emails, send
from mail.services.data_processors import serialize_email_message
from mail.services.lite_to_edifact_converter import licences_to_edifact

LICENCE_UPDATES_TASK_QUEUE = "licences_updates_queue"
MANAGE_TASK_QUEUE = "manage_inbox_queue"


@background(queue=LICENCE_UPDATES_TASK_QUEUE, schedule=0)
def email_lite_licence_updates():
    with transaction.atomic():
        try:
            last_email = Mail.objects.last()
            if last_email and (
                last_email.status != ReceptionStatusEnum.REPLY_SENT
                or ReplyStatusEnum.REJECTED in last_email.response_data
            ):
                logging.info("There is currently an update in progress or an email in flight")
                return

            logging.info("Fetching licences to send to HRMC")
            licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

            if not licences.exists():
                logging.info("There are currently no licences to send")
                return

            file_string = licences_to_edifact(licences)

            last_lite_update = LicenceUpdate.objects.filter(source=SourceEnum.LITE).last()
            last_lite_run_number = last_lite_update.source_run_number + 1 if last_lite_update else 1

            now = timezone.now()
            file_name = (
                "ILBDOTI_live_CHIEF_licenceUpdate_"
                + str(last_lite_run_number + 1)
                + "_"
                + "{:04d}{:02d}{:02d}{:02d}{:02d}".format(now.year, now.month, now.day, now.hour, now.minute)
            )
            mock_dto = EmailMessageDto(
                subject="licenceUpdate",
                raw_data="See licence payloads",
                sender="LITE",
                run_number=last_lite_run_number + 1,
                attachment=[file_name, file_string],
                receiver=HMRC_ADDRESS,
                body=None,
            )
            mail = serialize_email_message(mock_dto)

            _send_email(file_string, mail)
        except Exception as exc:  # noqa
            logging.error(f"An unexpected error occurred when sending email to HMRC -> {type(exc).__name__}: {exc}")
        else:
            licences.update(is_processed=True)
            logging.info("Email successfully sent to HMRC")


@background(queue=MANAGE_TASK_QUEUE, schedule=0)
def manage_inbox_queue():
    try:
        check_and_route_emails()
    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when managing inbox -> {type(exc).__name__}: {exc}")


def _send_email(file_string, mail):
    message_to_send_dto = build_mail_message_dto(sender=EMAIL_USER, receiver=HMRC_ADDRESS, file_string=file_string)
    send(message_to_send_dto)
    update_mail_status(mail)
