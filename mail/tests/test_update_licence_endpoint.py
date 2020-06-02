from django.test import tag
from django.urls import reverse
from rest_framework import status

from conf.test_client import LiteHMRCTestClient


class UpdateLicenceEndpointTests(LiteHMRCTestClient):
    url = reverse("mail:update_licence")

    @tag("2448")
    def test_post_data_failure_no_data(self):
        data = {}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2448", "success")
    def test_post_data_success(self):
        data = {
            "id": "GBSEI2020/50001",
            "start_date": "2018-09-10",
            "end_date": "2019-10-11",
            "application": {
                "organisation": {
                    "name": "john",
                    "address_1": "an address",
                    "postcode": "ALSDJA",
                },
                "goods": [
                    {
                        "description": "This is a good description",
                        "quantity": 10,
                        "unit": "NAR",
                    }
                ],
                "end_user": {
                    "name": "Bob",
                    "address_1": "an address",
                    "postcode": "ALSDJA",
                    "country": "FR",
                },
            },
        }

        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        print(response.json())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
