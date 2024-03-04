import json
import os

from django.conf import settings
from django.core.management import call_command
from django.test import TransactionTestCase

from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.tests.factories import LicencePayloadFactory, MailFactory


class TestAnonymiseDumps(TransactionTestCase):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.delete_test_data()

    @classmethod
    def create_test_data(cls):
        cls.mail = MailFactory(
            extract_type=ExtractTypeEnum.LICENCE_DATA,
            status=ReceptionStatusEnum.REPLY_SENT,
        )
        cls.licence_payload = LicencePayloadFactory(
            reference="GBSIEL/2024/0000001/P",
            data={"details": "organisation address"},
        )

    @classmethod
    def delete_test_data(cls):
        cls.mail.delete()

    def test_mail_anonymised(self):
        assert str(self.mail.id) in self.anonymised_sql
        assert self.mail.edi_data not in self.anonymised_sql
        assert self.mail.raw_data not in self.anonymised_sql
        assert self.mail.sent_data not in self.anonymised_sql
        assert "The content of the field edi_data is replaced with this static text" in self.anonymised_sql
        assert "The content of the field raw_data is replaced with this static text" in self.anonymised_sql
        assert "The content of the field sent_data is replaced with this static text" in self.anonymised_sql

    def test_licence_payload_anonymised(self):
        assert str(self.licence_payload.id) in self.anonymised_sql
        assert str(self.licence_payload.lite_id) in self.anonymised_sql
        assert str(self.licence_payload.action) in self.anonymised_sql
        assert json.dumps(self.licence_payload.data) not in self.anonymised_sql
