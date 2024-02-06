from unittest import mock
from django.test import TestCase, override_settings
from django.core.cache import cache
import email.mime.multipart

from mail.tasks import send_email_task
from mail.celery_tasks import get_lite_api_url


class GetLiteAPIUrlTests(TestCase):
    def test_get_url_with_no_path(self):
        with self.settings(LITE_API_URL="https://example.com"):
            result = get_lite_api_url()

        self.assertEqual(result, "https://example.com/licences/hmrc-integration/")

    def test_get_url_with_root_path(self):
        with self.settings(LITE_API_URL="https://example.com/"):
            result = get_lite_api_url()

        self.assertEqual(result, "https://example.com/licences/hmrc-integration/")

    def test_get_url_with_path_from_setting(self):
        with self.settings(LITE_API_URL="https://example.com/foo"):
            result = get_lite_api_url()

        self.assertEqual(result, "https://example.com/foo")


class SendEmailTaskTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])
    @mock.patch("mail.tasks.smtp_send")
    @mock.patch("mail.tasks.cache")
    def test_locking_prevents_multiple_executions(self, mock_cache, mock_smtp_send):
        mock_cache.add.side_effect = [True, False]  # First call acquires the lock, second call finds it locked

        # Simulate the lock being released after the first task finishes
        mock_cache.delete.return_value = None

        # Execute the task twice with the same parameters
        send_email_task.apply(kwargs={"mail_id": "123", "mail_response_subject": "Test Subject"})
        send_email_task.apply(kwargs={"mail_id": "123", "mail_response_subject": "Test Subject"})

        # Assert smtp_send was called once due to locking
        mock_smtp_send.assert_called_once()
        self.assertEqual(mock_cache.add.call_count, 2)
        mock_cache.delete.assert_called_once_with("global_send_email_lock")


class NotifyUsersOfRejectedMailTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])  # /PS-IGNORE
    @mock.patch("mail.tasks.smtp_send")
    def test_send_success(self, mock_send):
        send_email_task(mail_id="123", mail_response_subject="CHIEF_SPIRE_licenceReply_202401180900_42557")

        mock_send.assert_called_once()

        self.assertEqual(len(mock_send.call_args_list), 1)
        message = mock_send.call_args[0][0]
        self.assertIsInstance(message, email.mime.multipart.MIMEMultipart)

        expected_headers = {
            "Content-Type": "multipart/mixed",
            "MIME-Version": "1.0",
            "From": "test@example.com",  # /PS-IGNORE
            "To": "notify@example.com",  # /PS-IGNORE
            "Subject": "Licence rejected by HMRC",
        }
        self.assertDictEqual(dict(message), expected_headers)

        text_payload = message.get_payload(0)
        expected_body = "Mail (Id: 123) with subject CHIEF_SPIRE_licenceReply_202401180900_42557 has rejected licences"
        self.assertEqual(text_payload.get_payload(), expected_body)
