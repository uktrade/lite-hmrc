import poplib
import uuid
from datetime import timedelta
from unittest.mock import patch

from background_task.models import Task
from django.conf import settings
from django.test import testcases
from django.urls import reverse
from django.utils import timezone
from parameterized import parameterized
from rest_framework import status

from mail.enums import LicenceActionEnum, ReplyStatusEnum
from mail.models import LicencePayload, Mail
from mail.tasks import LICENCE_DATA_TASK_QUEUE, MANAGE_INBOX_TASK_QUEUE


class TestHealthCheckP1(testcases.TestCase):
    MAILSERVERS_TO_PATCH = [
        "get_hmrc_to_dit_mailserver",
        "get_spire_to_dit_mailserver",
    ]

    def setUp(self):
        super().setUp()

        self.mocked_mailservers = {}
        for mailserver_to_patch in self.MAILSERVERS_TO_PATCH:
            patched_mailserver = patch(f"healthcheck.checks.{mailserver_to_patch}").start()
            self.mocked_mailservers[mailserver_to_patch] = patched_mailserver

        self.url = reverse("healthcheck_p1")

    def tearDown(self) -> None:
        super().tearDown()

        for mailserver_to_patch in self.MAILSERVERS_TO_PATCH:
            self.mocked_mailservers[mailserver_to_patch].stop()

    def test_healthcheck_return_ok(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "OK")
        self.assertEqual(response.context["status"], status.HTTP_200_OK)

    def test_healthcheck_service_unavailable_inbox_task_not_responsive(self):
        run_at = timezone.now() + timedelta(minutes=settings.INBOX_POLL_INTERVAL)
        task, _ = Task.objects.get_or_create(queue=MANAGE_INBOX_TASK_QUEUE)
        task.run_at = run_at
        task.save()
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "Manage inbox queue error")
        self.assertEqual(response.context["status"], status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_healthcheck_service_unavailable_licence_update_task_not_responsive(self):
        run_at = timezone.now() + timedelta(minutes=settings.LITE_LICENCE_DATA_POLL_INTERVAL)
        task, _ = Task.objects.get_or_create(queue=LICENCE_DATA_TASK_QUEUE)
        task.run_at = run_at
        task.save()
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "Licences updates queue error")
        self.assertEqual(response.context["status"], status.HTTP_503_SERVICE_UNAVAILABLE)

    @parameterized.expand(MAILSERVERS_TO_PATCH)
    def test_healthcheck_service_mailbox_authentication_failure(self, mailserver_factory):
        mock_mailserver_factory = self.mocked_mailservers[mailserver_factory]
        mock_mailserver_factory().connect_to_pop3.side_effect = poplib.error_proto("Failed to connect")
        mock_mailserver_factory().hostname = f"{mailserver_factory}.example.com"
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "Mailbox authentication error")
        self.assertEqual(response.context["status"], status.HTTP_503_SERVICE_UNAVAILABLE)


class TestHealthCheckP2(testcases.TestCase):
    def setUp(self):
        super().setUp()

        self.url = reverse("healthcheck_p2")

    def test_healthcheck_return_ok(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "OK")
        self.assertEqual(response.context["status"], status.HTTP_200_OK)

    def test_healthcheck_service_unavailable_pending_mail(self):
        sent_at = timezone.now() - timedelta(seconds=settings.EMAIL_AWAITING_REPLY_TIME)
        Mail.objects.create(
            edi_filename="filename",
            edi_data="1\\fileHeader\\CHIEF\\SPIRE\\",
            status=ReplyStatusEnum.PENDING,
            sent_at=sent_at,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "Pending mail error")
        self.assertEqual(response.context["status"], status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_healthcheck_service_unavailable_pending_payload(self):
        received_at = timezone.now() - timedelta(seconds=settings.LICENSE_POLL_INTERVAL)
        LicencePayload.objects.create(
            lite_id=uuid.uuid4(),
            reference="ABC12345",
            action=LicenceActionEnum.INSERT,
            is_processed=False,
            received_at=received_at,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.context["message"], "Payload objects error")
        self.assertEqual(response.context["status"], status.HTTP_503_SERVICE_UNAVAILABLE)
