from django.http import JsonResponse
from rest_framework import status

# from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from conf.authentication import HawkOnlyAuthentication

# from mail.libraries.builders import build_mail_message_dto
# from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
# from mail.libraries.email_message_dto import to_json
# from mail.libraries.helpers import build_email_message
# from mail.libraries.mailbox_service import send_email, read_last_message
# from mail.libraries.routing_controller import check_and_route_emails
# from mail.models import Mail, LicenceUpdate, LicencePayload
from mail.models import Mail, LicenceUpdate, LicencePayload
from mail.serializers import (
    LiteLicenceUpdateSerializer,
    ForiegnTraderSerializer,
    GoodSerializer,
)
from mail.servers import MailServer


# class SendMailView(APIView):
#     def get(self, request):
#         server = MailServer()
#         smtp_conn = server.connect_to_smtp()
#         send_email(
#             smtp_conn,
#             build_email_message(
#                 build_mail_message_dto(sender="icmshmrc@mailgate.trade.gov.uk", receiver="hmrc@mailgate.trade.gov.uk",)
#             ),
#         )
#         smtp_conn.quit()
#         return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})
#
#
# class ReadMailView(APIView):
#     def get(self, request):
#         server = MailServer()
#         pop3_conn = server.connect_to_pop3()
#         last_msg_dto = read_last_message(pop3_conn)
#         pop3_conn.quit()
#         print(last_msg_dto)
#         return JsonResponse(status=HTTP_200_OK, data=last_msg_dto, safe=False)
#
#
# class RouteMailView(APIView):
#     def get(self, request):
#         response_message = check_and_route_emails()
#         return JsonResponse(status=HTTP_200_OK, data={"message": response_message}, safe=False)
#
#
# class SeedMail(APIView):
#     def get(self, request):
#         if LicenceUpdate.objects.count() == 0:
#             mail = Mail.objects.create(
#                 edi_data="blank",
#                 extract_type=ExtractTypeEnum.USAGE_UPDATE,
#                 status=ReceptionStatusEnum.PENDING,
#                 edi_filename="blank",
#             )
#
#             license = LicenceUpdate.objects.create(
#                 mail=mail, hmrc_run_number=12, source_run_number=11, source=SourceEnum.SPIRE,
#             )
#
#             return JsonResponse(status=HTTP_200_OK, data={"message": str(mail) + str(license)}, safe=False,)


class UpdateLicence(APIView):
    authentication_classes = (HawkOnlyAuthentication,)

    def post(self, request):
        data = request.data.get("licence")

        errors = []

        serializer = LiteLicenceUpdateSerializer(data=data)

        if not serializer.is_valid():
            errors += serializer.errors

        if data:
            end_user = data.get("end_user")
            serializer = ForiegnTraderSerializer(data=end_user)
            if not serializer.is_valid():
                errors.append({"end_user_errors": serializer.errors})

            if data.get("goods") and data.get("type") == "siel":
                goods = data.get("goods")
                for good in goods:
                    serializer = GoodSerializer(data=good)
                    if not serializer.is_valid():
                        errors.append({"good_errors": serializer.errors})

            if not errors:
                LicencePayload.objects.create(lite_id=data["id"], reference=data["reference"], data=data)

                return JsonResponse(status=status.HTTP_201_CREATED, data={"data": data})

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data={"errors": errors})
