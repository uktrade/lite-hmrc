from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from conf.settings import EMAIL_PASSWORD
from mail.builders import build_text_message
from mail.dtos import to_json
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.data_processing import check_and_route_emails


# Leaving the endpoints in place for now for testing purposes
class SendMailView(APIView):
    def get(self, request):
        server = MailServer(
            hostname="localhost",
            user="test18",
            pwd=EMAIL_PASSWORD,
            pop3_port=995,
            smtp_port=587,
        )
        smtp_conn = server.connect_smtp()
        mailbox_service = MailboxService()
        mailbox_service.send_email(
            smtp_conn, build_text_message("junk@mail.com", "junk2@mail.com")
        )
        smtp_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})


class ReadMailView(APIView):
    def get(self, request):
        server = MailServer(
            hostname="localhost",
            user="test18",
            pwd=EMAIL_PASSWORD,
            pop3_port=995,
            smtp_port=587,
        )
        pop3_conn = server.connect_pop3()
        last_msg_dto = MailboxService().read_last_message(pop3_conn)
        pop3_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data=to_json(last_msg_dto), safe=False)


class RouteMailView(APIView):
    def get(self, request):
        response_message = check_and_route_emails()
        return JsonResponse(
            status=HTTP_200_OK, data={"message": response_message}, safe=False
        )
