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
        parser.add_argument("--edi_file_path", type=str, nargs="?", help="Path to local EDI file that should be sent")
        parser.add_argument("--edi_file_name", type=str, nargs="?", help="Filename for edi data to resend")
        parser.add_argument("--sender_email", type=str, nargs="?", help="Email for the sender")
        parser.add_argument("--sender_email_password", type=str, nargs="?", help="Password for the sender")
        parser.add_argument("--sender_mailbox_url", type=str, nargs="?", help="URL for sender mailbox")
        parser.add_argument(
            "--target_email", type=str, nargs="?", help="Email for the lite-hmrc mailbox to send this to"
        )

        parser.add_argument("--dry_run", help="Is it a test run?", action="store_true")

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
