from django.http import JsonResponse
from rest_framework import status
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from mail.builders import build_mail_message_dto
from mail.dtos import to_json
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum, UnitMapping
from mail.models import Mail, LicenceUpdate
from mail.routing_controller import check_and_route_emails
from mail.serializers import (
    LiteLicenceUpdateSerializer,
    ForiegnTraderSerializer,
    GoodSerializer,
)
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.helpers import build_email_message, map_unit


class SendMailView(APIView):
    def get(self, request):
        server = MailServer()
        smtp_conn = server.connect_to_smtp()
        mailbox_service = MailboxService()
        mailbox_service.send_email(
            smtp_conn,
            build_email_message(
                build_mail_message_dto(
                    sender="anemail@gmail.com",
                    receiver="username@example.com",
                    file_path="/app/Pipfile",
                )
            ),
        )
        smtp_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data={"message": "email_sent !"})


class ReadMailView(APIView):
    def get(self, request):
        server = MailServer()
        pop3_conn = server.connect_to_pop3()
        last_msg_dto = MailboxService().read_last_message(pop3_conn)
        pop3_conn.quit()
        print(last_msg_dto)
        return JsonResponse(status=HTTP_200_OK, data=last_msg_dto, safe=False)


class RouteMailView(APIView):
    def get(self, request):
        response_message = check_and_route_emails()
        return JsonResponse(
            status=HTTP_200_OK, data={"message": response_message}, safe=False
        )


class SeedMail(APIView):
    def get(self, request):
        if LicenceUpdate.objects.count() == 0:
            mail = Mail.objects.create(
                edi_data="blank",
                extract_type=ExtractTypeEnum.USAGE_UPDATE,
                status=ReceptionStatusEnum.PENDING,
                edi_filename="blank",
            )

            license = LicenceUpdate.objects.create(
                mail=mail,
                hmrc_run_number=12,
                source_run_number=11,
                source=SourceEnum.SPIRE,
            )

            return JsonResponse(
                status=HTTP_200_OK,
                data={"message": str(mail) + str(license)},
                safe=False,
            )


class MailList(APIView):
    def get(self):
        server = MailServer()
        pop3_conn = server.connect_to_pop3()
        last_msg_dto = MailboxService().read_last_message(pop3_conn)
        pop3_conn.quit()
        return JsonResponse(status=HTTP_200_OK, data=to_json(last_msg_dto), safe=False)


class TurnOnScheduler(APIView):
    def get(self, request):
        pass


class UpdateLicence(APIView):
    def post(self, request):
        # print(request.data)
        data = request.data.get("licence")
        # print(type(data))

        errors = []

        serializer = LiteLicenceUpdateSerializer(data=data)

        if not serializer.is_valid():
            errors += serializer.errors

        # print(errors)

        if data:
            print("application data", data)

            end_user = data.get("end_user")
            print("end_user", end_user)
            serializer = ForiegnTraderSerializer(data=end_user)
            if not serializer.is_valid():
                errors.append({"end_user_errors": serializer.errors})

            if data.get("goods") and data.get("type") == "siel":
                goods = data.get("goods")
                g = 0
                for good in goods:
                    serializer = GoodSerializer(data=good)
                    if not serializer.is_valid():
                        errors.append({"good_errors": serializer.errors})
                    else:
                        data = map_unit(data, g)
                    g += 1

            if not errors:
                print("\n\n\n")
                print(serializer.data)
                print("\n\n\n")

                return JsonResponse(status=status.HTTP_200_OK, data={"data": data})
        print("\n\n\n")

        print(errors)
        print("\n\n\n")

        return JsonResponse(status=status.HTTP_400_BAD_REQUEST, data={"errors": errors})
