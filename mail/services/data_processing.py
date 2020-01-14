from django.http import JsonResponse
from rest_framework.status import HTTP_400_BAD_REQUEST

from conf.settings import EMAIL_PASSWORD
from mail.dtos import EmailMessageDto
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.helpers import (
    convert_sender_to_source,
    process_attachment,
    build_msg,
)
from mail.models import LicenseUpdate
from mail.serializers import LicenseUpdateSerializer, InvalidEmailSerializer


def process_and_save_email_message(dto: EmailMessageDto):
    data = convert_dto_data_for_serialization(dto)

    serializer = LicenseUpdateSerializer(data=data)

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
    data = {}
    last_hmrc_number = LicenseUpdate.objects.last().hmrc_run_number
    data["hmrc_run_number"] = (
        last_hmrc_number + 1 if last_hmrc_number != 99999 else 0
    )  # TODO: Extra logic to generalise
    data["source_run_number"] = dto.run_number

    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)

    data["extract_type"] = "insert"  # TODO: extract from data
    data[
        "license_id"
    ] = "00000000-0000-0000-0000-000000000001"  # TODO: extract from data
    data["source"] = convert_sender_to_source(dto.sender)
    data["raw_data"] = dto.raw_data

    return data


def collect_and_send_data_to_dto():
    # determine run_number to use
    # get data out
    # return dto
    return True


def check_and_route_emails():
    server = MailServer(
        hostname="localhost",
        user="test18",
        pwd=EMAIL_PASSWORD,
        pop3_port=995,
        smtp_port=587,
    )
    pop3_conn = server.connect_pop3()
    mail_box_service = MailboxService()
    last_msg_dto = mail_box_service.read_last_message(pop3_conn)
    pop3_conn.quit()
    # todo
    # TODO: Process data (saves data to db from dto)
    if not process_and_save_email_message(last_msg_dto):
        return JsonResponse(status=HTTP_400_BAD_REQUEST, data={"errors": "Bad data"})
    # mail_box_service.handle_run_number(last_msg_dto) this should go into the process part
    # TODO: Collect data (retrieves data from db back into dto) return -> message_to_send_dto
    message_to_send_dto = collect_and_send_data_to_dto()
    smtp_conn = server.connect_smtp()
    # todo
    mail_box_service.send_email(smtp_conn, build_msg(message_to_send_dto))

    response_message = "Email routed from {} to {}".format(
        last_msg_dto.sender, "receiver tbd"
    )
    return response_message
