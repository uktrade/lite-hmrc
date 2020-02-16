from django.urls import path

from mail.views.test_endpoints import (
    SendMailView,
    ReadMailView,
    SeedMail,
    RouteMailView,
)

app_name = "mail"

urlpatterns = [
    path("send", SendMailView.as_view(), name="send_mail"),
    path("read", ReadMailView.as_view(), name="read_mail"),
    path("seed", SeedMail.as_view(), name="seed"),
    path("route", RouteMailView.as_view(), name="route"),
]
