import email.mime.multipart
from unittest import mock

import pytest
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.conf import settings
from celery.exceptions import Retry, MaxRetriesExceededError

import email.mime.multipart
from mail.celery_tasks import SendSmtpFailureTask, manage_inbox, notify_users_of_rejected_licences
from mail.libraries.email_message_dto import EmailMessageDto
from mail.celery_tasks import send_smtp_task
from mail.celery_tasks import get_lite_api_url


class NotifyUsersOfRejectedMailTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])  # /PS-IGNORE
    @mock.patch("mail.celery_tasks.send_smtp_task")
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


class NotifyUsersOfRejectedMailTests(TestCase):
    @override_settings(EMAIL_USER="test@example.com", NOTIFY_USERS=["notify@example.com"])  # /PS-IGNORE
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


class SendEmailTaskTests(TestCase):
    def setUp(self):
        attachment = "30 \U0001d5c4\U0001d5c6/\U0001d5c1 \u5317\u4EB0"
        self.email_message_dto = EmailMessageDto(
            run_number=1,
            sender=settings.HMRC_ADDRESS,
            receiver=settings.SPIRE_ADDRESS,
            date="Mon, 17 May 2021 14:20:18 +0100",
            body=None,
            subject="Some subject",
            attachment=["some filename", attachment],
            raw_data="",
        )

    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    def test_locking_prevents_multiple_executions(self, mock_cache, mock_smtp_send):
        mock_cache.add.side_effect = [True, False]  # First call acquires the lock, second call finds it locked

        # Simulate the lock being released after the first task finishes
        mock_cache.delete.return_value = None

        email_message_data = self.email_message_dto._asdict()
        send_smtp_task.apply_async(kwargs={"email_message_data": email_message_data})
        send_smtp_task.apply_async(kwargs={"email_message_data": email_message_data})

        # Failed and re-tried so in total 3 times
        self.assertEqual(mock_cache.add.call_count, 3)
        # Check if lock was deleted
        self.assertTrue(mock_cache.delete.called)

    @mock.patch("mail.celery_tasks.send_smtp_task.retry", side_effect=Retry)
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    def test_retry_on_lock_failure(self, mock_cache, mock_smtp_send, mock_retry):
        mock_cache.add.return_value = False
        mock_smtp_send.return_value = None

        email_message_data = self.email_message_dto._asdict()
        try:
            send_smtp_task.apply_async(kwargs={"email_message_data": email_message_data})
        except Retry:
            pass

        mock_retry.assert_called_once()

    @mock.patch("mail.celery_tasks.logger")
    def test_on_failure_logging(self, mock_logger):
        # Create an instance of the task
        task = SendSmtpFailureTask()

        # Simulated task failure information
        exc = MaxRetriesExceededError()
        task_id = "test_task_id"
        args = ("arg1", "arg2")
        kwargs = {"mail_id": "12345"}
        einfo = "Simulated exception info"

        # Manually call the on_failure method
        task.on_failure(exc, task_id, args, kwargs, einfo)

        # Build the expected message
        expected_message = f"""
            Task failed permanently after all retries: send_smtp_task
            Mail ID: {kwargs['mail_id']}
            Exception: {exc}
            Args: {args}
            Kwargs: {kwargs}
            Task ID: {task_id}
            Exception Info: {einfo}
        """

        self.assertEqual(
            " ".join(mock_logger.critical.call_args[0][0].strip().split()), " ".join(expected_message.strip().split())
        )
