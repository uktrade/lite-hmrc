from django.test import testcases

from mail.models import Mail
from mail.services.data_processing import process_and_save_email_message
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum


class TestModels(testcases.TestCase):
    def setUp(self):
        self.hmrc_run_number = 28
        self.source_run_number = 15
        Mail(
            edi_data="blank",
            extract_type=ExtractTypeEnum.INSERT,
            status=ReceptionStatusEnum.ACCEPTED,
            edi_filename="blank",
        ).save()

    def test_email_processed_successfully(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="test@spire.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=["filename", "a line".encode("ascii", "replace")],
            raw_data="qwerty",
        )

        process_and_save_email_message(email_message_dto)

        email = Mail.objects.valid().last()
        self.assertEqual(email.edi_data, str(email_message_dto.attachment[1]))
        self.assertEqual(email.extract_type, ExtractTypeEnum.INSERT)
        self.assertEqual(email.response_file, None)
        self.assertEqual(email.response_date, None)
        self.assertEqual(email.edi_filename, email_message_dto.attachment[0])
        self.assertEqual(email.source_run_number, email_message_dto.run_number)
        self.assertEqual(email.hmrc_run_number, self.hmrc_run_number + 1)
        self.assertEqual(email.raw_data, email_message_dto.raw_data)

    def test_bad_email_sent_to_issues_log(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="test@example.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=[],
            raw_data="qwerty",
        )

        initial_issues_count = Mail.objects.invalid().count()
        initial_license_update_count = Mail.objects.invalid().count()

        process_and_save_email_message(email_message_dto)

        self.assertEqual(Mail.objects.invalid().count(), initial_issues_count + 1)
        self.assertEqual(Mail.objects.invalid().count(), initial_license_update_count)

        email = Mail.objects.invalid().last()

        self.assertEqual(email.edi_data, "")
        self.assertEqual(email.extract_type, ExtractTypeEnum.INSERT)
        self.assertEqual(email.response_file, None)
        self.assertEqual(email.response_date, None)
        self.assertEqual(email.edi_filename, "")
        self.assertEqual(email.raw_data, email_message_dto.raw_data)
