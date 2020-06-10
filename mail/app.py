from django.apps import AppConfig

from mail.scheduling.scheduler import scheduled_job


class MailConfig(AppConfig):
    name = "mail"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from mail.tasks import email_licences

        Task.objects.filter(task_name="mail.tasks.email_licences").delete()
        email_licences(repeat=Task.HOURLY // 3, repeat_until=None)  # noqa

    def ready(self):
        self.initialize_background_tasks()

        scheduled_job()
