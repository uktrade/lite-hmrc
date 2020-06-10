import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart

from background_task import background
from django.db import transaction

from conf.settings import HMRC_ADDRESS
from mail.builders import build_mail_message_dto
from mail.dtos import EmailMessageDto
from mail.enums import ReceptionStatusEnum, ReplyStatusEnum, SourceEnum
from mail.models import LicencePayload, Mail, LicenceUpdate
from mail.routing_controller import _update_mail_status
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.data_processors import serialize_email_message
from mail.services.helpers import build_email_message
from mail.services.lite_to_edifact_converter import licences_to_edifact

TASK_QUEUE = "email_licences_queue"


@background(queue=TASK_QUEUE, schedule=0)
def email_licences():
    with transaction.atomic():
        try:
            last_email = Mail.objects.last()
            if last_email and (
                last_email.status != ReceptionStatusEnum.REPLY_SENT or "rejected" in last_email.response_data
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
            now = datetime.now()
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

            smtp_conn = send_email(file_string, mail)
        except Exception as exc:  # noqa
            logging.error(f"An unexpected error occurred when sending email to HMRC -> {type(exc).__name__}: {exc}")
        else:
            licences.update(is_processed=True)
            logging.info("Email successfully sent to HMRC")
        finally:
            smtp_conn.quit()


def prepare_email(licences):
    payload_string = ""
    licences_with_errors = []

    multipart_msg = MIMEMultipart()
    multipart_msg["From"] = "icmshmrc@mailgate.trade.gov.uk"
    multipart_msg["To"] = "hmrc@mailgate.trade.gov.uk"
    multipart_msg["Subject"] = "testing"

    for licence in licences:
        try:
            payload_string += process_licence(licence)
        except Exception as exc:  # noqa
            logging.warning(f"An unexpected error occurred when processing licence -> {type(exc).__name__}: {exc}")
            licences_with_errors += licence.id

    return multipart_msg, licences_with_errors


def process_licence(licence):
    return str(licence)


def send_email(file_string, mail):
    server = MailServer()
    smtp_conn = server.connect_to_smtp()
    mailbox_service = MailboxService()
    mailbox_service.send_email(
        smtp_conn,
        build_email_message(
            build_mail_message_dto(
                sender="icmshmrc@mailgate.trade.gov.uk", receiver="hmrc@mailgate.trade.gov.uk", file_string=file_string,
            )
        ),
    )
    _update_mail_status(mail)
    return smtp_conn
