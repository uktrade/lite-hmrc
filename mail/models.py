import json
import logging
import uuid
from datetime import timedelta
from typing import List

from django.conf import settings
from django.db import IntegrityError, models
from django.utils import timezone
from model_utils.models import TimeStampedModel

from mail.enums import (
    ChiefSystemEnum,
    ExtractTypeEnum,
    LicenceActionEnum,
    MailReadStatuses,
    ReceptionStatusEnum,
    SourceEnum,
)

logger = logging.getLogger(__name__)


class Mail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # For licence_data / licence_reply emails they are saved on a single db record.
    # e.g. the licence_reply email is saved on the licence_data record
    extract_type = models.CharField(choices=ExtractTypeEnum.choices, max_length=20, null=True)

    # Status of mail through the lite-hmrc workflow
    status = models.CharField(choices=ReceptionStatusEnum.choices, default=ReceptionStatusEnum.PENDING, max_length=20)

    # licenceData fields
    edi_filename = models.TextField(null=True, blank=True)
    edi_data = models.TextField(null=True, blank=True)
    sent_filename = models.TextField(blank=True, null=True)
    sent_data = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)

    # licenceReply / Usage fields
    response_filename = models.TextField(blank=True, null=True)
    response_data = models.TextField(blank=True, null=True)
    response_date = models.DateTimeField(blank=True, null=True)
    response_subject = models.TextField(null=True, blank=True)

    sent_response_filename = models.TextField(blank=True, null=True)
    sent_response_data = models.TextField(blank=True, null=True)

    raw_data = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    currently_processing_at = models.DateTimeField(null=True)
    currently_processed_by = models.CharField(null=True, max_length=100)

    retry = models.BooleanField(default=False)

    class Meta:
        db_table = "mail"
        ordering = ["created_at"]

    def __repr__(self):
        return f"id={self.id} status={self.status}"

    def save(self, *args, **kwargs):
        if not self.edi_data or not self.edi_filename:
            logger.error(
                "Setting `edi_data` or `edi_filename` to null or blank: self=%s, edi_data=%s edi_filename=%s",
                self,
                self.edi_data,
                self.edi_filename,
                exc_info=True,
            )
            raise IntegrityError("The field edi_filename or edi_data is empty which is not valid")

        super(Mail, self).save(*args, **kwargs)

    def set_locking_time(self, offset: int = 0):
        self.currently_processing_at = timezone.now() + timedelta(seconds=offset)
        self.save()

    def set_last_submitted_time(self, offset: int = 0):
        self.last_submitted_on = timezone.now() + timedelta(seconds=offset)
        self.save()

    def set_response_date_time(self, offset: int = 0):
        self.response_date = timezone.now() + timedelta(seconds=offset)
        self.save()


class LicenceData(models.Model):
    licence_ids = models.TextField()
    hmrc_run_number = models.IntegerField()
    source_run_number = models.IntegerField(null=True)
    source = models.CharField(choices=SourceEnum.choices, max_length=10)
    mail = models.ForeignKey(Mail, on_delete=models.DO_NOTHING)
    licence_payloads = models.ManyToManyField(
        "LicencePayload", help_text="LicencePayload records linked to this LicenceData instance", related_name="+"
    )

    class Meta:
        ordering = ["mail__created_at"]

    def __repr__(self):
        source = self.source
        if source == SourceEnum.SPIRE:
            source = f"{source} ({self.source_run_number})"

        return f"hmrc_run_number={self.hmrc_run_number} source={source} status={self.mail.status}"

    def set_licence_ids(self, data: List):
        self.licence_ids = json.dumps(data)

    def get_licence_ids(self):
        return json.loads(self.licence_ids)


class UsageData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    licence_ids = models.JSONField(default=list)
    mail = models.ForeignKey(Mail, on_delete=models.DO_NOTHING, null=False)
    spire_run_number = models.IntegerField()
    hmrc_run_number = models.IntegerField()
    has_lite_data = models.BooleanField(null=True)
    has_spire_data = models.BooleanField(null=True)
    lite_payload = models.JSONField(default=dict)
    lite_sent_at = models.DateTimeField(blank=True, null=True)  # When update was sent to LITE API
    lite_accepted_licences = models.JSONField(default=list)
    lite_rejected_licences = models.JSONField(default=list)
    spire_accepted_licences = models.JSONField(default=dict)
    spire_rejected_licences = models.JSONField(default=dict)
    lite_licences = models.JSONField(default=dict)
    spire_licences = models.JSONField(default=dict)
    lite_response = models.JSONField(default=dict)

    class Meta:
        ordering = ["mail__created_at"]

    def get_licence_ids(self):
        return json.loads(self.licence_ids)

    @staticmethod
    def send_usage_updates_to_lite(id):
        from mail.celery_tasks import send_licence_usage_figures_to_lite_api

        send_licence_usage_figures_to_lite_api.delay(str(id))


class LicencePayload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lite_id = models.UUIDField(null=False, blank=False, unique=False)
    reference = models.CharField(null=False, blank=False, max_length=35)
    action = models.CharField(choices=LicenceActionEnum.choices, null=False, blank=False, max_length=7)
    data = models.JSONField(default=dict)
    received_at = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)
    # This allows us to skip License requests to be skipped
    skip_process = models.BooleanField(default=False)

    # For LITE updates only
    old_lite_id = models.UUIDField(null=True, blank=False, unique=False)
    old_reference = models.CharField(null=True, blank=False, max_length=35)

    class Meta:
        unique_together = [["lite_id", "action"]]
        ordering = ["received_at"]

    def save(self, *args, **kwargs):
        super(LicencePayload, self).save(*args, **kwargs)

        # This causes errors for ICMS as reference doesn't need to be unique.
        # reference only needs to be unique within a licenceData file.
        if settings.CHIEF_SOURCE_SYSTEM == ChiefSystemEnum.SPIRE:
            LicenceIdMapping.objects.get_or_create(lite_id=self.lite_id, reference=self.reference)

    def __repr__(self):
        return f"lite_id={self.lite_id} reference={self.reference} action={self.action}"


class LicenceIdMapping(models.Model):
    lite_id = models.UUIDField(primary_key=True, null=False, blank=False)
    reference = models.CharField(null=False, blank=False, max_length=35, unique=True)


class OrganisationIdMapping(models.Model):
    lite_id = models.UUIDField(null=False, blank=False)
    rpa_trader_id = models.AutoField(primary_key=True)


class GoodIdMapping(models.Model):
    lite_id = models.UUIDField(primary_key=False, null=False, blank=False, unique=False)
    licence_reference = models.CharField(null=False, blank=False, max_length=35, unique=False)
    line_number = models.PositiveIntegerField()


class TransactionMapping(models.Model):
    licence_reference = models.CharField(null=False, blank=False, max_length=35, unique=False)
    line_number = models.PositiveIntegerField(null=True, blank=True)
    usage_transaction = models.CharField(null=False, blank=False, max_length=35)
    usage_data = models.ForeignKey(UsageData, on_delete=models.DO_NOTHING)


class MailboxConfig(TimeStampedModel):
    username = models.TextField(null=False, blank=False, primary_key=True, help_text="Username of the POP3 mailbox")


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

    def __repr__(self):
        return f"message_id={self.message_id} status={self.status}"
