from django.apps import AppConfig

from conf.settings import INBOX_POLL_INTERVAL, LITE_LICENCE_UPDATE_POLL_INTERVAL


class MailConfig(AppConfig):
    name = "mail"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from mail.tasks import email_lite_licence_updates, manage_inbox_queue

        Task.objects.filter(task_name="mail.tasks.email_lite_licence_updates").delete()
        email_lite_licence_updates(repeat=LITE_LICENCE_UPDATE_POLL_INTERVAL, repeat_until=None)  # noqa

        Task.objects.filter(task_name="mail.tasks.manage_inbox_queue").delete()
        manage_inbox_queue(repeat=INBOX_POLL_INTERVAL, repeat_until=None)  # noqa

    def ready(self):
        # Note: If migrations wont compile if making them from scratch, this will need to be commented out
        self.initialize_background_tasks()
