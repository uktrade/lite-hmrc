import logging
from poplib import POP3_SSL, error_proto
from typing import Callable, Iterator, List, Tuple

from django.conf import settings

from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import to_mail_message_dto
from mail.models import Mail
from mailboxes.enums import MailReadStatuses
from mailboxes.models import MailboxConfig
from mailboxes.utils import get_unread_message_ids

logger = logging.getLogger(__name__)


def get_message_iterator(pop3_connection: POP3_SSL, username: str) -> Iterator[Tuple[EmailMessageDto, Callable]]:
    mailbox_config, _ = MailboxConfig.objects.get_or_create(username=username)

    for message_id, message_num in get_unread_message_ids(
        pop3_connection,
        mailbox_config,
        settings.INCOMING_EMAIL_CHECK_LIMIT,
    ):
        read_status, _ = mailbox_config.mail_read_statuses.get_or_create(
            message_id=message_id,
            message_num=message_num,
        )

        def mark_status(status):
            """
            :param status: A choice from `MailReadStatuses.choices`
            """
            logger.info(
                "Marking message_id %s with message_num %s from %s as %s",
                message_id,
                message_num,
                read_status.mailbox,
                status,
            )
            read_status.status = status
            read_status.save()

        try:
            m = pop3_connection.retr(message_num)
            logger.info(
                "Retrieved message_id %s with message_num %s from %s",
                message_id,
                message_num,
                read_status.mailbox,
            )
        except error_proto as err:
            logger.error(
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
            logger.error(
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
        logger.warning("Can not find any mail in [%s] of extract type [%s]", reception_status, extract_types)
        return

    logger.info("Found mail in [%s] of extract type [%s]", reception_status, extract_types)
    return mail
