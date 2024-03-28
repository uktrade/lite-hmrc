import os
import subprocess

from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase
from parameterized import parameterized

from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from mail.tests.factories import LicencePayloadFactory, MailFactory


class TestAnonymiseDumps(TransactionTestCase):
    def _fixture_teardown(self):
        # NOTE: TransactionTestCase will truncate all tables by default
        # before the run of each test case.  By overriding this method,
        # we prevent this truncation from happening.  It would be nice if Django
        # supplied some configurable way to do this, but that does not seem to be
        # the case.
        return

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.create_test_data()
        cls.dump_location = f"/tmp/{settings.DB_ANONYMISER_DUMP_FILE_NAME}"
        try:
            os.remove(cls.dump_location)
        except FileNotFoundError:
            pass

        call_command("dump_and_anonymise", keep_local_dumpfile=True, skip_s3_upload=True)

        with open(cls.dump_location, "r") as f:
            cls.anonymised_sql = f.read()

        # Drop the existing test DB
        connection.close()
        db_details = settings.DATABASES["default"]
        postgres_url_base = (
            f"postgresql://{db_details['USER']}:{db_details['PASSWORD']}@{db_details['HOST']}:{db_details['PORT']}"
        )
        postgres_db_url = f"{postgres_url_base}/postgres"
        subprocess.run(
            (
                "psql",
                "--dbname",
                postgres_db_url,
            ),
            input=f"DROP DATABASE \"{db_details['NAME']}\"; CREATE DATABASE \"{db_details['NAME']}\";",
            encoding="utf-8",
            stdout=subprocess.PIPE,
        )

        # Load the dumped data in to the test DB
        lite_hmrc_db_url = f"{postgres_url_base}/{db_details['NAME']}"
        subprocess.run(
            (
                "psql",
                "--dbname",
                lite_hmrc_db_url,
            ),
            input=cls.anonymised_sql,
            encoding="utf-8",
            stdout=subprocess.PIPE,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.delete_test_data()

    @classmethod
    def load_edi_data_from_file(cls, filename):
        licence_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        with open(licence_data_file) as f:
            return MailFactory(
                edi_data=f.read(),
                extract_type=ExtractTypeEnum.LICENCE_DATA,
                status=ReceptionStatusEnum.REPLY_SENT,
            )

    @classmethod
    def create_test_data(cls):
        cls.siel_mail_nar = cls.load_edi_data_from_file("CHIEF_LIVE_SPIRE_licenceData_78859_unitNAR")
        cls.siel_mail_kgm = cls.load_edi_data_from_file("CHIEF_LIVE_SPIRE_licenceData_78860_unitKGM")
        cls.open_licences_mail = cls.load_edi_data_from_file("CHIEF_LIVE_SPIRE_licenceData_78861_202109101531")
        cls.licence_payload = LicencePayloadFactory(
            reference="GBSIEL/2024/0000001/P",
            data={"reference": "GBSIEL/2024/0000001/P", "action": "insert"},
        )
        cls.mail_invalid = MailFactory(edi_data="invalid edi data")
        cls.mail_invalid_lines = cls.load_edi_data_from_file("CHIEF_LIVE_SPIRE_licenceData_78859_invalid")

    def get_licences_in_message(self, edi_data):
        message_lines = edi_data.split("\n")

        # In a given message there can be multiple licences of different types
        # so extract all licences details along with their line positions in the file
        start = 0
        licences = []
        for index in range(len(message_lines)):
            tokens = message_lines[index].split("\\")
            if len(tokens) < 2:
                continue
            line_type = tokens[1]
            if line_type == "licence":
                start = index
            if line_type == "end":
                licence_lines = message_lines[start : index + 1]
                licence_type = licence_lines[0].split("\\")[5]
                licences.append({"licence_type": licence_type, "start": start, "lines": licence_lines})

        return licences

    @classmethod
    def delete_test_data(cls):
        cls.siel_mail_nar.delete()
        cls.siel_mail_kgm.delete()
        cls.mail_invalid.delete()
        cls.mail_invalid_lines.delete()
        cls.open_licences_mail.delete()

    @parameterized.expand(
        [
            ## chief_line_type, expected_line_format
            (
                "trader",
                "%s\\trader\\\\GB123456789000\\\\\\Exporter name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode",
            ),
            (
                "foreignTrader",
                "%s\\foreignTrader\\End-user name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode\\AU",
            ),
            (
                "line",
                "%s\\line\\1\\\\\\\\\\PRODUCT NAME\\Q\\\\030\\\\1\\\\\\\\\\\\",
            ),
        ]
    )
    def test_mail_with_siels_unit_NAR_anonymised(self, chief_line_type, expected_line_format):
        """
        Test to verify line types that have PI data are correctly anonymised for SIEL licences
        Product lines are defined by quantity with number of items as unit.
        """
        anonymised_mail = Mail.objects.get(id=self.siel_mail_nar.id)
        assert anonymised_mail.edi_filename == self.siel_mail_nar.edi_filename
        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_mail.raw_data == f"{today}: raw_data contents anonymised"
        assert anonymised_mail.sent_data == f"{today}: sent_data contents anonymised"

        licences = self.get_licences_in_message(anonymised_mail.edi_data)
        assert len(licences) == 2

        # For each licence ensure given line type fields are correctly anonymised
        for licence in licences:
            for index, line in enumerate(licence["lines"], start=licence["start"] + 1):
                line_type = line.split("\\")[1]

                if line_type == chief_line_type:
                    # format line to populate line index as per current line
                    expected_line = expected_line_format % index
                    assert line == expected_line

    @parameterized.expand(
        [
            ## chief_line_type, expected_line_format
            (
                "trader",
                "%s\\trader\\\\GB123456789000\\\\\\Exporter name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode",
            ),
            (
                "foreignTrader",
                "%s\\foreignTrader\\End-user name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode\\AU",
            ),
            (
                "line",
                "%s\\line\\1\\\\\\\\\\PRODUCT NAME\\Q\\\\023\\\\15.0\\\\\\\\\\\\",
            ),
        ]
    )
    def test_mail_with_siels_unit_KGM_anonymised(self, chief_line_type, expected_line_format):
        """
        Test to verify line types that have PI data are correctly anonymised for SIEL licences
        Product lines are defined by quantity with Kilogram as unit.
        """
        anonymised_mail = Mail.objects.get(id=self.siel_mail_kgm.id)
        assert anonymised_mail.edi_filename == self.siel_mail_kgm.edi_filename
        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_mail.raw_data == f"{today}: raw_data contents anonymised"
        assert anonymised_mail.sent_data == f"{today}: sent_data contents anonymised"

        licences = self.get_licences_in_message(anonymised_mail.edi_data)
        assert len(licences) == 1

        # For each licence ensure given line type fields are correctly anonymised
        for licence in licences:
            for index, line in enumerate(licence["lines"], start=licence["start"] + 1):
                line_type = line.split("\\")[1]

                if line_type == chief_line_type:
                    # format line to populate line index as per current line
                    expected_line = expected_line_format % index
                    assert line == expected_line

    @parameterized.expand(
        [
            ## chief_line_type, expected_line_format
            (
                "trader",
                "%s\\trader\\\\GB123456789000\\\\\\Exporter name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode",
            ),
            (
                "foreignTrader",
                "%s\\foreignTrader\\End-user name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode\\AU",
            ),
            (
                "line",
                "%s\\line\\1\\\\\\\\\\PRODUCT NAME\\O\\\\\\\\\\\\\\\\\\\\",
            ),
        ]
    )
    def test_mail_with_open_licences_anonymised(self, chief_line_type, expected_line_format):
        """
        Test to verify line types that have PI data are correctly anonymised for Open licences
        """
        anonymised_mail = Mail.objects.get(id=self.open_licences_mail.id)
        assert anonymised_mail.edi_filename == self.open_licences_mail.edi_filename
        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_mail.raw_data == f"{today}: raw_data contents anonymised"
        assert anonymised_mail.sent_data == f"{today}: sent_data contents anonymised"

        licences = self.get_licences_in_message(anonymised_mail.edi_data)
        assert len(licences) == 2

        # For each licence ensure given line type fields are correctly anonymised
        for licence in licences:
            for index, line in enumerate(licence["lines"], start=licence["start"] + 1):
                line_type = line.split("\\")[1]

                if line_type == chief_line_type:
                    # format line to populate line index as per current line
                    expected_line = expected_line_format % index
                    assert line == expected_line

    def test_mail_with_invalid_edi_data_anonymised(self):
        anonymised_mail = Mail.objects.get(id=self.mail_invalid.id)
        assert anonymised_mail.edi_filename == self.mail_invalid.edi_filename
        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_mail.raw_data == f"{today}: raw_data contents anonymised"
        assert anonymised_mail.sent_data == f"{today}: sent_data contents anonymised"
        assert anonymised_mail.edi_data == f"{today}: invalid edi data"

    def test_mail_with_valid_header_footer_invalid_lines_anonymised(self):
        anonymised_mail = Mail.objects.get(id=self.mail_invalid_lines.id)
        assert anonymised_mail.edi_filename == self.mail_invalid_lines.edi_filename
        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_mail.raw_data == f"{today}: raw_data contents anonymised"
        assert anonymised_mail.sent_data == f"{today}: sent_data contents anonymised"
        licences = self.get_licences_in_message(anonymised_mail.edi_data)
        assert len(licences) == 0

        assert (
            anonymised_mail.edi_data
            == "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\202008101531\\71859\\N\n5\\fileTrailer\\0"
        )

    def test_licence_payload_anonymised(self):
        anonymised_licence_payload = LicencePayload.objects.get(id=self.licence_payload.id)
        assert anonymised_licence_payload.lite_id == self.licence_payload.lite_id
        assert anonymised_licence_payload.action == self.licence_payload.action

        today = datetime.strftime(datetime.today().date(), "%d %B %Y")
        assert anonymised_licence_payload.data == {
            "reference": "GBSIEL/2024/0000001/P",
            "action": "insert",
            "details": f"{today}, other details anonymised",
        }
