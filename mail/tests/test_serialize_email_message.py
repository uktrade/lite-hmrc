import logging
from django.test import tag
from conf.settings import SPIRE_ADDRESS, HMRC_ADDRESS
from conf.test_client import LiteHMRCTestClient
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate, UsageUpdate
from mail.services.data_processors import (
    to_email_message_dto_from,
    serialize_email_message,
)
from mail.services.logging_decorator import lite_log
from mail.tests.test_helpers import print_all_mails

logger = logging.getLogger(__name__)


class SerializeEmailMessageTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.hmrc_run_number = 28
        self.source_run_number = 15
        self.license_ids = "GBOIE2017/12345B"
        self.mail = Mail.objects.create(
            edi_data=self.licence_usage_file_body,
            extract_type=ExtractTypeEnum.LICENCE_UPDATE,
            status=ReceptionStatusEnum.PENDING,
            edi_filename=self.licence_usage_file_name,
        )

        self.licence_update = LicenceUpdate.objects.create(
            mail=self.mail,
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            license_ids=self.license_ids,
            source=SourceEnum.SPIRE,
        )

        self.usage_update = UsageUpdate.objects.create(
            mail=self.mail,
            spire_run_number=self.source_run_number,
            license_ids=self.license_ids,
            hmrc_run_number=self.hmrc_run_number,
        )

    @tag("failed")
    def test_successful_usage_update_inbound_dto_converts_to_outbound_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender=HMRC_ADDRESS,
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
        self.assertEqual(dto.sender, HMRC_ADDRESS)
        self.assertEqual(dto.attachment[0], email_message_dto.attachment[0])
        self.assertIn(
            dto.attachment[1], str(email_message_dto.attachment[1]),
        )
        self.assertEqual(dto.subject, self.licence_usage_file_name)
        self.assertEqual(dto.receiver, SPIRE_ADDRESS)
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

    @tag("skip")
    def test_licence_reply_mail_serialized(self):
        # license update mail received
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender=HMRC_ADDRESS,
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
        lite_log(logger, logging.DEBUG, "# email_message_dto saved")
        print_all_mails()
        # serialize mail message
        _mail = serialize_email_message(email_message_dto)
        dto_from_serialized_mail = to_email_message_dto_from(_mail)

        self.assertEqual(
            dto_from_serialized_mail.run_number, self.licence_update.source_run_number
        )
        self.assertEqual(dto_from_serialized_mail.sender, HMRC_ADDRESS)
        self.assertEqual(
            dto_from_serialized_mail.attachment[0], email_message_dto.attachment[0]
        )
        self.assertIn(
            dto_from_serialized_mail.attachment[1],
            str(email_message_dto.attachment[1]),
        )
        self.assertEqual(
            dto_from_serialized_mail.subject, self.licence_update_reply_name
        )
        self.assertEqual(dto_from_serialized_mail.receiver, SPIRE_ADDRESS)
        self.assertEqual(dto_from_serialized_mail.body, None)
        self.assertEqual(dto_from_serialized_mail.raw_data, None)

    @tag("skip")
    def test_licence_update_dto_to_dto(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender=SPIRE_ADDRESS,
            receiver=HMRC_ADDRESS,
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
        self.assertEqual(dto.subject, self.licence_update_file_name)
        self.assertEqual(dto.receiver, HMRC_ADDRESS)
        self.assertEqual(dto.body, None)
        self.assertEqual(dto.raw_data, None)
