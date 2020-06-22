from django.apps import AppConfig
from django.db.models.signals import post_migrate

from conf.settings import INBOX_POLL_INTERVAL, LITE_LICENCE_UPDATE_POLL_INTERVAL, BACKGROUND_TASK_ENABLED


class MailConfig(AppConfig):
    name = "mail"

    @classmethod
    def initialize_background_tasks(cls, **kwargs):
        from background_task.models import Task
        from mail.tasks import send_lite_licence_updates_to_hmrc, manage_inbox_queue
        from mail.models import UsageUpdate
        from mail.tasks import send_licence_usage_figures_to_lite_api

        Task.objects.filter(queue="mail.tasks.manage_inbox_queue").delete()
        Task.objects.filter(queue="mail.tasks.send_lite_licence_updates_to_hmrc").delete()

        if BACKGROUND_TASK_ENABLED:
            manage_inbox_queue(repeat=INBOX_POLL_INTERVAL, repeat_until=None)  # noqa
            send_lite_licence_updates_to_hmrc(repeat=LITE_LICENCE_UPDATE_POLL_INTERVAL, repeat_until=None)  # noqa

            usage_update_not_sent_to_lite = UsageUpdate.objects.filter(
                lite_payload__isnull=False, lite_sent_at__isnull=True
            )
            for usage_update_not_sent_to_lite in usage_update_not_sent_to_lite:
                send_licence_usage_figures_to_lite_api(str(usage_update_not_sent_to_lite.id))

    def ready(self):
        post_migrate.connect(self.initialize_background_tasks, sender=self)
