from django.urls import path

from . import views

urlpatterns = [
    path("", views.HealthCheckP1.as_view(), name="healthcheck_p1"),
    path("p2/", views.HealthCheckP2.as_view(), name="healthcheck_p2"),
]
