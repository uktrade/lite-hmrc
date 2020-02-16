from django.urls import path
from pingdom.views.healthchecks import HealthCheckView

app_name = "pingdom"

urlpatterns = [
    path("healthcheck", HealthCheckView.as_view(), name="healthcheck"),
]
