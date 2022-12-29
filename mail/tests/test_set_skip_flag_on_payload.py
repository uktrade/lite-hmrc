import uuid

from django.core.management import call_command
from django.test import TestCase
from parameterized import parameterized

from mail.enums import LicenceActionEnum
from mail.models import LicencePayload


class SetSkipFlagOnPayloadTests(TestCase):
    def get_payload(self, **values):
        return LicencePayload.objects.create(
            lite_id=uuid.uuid4(),
            reference="AB/1278479/24568",
            action=LicenceActionEnum.INSERT,
            is_processed=False,
            **values,
        )

    @parameterized.expand(
        [
            ("True", "False", True),
            ("False", "False", False),
            ("False", "True", False),
            ("True", "True", False),
        ]
    )
    def test_default_skip_process(self, skip_process, dry_run, expected):

        payload = self.get_payload()
        call_command(
            "set_skip_flag_on_payload",
            "--reference",
            payload.reference,
            "--skip_process",
            skip_process,
            "--dry_run",
            dry_run,
        )
        payload.refresh_from_db()
        self.assertEqual(payload.skip_process, expected)
