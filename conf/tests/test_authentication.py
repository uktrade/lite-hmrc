from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from conf.authentication import convert_gov_paas_url


# override_settings doesn't work - left here for reference
# @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
@patch("conf.authentication.hawk_authentication_enabled", lambda: True)
class TestHawkAuthentication(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # test endpoint that retrieves licence details
        cls.test_url = reverse("mail:licence")

    def test_hawk_authentication_returns_401(self):
        resp = self.client.get(self.test_url)

        # This will trigger an unknown Exception (as HTTP_HAWK_AUTHENTICATION isn't set)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # This will trigger a HawkException as HTTP_HAWK_AUTHENTICATION is invalid
        hawk_header = 'Hawk mac="", hash="", id="lite-api", ts="", nonce=""'
        resp = self.client.get(self.test_url, HTTP_HAWK_AUTHENTICATION=hawk_header)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("conf.authentication.is_env_gov_paas", lambda: True)
    @patch("conf.authentication.convert_gov_paas_url")
    def test_hawk_authentication_calls_convert_url_on_gov_paas(self, mock_convert_gov_paas_url):
        resp = self.client.get(self.test_url)
        mock_convert_gov_paas_url.assert_called_with(resp.wsgi_request.build_absolute_uri())

    def test_convert_gov_paas_url(self):
        resp = self.client.get(self.test_url)
        assert convert_gov_paas_url(resp.wsgi_request.build_absolute_uri()) == "https://testserver/mail/licence/"
