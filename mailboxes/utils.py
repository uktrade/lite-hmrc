import logging
from email.headerregistry import Address
from email.parser import BytesHeaderParser
from email.utils import parseaddr
from poplib import error_proto
from typing import Callable, Iterator, Tuple

from django.conf import settings
from django.utils.functional import cached_property

from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import to_mail_message_dto
from mail_servers.servers import MailServer
from mailboxes.enums import MailReadStatuses
from mailboxes.models import MailboxConfig

logger = logging.getLogger(__name__)


def get_message_header(pop3_connection, msg_num):
    # retrieves the header information
    # 0 indicates the number of lines of message to be retrieved after the header
    _, msg_header, _ = pop3_connection.top(msg_num, 0)

    parser = BytesHeaderParser()
    header = parser.parsebytes(b"\n".join(msg_header))

    return header


def get_message_id(msg_header):
    _, message_id = parseaddr(str(msg_header["message-id"]))
    message_id = Address(addr_spec=message_id).username
    return message_id


def get_message_number(listing_message):
    listing_msg = listing_message.decode(settings.DEFAULT_ENCODING)
    msg_num, _, _ = listing_msg.partition(" ")
    return msg_num


def get_read_messages(mailbox_config):
    mail_read_statuses = mailbox_config.mail_read_statuses.filter(
        status__in=[
            MailReadStatuses.READ,
            MailReadStatuses.UNPROCESSABLE,
        ]
    )
    read_message_ids = set(mail_read_statuses.values_list("message_id", flat=True))
    return read_message_ids


def is_from_valid_sender(message, valid_addresses):
    _, from_address = parseaddr(str(message.message_header["From"]))
    logger.info("Found from address %s", from_address)
    valid_addresses = [address.replace("From: ", "") for address in valid_addresses]

    return from_address in valid_addresses


class MarkStatus:
    def __init__(self, message, read_status):
        self.message = message
        self.read_status = read_status

    def __call__(self, status):
        logger.info(
            "Marking message_id %s with message_num %s from %r as %s",
            self.message.message_id,
            self.message.message_number,
            self.read_status.mailbox,
            status,
        )
        self.read_status.status = status
        self.read_status.save()


class MailboxMessage:
    def __init__(self, pop3_connection, mailbox_config, message_number):
        self.pop3_connection = pop3_connection
        self.mailbox_config = mailbox_config
        self.message_number = message_number

    @cached_property
    def message_header(self):
        return get_message_header(self.pop3_connection, self.message_number)

    @cached_property
    def message_id(self):
        message_id = get_message_id(self.message_header)
        logger.info("Extracted Message-Id as %s for the message_num %s", message_id, self.message_number)
        return message_id

    @cached_property
    def mail_data(self):
        return self.pop3_connection.retr(self.message_number)

    @cached_property
    def binary_data(self):
        return b"\n".join(self.mail_data[1])


def get_messages(pop3_connection, mailbox_config, max_limit):
    _, mails, _ = pop3_connection.list()
    logger.debug(mails)
    mails = mails[-max_limit:]
    for mail in mails:
        message_number = get_message_number(mail)
        message = MailboxMessage(pop3_connection, mailbox_config, message_number)
        yield message


def is_read(message, read_messages):
    return message.message_id in read_messages


def get_message_dto(message):
    mail_data = message.mail_data
    logger.info(
        "Retrieved message_id %s with message_num %s from %s",
        message.message_id,
        message.message_number,
        message.mailbox_config,
    )

    mail_message = to_mail_message_dto(mail_data)

    return mail_message


def get_message_iterator(server: MailServer) -> Iterator[Tuple[EmailMessageDto, Callable]]:
    mailbox_config, _ = MailboxConfig.objects.get_or_create(username=server.user)
    read_messages = get_read_messages(mailbox_config)

    with server.connect_to_pop3() as pop3_connection:
        messages = get_messages(
            pop3_connection,
            mailbox_config,
            settings.INCOMING_EMAIL_CHECK_LIMIT,
        )

        for message in messages:
            if not is_from_valid_sender(message, [settings.SPIRE_FROM_ADDRESS, settings.HMRC_TO_DIT_REPLY_ADDRESS]):
                logger.warning(
                    "Found mail with message_num %s that is not from SPIRE (%s) or HMRC (%s), skipping ...",
                    message.message_number,
                    settings.SPIRE_FROM_ADDRESS,
                    settings.HMRC_TO_DIT_REPLY_ADDRESS,
                )
                continue

            if is_read(message, read_messages):
                logger.debug("Already read message %s", message.message_id)
                continue

            try:
                mail_data = message.binary_data
            except error_proto:
                logger.exception(
                    "Unable to RETR message num %s with Message-ID %s in %r",
                    message.message_number,
                    message.message_id,
                    message.mailbox_config,
                )
                continue

            logger.debug(
                "About to create or update mail_read_status for %s (%s)", message.message_id, message.message_number
            )

            # The `mail_data` really shouldn't be changing here so the `update` part seems redundant.
            # However, even if we read an email that we've read previously we get back some header information that
            # does change on every read e.g. a request id and some timestamps.
            # Given that the data is changing I chose to allow it to update each time to save the latest headers.
            read_status, created = mailbox_config.mail_read_statuses.update_or_create(
                message_id=message.message_id,
                message_num=message.message_number,
                defaults={
                    "mail_data": mail_data,
                },
            )
            logger.debug(
                "%s read_status for %s (%s)",
                "Created" if created else "Updated",
                message.message_id,
                message.message_number,
            )

            mark_status = MarkStatus(message, read_status)

            try:
                message_dto = get_message_dto(message)
            except ValueError:
                mark_status(MailReadStatuses.UNPROCESSABLE)
                logger.exception(
                    "Unable to convert message num %s with Message-Id %s to DTO in %r",
                    message.message_number,
                    message.message_id,
                    message.mailbox_config,
                )
                continue

            yield message_dto, mark_status
