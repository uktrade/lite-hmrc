from django.urls import path

from mail.views import (
    SendMailView,
    ReadMailView,
    SeedMail,
    RouteMailView,
    UpdateLicence,
)

app_name = "mail"

urlpatterns = [
    path("send/", SendMailView.as_view(), name="send_mail"),
    path("read/", ReadMailView.as_view(), name="read_mail"),
    path("seed/", SeedMail.as_view(), name="seed"),
    path("route/", RouteMailView.as_view(), name="route"),
    path("update-licence/", UpdateLicence.as_view(), name="update_licence"),
    path("status", Status.as_view(), name="status"),
]
