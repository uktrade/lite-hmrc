from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MailConfig(AppConfig):
    name = "mail"

    @staticmethod
    def initialize_background_tasks(**kwargs):
        from background_task.models import Task
        from mail.tasks import email_licences

        if not Task.objects.filter(task_name="mail.tasks.email_licences").exists():
            email_licences(repeat=Task.HOURLY // 3, repeat_until=None)  # noqa

    def ready(self):
        post_migrate.connect(self.initialize_background_tasks, sender=self)
