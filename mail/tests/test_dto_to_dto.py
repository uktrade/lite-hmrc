from conf.test_client import LiteHMRCTestClient
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate
from mail.services.data_processing import (
    to_email_message_dto_from,
    process_and_save_email_message,
)
from mail.services.helpers import convert_source_to_sender


class DtoToDtoTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.hmrc_run_number = 28
        self.source_run_number = 15
        self.mail = Mail.objects.create(
            edi_data=self.licence_usage_file_body,
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
            status=ReceptionStatusEnum.ACCEPTED,
            edi_filename=self.licence_usage_file_name,
        )

        self.licence_update = LicenceUpdate.objects.create(
            mail=self.mail,
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            source=SourceEnum.SPIRE,
        )

    def test_successful_inbound_dto_converts_to_outbound_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="test@spire.com",
            receiver="receiver@example.com",
            body="body",
            subject=self.licence_usage_file_name,
            attachment=[self.licence_usage_file_name, self.licence_usage_file_body,],
            raw_data="qwerty",
        )

        # dto to dto processing
        mail = process_and_save_email_message(email_message_dto)
        dto = to_email_message_dto_from(mail)

        self.assertEqual(dto.run_number, self.licence_update.hmrc_run_number + 1)
        self.assertEqual(
            dto.sender, convert_source_to_sender(self.licence_update.source)
        )
        self.assertEqual(dto.attachment[0], email_message_dto.attachment[0])
        self.assertEqual(
            dto.attachment[1], email_message_dto.attachment[1],
        )
        self.assertEqual(dto.subject, self.licence_usage_file_name)
        self.assertEqual(dto.receiver, "HMRC")
        self.assertEqual(dto.body, "")
        self.assertEqual(dto.raw_data, None)

    def test_unsuccessful_inbound_dto_does_not_convert_to_outbound_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="test@general.com",
            receiver="receiver@example.com",
            body="body",
            subject=self.licence_usage_file_name,
            attachment=[self.licence_usage_file_name, self.licence_usage_file_body],
            raw_data="qwerty",
        )

        self.assertEqual(process_and_save_email_message(email_message_dto), False)
