import unittest
from unittest.mock import patch

from django.test import override_settings

from mail.libraries.routing_controller import (
    get_hmrc_to_dit_mailserver,
    get_mock_hmrc_mailserver,
    get_spire_to_dit_mailserver,
)
from mail_servers.auth import BasicAuthentication, ModernAuthentication


class RoutingControllerTest(unittest.TestCase):
    @patch(
        "mail_servers.auth.ModernAuthentication",
        spec=ModernAuthentication,
    )
    @patch("mail_servers.utils.MailServer")
    @override_settings(
        MAIL_SERVERS={
            "spire_to_dit": {
                "HOSTNAME": "host.example.com",
                "POP3_PORT": 123,
                "AUTHENTICATION_CLASS": "mail_servers.auth.ModernAuthentication",
                "AUTHENTICATION_OPTIONS": {
                    "user": "incoming.email.user@example.com",
                    "client_id": "azure-auth-client-id",
                    "client_secret": "azure-auth-client-secret",
                    "tenant_id": "azure-auth-tenant-id",
                },
            },
        }
    )
    def test_get_spire_to_dit_mailserver(self, mock_MailServer, mock_ModernAuthentication):
        spire_to_dit_mailserver = get_spire_to_dit_mailserver()

        mock_ModernAuthentication.assert_called_with(  # nosec
            user="incoming.email.user@example.com",
            client_id="azure-auth-client-id",
            client_secret="azure-auth-client-secret",
            tenant_id="azure-auth-tenant-id",
        )
        mock_MailServer.assert_called_with(
            mock_ModernAuthentication(),
            hostname="host.example.com",
            pop3_port=123,
        )

        self.assertEqual(spire_to_dit_mailserver, mock_MailServer())

    @patch(
        "mail_servers.auth.ModernAuthentication",
        spec=ModernAuthentication,
    )
    @patch("mail_servers.utils.MailServer")
    @override_settings(
        MAIL_SERVERS={
            "hmrc_to_dit": {
                "HOSTNAME": "host.example.com",
                "POP3_PORT": 123,
                "AUTHENTICATION_CLASS": "mail_servers.auth.ModernAuthentication",
                "AUTHENTICATION_OPTIONS": {
                    "user": "hmrc.to.dit.email.user@example.com",
                    "client_id": "azure-auth-client-id",
                    "client_secret": "azure-auth-client-secret",
                    "tenant_id": "azure-auth-tenant-id",
                },
            },
        }
    )
    def test_get_hmrc_to_dit_mailserver(self, mock_MailServer, mock_ModernAuthentication):
        hmrc_to_dit_mailserver = get_hmrc_to_dit_mailserver()

        mock_ModernAuthentication.assert_called_with(  # nosec
            user="hmrc.to.dit.email.user@example.com",
            client_id="azure-auth-client-id",
            client_secret="azure-auth-client-secret",
            tenant_id="azure-auth-tenant-id",
        )
        mock_MailServer.assert_called_with(
            mock_ModernAuthentication(),
            hostname="host.example.com",
            pop3_port=123,
        )

        self.assertEqual(hmrc_to_dit_mailserver, mock_MailServer())

    @patch(
        "mail_servers.auth.BasicAuthentication",
        spec=BasicAuthentication,
    )
    @patch("mail_servers.utils.MailServer")
    @override_settings(
        MAIL_SERVERS={
            "mock": {
                "HOSTNAME": "host.example.com",
                "POP3_PORT": 123,
                "AUTHENTICATION_CLASS": "mail_servers.auth.BasicAuthentication",
                "AUTHENTICATION_OPTIONS": {
                    "user": "mock.hmrc.email.user@example.com",
                    "password": "shhh",
                },
            },
        }
    )
    def test_get_mock_hmrc_mailserver(self, mock_MailServer, mock_BasicAuthentication):
        mock_hmrc_mailserver = get_mock_hmrc_mailserver()

        mock_BasicAuthentication.assert_called_with(
            user="mock.hmrc.email.user@example.com",
            password="shhh",
        )
        mock_MailServer.assert_called_with(
            mock_BasicAuthentication(),
            hostname="host.example.com",
            pop3_port=123,
        )

        self.assertEqual(mock_hmrc_mailserver, mock_MailServer())
