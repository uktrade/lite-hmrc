import logging

from django.core.management import BaseCommand
from lark.exceptions import LarkError

from edifact.parsers import usage_data_parser
from edifact.visitors import Edifact, JsonPayload, SourceSplitter
from mail.enums import SourceEnum
from mail.models import UsageData

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Validating usage data parser…")
        self.stdout.write("Checking all previous data against new parser…")

        count = UsageData.objects.count()
        passed = 0
        for usage_data in UsageData.objects.all():
            edi_data = usage_data.mail.edi_data
            try:
                tree = usage_data_parser.parse(edi_data)
            except LarkError:
                logger.warning("Failed to parse %s", usage_data, exc_info=True)
                self.stdout.write(self.style.ERROR(f"Failed to parse {usage_data}"))
                continue

            try:
                transformed_edi_data = Edifact().transform(tree)
            except LarkError:
                logger.warning("Failed to transform tree into edifact %s", usage_data, exc_info=True)
                self.stdout.write(self.style.ERROR(f"Failed to transform tree for {usage_data}"))
                continue

            if edi_data != transformed_edi_data:
                logger.warning("Original edi data does not equal the transformed edi data for %s", usage_data)
                self.stdout.write(
                    self.style.ERROR(f"Original edi data does not equal the transformed edi data for {usage_data}")
                )
                continue

            try:
                lite_only_data = SourceSplitter(SourceEnum.LITE).transform(tree)
                transformed_json_data = JsonPayload().transform(lite_only_data)
            except LarkError:
                logger.warning("Failed to transform tree into JSON %s", usage_data, exc_info=True)
                self.stdout.write(self.style.ERROR(f"Failed to transform tree for {usage_data}"))
                continue

            transformed_json_data["usage_data_id"] = str(usage_data.pk)
            if transformed_json_data != usage_data.lite_payload:
                logger.warning("Original JSON does not equal transformed JSON for %s", usage_data)
                self.stdout.write(self.style.ERROR(f"Original JSON does not equal transformed JSON for {usage_data}"))
                continue

            passed += 1

            self.stdout.write(self.style.SUCCESS(f"Everything was parsed fine for {usage_data}"))

        self.stdout.write(self.style.SUCCESS("Finished validating"))
        self.stdout.write(self.style.SUCCESS(f"{passed} out of {count} passed"))
        self.stdout.write(self.style.ERROR(f"{count - passed} out of {count} failed"))
