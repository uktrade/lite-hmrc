import poplib
import smtplib

from conf.settings import EMAIL_PASSWORD, EMAIL_HOSTNAME, EMAIL_USER


class MailServer(object):
    def __init__(
        self,
        hostname: str = EMAIL_HOSTNAME,
        user: str = EMAIL_USER,
        password: str = EMAIL_PASSWORD,
        pop3_port: int = 995,
        smtp_port: int = 587,
    ):
        self.smtp_port = smtp_port
        self.pop3_port = pop3_port
        self.password = password
        self.user = user
        self.hostname = hostname

    def connect_pop3(self):
        pop3 = poplib.POP3_SSL(self.hostname, str(self.pop3_port))
        pop3.user(self.user)
        pop3.pass_(self.password)
        return pop3

    def connect_smtp(self):
        smtp = smtplib.SMTP(self.hostname, str(self.smtp_port))
        smtp.starttls()
        smtp.login(self.user, self.password)
        return smtp
