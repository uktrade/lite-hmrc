class MailboxService(object):
    def __init__(self):
        pass

    def send_email(self, smtpConn: object, message: object):
        smtpConn.send_message(message)

    def read_last_message(self, pop3Conn: object):
        msg_obj = pop3Conn.list()
        return str(pop3Conn.retr(len(msg_obj[1])))
