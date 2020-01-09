from mail.dtos import EmailMessageDto
from mail.helpers import sender_to_source, process_attachment
from mail.models import LicenseUpdate
from mail.serializers import LicenseUpdateSerializer, InvalidEmailSerializer


def process_and_save_email_message(dto: EmailMessageDto):
    data = {}
    last_hmrc_number = LicenseUpdate.objects.last().hmrc_run_number
    data["hmrc_run_number"] = last_hmrc_number + 1 if last_hmrc_number != 99999 else 0
    data["source_run_number"] = dto.run_number
    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)
    data["extract_type"] = "insert"  # TODO: extract from data
    data[
        "license_id"
    ] = "00000000-0000-0000-0000-000000000001"  # TODO: extract from data
    data["source"] = sender_to_source(dto.sender)
    data["raw_data"] = dto.raw_data
    serializer = LicenseUpdateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
    else:
        data["serializer_errors"] = str(serializer.errors)
        serializer = InvalidEmailSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
