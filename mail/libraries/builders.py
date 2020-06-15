import json

from django.utils import timezone

from conf.settings import HMRC_ADDRESS, SPIRE_ADDRESS, EMAIL_USER
from mail.enums import SourceEnum, ExtractTypeEnum
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import convert_source_to_sender
from mail.libraries.lite_to_edifact_converter import licences_to_edifact
from mail.models import LicenceUpdate, Mail, UsageUpdate


def build_request_mail_message_dto(mail: Mail) -> EmailMessageDto:
    sender = None
    receiver = None
    run_number = 0

    if mail.extract_type in [ExtractTypeEnum.LICENCE_UPDATE, ExtractTypeEnum.USAGE_REPLY]:
        sender = EMAIL_USER
        receiver = HMRC_ADDRESS
        licence_update = LicenceUpdate.objects.get(mail=mail)
        run_number = licence_update.hmrc_run_number
    elif mail.extract_type in [ExtractTypeEnum.USAGE_UPDATE, ExtractTypeEnum.LICENCE_REPLY]:
        sender = HMRC_ADDRESS
        receiver = SPIRE_ADDRESS
        update = UsageUpdate.objects.get(mail=mail)
        run_number = update.spire_run_number

    attachment = [
        build_sent_filename(mail.edi_filename, run_number),
        build_sent_file_data(mail.edi_data, run_number),
    ]

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=attachment[0],
        body=None,
        attachment=attachment,
        raw_data=None,
    )


def build_sent_filename(filename: str, run_number: int) -> str:
    filename = filename.split("_")
    filename[4] = str(run_number)
    return "_".join(filename)


def build_sent_file_data(file_data: str, run_number: int) -> str:
    file_data_lines = file_data.split("\n", 1)

    file_data_line_1 = file_data_lines[0]
    file_data_line_1 = file_data_line_1.split("\\")
    file_data_line_1[6] = str(run_number)
    file_data_line_1 = "\\".join(file_data_line_1)

    return file_data_line_1 + "\n" + file_data_lines[1]


def build_reply_mail_message_dto(mail) -> EmailMessageDto:
    sender = HMRC_ADDRESS
    receiver = SPIRE_ADDRESS
    run_number = None

    if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        licence_update = LicenceUpdate.objects.get(mail=mail)
        run_number = licence_update.source_run_number
        receiver = convert_source_to_sender(licence_update.source)
    elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
        usage_update = UsageUpdate.objects.get(mail=mail)
        run_number = usage_update.spire_run_number
        sender = SPIRE_ADDRESS
        receiver = HMRC_ADDRESS

    attachment = [
        build_sent_filename(mail.response_filename, run_number),
        build_sent_file_data(mail.response_data, run_number),
    ]

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=attachment[0],
        body=None,
        attachment=attachment,
        raw_data=None,
    )


def build_update_mail(licences) -> Mail:
    last_lite_update = LicenceUpdate.objects.last()
    run_number = last_lite_update.hmrc_run_number + 1 if last_lite_update else 1
    file_name, file_content = build_licence_updates_file(licences, run_number)
    mail = Mail.objects.create(
        edi_filename=file_name,
        edi_data=file_content,
        extract_type=ExtractTypeEnum.LICENCE_UPDATE,
        raw_data="See Licence Payload",
    )
    licence_ids = json.dumps([str(licence.reference) for licence in licences])
    LicenceUpdate.objects.create(hmrc_run_number=run_number, source=SourceEnum.LITE, mail=mail, licence_ids=licence_ids)

    return mail


def build_licence_updates_file(licences, run_number) -> (str, str):
    now = timezone.now()
    file_name = "ILBDOTI_live_CHIEF_licenceUpdate_{}_{:04d}{:02d}{:02d}{:02d}{:02d}".format(
        run_number, now.year, now.month, now.day, now.hour, now.minute
    )

    file_content = licences_to_edifact(licences, run_number)

    return file_name, file_content
