from django.urls import path

from mail import views

app_name = "mail"

urlpatterns = [
    path("send", views.SendMailView.as_view(), name="send_mail"),
    path("receive", views.ReceiveMailView.as_view(), name="receive_mail"),
]
