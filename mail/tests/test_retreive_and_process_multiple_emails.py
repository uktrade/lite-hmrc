import base64

from django.test import tag

from conf.settings import HMRC_ADDRESS, SPIRE_ADDRESS, EMAIL_USER
from conf.test_client import LiteHMRCTestClient
from mail.dtos import EmailMessageDto
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.models import Mail, LicenceUpdate
from mail.services.data_processors import serialize_email_message
from mail.services.helpers import select_email_for_sending


class MultipleEmailRetrievalTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.dto_1 = EmailMessageDto(
            run_number=49543,
            sender=HMRC_ADDRESS,
            receiver=EMAIL_USER,
            body="lite licence reply",
            subject="ILBDOTI_live_CHIEF_licenceReply_49543_201901130300",
            attachment=["ILBDOTI_live_CHIEF_licenceReply_49543_201901130300", self.licence_update_reply_body,],
            raw_data="qwerty",
        )
        string = """
                        1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202006051240\\1234
                        \n2\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\20200602\\20220602
                        \n3\\trader\\0192301\\123791\\20200602\\20220602\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580
                        \n4\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB
                        \n5\\restrictions\\Provisos may apply please see licence
                        \n6\\line\\1\\\\\\\\\\finally\\Q\\30\\10
                        \n7\\end\\licence\\6
                        \n8\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\20200602\\20220602
                        \n9\\trader\\0192301\\123791\\20200602\\20220602\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580
                        \n10\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB
                        \n11\\restrictions\\Provisos may apply please see licence
                        \n12\\line\\1\\\\\\\\\\finally\\Q\\30\\10
                        \n13\\end\\licence\\6
                        \n14\\fileTrailer\\2
                        """
        self.dto_2 = EmailMessageDto(
            run_number=17,
            sender=SPIRE_ADDRESS,
            receiver=EMAIL_USER,
            body="spire licence update",
            subject="ILBDOTI_live_CHIEF_licenceUpdate_17_201901130300",
            attachment=[
                "ILBDOTI_live_CHIEF_licenceUpdate_49543_201901130300",
                base64.b64encode(bytes(string, "ASCII")),
            ],
            raw_data="qwerty",
        )
        self.dto_3 = EmailMessageDto(
            run_number=49541,
            sender=HMRC_ADDRESS,
            receiver=EMAIL_USER,
            body="spire licence reply",
            subject="ILBDOTI_live_CHIEF_licenceReply_49542_201901130300",
            attachment=["ILBDOTI_live_CHIEF_licenceReply_49542_201901130300", self.licence_update_reply_body],
            raw_data="qwerty",
        )

    @tag("no-duplication")
    def test_duplicate_emails_and_licence_updates_not_saved(self):
        mail = Mail.objects.create(
            edi_filename=self.dto_2.attachment[0],
            edi_data=self.dto_2.attachment[1],
            extract_type=ExtractTypeEnum.LICENCE_UPDATE,
            status=ReceptionStatusEnum.REPLY_SENT,
        )
        LicenceUpdate.objects.create(source_run_number=17, hmrc_run_number=49542, mail=mail, source=SourceEnum.SPIRE)
        mail_count = Mail.objects.count()
        licence_update_count = LicenceUpdate.objects.count()

        serialize_email_message(self.dto_3)

        self.assertEqual(mail_count, Mail.objects.count())
        self.assertEqual(licence_update_count, LicenceUpdate.objects.count())

    @tag("sequencing")
    def test_emails_are_sequenced_correctly(self):
        mail = Mail.objects.create(
            edi_filename="something",
            edi_data="some data",
            extract_type=ExtractTypeEnum.LICENCE_UPDATE,
            status=ReceptionStatusEnum.REPLY_PENDING,
        )
        LicenceUpdate.objects.create(source_run_number=4, hmrc_run_number=49543, mail=mail, source=SourceEnum.LITE)

        mail_lite = serialize_email_message(self.dto_2)
        mail_spire = serialize_email_message(self.dto_1)

        self.assertEqual(Mail.objects.filter(status=ReceptionStatusEnum.REPLY_RECEIVED), 1)
        self.assertEqual(Mail.objects.filter(status=ReceptionStatusEnum.PENDING), 1)

        mail = select_email_for_sending()

        self.assertEqual(mail, mail_lite)
