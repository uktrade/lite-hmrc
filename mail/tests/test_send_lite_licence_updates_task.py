from unittest import mock

from django.test import override_settings
from parameterized import parameterized
from smtplib import SMTPException

from mail.celery_tasks import send_licence_details_to_hmrc
from mail.enums import ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from mail.tests.libraries.client import LiteHMRCTestClient


@override_settings(BACKGROUND_TASK_ENABLED=False)  # Disable task from being run on app initialization
class TaskTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.mail = Mail.objects.create(edi_filename="filename", edi_data="1\\fileHeader\\CHIEF\\SPIRE\\")

    @parameterized.expand(
        [
            (ReceptionStatusEnum.PENDING, 1, 1, 0),
            (ReceptionStatusEnum.REPLY_PENDING, 1, 1, 0),
            (ReceptionStatusEnum.REPLY_RECEIVED, 1, 1, 0),
            (ReceptionStatusEnum.REPLY_SENT, 2, 1, 1),
        ]
    )
    @mock.patch("mail.celery_tasks.send")
    def test_send_licence_details_with_active_mail_status(
        self, mail_status, expected_mail_count, payload_count, processed_payload_count, mock_send
    ):
        """
        We can only send one message at a time to HMRC so before we send next message the
        previous message should be fully processed (status will be 'reply_sent') so before sending
        details we need to check if there is an active email.
        In this test we ensure payload is only processed where there are no active emails.
        """
        self.mail.status = mail_status
        self.mail.save()

        self.assertEqual(LicencePayload.objects.count(), payload_count)

        send_licence_details_to_hmrc.delay()
        self.assertEqual(Mail.objects.count(), expected_mail_count)
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), processed_payload_count)

    @mock.patch("mail.celery_tasks.send")
    def test_send_licence_details_not_sent_when_there_are_no_payloads(self, mock_send):
        """Test to ensure no details are sent if there are no payloads to process"""
        self.mail.status = ReceptionStatusEnum.REPLY_SENT
        self.mail.save()

        # Mark existing payload as processed
        self.single_siel_licence_payload.is_processed = True
        self.single_siel_licence_payload.save()

        self.assertEqual(LicencePayload.objects.count(), 1)

        send_licence_details_to_hmrc.delay()
        self.assertEqual(Mail.objects.count(), 1)
        mock_send.assert_not_called()

    @mock.patch("mail.celery_tasks.send")
    def test_send_licence_details_task_payload_not_processed_if_validation_error(self, mock_send):
        """Test to ensure payload is not processed if there is a validation error"""
        self.mail.status = ReceptionStatusEnum.REPLY_SENT
        self.mail.save()

        # invalid post code triggers validation error
        self.single_siel_licence_payload.data["organisation"]["address"]["postcode"] = "invalid_postcode"
        self.single_siel_licence_payload.is_processed = False
        self.single_siel_licence_payload.save()

        self.assertEqual(LicencePayload.objects.filter(is_processed=False).count(), 1)

        send_licence_details_to_hmrc.delay()

        self.assertEqual(LicencePayload.objects.filter(is_processed=False).count(), 1)
        mock_send.assert_not_called()

    @mock.patch("mail.celery_tasks.send")
    def test_send_licence_details_raises_exception(self, mock_send):
        mock_send.side_effect = SMTPException()
        with self.assertRaises(SMTPException):
            self.mail.status = ReceptionStatusEnum.REPLY_SENT
            self.mail.save()
            send_licence_details_to_hmrc()
