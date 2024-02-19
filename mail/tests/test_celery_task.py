import email.mime.multipart
import pytest

from datetime import datetime, timezone
from parameterized import parameterized
from unittest import mock
from django.test import TestCase, override_settings

from mail.celery_tasks import manage_inbox, notify_users_of_rejected_licences
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.libraries.routing_controller import check_and_route_emails
from mail.models import LicenceData, Mail
from mail.tests.libraries.client import LiteHMRCTestClient


class NotifyUsersOfRejectedMailTests(TestCase):
    @parameterized.expand(
        [
            # lock_acquired
            ([True],),
            ([False, True],),
        ]
    )
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])  # /PS-IGNORE
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    def test_send_rejected_notification_email_success(self, lock_acquired, mock_cache, mock_smtp_send):
        """Test sending of licence rejected emails without and with retry scenario"""
        mock_cache.add.side_effect = lock_acquired

        notify_users_of_rejected_licences.delay("123", "CHIEF_SPIRE_licenceReply_202401180900_42557")

        assert mock_cache.add.call_count == len(lock_acquired)
        mock_smtp_send.assert_called_once()

        self.assertEqual(len(mock_smtp_send.call_args_list), 1)
        message = mock_smtp_send.call_args[0][0]
        self.assertIsInstance(message, email.mime.multipart.MIMEMultipart)

        expected_headers = {
            "Content-Type": "multipart/mixed",
            "MIME-Version": "1.0",
            "From": "test@example.com",  # /PS-IGNORE
            "To": "notify@example.com",  # /PS-IGNORE
            "Subject": "Licence rejected by HMRC",
            "name": "Licence rejected by HMRC",
        }
        self.assertDictEqual(dict(message), expected_headers)

        text_payload = message.get_payload(0)
        expected_body = "Mail (Id: 123) with subject CHIEF_SPIRE_licenceReply_202401180900_42557 has rejected licences"
        self.assertEqual(text_payload.get_payload(), expected_body)


class ManageInboxTests(LiteHMRCTestClient):
    @mock.patch("mail.celery_tasks.check_and_route_emails")
    def test_manage_inbox(self, mock_function):
        manage_inbox()
        mock_function.assert_called_once()

    @mock.patch("mail.celery_tasks.check_and_route_emails")
    def test_error_manage_inbox(self, mock_function):
        mock_function.side_effect = Exception("Test Error")
        with pytest.raises(Exception) as excinfo:
            manage_inbox()
        assert str(excinfo.value) == "Test Error"

    @parameterized.expand(
        [
            # lock_acquired
            ([True],),
            ([False, True],),
        ]
    )
    @mock.patch("mail.libraries.routing_controller.get_spire_to_dit_mailserver")
    @mock.patch("mail.libraries.routing_controller.get_hmrc_to_dit_mailserver")
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail.libraries.routing_controller.get_email_message_dtos")
    def test_sending_of_new_message_from_spire_success(
        self,
        lock_acquired,
        email_dtos,
        mock_cache,
        mock_smtp_send,
        mock_get_hmrc_to_dit_mailserver,
        mock_get_spire_to_dit_mailserver,
    ):
        """Test sending of email when a message from SPIRE is processed without and with retry scenario"""
        email_dtos.return_value = []
        mock_cache.add.side_effect = lock_acquired

        # When a new message is processed from inbox it will be created with 'pending' status
        pending_mail = Mail.objects.create(
            extract_type=ExtractTypeEnum.LICENCE_DATA,
            edi_filename=self.licence_data_file_name,
            edi_data=self.licence_data_file_body.decode("utf-8"),
            status=ReceptionStatusEnum.PENDING,
            sent_at=datetime.now(timezone.utc),
        )
        LicenceData.objects.create(
            mail=pending_mail,
            source_run_number=78120,
            hmrc_run_number=78120,
            source=SourceEnum.SPIRE,
            licence_ids=f"{78120}",
        )

        check_and_route_emails()

        # assert that the pending mail is sent and status updated
        mail = Mail.objects.get(id=pending_mail.id)
        self.assertEqual(mail.status, ReceptionStatusEnum.REPLY_PENDING)

        assert mock_cache.add.call_count == len(lock_acquired)
        mock_smtp_send.assert_called_once()
