import email.mime.multipart
import pytest

from unittest import mock
from django.test import TestCase, override_settings

from mail.celery_tasks import manage_inbox, notify_users_of_rejected_licences


class NotifyUsersOfRejectedMailTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])  # /PS-IGNORE
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    def test_send_success(self, mock_cache, mock_smtp_send):
        mock_cache.add.return_value = True

        notify_users_of_rejected_licences.delay("123", "CHIEF_SPIRE_licenceReply_202401180900_42557")

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


class ManageInboxTests(TestCase):
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
