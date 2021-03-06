import logging

from django.conf import settings
from django.utils import timezone

from conf.settings import SPIRE_ADDRESS
from mail.enums import ReceptionStatusEnum, SourceEnum, ExtractTypeEnum
from mail.libraries.builders import build_email_message
from mail.libraries.data_processors import (
    serialize_email_message,
    to_email_message_dto_from,
    lock_db_for_sending_transaction,
)
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import select_email_for_sending
from mail.libraries.mailbox_service import read_last_three_emails, send_email
from mail.models import Mail
from mail.servers import MailServer


def get_incoming_mailserver():
    return MailServer(
        hostname=settings.INCOMING_EMAIL_HOSTNAME,
        user=settings.INCOMING_EMAIL_USER,
        password=settings.INCOMING_EMAIL_PASSWORD,
        pop3_port=settings.INCOMING_EMAIL_POP3_PORT,
        smtp_port=settings.INCOMING_EMAIL_SMTP_PORT,
    )


def get_outgoing_mailserver():
    return MailServer(
        hostname=settings.OUTGOING_EMAIL_HOSTNAME,
        user=settings.OUTGOING_EMAIL_USER,
        password=settings.OUTGOING_EMAIL_PASSWORD,
        pop3_port=settings.OUTGOING_EMAIL_POP3_PORT,
        smtp_port=settings.OUTGOING_EMAIL_SMTP_PORT,
    )


def check_and_route_emails():
    logging.info("Checking for emails")
    server = get_incoming_mailserver()
    email_message_dtos = _get_email_message_dtos(server)
    if not email_message_dtos:
        logging.info("Emails considered invalid")
        return

    for email in email_message_dtos:
        serialize_email_message(email)

    logging.info("Finished checking for emails")

    mail = select_email_for_sending()  # Can return None in the event of in flight or no pending or no reply_received
    if mail:
        _collect_and_send(mail)


def update_mail(mail: Mail, mail_dto: EmailMessageDto):
    if mail.status == ReceptionStatusEnum.PENDING:
        mail.status = ReceptionStatusEnum.REPLY_PENDING
        # Update the mail object to record what we sent to destination
        mail.sent_filename = mail_dto.attachment[0]
        mail.sent_data = mail_dto.attachment[1]
        mail.sent_at = timezone.now()
    else:
        mail.status = ReceptionStatusEnum.REPLY_SENT
        # Update the mail object to record what we sent to source
        mail.sent_response_filename = mail_dto.attachment[0]
        mail.sent_response_data = mail_dto.attachment[1]

    mail.save()


def send(server: MailServer, email_message_dto: EmailMessageDto):
    smtp_connection = server.connect_to_smtp()
    send_email(smtp_connection, build_email_message(email_message_dto))
    server.quit_smtp_connection()


def _collect_and_send(mail: Mail):
    from mail.tasks import send_licence_updates_to_hmrc

    logging.info(f"Sending Mail [{mail.id}]")

    message_to_send_dto = to_email_message_dto_from(mail)
    is_locked_by_me = lock_db_for_sending_transaction(mail)

    if not is_locked_by_me:
        logging.info(f"Mail [{mail.id}] is being sent by another thread")

    if message_to_send_dto:
        if message_to_send_dto.receiver != SourceEnum.LITE and message_to_send_dto.subject:
            server = get_incoming_mailserver()
            send(server, message_to_send_dto)
            update_mail(mail, message_to_send_dto)

            logging.info(
                f"Mail [{mail.id}] routed from [{message_to_send_dto.sender}] to [{message_to_send_dto.receiver}]"
            )
        else:
            update_mail(mail, message_to_send_dto)

        if message_to_send_dto.receiver == SPIRE_ADDRESS and mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
            # Pick up any LITE licence updates once we send a licence update reply email to SPIRE
            # so LITE does not get locked out of the queue by SPIRE
            send_licence_updates_to_hmrc(schedule=0)  # noqa


def _get_email_message_dtos(server) -> list:
    pop3_connection = server.connect_to_pop3()
    emails = read_last_three_emails(pop3_connection)
    server.quit_pop3_connection()
    return emails
