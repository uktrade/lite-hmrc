from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


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
