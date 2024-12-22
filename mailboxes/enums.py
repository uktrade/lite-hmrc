from django.db.models import TextChoices


class MailReadStatuses(TextChoices):
    READ = "READ"
    UNREAD = "UNREAD"
    UNPROCESSABLE = "UNPROCESSABLE"
