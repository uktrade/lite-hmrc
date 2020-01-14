import json

from conf.constants import VALID_SENDERS
from mail.dtos import EmailMessageDto
from mail.models import Mail
from mail.serializers import (
    InvalidEmailSerializer,
    LicenceUpdateMailSerializer,
    LicenceUpdateUpdateSerializer,
)
from mail.services.helpers import (
    convert_sender_to_source,
    process_attachment,
    new_hmrc_run_number,
)


def process_and_save_email_message(dto: EmailMessageDto):
    data, serializer, instance = convert_dto_data_for_serialization(dto)
    serializer = serializer(instance=instance, data=data)

    if serializer.is_valid():
        mail = serializer.save()
        return mail
    else:
        data["serializer_errors"] = str(serializer.errors)
        serializer = InvalidEmailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
    return False


def convert_dto_data_for_serialization(dto: EmailMessageDto):
    if convert_sender_to_source(dto.sender) in VALID_SENDERS:
        data = _for_licence_update_outbound(dto)
        serializer = LicenceUpdateMailSerializer
        return data, serializer, None
    elif convert_sender_to_source(dto.sender) == "HMRC":
        data, instance = _for_licence_update_response(dto)
        serializer = LicenceUpdateUpdateSerializer(partial=True)
        return data, serializer, instance
    # TODO: Licence Usage emails
    # TODO: Refine conditions and create a serializer to valid against all fields for bad emails
    else:
        data = _for_licence_update_outbound(dto)
        serializer = LicenceUpdateMailSerializer
        return data, serializer, None


def collect_and_send_data_to_dto(mail: Mail):
    # determine run_number to use
    # get data out
    # return dto
    return True


def _for_licence_update_outbound(dto: EmailMessageDto):
    data = {"licence_update": {}}
    data["licence_update"]["source"] = convert_sender_to_source(dto.sender)
    data["licence_update"]["hmrc_run_number"] = new_hmrc_run_number(dto.run_number)
    data["licence_update"]["source_run_number"] = dto.run_number

    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)

    data["extract_type"] = "insert"  # TODO: extract from data
    data["licence_update"]["license_ids"] = json.dumps(
        ["00000000-0000-0000-0000-000000000001"]
    )  # TODO: extract from data
    data["raw_data"] = dto.raw_data

    return data


def _for_licence_update_response(dto: EmailMessageDto):
    return True
