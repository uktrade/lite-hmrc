import poplib
import smtplib
import schedule
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

class SendMailView(APIView):
    def get(self, request):
        sender_email = "charles@example.com"
        receiver_email = "test18@example.com"
        msg = MIMEMultipart()
        # storing the senders email address

        msg['From'] = sender_email
        # storing the receivers email address
        msg['To'] = receiver_email
        # storing the subject
        msg['Subject'] = "Subject of the Mail"
        # string to store the body of the mail
        body = "Body_of_the_mail"
        # attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))
        # open the file to be sent
        filename = "File_name_with_extension"
        attachment = open("path_to_file", "rb")
        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')
        # To change the payload into encoded form
        p.set_payload((attachment).read())
        # encode into base64
#         encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        # attach the instance 'p' to instance 'msg'
        msg.attach(p)
        server = smtplib.SMTP("localhost", "587")
        server.starttls()
        server.login("test18", "password")
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent?"})

class ReceiveMailView(APIView):
    def get(self, request):
        server = poplib.POP3_SSL("localhost", 995)
        server.user("test18")
        server.pass_("password")
        messages_info = server.list()

        output=str(messages_info) + "\n" + "\n"
        output+=str(server.retr(len(messages_info[1])))
        print(output)
        server.quit()
        return JsonResponse(status=HTTP_200_OK, data=output, safe=False)


def job():
   print(time.time())

schedule.every(5).seconds.do(job)
# schedule.every().hour.do(job)
# schedule.every().day.at("10:30").do(job)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)
# while True:
#     schedule.run_pending()
#     time.sleep(1)





