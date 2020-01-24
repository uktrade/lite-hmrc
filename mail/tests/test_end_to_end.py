from time import sleep

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.builders import build_text_message
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import LicenceUpdate, Mail
from mail.scheduling.scheduler import scheduled_job
from mail.servers import MailServer
from mail.services.MailboxService import MailboxService


class EndToEndTest(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.hmrc_run_number = 28
        self.source_run_number = 15
        self.mail = Mail.objects.create(
            edi_data=self.file_body,
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
            status=ReceptionStatusEnum.ACCEPTED,
            edi_filename=self.file_name,
        )

        self.licence_update = LicenceUpdate.objects.create(
            mail=self.mail,
            hmrc_run_number=self.hmrc_run_number,
            source_run_number=self.source_run_number,
            source=SourceEnum.SPIRE,
        )

    @tag("end-to-end")
    def test_end_to_end_success_licence_update(self):
        # send email to lite from spire
        service = MailboxService()
        service.send_email(
            MailServer().connect_to_smtp(),
            build_text_message(
                "test@spire.com",
                "username@example.com",
                [self.file_name, self.file_body.decode("ascii", "replace")],
            ),
        )
        scheduled_job()
        sleep(6)
