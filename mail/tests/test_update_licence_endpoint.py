from django.test import tag
from django.urls import reverse
from parameterized import parameterized
from rest_framework import status

from mail.enums import UnitMapping
from mail.libraries.helpers import map_unit
from mail.models import LicencePayload
from mail.tests.libraries.client import LiteHMRCTestClient


class UpdateLicenceEndpointTests(LiteHMRCTestClient):
    url = reverse("mail:update_licence")

    @tag("2448", "fail")
    def test_post_data_failure_no_data(self):
        data = {}

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @tag("2448", "success")
    def test_post_data_success(self):
        initial_licence_count = LicencePayload.objects.count()
        response = self.client.post(self.url, data=self.licence_payload_json, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LicencePayload.objects.count(), initial_licence_count + 1)

    @parameterized.expand(
        [("NAR", 30), ("GRM", 21), ("KGM", 23), ("MTK", 45), ("MTR", 57), ("LTR", 94), ("MTQ", 2), ("ITG", 30),]
    )
    @tag("2448", "unit")
    def test_convert(self, lite_input, output):
        self.assertEqual(output, UnitMapping.convert(lite_input))

    @parameterized.expand(
        [("NAR", 30), ("GRM", 21), ("KGM", 23), ("MTK", 45), ("MTR", 57), ("LTR", 94), ("MTQ", 2), ("ITG", 30),]
    )
    @tag("2448", "mapping")
    def test_mapping(self, lite_input, output):
        data = {"goods": [{"unit": lite_input}]}
        self.assertEqual(output, map_unit(data, 0)["goods"][0]["unit"])
