import io
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.utils import timezone

from mail.enums import SourceEnum
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.lite_to_edifact_converter import licences_to_edifact
from mail.models import LicenceUpdate


def build_licence_updates_file(licences, run_number):

    now = timezone.now()
    file_name = (
        "ILBDOTI_live_CHIEF_licenceUpdate_"
        + str(run_number)
        + "_"
        + "{:04d}{:02d}{:02d}{:02d}{:02d}".format(now.year, now.month, now.day, now.hour, now.minute)
    )

    file_content = licences_to_edifact(licences)

    return file_name, file_content


# def build_text_message(sender, receiver, body="Body_of_the_mail 2", file=None, file_path=None):
#     """build a message of `MineMultipart` with a text attachment and octet-stream payload.\n
#         Todo: using a custom builder to build mail message
#     """
#     if file_path:
#         attachment = open(file_path, "rb")
#     elif file:
#         attachment = file
#     else:
#         attachment = io.BytesIO(b"file_string")
#     msg = MIMEMultipart()
#     msg["From"] = sender
#     msg["To"] = receiver
#     msg["Subject"] = "ILBDOTI_test_CHIEF_usageData_9876_201901130300"
#     body = body
#     msg.attach(MIMEText(body, "plain"))
#     filename = "ILBDOTI_test_CHIEF_usageData_9876_201901130300"
#     payload = MIMEBase("application", "octet-stream")
#     payload.set_payload(attachment.read())
#     payload.add_header("Content-Disposition", "attachment; filename= %s" % filename)
#     msg.attach(payload)
#     return msg
