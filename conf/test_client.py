from datetime import datetime
from django.test import testcases
from conf import colours, settings
from mail.services.helpers import read_file
from mail.services.helpers import (
    to_smart_text,
)
import logging

logger = logging.getLogger('LiteHMRCTestClient')

class LiteHMRCTestClient(testcases.TestCase):
    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        if settings.TIME_TESTS:
            self.tick = datetime.now()
        self.licence_usage_file_name = "ILBDOTI_live_CHIEF_usageData_9876_201901130300"
        self.licence_usage_file_body = to_smart_text(
            read_file('mail/tests/files/license_usage_file')
        )
        # print("licence_usage_file_body: \n{}".format(self.licence_usage_file_body))
        self.licence_update_reply_body = to_smart_text(read_file('mail/tests/files/license_update_reply_file'))
        logger.debug("licence_update_reply_body: \n{}".format(self.licence_update_reply_body))
        self.licence_update_reply_name = (
            "ILBDOTI_live_CHIEF_licenceReply_49543_201902080025"
        )

        self.usage_update_reply_name = (
            "ILBDOTI_live_CHIEF_usageReply_49543_201902080025"
        )

        self.licence_update_file_name = (
            "ILBDOTI_live_CHIEF_licenceUpdate_49543_201902080025"
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
