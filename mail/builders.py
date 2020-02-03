from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from mail.dtos import EmailMessageDto


def build_text_message(sender, receiver, attachment):
    """build a message of `MineMultipart` with a text attachment and octet-stream payload.\n
        Todo: using a custom builder to build mail message
    """
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = attachment[0]
    filename = attachment[0]
    _attachment = attachment[1]
    payload = MIMEBase("application", "octet-stream")
    payload.set_payload(_attachment)
    payload.add_header("Content-Disposition", "attachment; filename= %s" % filename)
    msg.attach(payload)
    return msg


def _read_file(file_path):
    _file = open(file_path, "rb")
    return _file.read()


def build_mail_message_dto(sender, receiver, file_path):
    _subject = "ILBDOTI_test_CHIEF_licenceUpdate_1010_201901130300"
    return EmailMessageDto(
        run_number=1010,
        sender=sender,
        receiver=receiver,
        body="mail body",
        subject=_subject,
        attachment=[_subject, _read_file(file_path)],
        raw_data=build_text_message(sender, receiver, "mail body ..."),
    )
