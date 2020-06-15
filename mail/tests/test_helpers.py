import logging

from parameterized import parameterized

from conf.settings import SPIRE_ADDRESS
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.libraries.helpers import (
    convert_sender_to_source,
    convert_source_to_sender,
    new_hmrc_run_number,
    get_run_number,
)
from mail.models import LicenceUpdate, Mail
from mail.tests.libraries.client import LiteHMRCTestClient


class HelpersTests(LiteHMRCTestClient):
    @parameterized.expand([[SPIRE_ADDRESS, SourceEnum.SPIRE], ["test@lite.com", "LITE"]])
    def test_convert_sender_to_source(self, sender, source):
        self.assertEqual(convert_sender_to_source(sender), source)

    @parameterized.expand([[SPIRE_ADDRESS, SourceEnum.SPIRE], ["test@lite.com", "LITE"]])
    def test_convert_source_to_sender(self, sender, source):
        self.assertEqual(convert_source_to_sender(source), sender)

    @parameterized.expand([[5, 4, 5], [1234568, 34567, 34568], [0, 99999, 0], [7, 7, 7]])
    def test_new_hmrc_run_number(self, source, old, new):
        mail = self._setup_mail()
        LicenceUpdate.objects.create(
            mail=mail, hmrc_run_number=old, source_run_number=old, source=SourceEnum.SPIRE,
        )
        self.assertEqual(new_hmrc_run_number(source), new)

    @parameterized.expand(
        [[["name", b"data"], "name", "data"], [[], "", ""], [["something"], "", ""], ["something", "", ""],]
    )
    def test_process_attachment(self, attachment, attachment_name, attachment_data):
        # todo
        pass

    def test_get_run_number_from_subject(self):
        subject = "ILBDOTI_live_CHIEF_usageData_9876_201901130300"
        run_number = get_run_number(subject)
        self.assertEqual(run_number, "9876")

    def test_value_error_thrown_cannot_find_run_number(self):
        subject = "usageData_9876_201901130300"
        with self.assertRaises(ValueError) as context:
            get_run_number(subject)
        self.assertEqual("Can not find valid run-number", str(context.exception))

    def test_value_error_thrown_run_number_wrong_format(self):
        subject = "abc_xyz_nnn_yyy_a1b34_datetime"
        with self.assertRaises(ValueError) as context:
            get_run_number(subject)
        self.assertEqual("Can not find valid run-number", str(context.exception))

    @staticmethod
    def _setup_mail():
        return Mail.objects.create(
            edi_data="blank",
            extract_type=ExtractTypeEnum.USAGE_UPDATE,
            status=ReceptionStatusEnum.PENDING,
            edi_filename="blank",
        )


def print_all_mails():
    all_mails = Mail.objects.all()
    for mail in all_mails:
        rec = {
            "id": mail.id,
            "edi_filename": mail.edi_filename,
            "status": mail.status,
            "extract_type": mail.extract_type,
        }
        logging.debug("Mail -> {}".format(rec))
