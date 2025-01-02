import concurrent.futures
import email.mime.multipart
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPException
from unittest import mock
from unittest.mock import MagicMock

import pytest
from django.test import TestCase, override_settings
from parameterized import parameterized

from mail.celery_tasks import (
    MAX_RETRIES,
    get_lite_api_url,
    manage_inbox,
    notify_users_of_rejected_licences,
    send_email_task,
)
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.routing_controller import check_and_route_emails
from mail.models import LicenceData, Mail
from mail.tests.factories import LicenceDataFactory, MailFactory
from mail.tests.libraries.client import LiteHMRCTestClient


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
    @mock.patch("mail.celery_tasks.cache")
    def test_send_rejected_notification_email_success(self, mock_cache, mock_smtp_send):
        notify_users_of_rejected_licences("123", "CHIEF_SPIRE_licenceReply_202401180900_42557")

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

    @mock.patch("mail.libraries.routing_controller.get_spire_to_dit_mailserver")
    @mock.patch("mail.libraries.routing_controller.get_hmrc_to_dit_mailserver")
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail.libraries.routing_controller.get_email_message_dtos")
    def test_sending_of_new_message_from_spire_success(
        self,
        email_dtos,
        mock_cache,
        mock_smtp_send,
        mock_get_hmrc_to_dit_mailserver,
        mock_get_spire_to_dit_mailserver,
    ):
        email_dtos.return_value = []

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

        mock_smtp_send.assert_called_once()

    @parameterized.expand(
        [
            # SEND_REJECTED_EMAIL state, mail sender and recipients
            (
                True,
                [
                    {
                        "sender": "lite-hmrc@gov.uk",  # /PS-IGNORE
                        "recipients": "spire@example.com",  # /PS-IGNORE
                        "subject": "ILBDOTI_live_CHIEF_licenceReply_78120_202403060300",
                    },
                    {
                        "sender": "lite-hmrc@gov.uk",  # /PS-IGNORE
                        "recipients": "ecju@gov.uk",  # /PS-IGNORE
                        "subject": "Licence rejected by HMRC",
                    },
                ],
            ),
            (
                False,
                [
                    {
                        "sender": "lite-hmrc@gov.uk",  # /PS-IGNORE
                        "recipients": "spire@example.com",  # /PS-IGNORE
                        "subject": "ILBDOTI_live_CHIEF_licenceReply_78120_202403060300",
                    }
                ],
            ),
        ]
    )
    @override_settings(
        EMAIL_USER="lite-hmrc@gov.uk",  # /PS-IGNORE
        NOTIFY_USERS=["ecju@gov.uk"],  # /PS-IGNORE
        SPIRE_ADDRESS="spire@example.com",  # /PS-IGNORE
    )
    @mock.patch("mail.libraries.routing_controller.get_spire_to_dit_mailserver")
    @mock.patch("mail.libraries.routing_controller.get_hmrc_to_dit_mailserver")
    @mock.patch("mail.celery_tasks.smtp_send")
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail.libraries.routing_controller.get_email_message_dtos")
    def test_processing_of_licence_reply_with_rejected_licences(
        self,
        send_rejected_email_flag,
        emails_data,
        email_dtos,
        mock_cache,
        mock_smtp_send,
        mock_get_hmrc_to_dit_mailserver,
        mock_get_spire_to_dit_mailserver,
    ):
        """
        Test processing of licence reply from HMRC with rejected licences.
        If SEND_REJECTED_EMAIL=True then we send email notifications to users if any licences are rejected.
        """
        obj = MagicMock()
        mock_get_hmrc_to_dit_mailserver.return_value = obj
        mock_get_spire_to_dit_mailserver.return_value = obj

        run_number = 78120
        mail = MailFactory(
            extract_type=ExtractTypeEnum.LICENCE_DATA,
            edi_filename=self.licence_data_file_name,
            edi_data=self.licence_data_file_body.decode("utf-8"),
            status=ReceptionStatusEnum.REPLY_PENDING,
        )
        LicenceDataFactory(mail=mail, source_run_number=run_number, hmrc_run_number=run_number)

        licence_reply_filename = f"ILBDOTI_live_CHIEF_licenceReply_{run_number}_202403060300"
        file_lines = "\n".join(
            [
                f"1\\fileHeader\\CHIEF\SPIRE\\licenceReply\\202403061600\\{run_number}",
                "2\\accepted\\340631",
                "3\\rejected\\340632",
                "4\\end\\rejected\\3",
                "5\\fileTrailer\\1\\1\\0",
            ]
        )

        email_message_dto = EmailMessageDto(
            run_number=f"{run_number}",
            sender="test@example.com",  # /PS-IGNORE
            receiver="receiver@example.com",  # /PS-IGNORE
            date="Mon, 17 May 2021 14:20:18 +0100",
            body="licence rejected",
            subject=licence_reply_filename,
            attachment=[licence_reply_filename, file_lines.encode("utf-8")],
            raw_data="qwerty",
        )
        email_dtos.return_value = [
            (email_message_dto, lambda x: x),
        ]

        with override_settings(SEND_REJECTED_EMAIL=send_rejected_email_flag):
            check_and_route_emails()

            mail.refresh_from_db()
            self.assertEqual(mail.status, ReceptionStatusEnum.REPLY_SENT)

            self.assertEqual(mock_smtp_send.call_count, len(emails_data))

            for index, item in enumerate(mock_smtp_send.call_args_list):
                message = item.args[0]
                self.assertIsInstance(message, MIMEMultipart)
                self.assertEqual(message["From"], emails_data[index]["sender"])
                self.assertEqual(message["To"], emails_data[index]["recipients"])
                self.assertEqual(message["Subject"], emails_data[index]["subject"])


class SendEmailTestTests(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail_servers.servers.get_smtp_connection")
    def test_sends_email(self, mock_get_smtp_connection, mock_cache):
        mock_conn = mock_get_smtp_connection().__enter__()
        message = {
            "From": "from@example.com",  # /PS-IGNORE
            "To": "to@example.com",  # /PS-IGNORE
        }
        send_email_task.apply(args=[message])
        mock_conn.send_message.assert_called_with(message)
        mock_cache.lock.assert_called_with("global_send_email_lock", timeout=600)

    @parameterized.expand(
        [
            (ConnectionResetError,),
            (SMTPException,),
        ]
    )
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail_servers.servers.get_smtp_connection")
    def test_sends_email_failed_then_succeeds(self, exception_class, mock_get_smtp_connection, mock_cache):
        mock_conn = mock_get_smtp_connection().__enter__()
        message = {
            "From": "from@example.com",  # /PS-IGNORE
            "To": "to@example.com",  # /PS-IGNORE
        }
        mock_conn.send_message.side_effect = [exception_class(), None]
        send_email_task.apply(args=[message])
        mock_conn.send_message.assert_called_with(message)
        self.assertEqual(mock_conn.send_message.call_count, 2)
        mock_cache.lock.assert_called_with("global_send_email_lock", timeout=600)

    @parameterized.expand(
        [
            (ConnectionResetError,),
            (SMTPException,),
        ]
    )
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail_servers.servers.get_smtp_connection")
    def test_sends_email_max_retry_failures(self, exception_class, mock_get_smtp_connection, mock_cache):
        mock_conn = mock_get_smtp_connection().__enter__()
        message = {
            "From": "from@example.com",  # /PS-IGNORE
            "To": "to@example.com",  # /PS-IGNORE
        }
        mock_conn.send_message.side_effect = exception_class()
        send_email_task.apply(args=[message])
        mock_conn.send_message.assert_called_with(message)
        self.assertEqual(
            mock_conn.send_message.call_count,
            MAX_RETRIES + 1,
        )
        mock_cache.lock.assert_called_with("global_send_email_lock", timeout=600)

    @mock.patch("mail_servers.servers.get_smtp_connection")
    def test_locking(self, mock_get_smtp_connection):
        results = []

        SLEEP_TIME = 1

        def _sleepy(message):
            call = {}
            call["start"] = {
                "message": message,
                "time": time.monotonic(),
            }
            time.sleep(SLEEP_TIME)
            call["end"] = {
                "message": message,
                "time": time.monotonic(),
            }
            results.append(call)

        mock_conn = mock_get_smtp_connection().__enter__()
        mock_conn.send_message.side_effect = _sleepy

        with concurrent.futures.ThreadPoolExecutor() as executor:
            message_1 = {
                "From": "from1@example.com",  # /PS-IGNORE
                "To": "to1@example.com",  # /PS-IGNORE
            }
            future_1 = executor.submit(send_email_task.apply, args=[message_1])

            message_2 = {
                "From": "from2@example.com",  # /PS-IGNORE
                "To": "to2@example.com",  # /PS-IGNORE
            }
            future_2 = executor.submit(send_email_task.apply, args=[message_2])

        future_1.result()
        future_2.result()

        assert len(results) == 2
        first_call, second_call = results

        # We don't particularly care about the exact order of these calls
        # We just care that they didn't happen at the same time due to the lock

        self.assertEqual(first_call["start"]["message"], first_call["end"]["message"])
        self.assertEqual(second_call["start"]["message"], second_call["end"]["message"])
        self.assertNotEqual(first_call["start"]["message"], second_call["start"]["message"])
        self.assertNotEqual(first_call["end"]["message"], second_call["end"]["message"])

        self.assertGreater(
            second_call["start"]["time"],
            first_call["end"]["time"],
            "The second call should start after the end of the first call",
        )
        self.assertGreater(
            second_call["start"]["time"],
            first_call["start"]["time"] + SLEEP_TIME,
            f"The second call should start at least {SLEEP_TIME} after the first started",
        )
