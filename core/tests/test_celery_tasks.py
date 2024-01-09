from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core import celery_tasks
from mail.enums import ReplyStatusEnum
from mail.models import Mail


class CeleryMailTest(APITestCase):
    def test_debug_add(self):
        res = celery_tasks.debug_add(1, 2)
        assert res == 3

    def test_debug_exception(self):
        self.assertRaises(Exception, celery_tasks.debug_exception)

    def test_debug_count_mail(self):
        sent_at = timezone.now() - timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME)
        Mail.objects.create(
            edi_filename="filename",
            edi_data="1\\fileHeader\\CHIEF\\SPIRE\\",
            status=ReplyStatusEnum.PENDING,
            sent_at=sent_at,
        )
        res = celery_tasks.debug_count_mail()
        assert res == 1
