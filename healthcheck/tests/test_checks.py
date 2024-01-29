import poplib
import uuid
import datetime

from parameterized import parameterized
from django.test import TestCase
from unittest.mock import patch
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from healthcheck.checks import (
    MailboxAuthenticationHealthCheck,
    LicencePayloadsHealthCheck,
    ManageInboxTaskHealthCheck,
    PendingMailHealthCheck,
)
from health_check.exceptions import HealthCheckException
from mail.enums import LicenceActionEnum, ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from background_task.models import Task
from mail.tasks import LICENCE_DATA_TASK_QUEUE, MANAGE_INBOX_TASK_QUEUE


class MailboxAuthenticationHealthCheckTest(TestCase):
    MAILSERVERS_TO_PATCH = [
        "get_hmrc_to_dit_mailserver",
        "get_spire_to_dit_mailserver",
    ]

    def setUp(self):
        super().setUp()

        self.mocked_mailservers = {}
        for mailserver_to_patch in self.MAILSERVERS_TO_PATCH:
            patched_mailserver = patch(f"healthcheck.checks.{mailserver_to_patch}").start()
            self.mocked_mailservers[mailserver_to_patch] = patched_mailserver

    def tearDown(self) -> None:
        super().tearDown()

        for mailserver_to_patch in self.MAILSERVERS_TO_PATCH:
            self.mocked_mailservers[mailserver_to_patch].stop()

    @parameterized.expand(MAILSERVERS_TO_PATCH)
    def test_mailbox_authentication_failure(self, mailserver_factory):
        mock_mailserver_factory = self.mocked_mailservers[mailserver_factory]
        mock_mailserver_factory().connect_to_pop3.side_effect = poplib.error_proto("Failed to connect")
        mock_mailserver_factory().hostname = f"{mailserver_factory}.example.com"

        check = MailboxAuthenticationHealthCheck()
        with self.assertRaises(HealthCheckException):
            check.check_status()

    @parameterized.expand(MAILSERVERS_TO_PATCH)
    def test_mailbox_authentication_success(self, mailserver_factory):
        self.mocked_mailservers[mailserver_factory]

        check = MailboxAuthenticationHealthCheck()
        check.check_status()

    def test_unprocessed_payloads(self):
        LicencePayload.objects.create(
            lite_id=uuid.uuid4(),
            reference="test_reference_1",
            action=LicenceActionEnum.INSERT,
            received_at=timezone.now() - datetime.timedelta(seconds=settings.LICENSE_POLL_INTERVAL + 1),
            is_processed=False,
        )
        check = LicencePayloadsHealthCheck()
        with self.assertRaises(HealthCheckException):
            check.check_status()

    def test_all_payloads_processed(self):
        LicencePayload.objects.create(
            lite_id=uuid.uuid4(),
            reference="test_reference_2",
            action=LicenceActionEnum.CANCEL,
            received_at=timezone.now(),
            is_processed=True,
        )

        check = LicencePayloadsHealthCheck()
        check.check_status()

    def test_inbox_task_is_responsive(self):
        Task.objects.create(
            queue=MANAGE_INBOX_TASK_QUEUE,
            run_at=timezone.now() - datetime.timedelta(seconds=settings.INBOX_POLL_INTERVAL),
        )

        check = ManageInboxTaskHealthCheck()
        check.check_status()

    def test_inbox_task_is_unresponsive(self):
        run_at = timezone.now() + timedelta(minutes=settings.INBOX_POLL_INTERVAL)
        task, _ = Task.objects.get_or_create(queue=MANAGE_INBOX_TASK_QUEUE)
        task.run_at = run_at
        task.save()

        check = ManageInboxTaskHealthCheck()
        with self.assertRaises(HealthCheckException):
            check.check_status()

    def test_unprocessed_pending_mails(self):
        Mail.objects.create(
            edi_data="Test EDI data",
            edi_filename="test_edi_file.txt",
            sent_at=timezone.now() - datetime.timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME + 1),
            status=ReceptionStatusEnum.PENDING,
        )

        check = PendingMailHealthCheck()
        with self.assertRaises(HealthCheckException):
            check.check_status()

    def test_no_unprocessed_pending_mails(self):
        Mail.objects.create(
            edi_data="Test EDI data",
            edi_filename="test_edi_file.txt",
            sent_at=timezone.now(),
            status=ReceptionStatusEnum.REPLY_SENT,
        )

        check = PendingMailHealthCheck()
        check.check_status()
