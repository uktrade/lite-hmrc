from mail.dtos import EmailMessageDto
from mail.helpers import sender_to_source
from mail.models import LicenseUpdate
from mail.serializers import LicenseUpdateSerializer


def process_and_save_email_message_dto(dto: EmailMessageDto):
    print(dto)
    data = {}
    last_hmrc_number = LicenseUpdate.objects.last().hmrc_run_number
    data["hmrc_run_number"] = last_hmrc_number + 1 if last_hmrc_number != 99999 else 0
    data["source_run_number"] = dto.run_number
    data["edi_data"] = str(dto.attachment[1])
    data["edi_filename"] = dto.attachment[0]
    data["extract_type"] = "insert"  # TODO: extract from data
    data[
        "license_id"
    ] = "00000000-0000-0000-0000-000000000001"  # TODO: extract from data
    data["source"] = sender_to_source(dto.sender)
    serializer = LicenseUpdateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        for l in LicenseUpdate.objects.all():
            print("\n\n\n")
            print(l.__dict__)
        print(serializer.data)
    else:
        print(serializer.errors)
