import uuid

from django.db import models
from model_utils.models import TimeStampedModel

from mailboxes.enums import MailReadStatuses


class MailboxConfig(TimeStampedModel):
    username = models.TextField(null=False, blank=False, primary_key=True, help_text="Username of the POP3 mailbox")

    class Meta:
        db_table = (
            "mail_mailboxconfig"  # This was moved from another app and this makes the migrations backwards compatible
        )


class MailReadStatus(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_num = models.TextField(
        default="",
        help_text="Sequence number of the message as assigned by pop3 when the messages list is requested from the mailbox",
    )
    message_id = models.TextField(
        default=uuid.uuid4,
        unique=True,
        help_text="Unique Message-ID of the message that is retrieved from the message header",
    )
    status = models.TextField(choices=MailReadStatuses.choices, default=MailReadStatuses.UNREAD, db_index=True)
    mailbox = models.ForeignKey(MailboxConfig, on_delete=models.CASCADE)

    class Meta:
        db_table = (
            "mail_mailreadstatus"  # This was moved from another app and this makes the migrations backwards compatible
        )

    def __str__(self):
        return f"{self.__class__.__name__}(message_id={self.message_id}, status={self.status})"
