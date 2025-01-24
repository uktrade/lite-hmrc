from unittest.mock import Mock

from django.test import SimpleTestCase, override_settings

from mail_servers.auth import Authenticator
from mail_servers.utils import get_mail_server

FakeAuth = Mock(spec=Authenticator)


class GetMailServerTests(SimpleTestCase):
    @override_settings(
        MAIL_SERVERS={
            "config": {
                "HOSTNAME": "hostname",
                "POP3_PORT": 12345,
                "AUTHENTICATION_CLASS": "mail_servers.tests.test_utils.FakeAuth",
                "AUTHENTICATION_OPTIONS": {
                    "first_arg": "something",
                    "second_arg": "something_else",
                },
            },
        }
    )
    def test_get_mail_server(self):
        mail_server = get_mail_server("config")
        mail_server.hostname = "hostname"
        mail_server.pop3_port = 12345
        FakeAuth.assert_called_with(first_arg="something", second_arg="something_else")
        self.assertEqual(mail_server.auth, FakeAuth(first_arg="something", second_arg="something_else"))
