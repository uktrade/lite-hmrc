from mail.servers import MailServer
import mail.services.MailboxService


def reademail_job():
    server = MailServer()
    last_message = server.read_email()
    # TODO: Some logic which does the following:
    #   - reads the 'last_message'
    #   - Saves the message in a table (against a sent message if it is a reply)
    #   - Reads the sender
    #   - Records run number and if required and adjusts run number
    #   - calls build_and_send_message with new receiver address (keep the sender)
    #   - records the send message in table
    mailBoxService = mailBoxService()
