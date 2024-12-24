from django.test import TestCase, override_settings
from parameterized import parameterized

from mail_servers.utils import get_mail_server


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
)
class IntegrationTests(TestCase):
    @parameterized.expand(
        [
            "spire_to_dit",
            "hmrc_to_dit",
        ]
    )
    def test_mail_server(self, mail_server_key):
        mail_server = get_mail_server(mail_server_key)
        with mail_server.connect_to_pop3() as pop3_connection:
            self.assertEqual(
                pop3_connection.welcome.decode("ascii"),
                "+OK Mailpit POP3 server",
            )
