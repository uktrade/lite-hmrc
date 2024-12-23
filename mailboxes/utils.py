import logging
import sys
from email.headerregistry import Address
from email.parser import BytesHeaderParser
from email.utils import parseaddr
from poplib import error_proto
from typing import Callable, Iterator, Tuple

from django.conf import settings

from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import to_mail_message_dto
from mail_servers.servers import MailServer
from mailboxes.enums import MailReadStatuses
from mailboxes.models import MailboxConfig

logger = logging.getLogger(__name__)


def get_message_number(listing_message):
    listing_msg = listing_message.decode(settings.DEFAULT_ENCODING)
    msg_num, _, _ = listing_msg.partition(" ")
    return msg_num


def get_message_header(pop3_connection, msg_num):
    # retrieves the header information
    # 0 indicates the number of lines of message to be retrieved after the header
    _, msg_header, _ = pop3_connection.top(msg_num, 0)

    parser = BytesHeaderParser()
    header = parser.parsebytes(b"".join(msg_header))

    return header


def get_message_id(msg_header):
    _, message_id = parseaddr(str(msg_header["message-id"]))
    message_id = Address(addr_spec=message_id).username
    return message_id


def get_read_messages(mailbox_config):
    mail_read_statuses = mailbox_config.mail_read_statuses.filter(
        status__in=[
            MailReadStatuses.READ,
            MailReadStatuses.UNPROCESSABLE,
        ]
    )
    read_message_ids = set(mail_read_statuses.values_list("message_id", flat=True))
    return read_message_ids


def get_unread_message_ids(pop3_connection, mailbox_config, incoming_email_check_limit=sys.maxsize):
    read_messages = get_read_messages(mailbox_config)
    logger.info("Number of messages READ/UNPROCESSABLE in %s are %s", mailbox_config.username, len(read_messages))

    _, mails, _ = pop3_connection.list()
    mails = mails[-incoming_email_check_limit:]
    for mail in mails:
        message_num = get_message_number(mail)
        message_header = get_message_header(pop3_connection, message_num)

        if not is_from_valid_sender(message_header, [settings.SPIRE_FROM_ADDRESS, settings.HMRC_TO_DIT_REPLY_ADDRESS]):
            logger.warning(
                "Found mail with message_num %s that is not from SPIRE (%s) or HMRC (%s), skipping ...",
                message_num,
                settings.SPIRE_FROM_ADDRESS,
                settings.HMRC_TO_DIT_REPLY_ADDRESS,
            )
            continue

        message_id = get_message_id(message_header)
        logger.info("Extracted Message-Id as %s for the message_num %s", message_id, message_num)
        if message_id in read_messages:
            continue

        yield message_id, message_num


def is_from_valid_sender(msg_header, valid_addresses):
    _, from_address = parseaddr(str(msg_header["From"]))
    valid_addresses = [address.replace("From: ", "") for address in valid_addresses]

    return from_address in valid_addresses


class MarkStatus:
    def __init__(self, message_id, message_num, read_status):
        self.message_id = message_id
        self.message_num = message_num
        self.read_status = read_status

    def __call__(self, status):
        logger.info(
            "Marking message_id %s with message_num %s from %r as %s",
            self.message_id,
            self.message_num,
            self.read_status.mailbox,
            status,
        )
        self.read_status.status = status
        self.read_status.save()


def get_message_iterator(server: MailServer) -> Iterator[Tuple[EmailMessageDto, Callable]]:
    mailbox_config, _ = MailboxConfig.objects.get_or_create(username=server.username)

    with server.connect_to_pop3() as pop3_connection:
        for message_id, message_num in get_unread_message_ids(
            pop3_connection,
            mailbox_config,
            settings.INCOMING_EMAIL_CHECK_LIMIT,
        ):
            read_status, _ = mailbox_config.mail_read_statuses.get_or_create(
                message_id=message_id,
                message_num=message_num,
            )

            mark_status = MarkStatus(message_id, message_num, read_status)

            try:
                m = pop3_connection.retr(message_num)
                logger.info(
                    "Retrieved message_id %s with message_num %s from %s",
                    message_id,
                    message_num,
                    read_status.mailbox,
                )
            except error_proto:
                logger.exception(
                    "Unable to RETR message num %s with Message-ID %s in %r",
                    message_num,
                    message_id,
                    mailbox_config,
                )
                continue

            try:
                mail_message = to_mail_message_dto(m)
            except ValueError:
                mark_status(MailReadStatuses.UNPROCESSABLE)
                logger.exception(
                    "Unable to convert message num %s with Message-Id %s to DTO in %r",
                    message_num,
                    message_id,
                    mailbox_config,
                )
                continue

            yield mail_message, mark_status
