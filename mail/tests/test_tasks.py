from unittest import mock
from django.test import TestCase, override_settings
from django.core.cache import cache
from datetime import datetime
import pytz

import email.mime.multipart
from mail.libraries.email_message_dto import EmailMessageDto

from django.conf import settings

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

    @mock.patch("mail.tasks.smtp_send")
    @mock.patch("mail.tasks.cache")
    def test_send_email_task_with_message(self, mock_cache, mock_smtp_send):
        mock_cache.add.return_value = True
        mock_cache.delete.return_value = None

        # Prepare the email_message_dto as a serializable dictionary
        attachment = "30 \U0001d5c4\U0001d5c6/\U0001d5c1 \u5317\u4EB0"
        email_message_dto = EmailMessageDto(
            run_number=1,
            sender=settings.HMRC_ADDRESS,
            receiver=settings.SPIRE_ADDRESS,
            date="Mon, 17 May 2021 14:20:18 +0100",
            body=None,
            subject="Some subject",
            attachment=["some filename", attachment],
            raw_data="",
        )

        send_email_task(message=email_message_dto)
        mock_smtp_send.assert_called_once()

        # Verify the lock was acquired and released
        mock_cache.add.assert_called_once_with("global_send_email_lock", mock.ANY, 60 * 10)
        mock_cache.delete.assert_called_once_with("global_send_email_lock")

    @mock.patch("mail.tasks.smtp_send")
    def test_send_email_task_insufficient_parameters(self, mock_smtp_send):
        mock_smtp_send.side_effect = lambda *args, **kwargs: None

        with self.assertRaises(ValueError) as context:
            send_email_task.apply(kwargs={}).get()

        self.assertTrue("Insufficient parameters to build email." in str(context.exception))
        mock_smtp_send.assert_not_called()


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
