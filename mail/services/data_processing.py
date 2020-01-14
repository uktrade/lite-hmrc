from mail.dtos import EmailMessageDto
from mail.enums import SourceEnum
from mail.models import LicenceUpdate
from mail.serializers import InvalidEmailSerializer, LicenceUpdateMailSerializer
from mail.services.helpers import (
    convert_sender_to_source,
    process_attachment,
)


def process_and_save_email_message(dto: EmailMessageDto):
    data = convert_dto_data_for_serialization(dto)
    print("\n")
    print(data)
    print("\n")

    serializer = LicenceUpdateMailSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return True
    else:
        data["serializer_errors"] = str(serializer.errors)
        serializer = InvalidEmailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
    return False


def convert_dto_data_for_serialization(dto: EmailMessageDto):
    data = {"licence_update": {}}
    data["licence_update"]["source"] = convert_sender_to_source(dto.sender)

    # Needs working out
    if convert_sender_to_source(dto.sender) == SourceEnum.SPIRE:
        last_licence_update = LicenceUpdate.objects.last()
        if not last_licence_update.source_run_number == dto.run_number:
            if last_licence_update:
                data["licence_update"]["hmrc_run_number"] = (
                    last_licence_update.hmrc_run_number + 1
                    if last_licence_update.hmrc_run_number != 99999
                    else 0
                )
            else:
                data["licence_update"]["hmrc_run_number"] = 1
        else:
            data["licence_update"][
                "hmrc_run_number"
            ] = last_licence_update.hmrc_run_number
    elif convert_sender_to_source(dto.sender) == SourceEnum.LITE:
        data["licence_update"]["hmrc_run_number"] = 1

    data["licence_update"]["source_run_number"] = dto.run_number

    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)

    data["extract_type"] = "insert"  # TODO: extract from data
    data["licence_update"]["license_ids"] = [
        "00000000-0000-0000-0000-000000000001"
    ]  # TODO: extract from data
    data["raw_data"] = dto.raw_data

    return data


def collect_and_send_data_to_dto():
    # determine run_number to use
    # get data out
    # return dto
    return True
