import logging
from mail.services.helpers import to_mail_message_dto

log = logging.getLogger(__name__)


class MailboxService(object):
    def __init__(self):
        pass

    def send_email(self, smtp_connection: object, message: object):
        smtp_connection.send_message(message)

    def read_last_message(self, pop3_connection: object):
        _, mails, _ = pop3_connection.list()
        return to_mail_message_dto(pop3_connection.retr(len(mails)))
