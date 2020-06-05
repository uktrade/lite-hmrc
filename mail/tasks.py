import logging
from email.mime.multipart import MIMEMultipart

from background_task import background
from django.db import transaction

from mail.builders import build_mail_message_dto
from mail.models import LicencePayload
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.helpers import build_email_message
from mail.services.lite_to_edifact_converter import licences_to_edifact

TASK_QUEUE = "email_licences_queue"


@background(queue=TASK_QUEUE, schedule=0)
def email_licences():
    with transaction.atomic():
        licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

        file_string = licences_to_edifact(licences)

        try:
            smtp_conn = send_email(file_string)
        except Exception as exc:  # noqa
            print(exc)
            logging.error(f"An unexpected error occurred when sending email -> {type(exc).__name__}: {exc}")
        else:
            licences.update(is_processed=True)
        smtp_conn.quit()


def prepare_email(licences):
    payload_string = ""
    licences_with_errors = []

    multipart_msg = MIMEMultipart()
    multipart_msg["From"] = "icmshmrc@mailgate.trade.gov.uk"
    multipart_msg["To"] = "hmrc@mailgate.trade.gov.uk"
    multipart_msg["Subject"] = "Hahahaha"

    for licence in licences:
        try:
            payload_string += process_licence(licence)
        except Exception as exc:  # noqa
            logging.warning(f"An unexpected error occurred when processing licence -> {type(exc).__name__}: {exc}")
            licences_with_errors += licence.id

    # payload_file = io.StringIO(payload_string)
    # payload = MIMEApplication(payload_file)

    # payload.add_header(
    #     "Content-Disposition", "attachment; filename= %s" % "test-filename",
    # )
    # multipart_msg.attach(payload)

    return multipart_msg, licences_with_errors


def process_licence(licence):
    return str(licence)


def send_email(file_string):
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
    return smtp_conn
