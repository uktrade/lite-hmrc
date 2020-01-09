import json
import uuid
from typing import List

from django.db import models

from mail.enums import ReceptionStatusEnum, ExtractTypeEnum


class Mail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField()
    last_submitted_on = models.DateTimeField()  # TODO: Investigate what this is
    edi_data = models.TextField()
    status = models.CharField(choices=ReceptionStatusEnum.choices, null=True)
    extract_type = models.CharField(choices=ExtractTypeEnum.choices)
    response_file = models.TextField(null=True)
    response_date = models.DateTimeField(null=True)
    edi_filename = models.TextField()


class LicenseUpdate(Mail):
    license_id = models.UUIDField()
    hmrc_run_number = models.IntegerField()
    spire_run_number = models.IntegerField()


class LicenseUsage(Mail):
    licenses = models.TextField()

    def set_licenses(self, data: List):
        self.licenses = json.dumps(data)

    def get_licenses(self):
        return json.loads(self.licenses)


class RunNumberLedger(models.Model):
    hmrc_run_number = models.IntegerField()
    spire_run_number = models.IntegerField()
