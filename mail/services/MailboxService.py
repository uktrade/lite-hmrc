import logging
from mail.helpers import to_mail_message_dto
from mail.dtos import EmailMessageDto

log = logging.getLogger(__name__)


class MailboxService(object):
    def __init__(self):
        pass

    def send_email(self, smtpConn: object, message: object):
        smtpConn.send_message(message)

    def read_last_message(self, pop3Conn: object):
        resp, mails, octets = pop3Conn.list()
        # 'retr' returns a tripolet of response, ['line 1','line 2'], octets
        msgTripolet = pop3Conn.retr(len(mails))
        return to_mail_message_dto(msgTripolet[1])

    def handleRunnumber(self, mailMsgDto: EmailMessageDto):
        # todo
        pass
