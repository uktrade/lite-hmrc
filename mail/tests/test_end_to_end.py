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
from mail.models import LicenceData, LicencePayload, Mail, UsageData
from mail.servers import MailServer

pytestmark = pytest.mark.django_db


@pytest.fixture()
def outgoing_email_user():
    return "hmrc@example.com"


@pytest.fixture(autouse=True)
def set_settings(settings, outgoing_email_user):
    settings.EMAIL_HOSTNAME = settings.TEST_EMAIL_HOSTNAME
    settings.EMAIL_USER = "outbox-user"
    settings.EMAIL_PASSWORD = "password"

    settings.INCOMING_EMAIL_USER = "spire@example.com"
    settings.SPIRE_FROM_ADDRESS = "spire@example.com"
    settings.SPIRE_ADDRESS = "spire@example.com"

    settings.OUTGOING_EMAIL_USER = outgoing_email_user

    settings.HMRC_TO_DIT_REPLY_ADDRESS = "hmrctodit@example.com"
    settings.HMRC_ADDRESS = "hmrctodit@example.com"


@pytest.fixture()
def hmrc_to_dit_mailserver_api_url():
    return "http://hmrc-to-dit-mailserver:8025/api/v1/"


@pytest.fixture()
def spire_to_dit_mailserver_api_url():
    return "http://spire-to-dit-mailserver:8025/api/v1/"


@pytest.fixture()
def outbox_mailserver_api_url():
    return "http://outbox-mailserver:8025/api/v1/"


@pytest.fixture(autouse=True)
def clear_mailboxes(hmrc_to_dit_mailserver_api_url, spire_to_dit_mailserver_api_url, outbox_mailserver_api_url):
    requests.delete(f"{hmrc_to_dit_mailserver_api_url}messages")
    requests.delete(f"{spire_to_dit_mailserver_api_url}messages")
    requests.delete(f"{outbox_mailserver_api_url}messages")


@pytest.fixture()
def licence_payload_json():
    return json.loads(read_file("mail/tests/files/licence_payload_file", encoding="utf-8"))


@pytest.fixture()
def licence_data_file_name():
    return "CHIEF_LIVE_SPIRE_licenceData_1_202001010000"


@pytest.fixture()
def licence_data_file_body(licence_data_file_name):
    return read_file(f"mail/tests/files/end_to_end/{licence_data_file_name}", mode="rb")


@pytest.fixture()
def licence_reply_file_name():
    return "ILBDOTI_live_CHIEF_licenceReply_1_202001010000"


@pytest.fixture()
def licence_reply_file_body(licence_reply_file_name):
    return read_file(f"mail/tests/files/end_to_end/{licence_reply_file_name}", mode="rb")


@pytest.fixture()
def usage_data_file_name():
    return "ILBDOTI_live_CHIEF_usageData_1_202001010000"


@pytest.fixture()
def usage_data_file_body(usage_data_file_name):
    return read_file(f"mail/tests/files/end_to_end/{usage_data_file_name}", mode="rb")


@pytest.fixture(autouse=True)
def hmrc_to_dit_mailserver(mocker):
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


@pytest.fixture(autouse=True)
def spire_to_dit_mailserver(mocker):
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


def normalise_line_endings(string):
    return string.replace("\r", "").strip()


@pytest.fixture()
def get_smtp_message_count(outbox_mailserver_api_url):
    def _get_smtp_message_count():
        response = requests.get(f"{outbox_mailserver_api_url}messages")
        assert response.status_code == 200, response.content

        return len(response.json()["messages"])

    return _get_smtp_message_count


@pytest.fixture()
def get_smtp_message(outbox_mailserver_api_url):
    def _get_smtp_message():
        response = requests.get(f"{outbox_mailserver_api_url}messages")
        assert response.status_code == 200, response.content
        mail_id = response.json()["messages"][0]["ID"]

        response = requests.get(f"{outbox_mailserver_api_url}message/{mail_id}")
        assert response.status_code == 200

        return mail_id, response.json()

    return _get_smtp_message


@pytest.fixture()
def get_smtp_body(outbox_mailserver_api_url, get_smtp_message):
    def _get_smtp_body():
        mail_id, smtp_message = get_smtp_message()
        part_id = smtp_message["Attachments"][0]["PartID"]

        response = requests.get(f"{outbox_mailserver_api_url}message/{mail_id}/part/{part_id}")
        assert response.status_code == 200

        return response.content.decode("ascii")

    return _get_smtp_body


@freeze_time("2020-01-01")
def test_send_lite_licence_data_to_hmrc_e2e(
    client,
    licence_payload_json,
    licence_data_file_name,
    licence_data_file_body,
    get_smtp_message_count,
    get_smtp_message,
    get_smtp_body,
):
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

    assert get_smtp_message_count() == 1

    _, message = get_smtp_message()
    assert message["To"] == [{"Name": "", "Address": "hmrc@example.com"}]
    assert message["Subject"] == licence_data_file_name

    body = get_smtp_body()
    assert normalise_line_endings(body) == normalise_line_endings(licence_data_file_body.decode("ascii"))


def test_receive_lite_licence_reply_from_hmrc_e2e(
    licence_reply_file_body,
    licence_reply_file_name,
    get_smtp_message_count,
):
    mail = Mail.objects.create(
        extract_type=ExtractTypeEnum.LICENCE_REPLY,
        edi_filename=licence_reply_file_name,
        edi_data=licence_reply_file_body.decode("ascii"),
        status=ReceptionStatusEnum.REPLY_PENDING,
    )
    LicenceData.objects.create(
        hmrc_run_number=1,
        mail=mail,
        source=SourceEnum.LITE,
    )

    response = requests.post(
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
    assert response.status_code == status.HTTP_200_OK

    manage_inbox.delay()

    mail.refresh_from_db()
    assert mail.status == ReceptionStatusEnum.REPLY_SENT
    assert normalise_line_endings(mail.response_data) == normalise_line_endings(licence_reply_file_body.decode("ascii"))
    assert mail.response_filename == licence_reply_file_name
    assert mail.response_subject == licence_reply_file_name

    assert get_smtp_message_count() == 0


def test_receive_spire_licence_data_and_send_to_hmrc_e2e(
    spire_to_dit_mailserver_api_url,
    licence_data_file_name,
    licence_data_file_body,
    outgoing_email_user,
    get_smtp_message_count,
    get_smtp_message,
    get_smtp_body,
):
    assert not Mail.objects.exists()
    assert not LicenceData.objects.exists()

    response = requests.post(
        f"{spire_to_dit_mailserver_api_url}send",
        json={
            "From": {"Email": settings.INCOMING_EMAIL_USER, "Name": "SPIRE"},
            "Subject": licence_data_file_name,
            "To": [{"Email": "lite@example.com", "Name": "LITE"}],  # /PS-IGNORE
            "Attachments": [
                {
                    "Content": b64encode(licence_data_file_body).decode("ascii"),
                    "Filename": licence_data_file_name,
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_200_OK

    manage_inbox.delay()

    assert Mail.objects.count() == 1
    mail = Mail.objects.get()
    assert mail.status == ReceptionStatusEnum.REPLY_PENDING
    assert mail.edi_filename == licence_data_file_name
    assert normalise_line_endings(mail.edi_data) == normalise_line_endings(licence_data_file_body.decode("ascii"))

    assert LicenceData.objects.count() == 1
    licence_data = LicenceData.objects.get()
    assert licence_data.mail == mail
    assert licence_data.source == SourceEnum.SPIRE
    assert licence_data.hmrc_run_number == 1
    assert licence_data.source_run_number == 1
    assert not licence_data.licence_payloads.exists()

    assert get_smtp_message_count() == 1

    _, smtp_message = get_smtp_message()
    assert smtp_message["To"] == [{"Address": outgoing_email_user, "Name": ""}]
    assert smtp_message["Subject"] == licence_data_file_name

    body = get_smtp_body()
    assert normalise_line_endings(body) == normalise_line_endings(licence_data_file_body.decode("ascii"))


def test_receive_spire_licence_reply_from_hmrc_e2e(
    licence_data_file_name,
    licence_data_file_body,
    licence_reply_file_name,
    licence_reply_file_body,
    get_smtp_message_count,
    get_smtp_message,
    get_smtp_body,
):
    mail = Mail.objects.create(
        extract_type=ExtractTypeEnum.LICENCE_DATA,
        status=ReceptionStatusEnum.REPLY_PENDING,
        edi_filename=licence_data_file_name,
        edi_data=licence_data_file_body.decode("ascii"),
    )
    licence_data = LicenceData.objects.create(
        mail=mail,
        source=SourceEnum.SPIRE,
        hmrc_run_number=1,
        source_run_number=1,
    )

    response = requests.post(
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
    assert response.status_code == status.HTTP_200_OK

    manage_inbox.delay()

    mail.refresh_from_db()
    assert mail.status == ReceptionStatusEnum.REPLY_SENT
    assert mail.extract_type == ExtractTypeEnum.LICENCE_REPLY
    assert mail.response_filename == licence_reply_file_name
    assert normalise_line_endings(mail.response_data) == normalise_line_endings(licence_reply_file_body.decode("ascii"))

    assert get_smtp_message_count() == 1

    _, message = get_smtp_message()
    assert message["To"] == [{"Name": "", "Address": "spire@example.com"}]
    assert message["Subject"] == licence_reply_file_name

    body = get_smtp_body()
    assert normalise_line_endings(body) == normalise_line_endings(licence_reply_file_body.decode("ascii"))


def test_receive_spire_licence_reply_from_hmrc_e2e(
    usage_data_file_name,
    usage_data_file_body,
    get_smtp_message_count,
    get_smtp_message,
    get_smtp_body,
):
    assert not Mail.objects.exists()
    assert not UsageData.objects.exists()

    response = requests.post(
        "http://hmrc-to-dit-mailserver:8025/api/v1/send",
        json={
            "From": {"Email": settings.HMRC_TO_DIT_REPLY_ADDRESS, "Name": "HMRC"},
            "Subject": usage_data_file_name,
            "To": [{"Email": "lite@example.com", "Name": "LITE"}],  # /PS-IGNORE
            "Attachments": [
                {
                    "Content": b64encode(usage_data_file_body).decode("ascii"),
                    "Filename": usage_data_file_name,
                }
            ],
        },
    )
    assert response.status_code == status.HTTP_200_OK

    manage_inbox.delay()

    assert Mail.objects.count() == 1
    mail = Mail.objects.get()
    assert mail.extract_type == ExtractTypeEnum.USAGE_DATA
    assert mail.status == ReceptionStatusEnum.REPLY_SENT
    assert mail.edi_filename == usage_data_file_name
    assert normalise_line_endings(mail.edi_data) == normalise_line_endings(usage_data_file_body.decode("ascii"))

    assert UsageData.objects.count() == 1
    usage_data = UsageData.objects.get()
    assert usage_data.mail == mail
    assert usage_data.spire_run_number == 1
    assert usage_data.hmrc_run_number == 1
    assert not usage_data.has_lite_data
    assert usage_data.has_spire_data

    assert get_smtp_message_count() == 1

    _, message = get_smtp_message()
    assert message["To"] == [{"Name": "", "Address": "spire@example.com"}]
    assert message["Subject"] == usage_data_file_name

    body = get_smtp_body()
    assert normalise_line_endings(body) == normalise_line_endings(usage_data_file_body.decode("ascii"))
