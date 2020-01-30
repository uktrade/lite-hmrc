import threading

from django.db import transaction
from django.utils import timezone

from conf.constants import VALID_SENDERS
from conf.settings import (
    SYSTEM_INSTANCE_UUID,
    LOCK_INTERVAL,
    HMRC_ADDRESS,
    SPIRE_ADDRESS,
)
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.models import LicenceUpdate, Mail, UsageUpdate
from mail.serializers import (
    InvalidEmailSerializer,
    LicenceUpdateMailSerializer,
    UpdateResponseSerializer,
    UsageUpdateMailSerializer,
)
from mail.services.helpers import (
    convert_sender_to_source,
    process_attachment,
    new_hmrc_run_number,
    new_spire_run_number,
    convert_source_to_sender,
    get_extract_type,
    get_licence_ids,
    get_all_serializer_errors_for_mail,
)


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

        serializer = InvalidEmailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
    return False


def convert_dto_data_for_serialization(dto: EmailMessageDto):
    serializer = None
    mail = None
    extract_type = get_extract_type(dto.subject)

    print(extract_type)

    if extract_type == ExtractTypeEnum.LICENCE_UPDATE:
        data = {"licence_update": {}}
        data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)
        data["licence_update"]["source"] = convert_sender_to_source(dto.sender)
        data["licence_update"]["hmrc_run_number"] = (
            new_hmrc_run_number(int(dto.run_number))
            if convert_sender_to_source(dto.sender) in VALID_SENDERS
            else None
        )
        data["licence_update"]["source_run_number"] = dto.run_number
        data["licence_update"]["license_ids"] = get_licence_ids(data["edi_data"])
        serializer = LicenceUpdateMailSerializer

    elif extract_type == ExtractTypeEnum.LICENCE_REPLY:
        print("i am a licence reply")
        data = {}
        serializer = UpdateResponseSerializer
        data["response_filename"], data["response_data"] = process_attachment(
            dto.attachment
        )
        data["status"] = ReceptionStatusEnum.REPLY_RECEIVED
        mail = Mail.objects.get(
            status=ReceptionStatusEnum.REPLY_PENDING,
            extract_type=ExtractTypeEnum.LICENCE_UPDATE,
        )

    elif extract_type == ExtractTypeEnum.USAGE_UPDATE:
        data = {"usage_update": {}}
        data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)
        data["usage_update"]["spire_run_number"] = (
            new_spire_run_number(int(dto.run_number))
            if convert_sender_to_source(dto.sender) in VALID_SENDERS
            else None
        )
        data["usage_update"]["hmrc_run_number"] = dto.run_number
        data["usage_update"]["license_ids"] = get_licence_ids(data["edi_data"])
        serializer = UsageUpdateMailSerializer

    elif extract_type == ExtractTypeEnum.USAGE_REPLY:
        data = {}
        serializer = UpdateResponseSerializer
        data["response_filename"], data["response_data"] = process_attachment(
            dto.attachment
        )
        data["status"] = ReceptionStatusEnum.REPLY_RECEIVED
        mail = Mail.objects.get(
            status=ReceptionStatusEnum.REPLY_PENDING,
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
        )
    else:
        data = {}
        data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)

    data["extract_type"] = extract_type
    data["raw_data"] = dto.raw_data
    return data, serializer, mail


def to_email_message_dto_from(mail):
    if mail.status == ReceptionStatusEnum.PENDING:
        print("pending")
        if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
            print("licence update")
            licence_update = LicenceUpdate.objects.get(mail=mail)
            run_number = licence_update.hmrc_run_number
            sender = SPIRE_ADDRESS
            receiver = HMRC_ADDRESS
        elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
            print("usage update")
            update = UsageUpdate.objects.get(mail=mail)
            run_number = update.spire_run_number
            sender = HMRC_ADDRESS
            receiver = SPIRE_ADDRESS
        subject = mail.edi_filename
        filename = mail.edi_filename
        filedata = mail.edi_data
    elif mail.status == ReceptionStatusEnum.REPLY_RECEIVED:
        print("reply pending")
        if mail.extract_type == ExtractTypeEnum.LICENCE_UPDATE:
            print("licence reply")
            licence_update = LicenceUpdate.objects.get(mail=mail)
            run_number = licence_update.source_run_number
            sender = HMRC_ADDRESS
            receiver = SPIRE_ADDRESS
        elif mail.extract_type == ExtractTypeEnum.USAGE_UPDATE:
            print("usage reply")
            update = LicenceUpdate.objects.get(mail=mail)
            run_number = update.spire_run_number
            sender = SPIRE_ADDRESS
            receiver = HMRC_ADDRESS
        subject = mail.response_filename
        filename = mail.response_filename
        filedata = mail.response_data

    dto = EmailMessageDto(
        run_number=run_number,
        sender=sender,
        receiver=receiver,
        subject=subject,
        body=None,
        attachment=[filename, filedata],
        raw_data=None,
    )
    return dto


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
