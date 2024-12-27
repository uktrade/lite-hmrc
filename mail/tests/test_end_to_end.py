from unittest import mock
from urllib.parse import quote

import requests
from django.conf import settings
from django.urls import reverse

from mail.tests.libraries.client import LiteHMRCTestClient


def clear_stmp_mailbox():
    response = requests.get(f"{settings.MAILHOG_URL}/api/v2/messages")
    for message in response.json()["items"]:
        idx = message["ID"]
        requests.delete(f"{settings.MAILHOG_URL}/api/v1/messages/{idx}")


def get_smtp_body():
    response = requests.get(f"{settings.MAILHOG_URL}/api/v2/messages")
    return response.json()["items"][0]["MIME"]["Parts"][1]["Body"]


class EndToEndTests(LiteHMRCTestClient):
    @mock.patch("mail.celery_tasks.cache")
    def test_send_email_to_hmrc_e2e(self, mock_cache):
        mock_cache.add.return_value = True
        clear_stmp_mailbox()
        self.client.get(reverse("mail:set_all_to_reply_sent"))
        self.client.post(
            reverse("mail:update_licence"), data=self.licence_payload_json, content_type="application/json"
        )
        self.client.get(reverse("mail:send_updates_to_hmrc"))
        body = get_smtp_body().replace("\r", "")
        ymdhm_timestamp = body.split("\n")[0].split("\\")[5]
        run_number = body.split("\n")[0].split("\\")[6]
        expected_mail_body = rf"""1\fileHeader\SPIRE\CHIEF\licenceData\{ymdhm_timestamp}\{run_number}\N
2\licence\20200000001P\insert\GBSIEL/2020/0000001/P\SIE\E\20200602\20220602
3\trader\\GB123456789000\20200602\20220602\Organisation\might 248 James Key Apt. 515 Apt.\942 West Ashleyton Farnborough\Apt. 942\West Ashleyton\Farnborough\GU40 2LX
4\country\GB\\D
5\foreignTrader\End User\42 Road, London, Buckinghamshire\\\\\\GB
6\restrictions\Provisos may apply please see licence
7\line\1\\\\\Sporting shotgun\Q\\030\\10\\\\\\
8\line\2\\\\\Stock\Q\\111\\11.0\\\\\\
9\line\3\\\\\Metal\Q\\025\\1.0\\\\\\
10\line\4\\\\\Chemical\Q\\116\\20.0\\\\\\
11\line\5\\\\\Chemical\Q\\110\\20.0\\\\\\
12\line\6\\\\\Chemical\Q\\074\\20.0\\\\\\
13\line\7\\\\\Old Chemical\Q\\111\\20.0\\\\\\
14\line\8\\\\\A bottle of water\Q\\076\\1.0\\\\\\
15\end\licence\14
16\fileTrailer\1"""
        assert body == expected_mail_body  # nosec
        encoded_reference_code = quote("GBSIEL/2020/0000001/P", safe="")
        response = self.client.get(f"{reverse('mail:licence')}?id={encoded_reference_code}")
        assert response.json()["status"] == "reply_pending"  # nosec
