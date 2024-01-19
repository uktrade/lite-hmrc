from django.conf import settings
from django.core.management import BaseCommand

from mail.celery_tasks import send_licence_details_to_hmrc


class Command(BaseCommand):
    """Development command to trigger sending LITE licence details to HMRC."""

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stdout.write("This command is only for development environments")
            return

        send_licence_details_to_hmrc.delay()
