import smtplib

from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView


class MailView(APIView):
    def get(self, request):
        receiver_email = "<email>"
        sender_email = "<email>"
        # Make Gmail accept the email
        message = "From: <email>:" \
                  "Subject: tinkering with the settings:" \
                  "Message: body:" \
                  "."
        server = smtplib.SMTP("<domain>", "<port>")
        server.starttls()
        server.login("<username>", "<password>")
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent?"})
