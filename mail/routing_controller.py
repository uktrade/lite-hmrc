from django.http import JsonResponse
from rest_framework.status import HTTP_400_BAD_REQUEST

from conf.settings import EMAIL_PASSWORD
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.data_processing import (
    process_and_save_email_message,
    collect_and_send_data_to_dto,
)
from mail.services.helpers import build_msg


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
