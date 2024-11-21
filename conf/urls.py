"""conf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from healthcheck.views import HealthCheckPingdomView, ServiceAvailableHealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("mail/", include("mail.urls")),
    path("healthcheck/", include("health_check.urls")),
    path("pingdom/ping.xml", HealthCheckPingdomView.as_view(), name="healthcheck-pingdom"),
    path("service-available-check/", ServiceAvailableHealthCheckView.as_view(), name="service-available-check"),
]

if settings.ENABLE_MOCK_HMRC_SERVICE:  # pragma: no cover
    urlpatterns += [path("mock-hmrc/", include("mock_hmrc.urls"))]
