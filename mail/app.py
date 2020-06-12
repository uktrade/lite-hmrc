from django.apps import AppConfig


class MailConfig(AppConfig):
    name = "mail"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from mail.tasks import email_lite_licence_updates, manage_inbox_queue

        Task.objects.filter(task_name="mail.tasks.email_lite_licence_updates").delete()
        email_lite_licence_updates(repeat=Task.HOURLY // 3, repeat_until=None)  # noqa

        Task.objects.filter(task_name="mail.tasks.manage_inbox_queue").delete()
        # manage_inbox_queue(repeat=Task.HOURLY // 120, repeat_until=None)  # noqa

    def ready(self):
        self.initialize_background_tasks()
