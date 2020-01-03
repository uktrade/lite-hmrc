from django.urls import path

from mail.views import SendMailView, ReceiveMailView

app_name = "mail"

urlpatterns = [
    path("send", SendMailView.as_view(), name="send_mail"),
    path("receive", ReceiveMailView.as_view(), name="receive_mail"),
]
