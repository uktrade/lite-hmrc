import json
from base64 import b64encode

import pytest
import requests
from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from pytest_django.asserts import assertQuerySetEqual
from rest_framework import status

from mail.auth import BasicAuthentication
from mail.celery_tasks import manage_inbox, send_licence_details_to_hmrc
from mail.enums import ExtractTypeEnum, ReceptionStatusEnum, SourceEnum
from mail.libraries.helpers import read_file
from mail.models import LicenceData, LicencePayload, Mail
from mail.servers import MailServer


@pytest.fixture(autouse=True)
def set_settings(settings):
    settings.EMAIL_HOSTNAME = settings.TEST_EMAIL_HOSTNAME
    settings.EMAIL_USER = "spire-to-dit-user"
    settings.EMAIL_PASSWORD = "password"

    settings.HMRC_TO_DIT_REPLY_ADDRESS = "hmrctodit@example.com"


@pytest.fixture(autouse=True)
def clear_mailboxes():
    requests.delete("http://hmrc-to-dit-mailserver:8025/api/v1/messages")
    requests.delete("http://spire-to-dit-mailserver:8025/api/v1/messages")


@pytest.fixture()
def licence_payload_json():
    return json.loads(read_file("mail/tests/files/licence_payload_file", encoding="utf-8"))


@pytest.fixture()
def licence_data_file_body():
    return read_file("mail/tests/files/end_to_end/CHIEF_LIVE_SPIRE_licenceData_1_202001010000")


@pytest.fixture()
def licence_reply_file_name():
    return "ILBDOTI_live_CHIEF_licenceReply_1_202001010000"


@pytest.fixture()
def licence_reply_file_body(licence_reply_file_name):
    return read_file(f"mail/tests/files/end_to_end/{licence_reply_file_name}", mode="rb")


def normalise_line_endings(string):
    return string.replace("\r", "").strip()


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
def test_send_lite_licence_data_to_hmrc_e2e(client, licence_payload_json, licence_data_file_body):
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
    assert licence_data.source == SourceEnum.LITE
    assertQuerySetEqual(licence_data.licence_payloads.all(), [licence_payload])

    assert Mail.objects.count() == 1
    mail = Mail.objects.get()
    assert mail.status == ReceptionStatusEnum.REPLY_PENDING

    assert licence_data.mail == mail

    body = get_smtp_body()
    assert normalise_line_endings(body) == normalise_line_endings(licence_data_file_body)


@pytest.mark.django_db()
def test_receive_lite_licence_reply_from_hmrc_e2e(mocker, licence_reply_file_body, licence_reply_file_name):
    auth = BasicAuthentication(
        user="hmrc-to-dit-user",
        password="password",
    )
    hmrc_to_dit_mailserver = MailServer(
        auth,
        hostname="hmrc-to-dit-mailserver",
        pop3_port=1110,
    )
    mocker.patch(
        "mail.libraries.routing_controller.get_hmrc_to_dit_mailserver",
        return_value=hmrc_to_dit_mailserver,
    )

    auth = BasicAuthentication(
        user="spire-to-dit-user",
        password="password",
    )
    spire_to_dit_mailserver = MailServer(
        auth,
        hostname="spire-to-dit-mailserver",
        pop3_port=1110,
    )
    mocker.patch(
        "mail.libraries.routing_controller.get_spire_to_dit_mailserver",
        return_value=spire_to_dit_mailserver,
    )

    mail = Mail.objects.create(
        extract_type=ExtractTypeEnum.LICENCE_REPLY,
        edi_filename=licence_reply_file_name,
        edi_data=licence_reply_file_body.decode("ascii"),
        status=ReceptionStatusEnum.REPLY_PENDING,
    )
    licence_data = LicenceData.objects.create(
        hmrc_run_number=1,
        mail=mail,
        source=SourceEnum.LITE,
    )

    licence_reply_file_name = "ILBDOTI_live_CHIEF_licenceReply_1_202001010000"
    requests.post(
        "http://hmrc-to-dit-mailserver:8025/api/v1/send",
        json={
            "From": {"Email": settings.HMRC_TO_DIT_REPLY_ADDRESS, "Name": "HMRC"},
            "Subject": licence_reply_file_name,
            "To": [{"Email": "lite@example.com", "Name": "LITE"}],  # /PS-IGNORE
            "Attachments": [
                {
                    "Content": b64encode(licence_reply_file_body).decode("ascii"),
                    "Filename": licence_reply_file_name,
                }
            ],
        },
    )

    manage_inbox.delay()

    mail.refresh_from_db()
    assert mail.status == ReceptionStatusEnum.REPLY_SENT
    assert normalise_line_endings(mail.response_data) == normalise_line_endings(licence_reply_file_body.decode("ascii"))
    assert mail.response_filename == licence_reply_file_name
    assert mail.response_subject == licence_reply_file_name
