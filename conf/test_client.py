from datetime import datetime
from django.test import testcases
from conf import colours, settings
from mail.models import LicencePayload
from mail.services.helpers import read_file
from mail.services.helpers import to_smart_text
import logging


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
        self.licence_usage_file_body = to_smart_text(read_file("mail/tests/files/license_usage_file"))
        self.licence_update_reply_body = b"MVxmaWxlSGVhZGVyXENISUVGXFNQSVJFXGxpY2VuY2VSZXBseVwyMDE5MDIwODAwMjVcMTAxMAoyXGFjY2VwdGVkXEdCU0lFTC8yMDIwLzAwMDAwMDEvUAozXGFjY2VwdGVkXEdCU0lFTC8yMDIwLzAwMDAwMDEvUAo0XGZpbGVUcmFpbGVyXDJcMFww"
        # todo need to see a real example
        self.usage_update_reply_body = to_smart_text(read_file("mail/tests/files/usage_update_reply_file"))
        logging.debug("licence_update_reply_body: \n{}".format(self.licence_update_reply_body))
        self.licence_update_reply_name = "ILBDOTI_live_CHIEF_licenceReply_49543_201902080025"

        self.usage_update_reply_name = "ILBDOTI_live_CHIEF_usageReply_49543_201902080025"

        self.licence_update_file_name = "ILBDOTI_live_CHIEF_licenceUpdate_49543_201902080025"

        self.licence_update_file_body = to_smart_text(read_file("mail/tests/files/license_update_file"))

        self.single_siel_licence_payload = LicencePayload.objects.create(
            reference="GBSIEL2020/50001",
            data={
                "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
                "reference": "GBSIEL/2020/0000001/P",
                "type": "siel",
                "status": "Submitted",
                "start_date": "2020-06-02",
                "end_date": "2022-06-02",
                "organisation": {
                    "name": "Organisation",
                    "id": "10a21d56-9e9d-333d-77c5-479bb3de7ac9",
                    "address": {
                        "line_1": "might",
                        "line_2": "248 James Key Apt. 515",
                        "line_3": "Apt. 942",
                        "line_4": "West Ashleyton",
                        "line_5": "Tennessee",
                        "postcode": "99580",
                        "country": {"id": "GB", "name": "United Kingdom"},
                    },
                },
                "end_user": {
                    "name": "End User",
                    "address": {
                        "line_1": "42 Road, London, Buckinghamshire",
                        "country": {"id": "GB", "name": "United Kingdom"},
                    },
                },
                "goods": [
                    {
                        "id": "f95ded2a-354f-46f1-a572-c7f97d63bed1",
                        "description": "finally",
                        "unit": "NAR",
                        "quantity": 10.0,
                    }
                ],
            },
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
