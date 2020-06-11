import datetime
import time

from background_task.models import Task
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from rest_framework.views import APIView

from mail.enums import ReceptionStatusEnum, ReplyStatusEnum
from mail.models import Mail
from mail.tasks import LICENCE_UPDATES_TASK_QUEUE


class HealthCheck(APIView):
    def get(self, request):
        """
        Provides a health check endpoint as per [https://man.uktrade.io/docs/howtos/healthcheck.html#pingdom]
        """

        start_time = time.time()

        task = Task.objects.get(queue=LICENCE_UPDATES_TASK_QUEUE)
        if task.run_at + datetime.timedelta(seconds=task.repeat) < timezone.now():
            return self._build_response(HTTP_503_SERVICE_UNAVAILABLE, "not OK", start_time)

        last_email = Mail.objects.last()
        if (
            last_email
            and last_email.status == ReceptionStatusEnum.REPLY_SENT
            and ReplyStatusEnum.REJECTED in last_email.response_data.lower()
        ):
            return self._build_response(HTTP_503_SERVICE_UNAVAILABLE, "not OK", start_time)

        return self._build_response(HTTP_200_OK, "OK", start_time)

    @staticmethod
    def _build_response(status, message, start_time):
        duration_ms = (time.time() - start_time) * 1000
        response_time = "{:.3f}".format(duration_ms)
        xml = f"""
                   <pingdom_http_custom_check>
                     <status>{message}</status> 
                     <response_time>{response_time}</response_time>
                   </pingdom_http_custom_check>
                """

        return HttpResponse(content=xml, content_type="application/xml", status=status)
