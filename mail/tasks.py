import io
import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

from background_task import background
from django.db import transaction

from mail.models import LicencePayload
from mail.services.MailboxService import MailboxService

TASK_QUEUE = "email_licences_queue"


@background(queue=TASK_QUEUE, schedule=0)
def email_licences():
    with transaction.atomic():
        licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

        email, licences_with_errors = prepare_email(licences)

        if licences_with_errors:
            logging.warning(f"The following licences could not be processed: {licences_with_errors}")

        try:
            MailboxService().send_email(None, email)
        except Exception as exc:  # noqa
            logging.error(f"An unexpected error occurred when sending email -> {type(exc).__name__}: {exc}")
        else:
            licences.exclude(id__in=licences_with_errors).update(is_processed=True)


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
