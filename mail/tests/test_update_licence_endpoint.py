from django.test import tag
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from conf.test_client import LiteHMRCTestClient
from mail.enums import UnitMapping
from mail.models import LicencePayload
from mail.services.helpers import map_unit


class UpdateLicenceEndpointTests(LiteHMRCTestClient):
    url = reverse("mail:update_licence")

    @tag("2448", "fail")
    def test_post_data_failure_no_data(self):
        data = {}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2448", "success")
    def test_post_data_success(self):
        data = {
            "licence": {
                "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
                "reference": "GBSIEL/2020/0000001/P",
                "type": "siel",
                "status": "Submitted",
                "start_date": "2020-06-02",
                "end_date": "2022-06-02",
                "organisation": {
                    "name": "Organisation",
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
            }
        }

        response = self.client.post(
            self.url, data=data, content_type="application/json"
        )

        print(response.json())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(LicencePayload.objects.count() == 1)

    @parameterized.expand(
        [
            ("NAR", 30),
            ("GRM", 21),
            ("KGM", 23),
            ("MTK", 45),
            ("MTR", 57),
            ("LTR", 94),
            ("MTQ", 2),
            ("ITG", 30),
        ]
    )
    @tag("2448", "unit")
    def test_convert(self, lite_input, output):
        self.assertEqual(output, UnitMapping.convert(lite_input))

    @parameterized.expand(
        [
            ("NAR", 30),
            ("GRM", 21),
            ("KGM", 23),
            ("MTK", 45),
            ("MTR", 57),
            ("LTR", 94),
            ("MTQ", 2),
            ("ITG", 30),
        ]
    )
    @tag("2448", "mapping")
    def test_mapping(self, lite_input, output):
        data = {"goods": [{"unit": lite_input}]}
        self.assertEqual(output, map_unit(data, 0)["goods"][0]["unit"])


# {
#     "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
#     "reference": "GBSIEL/2020/0000001/P",
#     "type": "siel",
#     "status": "Submitted",
#     "start_date": "2020-06-02",
#     "end_date": "02 June 2022",
#     "organisation": {
#         "name": "Organisation",
#         "address": {
#             "line_1": "might",
#             "line_2": "248 James Key Apt. 515",
#             "line_3": "Apt. 942",
#             "line_4": "West Ashleyton",
#             "line_5": "Tennessee",
#             "postcode": "99580",
#             "country": {"id": "GB", "name": "United Kingdom"},
#         },
#     },
#     "end_user": {
#         "name": "End User",
#         "address": {
#             "line_1": "42 Road, London, Buckinghamshire",
#             "country": {"id": "GB", "name": "United Kingdom"},
#         },
#     },
#     "goods": [
#         {
#             "id": "f95ded2a-354f-46f1-a572-c7f97d63bed1",
#             "description": "finally",
#             "unit": "NAR",
#             "quantity": 10.0,
#         }
#     ],
# }


# {
#     "id": "ea589f5b-c1d1-41d3-852a-0cb7d138dda3",
#     "reference": "GBOIEL/2020/0000002/P",
#     "type": "oiel",
#     "status": "Submitted",
#     "start_date": "2020-06-02",
#     "end_date": "02 June 2023",
#     "organisation": {
#         "name": "Organisation",
#         "address": {
#             "line_1": "describe",
#             "line_2": "09633 Lisa Fort Suite 356",
#             "line_3": "Suite 491",
#             "line_4": "Kathleenmouth",
#             "line_5": "Colorado",
#             "postcode": "13288",
#             "country": {"id": "GB", "name": "United Kingdom"},
#         },
#     },
#     "countries": [{"id": "GB", "name": "United Kingdom"}],
#     "goods": [
#         {
#             "id": "bad2e6eb-9e8b-4a59-be26-cfd5850bc8f7",
#             "description": "television",
#         }
#     ],
# }
