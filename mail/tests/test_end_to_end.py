import json

import pytest
import requests
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from pytest_django.asserts import assertQuerySetEqual
from rest_framework import status

from mail.celery_tasks import send_licence_details_to_hmrc
from mail.enums import ReceptionStatusEnum
from mail.libraries.helpers import read_file
from mail.models import LicenceData, LicencePayload, Mail


@pytest.fixture(autouse=True)
def set_settings(settings):
    settings.EMAIL_HOSTNAME = settings.TEST_EMAIL_HOSTNAME
    settings.EMAIL_USER = "spire-to-dit-user"
    settings.EMAIL_PASSWORD = "password"


@pytest.fixture(autouse=True)
def clear_stmp_mailbox(settings):
    requests.delete(f"http://{settings.TEST_EMAIL_HOSTNAME}:8025/api/v1/messages")


@pytest.fixture()
def licence_payload_json():
    return json.loads(read_file("mail/tests/files/licence_payload_file", encoding="utf-8"))


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


@pytest.mark.django_db()
@freeze_time("2020-01-01")
def test_send_email_to_hmrc_e2e(client, licence_payload_json):
    assert not LicencePayload.objects.exists()

    response = client.post(
        reverse("mail:update_licence"),
        data=licence_payload_json,
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert LicencePayload.objects.count() == 1
    licence_payload = LicencePayload.objects.get()
    assert not licence_payload.is_processed

    assert not LicenceData.objects.exists()

    assert not Mail.objects.exists()

    send_licence_details_to_hmrc.delay()

    licence_payload.refresh_from_db()
    assert licence_payload.is_processed

    assert LicenceData.objects.count() == 1
    licence_data = LicenceData.objects.get()
    assert licence_data.hmrc_run_number == 1
    assertQuerySetEqual(licence_data.licence_payloads.all(), [licence_payload])

    assert Mail.objects.count() == 1
    mail = Mail.objects.get()
    assert mail.status == ReceptionStatusEnum.REPLY_PENDING

    assert licence_data.mail == mail

    body = get_smtp_body().replace("\r", "")
    expected_mail_body = rf"""1\fileHeader\SPIRE\CHIEF\licenceData\202001010000\1\N
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
    assert body == expected_mail_body
