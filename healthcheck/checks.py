import datetime
import logging
import poplib

from background_task.models import Task
from django.conf import settings
from django.utils import timezone

from mail.enums import ReceptionStatusEnum
from mail.libraries.routing_controller import get_hmrc_to_dit_mailserver, get_spire_to_dit_mailserver
from mail.models import LicencePayload, Mail
from mail.tasks import MANAGE_INBOX_TASK_QUEUE

logger = logging.getLogger(__name__)


def can_authenticate_mailboxes():
    mailserver_factories = (
        get_hmrc_to_dit_mailserver,
        get_spire_to_dit_mailserver,
    )
    mailbox_results = []
    for mailserver_factory in mailserver_factories:
        mailserver = mailserver_factory()
        try:
            mailserver.connect_to_pop3()
        except poplib.error_proto as e:
            response, *_ = e.args
            logger.error(
                "Failed to connect to mailbox: %s (%s)",
                mailserver.hostname,
                response,
            )
            mailbox_results.append(False)
        else:
            mailbox_results.append(True)
        finally:
            mailserver.quit_pop3_connection()

    return all(mailbox_results)


def is_licence_payloads_processing():
    dt = timezone.now() + datetime.timedelta(seconds=settings.LICENSE_POLL_INTERVAL)

    unprocessed_payloads = LicencePayload.objects.filter(is_processed=False, received_at__lte=dt)
    for unprocessed_payload in unprocessed_payloads:
        logger.error(
            "Payload object has been unprocessed for over %s seconds: %s",
            settings.LICENSE_POLL_INTERVAL,
            unprocessed_payload,
        )

    return not unprocessed_payloads.exists()


def is_manage_inbox_task_responsive():
    dt = timezone.now() + datetime.timedelta(seconds=settings.INBOX_POLL_INTERVAL)

    return Task.objects.filter(queue=MANAGE_INBOX_TASK_QUEUE, run_at__lte=dt).exists()


def is_pending_mail_processing():
    dt = timezone.now() - datetime.timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME)

    pending_mails = Mail.objects.exclude(status=ReceptionStatusEnum.REPLY_SENT).filter(sent_at__lte=dt)
    for pending_mail in pending_mails:
        logger.error(
            "The following Mail has been pending for over %s seconds: %s",
            settings.EMAIL_AWAITING_REPLY_TIME,
            pending_mail,
        )

    return not pending_mails.exists()
