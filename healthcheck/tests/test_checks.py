import datetime
import poplib
import uuid
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from health_check.exceptions import HealthCheckException

from healthcheck.checks import LicencePayloadsHealthCheck, MailboxAuthenticationHealthCheck, PendingMailHealthCheck
from mail.enums import LicenceActionEnum, ReceptionStatusEnum
from mail.models import LicencePayload, Mail


class MailboxAuthenticationHealthCheckTest(TestCase):
    @patch("healthcheck.checks.get_mail_server")
    def test_mailbox_authentication_failure(self, mock_get_mail_server):
        mock_get_mail_server().connect_to_pop3().__enter__.side_effect = poplib.error_proto("Failed to connect")
        mock_get_mail_server().hostname = "test.example.com"

        check = MailboxAuthenticationHealthCheck()
        check.check_status()
        # Assert that the add_error method was called with a HealthCheckException
        self.assertEqual(len(check.errors), 2)
        self.assertIsInstance(check.errors[0], HealthCheckException)
        self.assertIsInstance(check.errors[1], HealthCheckException)

        # Assert the error message
        error_message = str(check.errors[0])
        expected_error_message = f"unknown error: Failed to connect to mailbox: test.example.com (Failed to connect)"
        self.assertEqual(error_message, expected_error_message)

        error_message = str(check.errors[1])
        expected_error_message = f"unknown error: Failed to connect to mailbox: test.example.com (Failed to connect)"
        self.assertEqual(error_message, expected_error_message)

    @patch("healthcheck.checks.get_mail_server")
    def test_mailbox_authentication_success(self, mock_get_mail_server):
        check = MailboxAuthenticationHealthCheck()
        check.check_status()

        self.assertEqual(len(check.errors), 0)

    def test_unprocessed_payloads(self):
        LicencePayload.objects.create(
            lite_id=uuid.uuid4(),
            reference="test_reference_1",
            action=LicenceActionEnum.INSERT,
            received_at=timezone.now() - datetime.timedelta(seconds=settings.LICENSE_POLL_INTERVAL + 1),
            is_processed=False,
        )
        check = LicencePayloadsHealthCheck()
        check.check_status()
        assert len(check.errors) == 1
        assert "Payload object has been unprocessed for over" in check.errors[0].message

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

    def test_unprocessed_pending_mails(self):
        Mail.objects.create(
            edi_data="Test EDI data",
            edi_filename="test_edi_file.txt",
            sent_at=timezone.now() - datetime.timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME + 1),
            status=ReceptionStatusEnum.PENDING,
        )

        check = PendingMailHealthCheck()
        check.check_status()
        assert len(check.errors) == 1
        assert "The following Mail has been pending for over" in check.errors[0].message

    def test_no_unprocessed_pending_mails(self):
        Mail.objects.create(
            edi_data="Test EDI data",
            edi_filename="test_edi_file.txt",
            sent_at=timezone.now(),
            status=ReceptionStatusEnum.REPLY_SENT,
        )

        check = PendingMailHealthCheck()
        check.check_status()
