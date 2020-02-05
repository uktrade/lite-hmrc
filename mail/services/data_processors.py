import logging
import threading

from django.db import transaction
from django.utils import timezone

from conf.settings import (
    SYSTEM_INSTANCE_UUID,
    LOCK_INTERVAL,
    HMRC_ADDRESS,
    SPIRE_ADDRESS,
)
from mail.dtos import EmailMessageDto, dto_to_logs
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.models import LicenceUpdate, Mail, UsageUpdate
from mail.serializers import (
    InvalidEmailSerializer,
    LicenceUpdateMailSerializer,
    UpdateResponseSerializer,
    UsageUpdateMailSerializer,
)
from mail.services.data_converters import (
    convert_data_for_licence_update,
    convert_data_for_licence_update_reply,
    convert_data_for_usage_update,
    convert_data_for_usage_update_reply,
)
from mail.services.helpers import (
    process_attachment,
    get_extract_type,
    get_all_serializer_errors_for_mail,
)
from mail.services.logging_decorator import lite_logging_decorator


@lite_logging_decorator
def serialize_email_message(dto: EmailMessageDto):
    data, serializer, instance = convert_dto_data_for_serialization(dto)

    partial = True if instance else False
    if serializer:
        serializer = serializer(instance=instance, data=data, partial=partial)
    if serializer and serializer.is_valid():
        mail = serializer.save()
        if data["extract_type"] in ["licence_reply", "usage_reply"]:
            mail.set_response_date_time()
        return mail
    else:
        data["serializer_errors"] = get_all_serializer_errors_for_mail(data)
        logging.info(
            {
                "message": "liteolog hmrc",
                "info": "email considered invalid",
                "serializer_errors": data["serializer_errors"],
            }
        )
        serializer = InvalidEmailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
    return False


@lite_logging_decorator
def convert_dto_data_for_serialization(dto: EmailMessageDto):
    serializer = None
    mail = None
    extract_type = get_extract_type(dto.subject)
    logging.info({"email type identified as": extract_type})

    if extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        data = convert_data_for_licence_update(dto)
        serializer = LicenceUpdateMailSerializer

    elif extract_type == ExtractTypeEnum.LICENCE_REPLY:
        data, mail = convert_data_for_licence_update_reply(dto)
        serializer = UpdateResponseSerializer

    elif extract_type == ExtractTypeEnum.USAGE_UPDATE:
        data = convert_data_for_usage_update(dto)
        serializer = UsageUpdateMailSerializer

    elif extract_type == ExtractTypeEnum.USAGE_REPLY:
        data, mail = convert_data_for_usage_update_reply(dto)
        serializer = UpdateResponseSerializer

    else:
        data = {}
        data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)

    data["extract_type"] = extract_type
    data["raw_data"] = dto.raw_data
    logging.info(
        {
            "exiting function with": {
                "data": data,
                "serializer": serializer,
                "instance": mail,
            }
        }
    )
    return data, serializer, mail


def to_email_message_dto_from(mail):
    if mail.status == ReceptionStatusEnum.PENDING:
        print("pending")
        return _build_request_mail_message_dto(mail)
    elif mail.status == ReceptionStatusEnum.REPLY_RECEIVED:
        print("reply pending")
        return _build_reply_mail_message_dto(mail)
    raise ValueError("Invalid mail status: {}".format(mail.status))


def lock_db_for_sending_transaction(mail):
    mail.refresh_from_db()
    previous_locking_process_id = mail.currently_processed_by
    if (
        not previous_locking_process_id
        or (timezone.now() - mail.currently_processing_at).total_seconds()
        > LOCK_INTERVAL
    ):
        with transaction.atomic():
            _mail = Mail.objects.select_for_update().get(id=mail.id)
            if _mail.currently_processed_by != previous_locking_process_id:
                return
            _mail.currently_processed_by = (
                str(SYSTEM_INSTANCE_UUID) + "-" + str(threading.currentThread().ident)
            )
            _mail.set_locking_time()
            _mail.save()

            return True


def _build_request_mail_message_dto(mail):
    sender = SPIRE_ADDRESS
    receiver = HMRC_ADDRESS
    if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        print("licence update")
        licence_update = LicenceUpdate.objects.get(mail=mail)
        run_number = licence_update.hmrc_run_number
    elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
        print("usage update")
        update = UsageUpdate.objects.get(mail=mail)
        run_number = update.spire_run_number
        sender = HMRC_ADDRESS
        receiver = SPIRE_ADDRESS

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=mail.edi_filename,
        body=None,
        attachment=[mail.edi_filename, mail.edi_data],
        raw_data=None,
    )


def _build_reply_mail_message_dto(mail):
    sender = HMRC_ADDRESS
    receiver = SPIRE_ADDRESS
    if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        print("licence reply")
        licence_update = LicenceUpdate.objects.get(mail=mail)
        run_number = licence_update.source_run_number
    elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
        print("usage reply")
        update = LicenceUpdate.objects.get(mail=mail)
        run_number = update.spire_run_number
        sender = SPIRE_ADDRESS
        receiver = HMRC_ADDRESS

    return EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=mail.edi_filename,
        body=None,
        attachment=[mail.edi_filename, mail.edi_data],
        raw_data=None,
    )
