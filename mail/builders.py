import base64
import io
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from mail.dtos import EmailMessageDto


def build_text_message(sender, receiver, body="Body_of_the_mail 2", file=None, file_path=None, file_string="Test file"):
    """build a message of `MineMultipart` with a text attachment and octet-stream payload.\n
        Todo: using a custom builder to build mail message
    """
    if file_path:
        file = open(file_path, "rb")
    elif file:
        file = file
    else:
        file = io.BytesIO(b"file_string")
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "ILBDOTI_test_CHIEF_usageData_9876_201901130300"
    body = body
    msg.attach(MIMEText(body, "plain"))
    filename = "ILBDOTI_test_CHIEF_usageData_9876_201901130300"
    attachment = file
    payload = MIMEBase("application", "octet-stream")
    payload.set_payload(attachment.read())
    payload.add_header("Content-Disposition", "attachment; filename= %s" % filename)
    msg.attach(payload)
    return msg


def _read_file(file_path):
    _file = open(file_path, "rb")
    return _file.read()


def build_mail_message_dto(sender, receiver, file_string="Test file"):
    _subject = "ILBDOTI_test_CHIEF_licenceUpdate_1010_201901130300"
    attachment = [_subject, file_string]
    return EmailMessageDto(
        run_number=1010,
        sender=sender,
        receiver=receiver,
        body="mail body",
        subject=_subject,
        attachment=attachment,
        raw_data=build_text_message(sender, receiver, "mail body ..."),
    )
