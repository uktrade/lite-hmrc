import logging
import poplib
import smtplib
from contextlib import contextmanager

from django.conf import settings

from mail.auth import Authenticator


class MailServer(object):
    def __init__(
        self,
        auth: Authenticator,
        hostname: str = settings.EMAIL_HOSTNAME,
        pop3_port: int = settings.EMAIL_POP3_PORT,
    ):
        self.auth = auth
        self.pop3_port = pop3_port
        self.hostname = hostname
        self.pop3_connection = None

    def __eq__(self, other):
        if not isinstance(other, MailServer):
            return False

        return self.hostname == other.hostname and self.auth == other.auth and self.pop3_port == other.pop3_port

    def connect_to_pop3(self) -> poplib.POP3_SSL:
        logging.info("Establishing a pop3 connection to %s:%s", self.hostname, self.pop3_port)
        self.pop3_connection = poplib.POP3_SSL(self.hostname, self.pop3_port, timeout=60)
        self.auth.authenticate(self.pop3_connection)
        logging.info("pop3 connection established")
        return self.pop3_connection

    def quit_pop3_connection(self):
        self.pop3_connection.quit()

    @property
    def user(self):
        return self.auth.user


@contextmanager
def get_smtp_connection():
    """Connect to an SMTP server, specified by environment variables."""
    # Note that EMAIL_HOSTNAME is not Django's EMAIL_HOST setting.
    hostname = settings.EMAIL_HOSTNAME
    port = str(settings.EMAIL_SMTP_PORT)
    username = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD

    logging.info("SMTP=%r:%r, USERNAME=%r", hostname, port, username)
    with smtplib.SMTP(hostname, port, timeout=60) as conn:
        conn.starttls()
        conn.login(username, password)
        yield conn


def smtp_send(message):
    with get_smtp_connection() as conn:
        result = conn.send_message(message)

    return result
