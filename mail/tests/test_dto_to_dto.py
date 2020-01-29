from django.test import tag

from conf.settings import SPIRE_ADDRESS, HMRC_ADDRESS
from conf.test_client import LiteHMRCTestClient
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate, UsageUpdate
from mail.services.data_processing import (
    to_email_message_dto_from,
    serialize_email_message,
)


class DtoToDtoTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.hmrc_run_number = 28
        self.source_run_number = 15
        self.mail = Mail.objects.create(
            edi_data=self.licence_usage_file_body,
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
            status=ReceptionStatusEnum.PENDING,
            edi_filename=self.licence_usage_file_name,
        )

        self.licence_update = LicenceUpdate.objects.create(
            mail=self.mail,
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            source=SourceEnum.SPIRE,
        )

        self.usage_update = UsageUpdate.objects.create(
            mail=self.mail,
            spire_run_number=self.source_run_number,
            hmrc_run_number=self.hmrc_run_number,
        )

    def test_successful_inbound_dto_converts_to_outbound_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="receiver@example.com",
            body="body",
            subject=self.licence_usage_file_name,
            attachment=[self.licence_usage_file_name, self.licence_usage_file_body,],
            raw_data="qwerty",
        )

        # dto to dto processing
        mail = serialize_email_message(email_message_dto)
        dto = to_email_message_dto_from(mail)

        self.assertEqual(dto.run_number, self.usage_update.spire_run_number + 1)
        self.assertEqual(dto.sender, "HMRC")
        self.assertEqual(dto.attachment[0], email_message_dto.attachment[0])
        self.assertIn(
            dto.attachment[1], str(email_message_dto.attachment[1]),
        )
        self.assertEqual(dto.subject, self.licence_usage_file_name)
        self.assertEqual(dto.receiver, "spire")
        self.assertEqual(dto.body, None)
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

        self.assertEqual(serialize_email_message(email_message_dto), False)

    @tag("new")
    def test_licence_reply_dto_to_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="receiver@example.com",
            body=None,
            subject=self.licence_update_reply_name,
            attachment=[
                self.licence_update_reply_name,
                self.licence_update_reply_body,
            ],
            raw_data="qwerty",
        )

        self.mail.status = ReceptionStatusEnum.REPLY_PENDING
        self.mail.extract_type = ExtractTypeEnum.LICENCE_UPDATE
        self.mail.save()

        # dto to dto processing
        mail = serialize_email_message(email_message_dto)
        dto = to_email_message_dto_from(mail)

        self.assertEqual(dto.run_number, self.licence_update.source_run_number)
        self.assertEqual(dto.sender, "test@spire.com")
        self.assertEqual(dto.attachment[0], email_message_dto.attachment[0])
        self.assertIn(
            dto.attachment[1], str(email_message_dto.attachment[1]),
        )
        self.assertEqual(dto.subject, self.licence_update_reply_name)
        self.assertEqual(dto.receiver, "spire")
        self.assertEqual(dto.body, None)
        self.assertEqual(dto.raw_data, None)

    def test_licence_update_dto_to_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="receiver@example.com",
            body=None,
            subject=self.licence_update_file_name,
            attachment=[self.licence_update_file_name, self.licence_update_reply_body,],
            raw_data="qwerty",
        )

        # dto to dto processing
        mail = serialize_email_message(email_message_dto)
        dto = to_email_message_dto_from(mail)

        self.assertEqual(dto.run_number, self.licence_update.hmrc_run_number + 1)
        self.assertEqual(dto.sender, SPIRE_ADDRESS)
        self.assertEqual(dto.attachment[0], email_message_dto.attachment[0])
        self.assertIn(
            dto.attachment[1], str(email_message_dto.attachment[1]),
        )
        self.assertEqual(dto.subject, self.licence_update_reply_name)
        self.assertEqual(dto.receiver, HMRC_ADDRESS)
        self.assertEqual(dto.body, None)
        self.assertEqual(dto.raw_data, None)
