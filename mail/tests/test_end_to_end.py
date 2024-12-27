from urllib.parse import quote

import requests
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from mail.celery_tasks import send_licence_details_to_hmrc
from mail.tests.libraries.client import LiteHMRCTestClient


def clear_stmp_mailbox():
    requests.delete(f"http://{settings.TEST_EMAIL_HOSTNAME}:8025/api/v1/messages")


def get_smtp_body():
    response = requests.get(f"http://{settings.TEST_EMAIL_HOSTNAME}:8025/api/v1/messages")
    assert response.status_code == 200, response.content
    mail_id = response.json()["messages"][0]["ID"]

    response = requests.get(f"http://{settings.TEST_EMAIL_HOSTNAME}:8025/api/v1/message/{mail_id}")
    assert response.status_code == 200
    part_id = response.json()["Attachments"][0]["PartID"]

    response = requests.get(f"http://{settings.TEST_EMAIL_HOSTNAME}:8025/api/v1/message/{mail_id}/part/{part_id}")
    assert response.status_code == 200

    return response.content.decode("ascii")


@override_settings(
    EMAIL_HOSTNAME=settings.TEST_EMAIL_HOSTNAME,
    EMAIL_USER="spire-to-dit-user",
    EMAIL_PASSWORD="password",
)
class EndToEndTests(LiteHMRCTestClient):
    def test_send_email_to_hmrc_e2e(self):
        clear_stmp_mailbox()
        response = self.client.post(
            reverse("mail:update_licence"),
            data=self.licence_payload_json,
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        send_licence_details_to_hmrc.delay()
        body = get_smtp_body()
        body = body.replace("\r", "")
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
16\fileTrailer\1
"""
        self.assertEqual(
            body,
            expected_mail_body,
        )
        encoded_reference_code = quote("GBSIEL/2020/0000001/P", safe="")
        response = self.client.get(f"{reverse('mail:licence')}?id={encoded_reference_code}")
        self.assertEqual(
            response.json()["status"],
            "reply_pending",
        )
