import logging
import time

from django.shortcuts import render
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from .checks import (
    can_authenticate_mailboxes,
    is_licence_payloads_processing,
    is_manage_inbox_task_responsive,
    is_pending_mail_processing,
)

logger = logging.getLogger(__name__)


class BaseHealthCheckView(APIView):
    def get(self, request):
        """
        Provides a health check endpoint as per [https://man.uktrade.io/docs/howtos/healthcheck.html#pingdom]
        """

        start_time = time.time()

        for check, message in self.checks:
            if not check():
                logger.error("%s", message)
                return self._build_response(
                    HTTP_503_SERVICE_UNAVAILABLE,
                    message,
                    start_time,
                )

        logger.info("All services are responsive")
        return self._build_response(HTTP_200_OK, "OK", start_time)

    def _build_response(self, status, message, start_time):
        duration_ms = (time.time() - start_time) * 1000
        response_time = "{:.3f}".format(duration_ms)
        context = {"message": message, "response_time": response_time, "status": status}

        return render(self.request, "healthcheck.xml", context, content_type="application/xml", status=status)


class HealthCheckP1(BaseHealthCheckView):
    checks = [
        (can_authenticate_mailboxes, "Mailbox authentication error"),
        (is_manage_inbox_task_responsive, "Manage inbox queue error"),
    ]


class HealthCheckP2(BaseHealthCheckView):
    checks = [
        (is_licence_payloads_processing, "Payload objects error"),
        (is_pending_mail_processing, "Pending mail error"),
    ]
