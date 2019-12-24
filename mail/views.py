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
        server.send_email('charles@example.com','test18@example.com',
                          self._build_message('charles@example.com', 'test18@example.com'))
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})

    def _build_message(self, sender, receiver):
        msg = MIMEMultipart()
        # storing the senders email address
        msg['From'] = sender
        # storing the receivers email address
        msg['To'] = receiver
        # storing the subject
        msg['Subject'] = "Subject of the Mail run number: 99"
        # string to store the body of the mail
        body = "Body_of_the_mail"
        # attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))
        # open the file to be sent
        filename = "File_name_with_extension"
        attachment = open('<path_to_file>', 'rb')
        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')
        # To change the payload into encoded form
        p.set_payload((attachment).read())
        # encode into base64
#         encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        # attach the instance 'p' to instance 'msg'
        msg.attach(p)
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





