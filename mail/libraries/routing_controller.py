import logging

from mail.enums import ReceptionStatusEnum
from mail.libraries.data_processors import (
    serialize_email_message,
    to_email_message_dto_from,
    lock_db_for_sending_transaction,
)
from mail.libraries.helpers import build_email_message, select_email_for_sending
from mail.libraries.mailbox_service import read_last_three_emails, send_email
from mail.servers import MailServer


def check_and_route_emails():
    logging.info("Checking for emails")
    dtos = _read_last_message()
    if not dtos:
        logging.info("Last email considered invalid")
    for dto in dtos:
        serialize_email_message(dto)
    logging.info("Finished checking for emails")
    mail = select_email_for_sending()  # Can return None in the event of in flight or no pending or no reply_received
    if mail:
        return _collect_and_send(mail)


def update_mail_status(mail):
    if mail.status == ReceptionStatusEnum.PENDING:
        mail.status = ReceptionStatusEnum.REPLY_PENDING
    else:
        mail.status = ReceptionStatusEnum.REPLY_SENT
    mail.save()


def send(message_to_send_dto):
    server = MailServer()
    smtp_connection = server.connect_to_smtp()
    send_email(smtp_connection, build_email_message(message_to_send_dto))
    server.quit_smtp_connection()


def _collect_and_send(mail):
    logging.info("mail id being sent")
    message_to_send_dto = to_email_message_dto_from(mail)
    is_locked_by_me = lock_db_for_sending_transaction(mail)
    if not is_locked_by_me:
        logging.info("email being sent by another thread")
    if message_to_send_dto.receiver != "LITE":
        send(message_to_send_dto)
    update_mail_status(mail)
    logging.info(f"Email routed from {message_to_send_dto.sender} to {message_to_send_dto.receiver}")


def _read_last_message():
    server = MailServer()
    pop3_connection = server.connect_to_pop3()
    dtos = read_last_three_emails(pop3_connection)
    server.quit_pop3_connection()
    return dtos
