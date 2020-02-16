from django.http import JsonResponse
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from mail.builders import build_mail_message_dto
from mail.dtos import to_json
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate
from mail.routing_controller import check_and_route_emails
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.helpers import build_email_message


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