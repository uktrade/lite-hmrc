import json
import logging
from datetime import datetime

from django.test import testcases

from conf import settings
from mail.libraries.helpers import read_file
from mail.libraries.helpers import to_smart_text
from mail.models import LicencePayload
from mail.tests.libraries import colours


class LiteHMRCTestClient(testcases.TestCase):
    TEST_RUN_NUMBER = "49543"

    @classmethod
    def tearDownClass(cls):
        logging.debug("tearDownClass() is called")
        super().tearDownClass()

    def setUp(self):
        if settings.TIME_TESTS:
            self.tick = datetime.now()

        self.licence_usage_file_name = "ILBDOTI_live_CHIEF_usageData_49543_201901130300"
        self.licence_usage_file_body = to_smart_text(read_file("mail/tests/files/license_usage_file", mode="rb"))
        self.licence_update_reply_body = (
            b"MVxmaWxlSGVhZGVyXENISUVGXFNQSVJFXGxpY2VuY2VSZXBseVwyMDE5MDIwODAwMjVcMTAxMAo"
            b"yXGFjY2VwdGVkXEdCU0lFTC8yMDIwLzAwMDAwMDEvUAozXGFjY2VwdGVkXEdCU0lFTC8yMDIwLz"
            b"AwMDAwMDEvUAo0XGZpbGVUcmFpbGVyXDJcMFww"
        )
        # todo need to see a real example
        self.usage_update_reply_body = to_smart_text(read_file("mail/tests/files/usage_update_reply_file", mode="rb"))
        logging.debug("licence_update_reply_body: \n{}".format(self.licence_update_reply_body))
        self.licence_update_reply_name = "ILBDOTI_live_CHIEF_licenceReply_49543_201902080025"

        self.usage_update_reply_name = "ILBDOTI_live_CHIEF_usageReply_49543_201902080025"

        self.licence_update_file_name = "ILBDOTI_live_CHIEF_licenceUpdate_49543_201902080025"

        self.licence_update_file_body = to_smart_text(read_file("mail/tests/files/license_update_file", mode="rb"))

        self.licence_payload_json = json.loads(read_file("mail/tests/files/licence_payload_file", encoding="utf-8"))

        self.single_siel_licence_payload = LicencePayload.objects.create(
            lite_id=self.licence_payload_json["licence"]["id"],
            reference=self.licence_payload_json["licence"]["reference"],
            data=self.licence_payload_json["licence"],
        )

    def tearDown(self):
        """
        Print output time for tests if settings.TIME_TESTS is set to True
        """
        if settings.TIME_TESTS:
            self.tock = datetime.now()

            diff = self.tock - self.tick
            time = round(diff.microseconds / 1000, 2)
            colour = colours.green
            emoji = ""

            if time > 100:
                colour = colours.orange
            if time > 300:
                colour = colours.red
                emoji = " 🔥"

            print(self._testMethodName + emoji + " " + colour(str(time) + "ms") + emoji)