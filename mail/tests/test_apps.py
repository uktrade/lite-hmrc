from unittest import mock

from django.conf import settings
from rest_framework.status import HTTP_207_MULTI_STATUS

from mail.apps import MailConfig
from mail.models import LicencePayload, Mail, UsageData
from mail.tests.libraries.client import LiteHMRCTestClient


class MockResponse:
    def __init__(self, json: dict = None, status_code: int = HTTP_207_MULTI_STATUS):
        self.json_data = json or {}
        self.text = str(self.json_data)
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestApps(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()
        self.licence_payload_1 = LicencePayload.objects.create(
            lite_id="2e6f3fe2-40a2-4c7c-8b71-3f0e53f92298", reference="GBSIEL/2020/0000008/P"
        )
        self.licence_payload_2 = LicencePayload.objects.create(
            lite_id="80a3d9b2-09a9-4e86-840f-236d186e5b0c", reference="GBSIEL/2020/0000009/P"
        )
        self.mail = Mail.objects.create(
            edi_filename="usage_data",
            edi_data=(
                "1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\\n"
                "2\\licenceUsage\\LU04148/00001\\insert\\GBSIEL/2020/0000008/P\\O\\\n"
                "3\\line\\1\\0\\0\\\n"
                "4\\usage\\O\\9GB000001328000-PE112345\\R\\20190112\\0\\0\\\\000262\\\\\\\\\n"
                "5\\end\\line\\5\n"
                "6\\end\\licenceUsage\\5\n"
                "7\\licenceUsage\\LU04148/00002\\insert\\GBSIEL/2020/0000009/P\\O\\\n"
                "8\\line\\1\\0\\0\\\n"
                "9\\usage\\O\\9GB000003133000-445251012345\\Z\\20190112\\0\\0\\\\000962\\\\\\\\\n"
                "10\\end\\line\\3\n"
                "11\\end\\licenceUsage\\5\n"
                "12\\fileTrailer\\2"
            ),
        )
        self.usage_data = UsageData.objects.create(
            id="1e5a4fd0-e581-4efd-9770-ac68e04852d2",
            mail=self.mail,
            licence_ids='["GBSIEL/2020/0000008/P", "GBSIEL/2020/0000009/P"]',
            hmrc_run_number=0,
            spire_run_number=0,
            has_lite_data=True,
        )

    @mock.patch("mail.celery_tasks.mail_requests.put")
    def test_app_initialization_processes_usage_data(self, put_request):
        put_request.return_value = MockResponse(
            json={
                "usage_data_id": "1e5a4fd0-e581-4efd-9770-ac68e04852d2",
                "licences": {
                    "accepted": [
                        {
                            "id": "2e6f3fe2-40a2-4c7c-8b71-3f0e53f92298",
                            "goods": [{"id": "27ac9316-abd0-4dc1-981e-b50714c7fb8c", "usage": 10}],
                        }
                    ],
                    "rejected": [
                        {
                            "id": "80a3d9b2-09a9-4e86-840f-236d186e5b0c",
                            "goods": {
                                "accepted": [{"id": "7aaccfa6-1d60-4a87-9897-3c04c20192e7", "usage": 10}],
                                "rejected": [
                                    {
                                        "id": "87151418-dfff-4688-ab0c-ff8990db5365",
                                        "usage": 10,
                                        "errors": {"id": ["Good not found on Licence."]},
                                    }
                                ],
                            },
                            "errors": {"goods": ["One or more Goods were rejected."]},
                        }
                    ],
                },
            },
            status_code=HTTP_207_MULTI_STATUS,
        )

        # We expect our UsageData record to be processed as part of this initialization function
        MailConfig.initialize_send_licence_usage_figures_to_lite_api()

        self.usage_data.refresh_from_db()
        put_request.assert_called_with(
            f"{settings.LITE_API_URL}/licences/hmrc-integration/",
            self.usage_data.lite_payload,
            hawk_credentials=settings.HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
            timeout=settings.LITE_API_REQUEST_TIMEOUT,
        )
        self.usage_data.refresh_from_db()
        self.assertIsNotNone(self.usage_data.lite_sent_at)
        self.assertEqual(self.usage_data.lite_accepted_licences, ["GBSIEL/2020/0000008/P"])
        self.assertEqual(self.usage_data.lite_rejected_licences, ["GBSIEL/2020/0000009/P"])
