from unittest import mock

from parameterized import parameterized

from mail.celery_tasks import send_licence_details_to_hmrc
from mail.enums import LicenceActionEnum, ReceptionStatusEnum
from mail.libraries.lite_to_edifact_converter import EdifactValidationError
from mail.models import LicencePayload, Mail
from mail.tests.libraries.client import LiteHMRCTestClient


class SendLiteLicenceDetailsTaskTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.single_siel_licence_payload = LicencePayload.objects.create(
            lite_id=self.licence_payload_json["licence"]["id"],
            reference=self.licence_payload_json["licence"]["reference"],
            data=self.licence_payload_json["licence"],
            action=LicenceActionEnum.INSERT,
        )
        self.mail = Mail.objects.create(edi_filename="filename", edi_data="1\\fileHeader\\CHIEF\\SPIRE\\")

    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_licence_details_success(self, mock_smtp_send, mock_cache):
        self.mail.status = ReceptionStatusEnum.REPLY_SENT
        self.mail.save()

        self.assertEqual(LicencePayload.objects.count(), 1)
        send_licence_details_to_hmrc.delay()

        self.assertEqual(Mail.objects.count(), 2)
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 1)

        assert mock_smtp_send.call_count == 1

    @parameterized.expand(
        [
            (ReceptionStatusEnum.PENDING, 1, 1, 0, 0),
            (ReceptionStatusEnum.REPLY_PENDING, 1, 1, 0, 0),
            (ReceptionStatusEnum.REPLY_RECEIVED, 1, 1, 0, 0),
            (ReceptionStatusEnum.REPLY_SENT, 2, 1, 1, 1),
        ]
    )
    @mock.patch("mail.celery_tasks.cache")
    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_licence_details_with_active_mail_status(
        self,
        mail_status,
        expected_mail_count,
        payload_count,
        processed_payload_count,
        num_emails_sent,
        mock_smtp_send,
        mock_cache,
    ):
        """
        We can only send one message at a time to HMRC so before we send next message the
        previous message should be fully processed (status will be 'reply_sent') so before sending
        details we need to check if there is an active email.
        In this test we ensure payload is only processed where there are no active emails.
        """
        mock_cache.add.return_value = True
        self.mail.status = mail_status
        self.mail.save()

        self.assertEqual(LicencePayload.objects.count(), payload_count)
        send_licence_details_to_hmrc.delay()

        self.assertEqual(Mail.objects.count(), expected_mail_count)
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), processed_payload_count)

        assert mock_smtp_send.call_count == num_emails_sent

    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_licence_details_not_sent_when_there_are_no_payloads(self, mock_smtp_send):
        """Test to ensure no details are sent if there are no payloads to process"""
        self.mail.status = ReceptionStatusEnum.REPLY_SENT
        self.mail.save()

        # Mark existing payload as processed
        self.single_siel_licence_payload.is_processed = True
        self.single_siel_licence_payload.save()

        self.assertEqual(LicencePayload.objects.count(), 1)

        send_licence_details_to_hmrc.delay()
        self.assertEqual(Mail.objects.count(), 1)
        mock_smtp_send.assert_not_called()

    @mock.patch("mail.celery_tasks.smtp_send")
    def test_send_licence_details_task_payload_not_processed_if_validation_error(self, mock_smtp_send):
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
        mock_smtp_send.assert_not_called()

    @mock.patch("mail.libraries.builders.licences_to_edifact")
    def test_send_licence_details_raises_exception(self, mock_licences_to_edifact):
        mock_licences_to_edifact.side_effect = EdifactValidationError()
        with self.assertRaises(EdifactValidationError):
            self.mail.status = ReceptionStatusEnum.REPLY_SENT
            self.mail.save()
            send_licence_details_to_hmrc()
