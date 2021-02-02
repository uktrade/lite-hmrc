import json
import logging

from django.conf import settings
from django.utils import timezone
from mail.libraries.routing_controller import get_spire_standin_mailserver

from mail.enums import ExtractTypeEnum
from mail.libraries.helpers import get_extract_type
from mail.libraries.data_processors import convert_dto_data_for_serialization
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.routing_controller import send
from mock_hmrc import models, enums

MOCK_HMRC_SUPPORTED_EXTRACT_TYPES = [ExtractTypeEnum.LICENCE_DATA]


def update_retrieved_email_status(dto, status):
    data = {"message_id": dto.message_id, "sender": dto.sender, "status": status}
    models.RetrievedMail.objects.get_or_create(**data)


def save_hmrc_email_message_data(dto):
    extract_type = get_extract_type(dto.subject)
    if not extract_type:
        update_retrieved_email_status(dto, enums.RetrievedEmailStatusEnum.INVALID)
        logging.info(f"Extract type not supported ({dto.subject}), skipping")
        return None

    data = convert_dto_data_for_serialization(dto, extract_type)

    # ensure there is run number
    if data["licence_data"]["source_run_number"] is None:
        logging.error("Invalid email received")
        update_retrieved_email_status(dto, enums.RetrievedEmailStatusEnum.INVALID)
        return None

    source_run_number = data["licence_data"]["source_run_number"]
    try:
        hmrc_mail = models.HmrcMail.objects.get(extract_type=extract_type, source_run_number=source_run_number)
    except models.HmrcMail.DoesNotExist:
        hmrc_mail = models.HmrcMail.objects.create(
            extract_type=extract_type,
            source_run_number=data["licence_data"]["source_run_number"],
            source=data["licence_data"]["source"],
            edi_filename=data["edi_filename"],
            edi_data=data["edi_data"],
            licence_ids=data["licence_data"]["licence_ids"],
        )
        update_retrieved_email_status(dto, enums.RetrievedEmailStatusEnum.VALID)

    return hmrc_mail


def build_reply_pending_filename(filename):
    return f"{filename}_reply"


def build_reply_pending_file_data(mail):
    """
    Builds a reply file that looks like an actual reply from HMRC

    Since we are simulating this only some of the cases are included.
    Eg rejected and error cases are not considered.
    """
    line_num = 1
    reply_created_time = timezone.localtime().strftime("%Y%m%d%H%M")
    data = []
    data.append(
        f"{line_num}\\fileHeader\\CHIEF\\SPIRE\\licenceDataReply\\{reply_created_time}\\{mail.source_run_number}"
    )
    accepted_ids = json.loads(mail.licence_ids)
    for index, id in enumerate(accepted_ids, start=1):
        line_num += index
        data.append(f"{line_num}\\accepted\\{id}")

    data.append(f"{line_num}\\fileTrailer\\{len(accepted_ids)}\\0\\0")
    file_data = "\n".join(data)

    return file_data


def build_reply_mail_message_dto(mail) -> EmailMessageDto:
    sender = None
    receiver = None

    if mail.extract_type not in MOCK_HMRC_SUPPORTED_EXTRACT_TYPES:
        return None

    sender = settings.MOCK_HMRC_EMAIL_USER
    receiver = settings.SPIRE_STANDIN_EMAIL_USER
    attachment = [
        build_reply_pending_filename(mail.edi_filename),
        build_reply_pending_file_data(mail),
    ]

    return EmailMessageDto(
        run_number=mail.source_run_number,
        sender=sender,
        receiver=receiver,
        subject=attachment[0],
        body=None,
        attachment=attachment,
        raw_data=None,
    )


def to_email_message_dto_from(hmrc_mail):
    if hmrc_mail.status == enums.HmrcMailStatusEnum.ACCEPTED:
        return build_reply_mail_message_dto(hmrc_mail)

    return None


def send_reply(email):
    message_to_send = to_email_message_dto_from(email)
    if message_to_send:
        server = get_spire_standin_mailserver()
        send(server, message_to_send)
