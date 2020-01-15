from parameterized import parameterized

from conf.test_client import LiteHMRCTestClient
from mail.services.helpers import convert_sender_to_source


class HelpersTests(LiteHMRCTestClient):
    @parameterized.expand([["test@spire.com", "SPIRE"], ["test@lite.com", "LITE"]])
    def test_convert_sender_to_source(self, sender, source):
        self.assertEqual(convert_sender_to_source(sender), source)
