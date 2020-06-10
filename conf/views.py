import time
import datetime

from background_task.models import Task
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from mail.tasks import TASK_QUEUE


class HealthCheck(APIView):
    def get(self, request):
        """
        Provides a health check endpoint as per [https://man.uktrade.io/docs/howtos/healthcheck.html#pingdom]
        """
        start_time = time.time()
        status = (HTTP_200_OK, "OK")

        task = Task.objects.get(queue=TASK_QUEUE)
        if task.run_at + datetime.timedelta(seconds=task.repeat) < timezone.now():
            status = (HTTP_503_SERVICE_UNAVAILABLE, "not OK")

        return HttpResponse(
            status=status[0],
            content=self._build_xml_response_content(status[1], start_time),
            content_type="application/xml",
        )

    @staticmethod
    def _build_xml_response_content(status_message, start_time):
        duration_ms = (time.time() - start_time) * 1000
        response_time = "{:.3f}".format(duration_ms)

        return f"""
                   <pingdom_http_custom_check>
                     <status>{status_message}</status> 
                     <response_time>{response_time}</response_time>
                   </pingdom_http_custom_check>
                """
