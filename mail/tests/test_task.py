from unittest import mock

from django.test import tag

from mail.tests.test_client import LiteHMRCTestClient
from mail.enums import ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from mail.tasks import email_lite_licence_updates


class SmtpMock:
    def quit(self):
        pass


class TastTests(LiteHMRCTestClient):
    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_pending(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.PENDING)
        mail.save()
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_pending(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_PENDING)
        mail.save()
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_received(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_RECEIVED)
        mail.save()
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_sent_rejected(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_SENT, response_data="rejected")
        mail.save()
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_sent_accepted(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_SENT, response_data="accepted")
        mail.save()
        send_email.return_value = SmtpMock()
        email_lite_licence_updates.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 1)
