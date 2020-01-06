from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.builders import build_text_message


# Leaving the endpoints in place for now for testing purposes
class SendMailView(APIView):
    def get(self, request):
        server = MailServer(hostname='localhost', user='test18', pwd='password', pop3_port=995, smtp_port=587)
        smtp_conn = server.connect_smtp()
        mailBoxService = MailboxService()
        mailBoxService.send_email(smtp_conn, build_text_message("junk@mail.com", "junk2@mail.com"))
        smtp_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})


class ReadMailView(APIView):
    def get(self, request):
        server = MailServer(hostname='localhost', user='test18', pwd='password', pop3_port=995, smtp_port=587)
        pop3_conn = server.connect_pop3()
        mailBoxService = MailboxService()
        last_msg = mailBoxService.read_last_message(pop3_conn)
        pop3_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data=last_msg, safe=False)
