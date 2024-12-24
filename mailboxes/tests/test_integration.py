from unittest.mock import ANY

import requests
from django.conf import settings
from django.test import TestCase, override_settings

from mail.libraries.email_message_dto import EmailMessageDto
from mail_servers.utils import get_mail_server
from mailboxes.models import MailboxConfig
from mailboxes.utils import get_message_iterator


@override_settings(
    MAIL_SERVERS={
        "spire_to_dit": {
            "HOSTNAME": "spire-to-dit-mailserver",
            "POP3_PORT": 1110,
            "AUTHENTICATION_CLASS": "mail_servers.auth.BasicAuthentication",
            "AUTHENTICATION_OPTIONS": {
                "user": "spire-to-dit-user",
                "password": "password",
            },
        },
        "hmrc_to_dit": {
            "HOSTNAME": "hmrc-to-dit-mailserver",
            "POP3_PORT": 1110,
            "AUTHENTICATION_CLASS": "mail_servers.auth.BasicAuthentication",
            "AUTHENTICATION_OPTIONS": {
                "user": "hmrc-to-dit-user",
                "password": "password",
            },
        },
    },
    SPIRE_FROM_ADDRESS="from.spire@example.com",  # /PS-IGNORE
    HMRC_TO_DIT_REPLY_ADDRESS="from.hmrc@example.com",  # /PS-IGNORE
)
class IntegrationTests(TestCase):
    def setUp(self):
        super().setUp()

        requests.delete("http://spire-to-dit-mailserver:8025/api/v1/messages")
        requests.delete("http://hmrc-to-dit-mailserver:8025/api/v1/messages")

    def test_get_message_iterator_creates_mailbox_config(self):
        self.assertFalse(MailboxConfig.objects.exists())

        mail_server = get_mail_server("spire_to_dit")
        messages = get_message_iterator(mail_server)
        self.assertEqual(list(messages), [])
        self.assertEqual(MailboxConfig.objects.filter(username="spire-to-dit-user").count(), 1)

        mail_server = get_mail_server("hmrc_to_dit")
        messages = get_message_iterator(mail_server)
        self.assertEqual(list(messages), [])
        self.assertEqual(MailboxConfig.objects.filter(username="hmrc-to-dit-user").count(), 1)

    def test_get_message_iterator_creates_read_statuses(self):
        requests.post(
            "http://spire-to-dit-mailserver:8025/api/v1/send",
            json={
                "From": {"Email": settings.SPIRE_FROM_ADDRESS, "Name": "SPIRE"},
                "Subject": "abc_xyz_nnn_yyy_1111_datetime",
                "To": [{"Email": "lite@example.com", "Name": "LITE"}],  # /PS-IGNORE
            },
        )
        mail_server = get_mail_server("spire_to_dit")
        messages, _ = zip(*get_message_iterator(mail_server))
        self.assertEqual(
            list(messages),
            [
                EmailMessageDto(
                    run_number=1111,
                    sender='"SPIRE" <from.spire@example.com>',  # /PS-IGNORE
                    receiver='"LITE" <lite@example.com>',  # /PS-IGNORE
                    date=ANY,
                    subject="abc_xyz_nnn_yyy_1111_datetime",
                    body="",
                    attachment=[None, None],
                    raw_data=ANY,
                )
            ],
        )
        mailbox_config = MailboxConfig.objects.get(username="spire-to-dit-user")
        self.assertEqual(mailbox_config.mail_read_statuses.count(), 1)

        requests.post(
            "http://hmrc-to-dit-mailserver:8025/api/v1/send",
            json={
                "From": {"Email": settings.HMRC_TO_DIT_REPLY_ADDRESS, "Name": "HMRC"},
                "Subject": "abc_xyz_nnn_yyy_2222_datetime",
                "To": [{"Email": "lite@example.com", "Name": "LITE"}],  # /PS-IGNORE
            },
        )
        mail_server = get_mail_server("hmrc_to_dit")
        messages, _ = zip(*get_message_iterator(mail_server))
        self.assertEqual(
            list(messages),
            [
                EmailMessageDto(
                    run_number=2222,
                    sender='"HMRC" <from.hmrc@example.com>',  # /PS-IGNORE
                    receiver='"LITE" <lite@example.com>',  # /PS-IGNORE
                    date=ANY,
                    subject="abc_xyz_nnn_yyy_2222_datetime",
                    body="",
                    attachment=[None, None],
                    raw_data=ANY,
                )
            ],
        )
        mailbox_config = MailboxConfig.objects.get(username="hmrc-to-dit-user")
        self.assertEqual(mailbox_config.mail_read_statuses.count(), 1)
