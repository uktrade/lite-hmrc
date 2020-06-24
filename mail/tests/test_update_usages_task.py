from unittest import mock

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from conf.settings import LITE_API_URL, HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS, LITE_API_REQUEST_TIMEOUT, MAX_ATTEMPTS
from mail.models import Mail, UsageUpdate
from mail.tasks.send_licence_usage_figures_to_lite_api import (
    send_licence_usage_figures_to_lite_api,
    schedule_max_tried_task_as_new_task,
)
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


@mock.patch("mail.apps.BACKGROUND_TASK_ENABLED", False)  # Disable task from being run on app initialization
class UpdateUsagesTaskTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.mail = Mail.objects.create()
        self.usage_update = UsageUpdate.objects.create(
            mail=self.mail,
            licence_ids='["GBSIEL/2020/0000001/P", "GBSIEL/2020/0000002/P"]',
            hmrc_run_number=0,
            spire_run_number=0,
            lite_payload={},
        )

    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.put")
    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.build_lite_payload")
    def test_schedule_usages_for_lite_api_200_ok(self, build_payload, put_request):
        original_sent_at = self.usage_update.lite_sent_at
        build_payload.return_value = None
        put_request.return_value = MockResponse(status_code=HTTP_200_OK)

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

    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.put")
    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.build_lite_payload")
    def test_schedule_usages_for_lite_api_400_bad_request(self, build_payload, put_request):
        build_payload.return_value = None
        put_request.return_value = MockResponse(status_code=HTTP_400_BAD_REQUEST)

        with self.assertRaises(Exception) as error:
            send_licence_usage_figures_to_lite_api.now(str(self.usage_update.id))

        put_request.assert_called_with(
            f"{LITE_API_URL}/licences/hmrc-integration/",
            self.usage_update.lite_payload,
            hawk_credentials=HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
            timeout=LITE_API_REQUEST_TIMEOUT,
        )

        self.usage_update.refresh_from_db()
        self.assertIsNone(self.usage_update.lite_sent_at)

    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.schedule_max_tried_task_as_new_task")
    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.Task.objects.get")
    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.put")
    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.build_lite_payload")
    def test_schedule_usages_for_lite_api_max_tried_task(self, build_payload, put_request, get_task, schedule_new_task):
        build_payload.return_value = None
        put_request.return_value = MockResponse(status_code=HTTP_400_BAD_REQUEST)
        get_task.return_value = MockTask(MAX_ATTEMPTS - 1)
        schedule_new_task.return_value = None

        with self.assertRaises(Exception) as error:
            send_licence_usage_figures_to_lite_api.now(str(self.usage_update.id))

        put_request.assert_called_with(
            f"{LITE_API_URL}/licences/hmrc-integration/",
            self.usage_update.lite_payload,
            hawk_credentials=HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
            timeout=LITE_API_REQUEST_TIMEOUT,
        )

        schedule_new_task.assert_called_with(str(self.usage_update.id))

        self.usage_update.refresh_from_db()
        self.assertIsNone(self.usage_update.lite_sent_at)
        self.assertIsNone(self.usage_update.lite_sent_at)
        self.assertIsNone(self.usage_update.lite_sent_at)

    @mock.patch("mail.tasks.send_licence_usage_figures_to_lite_api.send_licence_usage_figures_to_lite_api")
    def test_schedule_new_task(self, send_licence_usage_figures):
        send_licence_usage_figures.return_value = None

        schedule_max_tried_task_as_new_task(str(self.usage_update.id))

        send_licence_usage_figures.assert_called_with(str(self.usage_update.id), schedule=mock.ANY)
