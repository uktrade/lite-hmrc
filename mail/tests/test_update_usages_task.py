import uuid
from unittest import mock

from rest_framework.status import HTTP_200_OK

from conf.settings import LITE_API_URL, HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS, LITE_API_REQUEST_TIMEOUT
from mail.models import Mail, UsageUpdate
from mail.tasks import send_licence_usage_figures_to_lite_api
from mail.tests.libraries.client import LiteHMRCTestClient


class MockTask:
    def __init__(self, attempts: int = 0, exists: bool = True):
        self.attempts = attempts
        self._exists = exists

    def exists(self):
        return self._exists


class MockResponse:
    def __init__(self, message: str = "Success!", status_code: int = HTTP_200_OK):
        self.json_data = message
        self.text = message
        self.status_code = status_code

    def json(self):
        return self.json_data


class UpdateUsagesTaskTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.mail = Mail.objects.create()
        self.usage_update = UsageUpdate.objects.create(
            mail=self.mail,
            licence_ids="",
            hmrc_run_number=0,
            spire_run_number=0,
            lite_payload={"licences": [{"id": str(uuid.uuid4()), "goods": [{"id": str(uuid.uuid4()), "usage": 10}]}]},
        )

    @mock.patch("mail.tasks.put")
    def test_schedule_usages_for_lite_api(self, put_request):
        original_sent_at = self.usage_update.lite_sent_at
        put_request.return_value = MockResponse()

        send_licence_usage_figures_to_lite_api.now(str(self.usage_update.id))

        put_request.assert_called_with(
            f"{LITE_API_URL}/licences/hmrc-integration/",
            self.usage_update.lite_payload,
            hawk_credentials=HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
            timeout=LITE_API_REQUEST_TIMEOUT,
        )

        self.usage_update.refresh_from_db()
        self.assertIsNotNone(self.usage_update.lite_sent_at)
        self.assertNotEqual(self.usage_update.lite_sent_at, original_sent_at)
