from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


class MailConfig(AppConfig):
    name = "mail"

    @classmethod
    def initialize_background_tasks(cls, **kwargs):
        from background_task.models import Task

        from mail.enums import ChiefSystemEnum
        from mail.models import UsageData
        from mail.tasks import (
            LICENCE_DATA_TASK_QUEUE,
            MANAGE_INBOX_TASK_QUEUE,
            manage_inbox,
        )
        from mail.celery_tasks import send_licence_usage_figures_to_lite_api

        Task.objects.filter(queue=MANAGE_INBOX_TASK_QUEUE).delete()
        Task.objects.filter(queue=LICENCE_DATA_TASK_QUEUE).delete()

        if settings.BACKGROUND_TASK_ENABLED:
            # LITE/SPIRE Tasks
            if settings.CHIEF_SOURCE_SYSTEM == ChiefSystemEnum.SPIRE:
                manage_inbox(repeat=settings.INBOX_POLL_INTERVAL, repeat_until=None)  # noqa

                usage_updates_not_sent_to_lite = UsageData.objects.filter(has_lite_data=True, lite_sent_at__isnull=True)
                for obj in usage_updates_not_sent_to_lite:
                    send_licence_usage_figures_to_lite_api.delay(str(obj.id))

    def ready(self):
        post_migrate.connect(self.initialize_background_tasks, sender=self)
