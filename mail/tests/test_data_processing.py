import base64

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate, UsageUpdate
from mail.services.data_processing import (
    process_and_save_email_message,
    to_email_message_dto_from,
)
from mail.services.helpers import convert_source_to_sender


class TestModels(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.hmrc_run_number = 28
        self.source_run_number = 15
        self.mail = Mail.objects.create(
            edi_data=str(base64.b64decode(self.licence_usage_file_body)).replace(
                "\\\\", "\\"
            ),
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
            status=ReceptionStatusEnum.REPLY_SENT,
            edi_filename=self.licence_usage_file_name,
        )

        self.licence_update = LicenceUpdate.objects.create(
            mail=self.mail,
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            source=SourceEnum.SPIRE,
        )

    @tag("body")
    def test_email_processed_successfully(self):
        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="test@spire.com",
            body="body",
            subject=self.licence_usage_file_name,
            attachment=[self.licence_usage_file_name, self.licence_usage_file_body],
            raw_data="qwerty",
        )

        process_and_save_email_message(email_message_dto)

        email = Mail.objects.valid().last()
        usage_update = UsageUpdate.objects.get(mail=email)

        self.assertEqual(
            email.edi_data,
            str(base64.b64decode(email_message_dto.attachment[1])).replace(
                "\\\\", "\\"
            ),
        )
        self.assertEqual(email.extract_type, ExtractTypeEnum.USAGE_UPDATE)
        self.assertEqual(email.response_filename, None)
        self.assertEqual(email.response_data, None)
        self.assertEqual(email.edi_filename, email_message_dto.attachment[0])
        self.assertEqual(usage_update.spire_run_number, self.source_run_number + 1)
        self.assertEqual(usage_update.hmrc_run_number, email_message_dto.run_number)
        self.assertEqual(email.raw_data, email_message_dto.raw_data)

    @tag("bad")
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
        initial_license_update_count = Mail.objects.valid().count()

        process_and_save_email_message(email_message_dto)

        self.assertEqual(Mail.objects.invalid().count(), initial_issues_count + 1)
        self.assertEqual(Mail.objects.valid().count(), initial_license_update_count)

        email = Mail.objects.invalid().last()

        self.assertEqual(email.edi_data, "")
        self.assertEqual(email.extract_type, None)
        self.assertEqual(email.response_filename, None)
        self.assertEqual(email.response_data, None)
        self.assertEqual(email.edi_filename, "")
        self.assertEqual(email.raw_data, email_message_dto.raw_data)

    def test_successful_email_db_record_converted_to_dto(self):
        self.mail.edi_data = self.licence_usage_file_body.decode("ascii", "replace")
        dto = to_email_message_dto_from(self.mail)

        self.assertEqual(dto.run_number, self.licence_update.hmrc_run_number)
        self.assertEqual(
            dto.sender, convert_source_to_sender(self.licence_update.source)
        )
        self.assertEqual(dto.attachment[0], self.mail.edi_filename)
        self.assertEqual(
            dto.attachment[1], self.mail.edi_data.encode("ascii", "replcae")
        )
        self.assertEqual(dto.subject, self.mail.edi_filename)
        self.assertEqual(dto.receiver, "HMRC")
        self.assertEqual(dto.body, "")
        self.assertEqual(dto.raw_data, None)

    @tag("reply")
    def test_licence_update_reply_is_saved(self):
        self.mail.extract_type = ExtractTypeEnum.LICENCE_UPDATE
        self.mail.status = ReceptionStatusEnum.REPLY_PENDING
        self.mail.save()

        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="receiver@example.com",
            body="body",
            subject=self.licence_update_reply_name,
            attachment=[
                self.licence_update_reply_name,
                bytes(self.licence_update_reply_body, "utf-8"),
            ],
            raw_data="qwerty",
        )

        process_and_save_email_message(email_message_dto)
        self.mail.refresh_from_db()

        self.assertEqual(
            self.mail.response_data,
            str(base64.b64decode(self.licence_update_reply_body)).replace("\\\\", "\\"),
        )
        self.assertEqual(self.mail.status, ReceptionStatusEnum.REPLY_RECEIVED)
        self.assertIsNotNone(self.mail.response_date)

    def test_usage_update_reply_is_saved(self):
        self.mail.status = ReceptionStatusEnum.REPLY_PENDING
        self.mail.save()

        email_message_dto = EmailMessageDto(
            run_number=self.source_run_number + 1,
            sender="HMRC",
            receiver="receiver@example.com",
            body="body",
            subject=self.licence_update_reply_name,
            attachment=[
                self.licence_update_reply_name,
                bytes(self.licence_update_reply_body, "utf-8"),
            ],
            raw_data="qwerty",
        )

        process_and_save_email_message(email_message_dto)
        self.mail.refresh_from_db()

        self.assertEqual(
            self.mail.response_data,
            str(base64.b64decode(self.licence_update_reply_body)).replace("\\\\", "\\"),
        )
        self.assertEqual(self.mail.status, ReceptionStatusEnum.REPLY_RECEIVED)
        self.assertIsNotNone(self.mail.response_date)
