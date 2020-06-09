from unittest import mock

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.enums import ReceptionStatusEnum
from mail.models import LicencePayload, Mail
from mail.tasks import email_licences
from mail.tests.test_licence_to_edifact import SmtpMock


class TastTests(LiteHMRCTestClient):
    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_pending(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.PENDING)
        mail.save()
        send_email.return_value = SmtpMock()
        email_licences.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_pending(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_PENDING)
        mail.save()
        send_email.return_value = SmtpMock()
        email_licences.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_received(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_RECEIVED)
        mail.save()
        send_email.return_value = SmtpMock()
        email_licences.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_sent_rejected(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_SENT, response_data="rejected")
        mail.save()
        send_email.return_value = SmtpMock()
        email_licences.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 0)

    @tag("missed-timing")
    @mock.patch("mail.tasks.send_email")
    def test_reply_sent_accepted(self, send_email):
        mail = Mail(status=ReceptionStatusEnum.REPLY_SENT, response_data="accepted")
        mail.save()
        send_email.return_value = SmtpMock()
        email_licences.now()
        self.assertEqual(LicencePayload.objects.filter(is_processed=True).count(), 1)
