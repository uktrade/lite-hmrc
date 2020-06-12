import logging
from email.message import Message
from poplib import POP3_SSL
from smtplib import SMTP

from mail.models import Mail
from mail.services.helpers import to_mail_message_dto


class MailboxService(object):
    def send_email(self, smtp_connection: SMTP, message: Message):
        smtp_connection.send_message(message)

    def read_last_message(self, pop3_connection: POP3_SSL):
        _, mails, _ = pop3_connection.list()
        return to_mail_message_dto(pop3_connection.retr(len(mails)))

    def read_last_three_emails(self, pop3connection: POP3_SSL):
        _, mails, _ = pop3connection.list()
        emails = [
            pop3connection.retr(len(mails)),
            pop3connection.retr(len(mails) - 1),
            pop3connection.retr(len(mails) - 2),
        ]
        dtos = []
        for email in emails:
            dtos.append(to_mail_message_dto(email))

        return dtos

    @staticmethod
    def find_mail_of(extract_type: str, reception_status: str):
        try:
            mail = Mail.objects.get(status=reception_status, extract_type=extract_type)
            logging.debug("Found mail in [%s] of extract type [%s] " % (reception_status, extract_type))
            return mail
        except Mail.DoesNotExist as ex:
            raise ex("Can not find any mail in [%s] of extract type [%s]" % (reception_status, extract_type))
