import logging
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
        pingdom_dto = _build_pingdom_dto(request)
        resp_cont = _build_xml_contents(pingdom_dto)
        lite_log(logger, logging.DEBUG, f"resp_cont: \n{resp_cont}")
        return HttpResponse(
            status=HTTP_200_OK, content=resp_cont, content_type="application/xml",
        )


def _build_pingdom_dto(request) -> PingdomHealthDto:
    return PingdomHealthDto(status="OK", response_time="20")


def _build_xml_contents(pingdom_dto: PingdomHealthDto):
    return f"""
           <pingdom_http_custom_check>
             <status>{pingdom_dto.status}</status> 
             <response_time>{pingdom_dto.response_time}</response_time>
           </pingdom_http_custom_check>
        """
