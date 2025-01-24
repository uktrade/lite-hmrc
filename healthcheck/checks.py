import datetime
import logging
import poplib

from django.conf import settings
from django.utils import timezone
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException

from mail.enums import ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from mail_servers.utils import get_mail_server

logger = logging.getLogger(__name__)


class MailboxAuthenticationHealthCheck(BaseHealthCheckBackend):
    def check_status(self):
        for server_name in settings.MAIL_SERVERS.keys():
            mailserver = get_mail_server(server_name)
            try:
                with mailserver.connect_to_pop3():
                    pass
            except poplib.error_proto as e:
                response, *_ = e.args
                error_message = f"Failed to connect to mailbox: {mailserver.hostname} ({response})"
                self.add_error(HealthCheckException(error_message))


class LicencePayloadsHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self):
        dt = timezone.now() + datetime.timedelta(seconds=settings.LICENSE_POLL_INTERVAL)
        unprocessed_payloads = LicencePayload.objects.filter(is_processed=False, received_at__lte=dt)

        for unprocessed_payload in unprocessed_payloads:
            error_message = f"Payload object has been unprocessed for over {settings.LICENSE_POLL_INTERVAL} seconds: {unprocessed_payload}"
            self.add_error(HealthCheckException(error_message))


class PendingMailHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self):
        dt = timezone.now() - datetime.timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME)
        pending_mails = Mail.objects.exclude(status=ReceptionStatusEnum.REPLY_SENT).filter(sent_at__lte=dt)

        for pending_mail in pending_mails:
            error_message = f"The following Mail has been pending for over {settings.EMAIL_AWAITING_REPLY_TIME} seconds: {pending_mail}"
            self.add_error(HealthCheckException(error_message))
