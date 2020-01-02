import poplib
import smtplib

MAIL_SERVER = "localhost"
MAIL_SERVER_USER = "test18"
MAIL_SERVER_PASS = "password"
SMTP_PORT = 587
POP3_PORT = 995


class MailServer(object):
    def __init__(self):
        pass

    def send_email(self, sender_email, receiver_email, message):
        server = smtplib.SMTP(MAIL_SERVER, str(SMTP_PORT))
        server.starttls()
        server.login(MAIL_SERVER_USER, MAIL_SERVER_PASS)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()

    def read_email(self):
        server = poplib.POP3_SSL(MAIL_SERVER, str(POP3_PORT))
        server.user(MAIL_SERVER_USER)
        server.pass_(MAIL_SERVER_PASS)
        msg = self._process_contents(server)
        server.quit()
        return msg

    def _process_contents(self, server):
        msg_obj = server.list()
        output = str(msg_obj) + "\n" + "\n"
        output += str(server.retr(len(msg_obj[1])))
        return output
