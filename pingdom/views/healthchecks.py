import logging
import time
from mail.services.logging_decorator import lite_log
from django.http import HttpResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework_xml.renderers import XMLRenderer

from mail.dtos import PingdomHealthDto

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    renderer_classes = [
        XMLRenderer,
    ]

    def get(self, request):
        """
        Provides a health check endpoint as per [https://man.uktrade.io/docs/howtos/healthcheck.html#pingdom]
        """
        start_time = time.time()
        pingdom_dto = _build_pingdom_dto(request, start_time)
        resp_cont = _build_xml_contents(pingdom_dto)
        lite_log(logger, logging.DEBUG, f"resp_cont: \n{resp_cont}")
        return HttpResponse(
            status=HTTP_200_OK, content=resp_cont, content_type="application/xml",
        )


def _build_pingdom_dto(request, start_time) -> PingdomHealthDto:
    # todo check request headers, dependencies such as Database connection, Mail server connection, etc
    duration_ms = (time.time() - start_time) * 1000
    resp_time = "{:.3f}".format(duration_ms)
    return PingdomHealthDto(status="OK", response_time=f"{resp_time}")


def _build_xml_contents(pingdom_dto: PingdomHealthDto):
    return f"""
           <pingdom_http_custom_check>
             <status>{pingdom_dto.status}</status> 
             <response_time>{pingdom_dto.response_time}</response_time>
           </pingdom_http_custom_check>
        """
