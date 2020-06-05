from datetime import datetime

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.models import LicencePayload
from mail.services.lite_to_edifact_converter import licences_to_edifact
from mail.tasks import email_licences


class LicenceToEdifactTests(LiteHMRCTestClient):
    @tag("edifact")
    def test_single_siel(self):
        LicencePayload.objects.create(
            reference="GBSIEL2020/50001",
            data={
                "licence": {
                    "id": "09e21356-9e9d-418d-bd4d-9792333e8cc8",
                    "reference": "GBSIEL/2020/0000001/P",
                    "type": "siel",
                    "status": "Submitted",
                    "start_date": "2020-06-02",
                    "end_date": "2022-06-02",
                    "organisation": {
                        "name": "Organisation",
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
            },
        )

        licences = LicencePayload.objects.filter(is_processed=False)

        result = licences_to_edifact(licences)
        now = datetime.now()
        expected = (
            "1\\fileHeader\\SPIRE\\CHIEF\\licenceData\\"
            + "{:04d}{:02d}{:02d}{:02d}{:02d}".format(now.year, now.month, now.day, now.hour, now.minute)
            + "\\1234"
            + "\n2\\licence\\34567\\insert\\GBSIEL/2020/0000001/P\\siel\\E\\2020-06-02\\2022-06-02"
            + "\n3\\trader\\0192301\\123791\\2020-06-02\\2022-06-02\\Organisation\\might\\248 James Key Apt. 515\\Apt. 942\\West Ashleyton\\Tennessee\\99580"
            + "\n4\\foreignTrader\\End User\\42 Road, London, Buckinghamshire\\\\\\\\\\\\GB"
            + "\n5\\restrictions\\Provisos may apply please see licence"
            + "\n6\\line\\1\\\\\\\\\\finally\\Q\\30\\10"
            + "\n7\\end\\licence\\6"
            + "\n8\\fileTrailer\\1"
        )

        # DO NOT UNCOMMENT UNLESS MANUALLY TESTING - DO NOT LET CIRCLE CI RUN THIS LINE
        # email_licences.now()

        self.assertEqual(result, expected)
