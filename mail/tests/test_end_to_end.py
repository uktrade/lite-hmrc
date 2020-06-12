from random import randint
from time import sleep
from unittest import mock

from django.test import tag
from django.urls import reverse

from conf.settings import SPIRE_ADDRESS
from conf.test_client import LiteHMRCTestClient
from mail.builders import build_text_message
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate, LicencePayload
from mail.routing_controller import check_and_route_emails, _collect_and_send
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService
from mail.services.data_processors import serialize_email_message
from mail.services.helpers import get_extract_type
from mail.tasks import email_lite_licence_updates


class SmtpMock:
    def quit(self):
        pass


class EndToEndTest(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

    @tag("end-to-end")
    def test_end_to_end_success_licence_update(self):
        file_name = "ILBDOTI_live_CHIEF_licenceUpdate_49543_201902" + str(randint(1, 99999))  # nosec

        # send email to lite from spire
        service = MailboxService()
        service.send_email(
            MailServer().connect_to_smtp(),
            build_text_message(SPIRE_ADDRESS, "username@example.com", [file_name, self.licence_usage_file_body],),
        )
        sleep(5)
        check_and_route_emails()
        sleep(5)
        server = MailServer()
        pop3_conn = server.connect_to_pop3()
        last_msg_dto = MailboxService().read_last_message(pop3_conn)
        pop3_conn.quit()

        print("\n\n\n")
        print(last_msg_dto)

        in_mail = Mail.objects.get(edi_filename=file_name)
        self.assertEqual(
            in_mail.edi_filename, file_name,
        )

        print("\n\n\n")
        print(in_mail.__dict__)
        print("\n\n\n")

    @tag("data manipulation")
    def test_true_e2e(self):
        data = (
            b"1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202006051240\\1234"
            b"\n2\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\20200602\\20220602"
            b"\n3\\trader\\0192301\\123791\\20200602\\20220602\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580"
            b"\n4\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB\n5\\restrictions\\Provisos may apply please see licence"
            b"\n6\\line\\1\\\\\\\\\\finally\\Q\\30\\10"
            b"\n7\\end\\licence\\6\n8\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\20200602\\20220602"
            b"\n9\\trader\\0192301\\123791\\20200602\\20220602\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580"
            b"\n10\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB"
            b"\n11\\restrictions\\Provisos may apply please see licence"
            b"\n12\\line\\1\\\\\\\\\\finally\\Q\\30\\10\n13\\end\\licence\\6"
            b"\n14\\fileTrailer\\2"
        )

        print(data)

        data = data.decode("utf-8")

        print(data)


class EndToEndTests(LiteHMRCTestClient):
    @staticmethod
    def print_mail(mail):
        print("id", mail.id)
        print("created_at", mail.created_at)
        print("last_submitted_on", mail.last_submitted_on)
        if mail.edi_filename:
            print("edi_filename", mail.edi_filename[0:100])
            print("edi_data", mail.edi_data[0:100])
        print("status", mail.status[:100])
        print("extract_type", mail.extract_type[:100])
        if mail.response_filename:
            print("response_filename", mail.response_filename[0:100])
            print("response_data", mail.response_data[:50])
            print("response_date", mail.response_date)
            print("response_subject", mail.response_subject)
        print("serializer_errors", mail.serializer_errors)
        print("errors", mail.errors)
        print("currently_processing_at", mail.currently_processing_at)
        print("currently_processed_by", mail.currently_processed_by)

    @tag("system-start")
    def test_system_start(self):
        print("\nThis is the system start\n------------------\n")
        count = Mail.objects.count()
        print("Current number of mail objects\t", count)
        if count:
            print("Status of last mail object\t", Mail.objects.last().status)

        server = MailServer()
        pop3_conn = server.connect_to_pop3()

        last_msg_dto = MailboxService().read_last_message(pop3_conn)

        print("\nMessage retrieved:\n----------------")
        print("run number\t", last_msg_dto.run_number)
        print("attachment\t", last_msg_dto.attachment[0])
        print("file\t\t", last_msg_dto.attachment[1][0:150])

        if get_extract_type(last_msg_dto.subject) == "licence_reply":
            mail = Mail(extract_type=ExtractTypeEnum.LICENCE_UPDATE, status=ReceptionStatusEnum.REPLY_PENDING,)
            mail.save()
            lu = LicenceUpdate(
                source=SourceEnum.SPIRE,
                source_run_number=last_msg_dto.run_number,
                hmrc_run_number=last_msg_dto.run_number,
                license_ids="['GBSIEL/2020/0000001/P', 'GBSIEL/2020/0000001/P']",
                mail=mail,
            )
            lu.save()

        serialize_email_message(last_msg_dto)

        count = Mail.objects.count()
        print("Current number of mail objects\t", count)
        if count:
            print("Status of last mail object\t", Mail.objects.last().status)

        print("\nMail snapshot\n-----------")
        mail = Mail.objects.get()
        self.print_mail(mail)

        _collect_and_send(mail)

        mail = Mail.objects.get()
        self.print_mail(mail)

    @tag("end-to-end")
    @tag("mocked")
    @mock.patch("mail.tasks.send_email")
    def test_send_email_to_hmrc_e2e_mocked(self, send_email):
        send_email.return_value = SmtpMock()
        self.single_siel_licence_payload.is_processed = True

        self.client.post(
            reverse("mail:update_licence"), data=self.licence_payload_json, content_type="application/json"
        )

        email_lite_licence_updates.now()  # Manually calling background task logic

        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 2)

    @tag("end-to-end")
    def test_send_email_to_hmrc_e2e_non_mocked(self):
        self.client.post(
            reverse("mail:update_licence"), data=self.licence_payload_json, content_type="application/json"
        )

        email_lite_licence_updates.now()

        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 2)
