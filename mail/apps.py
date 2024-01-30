from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class MailConfig(AppConfig):
    name = "mail"

    @classmethod
    def initialize_send_licence_usage_figures_to_lite_api(cls, **kwargs):
        from mail.celery_tasks import send_licence_usage_figures_to_lite_api
        from mail.models import UsageData

        usage_updates_not_sent_to_lite = UsageData.objects.filter(has_lite_data=True, lite_sent_at__isnull=True)
        for obj in usage_updates_not_sent_to_lite:
            send_licence_usage_figures_to_lite_api.delay(str(obj.id))

    def ready(self):
        post_migrate.connect(self.initialize_send_licence_usage_figures_to_lite_api, sender=self)
