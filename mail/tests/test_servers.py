from poplib import POP3_SSL
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from mail.auth import Authenticator
from mail.servers import MailServer


class MailServerTests(SimpleTestCase):
    def test_mail_server_equal(self):
        auth = Mock(spec=Authenticator)

        m1 = MailServer(auth, hostname="host", pop3_port=1)  # nosec
        m2 = MailServer(auth, hostname="host", pop3_port=1)  # nosec

        self.assertEqual(m1, m2)

    def test_mail_server_not_equal(self):
        auth = Mock(spec=Authenticator)

        m1 = MailServer(auth, hostname="host", pop3_port=1)  # nosec
        m2 = MailServer(auth, hostname="host", pop3_port=2)  # nosec

        self.assertNotEqual(m1, m2)

        auth = Mock(spec=Authenticator)

        m1 = MailServer(auth, hostname="host", pop3_port=1)  # nosec
        m2 = Mock()  # nosec

        self.assertNotEqual(m1, m2)

    @patch("mail.servers.poplib")
    def test_mail_server_connect_to_pop3(self, mock_poplib):
        hostname = "host"
        pop3_port = 1

        auth = Mock(spec=Authenticator)
        pop3conn = MagicMock(spec=POP3_SSL)
        mock_poplib.POP3_SSL = pop3conn

        mail_server = MailServer(
            auth,
            hostname=hostname,
            pop3_port=pop3_port,
        )
        with mail_server.connect_to_pop3() as pop3connection:
            pop3connection.list()

        pop3conn.assert_called_with(
            hostname,
            pop3_port,
            timeout=60,
        )
        mock_connection = pop3conn()
        self.assertEqual(pop3connection, mock_connection)
        auth.authenticate.assert_called_with(pop3connection)
        pop3connection.quit.assert_called_once()
        pop3connection.list.assert_called_once()

    @patch("mail.servers.poplib")
    def test_mail_server_connection_exception(self, mock_poplib):
        hostname = "host"
        pop3_port = 1

        auth = Mock(spec=Authenticator)
        pop3conn = MagicMock(spec=POP3_SSL)
        mock_connection = pop3conn()
        pop3conn.side_effect = Exception()
        mock_poplib.POP3_SSL = pop3conn

        mail_server = MailServer(
            auth,
            hostname=hostname,
            pop3_port=pop3_port,
        )
        with self.assertRaises(Exception):
            with mail_server.connect_to_pop3() as pop3connection:
                pop3connection.list()

        pop3conn.assert_called_with(
            hostname,
            pop3_port,
            timeout=60,
        )
        auth.authenticate.assert_not_called()
        mock_connection.quit.assert_not_called()
        mock_connection.list.assert_not_called()

    @patch("mail.servers.poplib")
    def test_mail_server_connection_context_exception(self, mock_poplib):
        hostname = "host"
        pop3_port = 1

        auth = Mock(spec=Authenticator)
        pop3conn = MagicMock(spec=POP3_SSL)
        mock_connection = pop3conn()
        mock_poplib.POP3_SSL = pop3conn

        mail_server = MailServer(
            auth,
            hostname=hostname,
            pop3_port=pop3_port,
        )
        with self.assertRaises(Exception):
            with mail_server.connect_to_pop3() as pop3connection:
                raise Exception()

        pop3conn.assert_called_with(
            hostname,
            pop3_port,
            timeout=60,
        )
        self.assertEqual(pop3connection, mock_connection)
        auth.authenticate.assert_called_with(pop3connection)
        pop3connection.quit.assert_called_once()

    @patch("mail.servers.poplib")
    def test_mail_server_connection_authentication_exception(self, mock_poplib):
        hostname = "host"
        pop3_port = 1

        auth = Mock(spec=Authenticator)
        auth.authenticate.side_effect = Exception()
        pop3conn = MagicMock(spec=POP3_SSL)
        mock_connection = pop3conn()
        mock_poplib.POP3_SSL = pop3conn

        mail_server = MailServer(
            auth,
            hostname=hostname,
            pop3_port=pop3_port,
        )
        with self.assertRaises(Exception):
            with mail_server.connect_to_pop3() as pop3connection:
                pop3connection.list()

        pop3conn.assert_called_with(
            hostname,
            pop3_port,
            timeout=60,
        )
        auth.authenticate.assert_called_with(mock_connection)
        mock_connection.quit.assert_called_once()
        mock_connection.list.assert_not_called()

    def test_mail_server_user(self):
        auth = Mock(spec=Authenticator)
        auth.user = Mock()
        mail_server = MailServer(
            auth,
            hostname="host",
            pop3_port=1,
        )
        self.assertEqual(mail_server.user, auth.user)
