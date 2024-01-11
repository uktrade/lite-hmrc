import email.mime.multipart
from unittest import mock

from django.test import TestCase

from mail.celery_tasks import notify_users_of_rejected_mail


class NotifyUsersOfRejectedMailTests(TestCase):
    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_success(self, mock_send):
        settings = {
            "EMAIL_USER": "test@example.com",  # /PS-IGNORE
            "NOTIFY_USERS": ["notify@example.com"],  # /PS-IGNORE
        }
        with self.settings(**settings):
            notify_users_of_rejected_mail("123", "1999-12-31 23:45:59")

        mock_send.assert_called_once()

        self.assertEqual(len(mock_send.call_args_list), 1)
        message = mock_send.call_args[0][0]
        self.assertIsInstance(message, email.mime.multipart.MIMEMultipart)

        expected_headers = {
            "Content-Type": "multipart/mixed",
            "MIME-Version": "1.0",
            "From": "test@example.com",  # /PS-IGNORE
            "To": "notify@example.com",  # /PS-IGNORE
            "Subject": "Mail rejected",
        }
        self.assertDictEqual(dict(message), expected_headers)

        text_payload = message.get_payload(0)
        expected_body = "Mail [123] received at [1999-12-31 23:45:59] was rejected"
        self.assertEqual(text_payload.get_payload(), expected_body)
