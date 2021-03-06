import logging
import poplib
import smtplib

from conf.settings import (
    EMAIL_PASSWORD,
    EMAIL_HOSTNAME,
    EMAIL_USER,
    EMAIL_POP3_PORT,
    EMAIL_SMTP_PORT,
)


class MailServer(object):
    def __init__(
        self,
        hostname: str = EMAIL_HOSTNAME,
        user: str = EMAIL_USER,
        password: str = EMAIL_PASSWORD,
        pop3_port: int = EMAIL_POP3_PORT,
        smtp_port: int = EMAIL_SMTP_PORT,
    ):
        self.smtp_port = smtp_port
        self.pop3_port = pop3_port
        self.password = password
        self.user = user
        self.hostname = hostname
        self.pop3_connection = None
        self.smtp_connection = None

    def connect_to_pop3(self) -> poplib.POP3_SSL:
        logging.info("establishing a pop3 connection...")
        self.pop3_connection = poplib.POP3_SSL(self.hostname, self.pop3_port, timeout=60)
        self.pop3_connection.user(self.user)
        self.pop3_connection.pass_(self.password)
        logging.info("pop3 connection established")
        return self.pop3_connection

    def quit_pop3_connection(self):
        self.pop3_connection.quit()

    def connect_to_smtp(self) -> smtplib.SMTP:
        logging.info("establishing an smtp connection...")
        self.smtp_connection = smtplib.SMTP(self.hostname, str(self.smtp_port), timeout=60)
        logging.info("smtp connection established")
        logging.info("starting tls...")
        self.smtp_connection.starttls()
        logging.info("tls started")
        logging.info("logging in...")
        self.smtp_connection.login(self.user, self.password)
        logging.info("logged in")
        return self.smtp_connection

    def quit_smtp_connection(self):
        self.smtp_connection.quit()
