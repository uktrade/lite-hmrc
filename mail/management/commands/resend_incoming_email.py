import smtplib
import ssl
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
    Resend EDI data to a lite-hmrc mailbox for the purposes of testing a lite-hmrc
    environment.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--edi_file_path",
            type=str,
            nargs="?",
            help="Path to local EDI file that should be sent. Contents can be sourced from a valid Mail ORM record on the lite-hmrc environment; "
            "Mail.edi_data.",
        )
        parser.add_argument(
            "--edi_file_name",
            type=str,
            nargs="?",
            help="Filename for edi data to resend. Can be sourced from a valid Mail ORM record on the lite-hmrc environment; Mail.edi_filename",
        )
        parser.add_argument(
            "--sender_email",
            type=str,
            nargs="?",
            help="Email for the sender.  This could be settings.HMRC_ADDRESS if re-sending an email that HMRC would send us",
        )
        parser.add_argument(
            "--sender_email_password",
            type=str,
            nargs="?",
            help="Password for the sender.  Found on Passman 'LITE / SPIRE / ICMS  - 0365/Exchange emails'",
        )
        parser.add_argument(
            "--sender_mailbox_url",
            type=str,
            nargs="?",
            help="URL for sender mailbox.  Found on Passman 'LITE / SPIRE / ICMS  - 0365/Exchange emails'",
        )
        parser.add_argument(
            "--target_email",
            type=str,
            nargs="?",
            help="Email for the lite-hmrc mailbox to send this to. e.g. settings.HMRC_TO_DIT_EMAIL_USER",
        )

    def handle(self, *args, **options):

        msg = MIMEMultipart()
        msg["Subject"] = options["edi_file_name"]
        msg["From"] = options["sender_email"]
        msg["To"] = options["target_email"]

        part = MIMEBase("application", "octet-stream")
        edi_data = ""
        with open(options["edi_file_path"], "rb") as f:
            edi_data = f.read()
        part.set_payload(edi_data)
        encode_base64(part)

        part.add_header("Content-Disposition", f'attachment; filename="{options["edi_file_name"]}"')

        msg.attach(part)

        context = ssl.create_default_context()
        server = smtplib.SMTP(options["sender_mailbox_url"], 587)
        server.starttls(context=context)
        server.login(options["sender_email"], options["sender_email_password"])
        server.sendmail(options["sender_email"], options["target_email"], msg.as_string())
