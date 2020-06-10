from datetime import datetime
from unittest import mock

from django.test import tag
from django.urls import reverse

from conf.test_client import LiteHMRCTestClient
from mail.models import LicencePayload, Mail, OrganisationIdMapping, GoodIdMapping
from mail.services.lite_to_edifact_converter import licences_to_edifact

from mail.tasks import email_lite_licence_updates


class SmtpMock:
    def quit(self):
        pass


class LicenceToEdifactTests(LiteHMRCTestClient):
    @tag("mapping-ids")
    def test_mappings(self):
        licence = LicencePayload.objects.get()

        organisation_id = licence.data["organisation"]["id"]
        good_id = licence.data["goods"][0]["id"]

        licences_to_edifact(LicencePayload.objects.filter())

        self.assertEqual(OrganisationIdMapping.objects.filter(lite_id=organisation_id, rpa_trader_id=1).count(), 1)
        self.assertEqual(
            GoodIdMapping.objects.filter(lite_id=good_id, line_number=1, licence_reference=licence.reference).count(), 1
        )

    @tag("edifact")
    def test_single_siel(self):
        licences = LicencePayload.objects.filter(is_processed=False)

        result = licences_to_edifact(licences)
        now = datetime.now()
        expected = (
            "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\"
            + "{:04d}{:02d}{:02d}{:02d}{:02d}".format(now.year, now.month, now.day, now.hour, now.minute)
            + "\\1234"
            + "\n2\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\20200602\\20220602"
            + "\n3\\trader\\0192301\\123791\\20200602\\20220602\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580"
            + "\n4\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB"
            + "\n5\\restrictions\\Provisos may apply please see licence"
            + "\n6\\line\\1\\\\\\\\\\finally\\Q\\30\\10"
            + "\n7\\end\\licence\\6"
            + "\n8\\fileTrailer\\1"
        )

        self.assertEqual(result, expected)

    @tag("sending")
    @mock.patch("mail.tasks.send_email")
    def test_licence_is_marked_as_processed_after_sending(self, send_email):
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()

        self.assertEqual(Mail.objects.count(), 1)
        self.single_siel_licence_payload.refresh_from_db()
        self.assertEqual(self.single_siel_licence_payload.is_processed, True)

    @tag("e2e-mocked")
    @mock.patch("mail.tasks.send_email")
    def test_send_email_to_hmrc_e2e_mocked(self, send_email):
        send_email.return_value = SmtpMock()
        self.single_siel_licence_payload.is_processed = True
        data = self._build_data()

        self.client.post(reverse("mail:update_licence"), data=data, content_type="application/json")

        email_lite_licence_updates.now()  # Manually calling background task logic

        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 2)

    @tag("e2e-non-mocked")
    def test_send_email_to_hmrc_e2e_non_mocked(self):
        data = self._build_data()

        self.client.post(reverse("mail:update_licence"), data=data, content_type="application/json")

        email_lite_licence_updates.now()

        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 2)

    def _build_data(self):
        return {
            "licence": {
                "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
                "reference": "GBSIEL/2020/0000001/P",
                "type": "siel",
                "status": "Submitted",
                "start_date": "2020-06-02",
                "end_date": "2022-06-02",
                "organisation": {
                    "name": "Organisation",
                    "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
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
