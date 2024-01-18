import email.mime.multipart
from unittest import mock

from django.test import override_settings, TestCase

from mail.celery_tasks import notify_users_of_rejected_licences


class NotifyUsersOfRejectedMailTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])
    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_success(self, mock_send):
        notify_users_of_rejected_licences("123", "CHIEF_SPIRE_licenceReply_202401180900_42557")

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
