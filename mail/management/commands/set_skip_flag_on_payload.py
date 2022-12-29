from django.conf import settings
from django.core.management.base import BaseCommand

from mail.libraries.mailbox_service import get_message_id
from mail.models import LicencePayload
from mail.servers import MailServer


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--reference", type=str, nargs="?", help="License Reference number of the license payload")
        parser.add_argument(
            "--skip_process", type=str, nargs="?", help="To skip processing set to true", default="False"
        )
        parser.add_argument("--dry_run", type=str, nargs="?", help="Is it a test run", default="True")

    def handle(self, *args, **options):
        dry_run = options.pop("dry_run")
        reference = options.pop("reference")
        skip_process = options.pop("skip_process")

        payload = LicencePayload.objects.get(reference=reference)
        payload.skip_process = skip_process

        if dry_run.lower() == "false":
            payload.save()
            self.stdout.write(self.style.SUCCESS(f"Reference  {reference} skip_process set to {payload.skip_process}"))
        elif dry_run.lower() == "true":
            self.stdout.write(
                self.style.SUCCESS(f"DRY RUN : Reference  {reference} skip_process set to {payload.skip_process}")
            )
