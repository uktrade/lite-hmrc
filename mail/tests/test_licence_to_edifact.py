from datetime import datetime
from unittest import mock

from django.test import tag

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
