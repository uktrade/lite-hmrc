import json
import uuid
from datetime import timedelta
from typing import List

from django.db import models
from django.db.models import Q
from django.utils import timezone
from jsonfield import JSONField

from mail.enums import ReceptionStatusEnum, ExtractTypeEnum, SourceEnum


class MailManager(models.Manager):
    def invalid(self):
        return self.filter(Q(errors__isnull=False) | Q(serializer_errors__isnull=False))

    def valid(self):
        return self.filter(Q(errors__isnull=True) & Q(serializer_errors__isnull=True))


class Mail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    last_submitted_on = models.DateTimeField(blank=True, null=True)
    edi_filename = models.TextField(null=True, blank=True)
    edi_data = models.TextField(null=True, blank=True)
    status = models.CharField(choices=ReceptionStatusEnum.choices, default=ReceptionStatusEnum.PENDING, max_length=20,)
    extract_type = models.CharField(choices=ExtractTypeEnum.choices, max_length=20, null=True)
    response_filename = models.TextField(blank=True, null=True)
    response_data = models.TextField(blank=True, null=True)
    response_date = models.DateTimeField(blank=True, null=True)
    response_subject = models.TextField(null=True, blank=True)

    raw_data = models.TextField()

    currently_processing_at = models.DateTimeField(null=True)
    currently_processed_by = models.CharField(null=True, max_length=100)

    objects = MailManager()

    class Meta:
        db_table = "mail"
        ordering = ["created_at"]

    def set_locking_time(self, offset: int = 0):
        self.currently_processing_at = timezone.now() + timedelta(seconds=offset)
        self.save()

    def set_last_submitted_time(self, offset: int = 0):
        self.last_submitted_on = timezone.now() + timedelta(seconds=offset)
        self.save()

    def set_response_date_time(self, offset: int = 0):
        self.response_date = timezone.now() + timedelta(seconds=offset)
        self.save()


class LicenceUpdate(models.Model):
    license_ids = models.TextField()
    hmrc_run_number = models.IntegerField()
    source_run_number = models.IntegerField(null=True)
    source = models.CharField(choices=SourceEnum.choices, max_length=10)
    mail = models.ForeignKey(Mail, on_delete=models.DO_NOTHING)

    def set_licence_ids(self, data: List):
        self.license_ids = json.dumps(data)

    def get_licence_ids(self):
        return json.loads(self.license_ids)


class UsageUpdate(models.Model):
    license_ids = models.TextField()
    mail = models.ForeignKey(Mail, on_delete=models.DO_NOTHING)
    spire_run_number = models.IntegerField()
    hmrc_run_number = models.IntegerField()

    def set_licence_ids(self, data: List):
        self.license_ids = json.dumps(data)

    def get_licence_ids(self):
        return json.loads(self.license_ids)


class LicencePayload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Convenience field for cross-referencing LITE services
    lite_id = models.CharField(null=False, blank=False, max_length=36)
    reference = models.CharField(null=False, blank=False, max_length=35)
    data = JSONField()
    received_at = models.DateTimeField(default=timezone.now)
    is_processed = models.BooleanField(default=False)


class OrganisationIdMapping(models.Model):
    lite_id = models.CharField(unique=True, null=False, blank=False, max_length=36)
    rpa_trader_id = models.AutoField(primary_key=True)


class GoodIdMapping(models.Model):
    lite_id = models.CharField(null=False, blank=False, max_length=36)
    licence_reference = models.CharField(null=False, blank=False, max_length=35)
    line_number = models.PositiveIntegerField()

    class Meta:
        unique_together = [["lite_id", "licence_reference"]]
