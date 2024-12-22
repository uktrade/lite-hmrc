import logging
from poplib import POP3_SSL, error_proto
from typing import Callable, Iterator, List, Tuple

from django.conf import settings

from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import to_mail_message_dto
from mail.models import Mail
from mailboxes.enums import MailReadStatuses
from mailboxes.models import MailboxConfig, MailReadStatus
from mailboxes.utils import get_message_header, get_message_id


def get_read_messages(mailbox_config):
    return [
        str(m.message_id)
        for m in MailReadStatus.objects.filter(
            mailbox=mailbox_config, status__in=[MailReadStatuses.READ, MailReadStatuses.UNPROCESSABLE]
        )
    ]


def get_message_iterator(pop3_connection: POP3_SSL, username: str) -> Iterator[Tuple[EmailMessageDto, Callable]]:
    mails: list
    _, mails, _ = pop3_connection.list()
    mailbox_config, _ = MailboxConfig.objects.get_or_create(username=username)
    incoming_email_check_limit = settings.INCOMING_EMAIL_CHECK_LIMIT

    # Check only the emails specified in the setting
    # Since we don't delete emails from these mailboxes the total number can be very high over a perio
    # and increases the processing time.
    # The mails is a list of message number and size - message number is an increasing value so the
    # latest emails will always be at the end.
    mail_message_ids = [
        get_message_id(*get_message_header(pop3_connection, m.decode(settings.DEFAULT_ENCODING)))
        for m in mails[-incoming_email_check_limit:]
    ]

    # these are mailbox message ids we've seen before
    read_messages = get_read_messages(mailbox_config)
    logging.info("Number of messages READ/UNPROCESSABLE in %s are %s", mailbox_config.username, len(read_messages))

    for message_id, message_num in mail_message_ids:
        # only return messages we haven't seen before
        if message_id is not None and message_id not in read_messages:
            read_status, _ = MailReadStatus.objects.get_or_create(
                message_id=message_id, message_num=message_num, mailbox=mailbox_config
            )

            def mark_status(status):
                """
                :param status: A choice from `MailReadStatuses.choices`
                """
                logging.info(
                    "Marking message_id %s with message_num %s from %s as %s",
                    message_id,
                    message_num,
                    read_status.mailbox.username,
                    status,
                )
                read_status.status = status
                read_status.save()

            try:
                m = pop3_connection.retr(message_num)
                logging.info(
                    "Retrieved message_id %s with message_num %s from %s",
                    message_id,
                    message_num,
                    read_status.mailbox.username,
                )
            except error_proto as err:
                logging.error(
                    "Unable to RETR message num %s with Message-ID %s in %s: %s",
                    message_num,
                    message_id,
                    mailbox_config,
                    err,
                    exc_info=True,
                )
                continue

            try:
                mail_message = to_mail_message_dto(m)
            except ValueError as ve:
                logging.error(
                    "Unable to convert message num %s with Message-Id %s to DTO in %s: %s",
                    message_num,
                    message_id,
                    mailbox_config,
                    ve,
                    exc_info=True,
                )
                mark_status(MailReadStatuses.UNPROCESSABLE)
                continue

            yield mail_message, mark_status


def find_mail_of(extract_types: List[str], reception_status: str) -> Mail or None:
    try:
        mail = Mail.objects.get(status=reception_status, extract_type__in=extract_types)
    except Mail.DoesNotExist:
        logging.warning("Can not find any mail in [%s] of extract type [%s]", reception_status, extract_types)
        return

    logging.info("Found mail in [%s] of extract type [%s]", reception_status, extract_types)
    return mail
