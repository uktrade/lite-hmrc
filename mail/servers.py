import logging
import poplib
import smtplib
from contextlib import contextmanager

from django.conf import settings

from mail.auth import Authenticator

logger = logging.getLogger(__name__)


class MailServer:
    def __init__(
        self,
        auth: Authenticator,
        hostname: str = settings.EMAIL_HOSTNAME,
        pop3_port: int = settings.EMAIL_POP3_PORT,
    ):
        self.auth = auth
        self.pop3_port = pop3_port
        self.hostname = hostname

    def __eq__(self, other):
        if not isinstance(other, MailServer):
            return False

        return self.hostname == other.hostname and self.auth == other.auth and self.pop3_port == other.pop3_port

    @contextmanager
    def connect_to_pop3(self):
        logger.info("Establishing a pop3 connection to %s:%s", self.hostname, self.pop3_port)
        pop3_connection = poplib.POP3_SSL(self.hostname, self.pop3_port, timeout=60)
        logger.info("Pop3 connection established")
        try:
            self.auth.authenticate(pop3_connection)
            yield pop3_connection
        finally:
            pop3_connection.quit()

    @property
    def user(self):
        return self.auth.user


def get_smtp_connection():
    """Connect to an SMTP server, specified by environment variables."""
    # Note that EMAIL_HOSTNAME is not Django's EMAIL_HOST setting.
    hostname = settings.EMAIL_HOSTNAME
    port = str(settings.EMAIL_SMTP_PORT)
    use_tls = settings.EMAIL_USE_TLS
    username = settings.EMAIL_USER
    password = settings.EMAIL_PASSWORD
    logging.info("SMTP=%r:%r, TLS=%r, USERNAME=%r", hostname, port, use_tls, username)
    conn = smtplib.SMTP(hostname, port, timeout=60)

    if use_tls:
        conn.starttls()

    conn.login(username, password)

    return conn


def smtp_send(message):
    conn = get_smtp_connection()
    try:
        # Result is an empty dict on success.
        result = conn.send_message(message)
    finally:
        conn.quit()

    return result
