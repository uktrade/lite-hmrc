from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from mail.servers import MailServer


class SendMailView(APIView):
    def get(self, request):
        server = MailServer()
        server.send_email(
            "charles@example.com",
            "test18@example.com",
            self._build_message("charles@example.com", "test18@example.com"),
        )
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})

    def _build_message(self, sender, receiver):
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = receiver
        msg["Subject"] = "Subject of the Mail run number: 99"
        body = "Body_of_the_mail"
        msg.attach(MIMEText(body, "plain"))
        filename = "File_name_with_extension"
        attachment = open("<path_to_file>", "rb")
        payload = MIMEBase("application", "octet-stream")
        payload.set_payload((attachment).read())
        payload.add_header("Content-Disposition", "attachment; filename= %s" % filename)
        msg.attach(payload)
        return msg.as_string()


class ReceiveMailView(APIView):
    def get(self, request):
        server = MailServer()
        last_msg = server.read_email()
        return JsonResponse(status=HTTP_200_OK, data=last_msg, safe=False)


def job():
    pass


# print(time.time())

# schedule.every(5).seconds.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)
# while True:
#     schedule.run_pending()
#     time.sleep(1)
