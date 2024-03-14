import os
import subprocess

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase

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
    def create_test_data(cls):
        licence_data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "CHIEF_LIVE_SPIRE_licenceData_78859_202109101531"
        )
        with open(licence_data_file) as f:
            cls.spire_mail = MailFactory(
                edi_data=f.read(),
                extract_type=ExtractTypeEnum.LICENCE_DATA,
                status=ReceptionStatusEnum.REPLY_SENT,
            )
        cls.licence_payload = LicencePayloadFactory(
            reference="GBSIEL/2024/0000001/P",
            data={"details": "organisation address"},
        )

    @classmethod
    def delete_test_data(cls):
        cls.spire_mail.delete()

    def test_spire_mail_anonymised(self):
        anonymised_mail = Mail.objects.get(id=self.spire_mail.id)
        assert anonymised_mail.edi_filename == self.spire_mail.edi_filename
        assert anonymised_mail.raw_data == "The content of the field raw_data is replaced with this static text"
        assert anonymised_mail.sent_data == "The content of the field sent_data is replaced with this static text"

        for index, line in enumerate(anonymised_mail.edi_data.split("\n"), start=1):
            line_type = line.split("\\")[1]
            if line_type == "trader":
                assert (
                    line
                    == f"{index}\\trader\\\\GB123456789000\\\\\\Exporter name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode"
                )

            if line_type == "foreignTrader":
                assert (
                    line
                    == f"{index}\\foreignTrader\\End-user name\\address line1\\address line2\\address line3\\address line4\\address line5\\postcode\\AU"
                )

    def test_licence_payload_anonymised(self):
        anonymised_licence_payload = LicencePayload.objects.get(id=self.licence_payload.id)
        assert anonymised_licence_payload.lite_id == self.licence_payload.lite_id
        assert anonymised_licence_payload.action == self.licence_payload.action
        assert anonymised_licence_payload.data != self.licence_payload.data
