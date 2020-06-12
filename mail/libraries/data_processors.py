import logging
import threading

from django.db import transaction
from django.utils import timezone

from conf.settings import SYSTEM_INSTANCE_UUID, LOCK_INTERVAL, HMRC_ADDRESS, SPIRE_ADDRESS, EMAIL_USER
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.libraries.data_converters import (
    convert_data_for_licence_update,
    convert_data_for_licence_update_reply,
    convert_data_for_usage_update,
    convert_data_for_usage_update_reply,
)
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.helpers import (
    process_attachment,
    get_extract_type,
    convert_source_to_sender,
)
from mail.libraries.mailbox_service import find_mail_of
from mail.models import LicenceUpdate, Mail, UsageUpdate
from mail.serializers import (
    LicenceUpdateMailSerializer,
    UpdateResponseSerializer,
    UsageUpdateMailSerializer,
)


def serialize_email_message(dto: EmailMessageDto) -> Mail or None:
    extract_type = get_extract_type(dto.subject)
    if not extract_type:
        return

    instance = get_mail_instance(extract_type, dto.run_number)
    if not instance and extract_type in [ExtractTypeEnum.LICENCE_REPLY, ExtractTypeEnum.USAGE_REPLY]:
        return

    partial = True if instance else False
    data = convert_dto_data_for_serialization(dto, extract_type)
    serializer = get_serializer_for_dto(extract_type)
    serializer = serializer(instance=instance, data=data, partial=partial)

    if serializer.is_valid():
        _mail = serializer.save()
        if data["extract_type"] in ["licence_reply", "usage_reply"]:
            _mail.set_response_date_time()

        logging.info("Successfully serialized email")
        return _mail
    else:
        logging.error(f"Failed to serialize email -> {serializer.errors}")


def convert_dto_data_for_serialization(dto: EmailMessageDto, extract_type):
    """
    Based on given mail message dto, prepare data for mail serialization.
    :param dto: the dto to be used
    :return: new dto for different extract type; corresponding Serializer;
            and existing mail if extract type is of reply. Both serializer and mail could be None
    """
    if extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        data = convert_data_for_licence_update(dto)
    elif extract_type == ExtractTypeEnum.LICENCE_REPLY:
        data = convert_data_for_licence_update_reply(dto)
    elif extract_type == ExtractTypeEnum.USAGE_UPDATE:
        data = convert_data_for_usage_update(dto)
    elif extract_type == ExtractTypeEnum.USAGE_REPLY:
        data = convert_data_for_usage_update_reply(dto)
    else:
        # todo raise ValueError here
        filename, filedata = process_attachment(dto.attachment)
        data = {
            "edi_filename": filename,
            "edi_data": filedata,
        }

    data["extract_type"] = extract_type
    data["raw_data"] = dto.raw_data

    return data


def get_serializer_for_dto(extract_type):
    serializer = None
    if extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        serializer = LicenceUpdateMailSerializer
    elif extract_type == ExtractTypeEnum.LICENCE_REPLY:
        serializer = UpdateResponseSerializer
    elif extract_type == ExtractTypeEnum.USAGE_UPDATE:
        serializer = UsageUpdateMailSerializer
    elif extract_type == ExtractTypeEnum.USAGE_REPLY:
        serializer = UpdateResponseSerializer

    return serializer


def get_mail_instance(extract_type, run_number) -> Mail or None:
    if extract_type == ExtractTypeEnum.LICENCE_REPLY:

        last_email = LicenceUpdate.objects.filter(hmrc_run_number=run_number).last()

        if last_email and last_email.mail.status == ReceptionStatusEnum.REPLY_SENT:
            logging.info("Licence update reply has already been processed")
            return
        return find_mail_of(ExtractTypeEnum.LICENCE_UPDATE, ReceptionStatusEnum.REPLY_PENDING)
    elif extract_type == ExtractTypeEnum.USAGE_REPLY:
        if UsageUpdate.objects.filter(spire_run_number=run_number).last().mail.status == ReceptionStatusEnum.REPLY_SENT:
            logging.info("Usage update reply has already been processed")
            return
        return find_mail_of(ExtractTypeEnum.USAGE_UPDATE, ReceptionStatusEnum.REPLY_PENDING)


def to_email_message_dto_from(mail: Mail):
    _check_and_raise_error(mail, "Invalid mail object received!")
    logging.debug(f"converting mail with status [{mail.status}] extract_type [{mail.extract_type}] to EmailMessageDto")
    if mail.status == ReceptionStatusEnum.PENDING:
        logging.debug(f"building request mail message dto from [{mail.status}] mail status")
        return build_request_mail_message_dto(mail)
    elif mail.status == ReceptionStatusEnum.REPLY_RECEIVED:
        logging.debug(f"building reply mail message dto from [{mail.status}] mail status")
        return _build_reply_mail_message_dto(mail)
    raise ValueError(f"Unexpected mail with status [{mail.status}] while converting to EmailMessageDto")


def lock_db_for_sending_transaction(mail: Mail):
    mail.refresh_from_db()
    previous_locking_process_id = mail.currently_processed_by
    if (
        not previous_locking_process_id
        or (timezone.now() - mail.currently_processing_at).total_seconds() > LOCK_INTERVAL
    ):
        with transaction.atomic():
            _mail = Mail.objects.select_for_update().get(id=mail.id)
            if _mail.currently_processed_by != previous_locking_process_id:
                return
            _mail.currently_processed_by = str(SYSTEM_INSTANCE_UUID) + "-" + str(threading.currentThread().ident)
            _mail.set_locking_time()
            _mail.save()

            return True


def build_request_mail_message_dto(mail: Mail):
    sender = None
    receiver = None
    run_number = 0

    if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        sender = EMAIL_USER
        receiver = HMRC_ADDRESS
        licence_update = LicenceUpdate.objects.get(mail=mail)
        run_number = licence_update.hmrc_run_number
    elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
        sender = HMRC_ADDRESS
        receiver = SPIRE_ADDRESS
        update = UsageUpdate.objects.get(mail=mail)
        run_number = update.spire_run_number

    print("\n\n\n", mail.edi_filename, "\n\n\n")

    attachment = [
        build_sent_filename(mail.edi_filename, run_number),
        build_sent_file_data(mail.edi_data, run_number),
    ]

    print("\n\n\n", attachment[0], "\n\n\n")

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=attachment[0],
        body=None,
        attachment=attachment,
        raw_data=None,
    )


def build_sent_filename(filename: str, run_number):
    filename = filename.split("_")
    filename[4] = str(run_number)
    return "_".join(filename)


def build_sent_file_data(file_data: str, run_number):
    file_data_lines = file_data.split("\n", 1)

    file_data_line_1 = file_data_lines[0]
    file_data_line_1 = file_data_line_1.split("\\")
    file_data_line_1[6] = str(run_number)
    file_data_line_1 = "\\".join(file_data_line_1)

    return file_data_line_1 + "\n" + file_data_lines[1]


def _build_reply_mail_message_dto(mail):
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

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=mail.response_subject,
        body=None,
        attachment=[mail.response_filename, mail.response_data],
        raw_data=None,
    )


def _check_and_raise_error(obj, error_msg: str):
    if obj is None:
        raise ValueError(error_msg)
