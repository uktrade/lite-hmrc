from mail.tests.libraries.client import LiteHMRCTestClient
from mail.models import Mail


class TestDataProcessors(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

    def test(self):
        Mail.send_rejection_notification_email()
