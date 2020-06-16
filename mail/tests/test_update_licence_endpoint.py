from django.test import tag
from django.urls import reverse
from rest_framework import status

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

    @tag("2448", "success")
    def test_post_data_idempotent(self):
        initial_licence_count = LicencePayload.objects.count()
        self.client.post(self.url, data=self.licence_payload_json, content_type="application/json")
        response = self.client.post(self.url, data=self.licence_payload_json, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_304_NOT_MODIFIED)
        self.assertEqual(LicencePayload.objects.count(), initial_licence_count + 1)
