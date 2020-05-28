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
