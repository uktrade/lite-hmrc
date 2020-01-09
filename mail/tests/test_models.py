import unittest

from mail.data_processing import process_and_save_email_message_dto
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import LicenseUpdate


class TestModels(unittest.TestCase):
    def setUp(self):
        self.hmrc_run_number = 28
        self.source_run_number = 15
        LicenseUpdate(
            edi_data="blank",
            extract_type=ExtractTypeEnum.INSERT,
            status=ReceptionStatusEnum.ACCEPTED,
            edi_filename="blank",
            license_id="00000000-0000-0000-0000-000000000001",
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            source=SourceEnum.SPIRE,
        ).save()

    def test_EmailMessageDto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="test@example.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=["filename", "a line".encode("ascii", "replace")],
        )

        process_and_save_email_message_dto(email_message_dto)

        email = LicenseUpdate.objects.first()
        self.assertEqual(email.edi_data, email_message_dto.attachment[1])
        self.assertEqual(email.extract_type, ExtractTypeEnum.INSERT)
        self.assertEqual(email.respnonse_file, None)
        self.assertEqual(email.respnonse_date, None)
        self.assertEqual(email.edi_filename, email_message_dto.attachment[0])
        self.assertEqual(email.source_run_number, email_message_dto.run_number)
        self.assertEqual(email.hmrc_run_number, self.hmrc_run_number + 1)
