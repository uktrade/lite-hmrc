from time import sleep

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.builders import build_text_message
from mail.enums import ReceptionStatusEnum
from mail.models import Mail
from mail.scheduling.scheduler import scheduled_job
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService


class EndToEndTest(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

    @tag("end-to-end")
    def test_end_to_end_success_licence_update(self):
        # send email to lite from spire
        service = MailboxService()
        service.send_email(
            MailServer().connect_to_smtp(),
            build_text_message(
                "test@spire.com",
                "username@example.com",
                [
                    self.licence_usage_file_name,
                    self.licence_usage_file_body.decode("ascii", "replace"),
                ],
            ),
        )
        scheduled_job()
        sleep(6)

        in_mail = Mail.objects.get(edi_filename=self.licence_usage_file_name)

        self.assertEqual(in_mail.status, ReceptionStatusEnum.REPLY_PENDING)
