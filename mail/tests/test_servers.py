from poplib import POP3_SSL
from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase, override_settings

from mail.auth import Authenticator
from mail.servers import MailServer, smtp_send


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


@override_settings(
    EMAIL_HOSTNAME="test.hostname",
    EMAIL_SMTP_PORT=1234,
    EMAIL_USER="test.user",
    EMAIL_PASSWORD="test_password",
)
@patch("mail.servers.smtplib.SMTP", autospec=True)
class SmtpSendTests(SimpleTestCase):
    def test_smtp_send(self, mock_SMTP):
        mock_result = MagicMock()
        mock_message = MagicMock()
        mock_conn = MagicMock()
        mock_SMTP().__enter__.return_value = mock_conn
        mock_conn.send_message.return_value = mock_result

        result = smtp_send(mock_message)

        mock_SMTP.assert_called_with(
            "test.hostname",
            "1234",
            timeout=60,
        )
        mock_conn.starttls.assert_called()
        mock_conn.login.assert_called_with(
            "test.user",
            "test_password",
        )
        mock_conn.send_message.assert_called_with(mock_message)
        self.assertEqual(result, mock_result)

    def test_smtp_send_handles_exception_from_send_message(self, mock_SMTP):
        mock_message = MagicMock()
        mock_conn = MagicMock()
        mock_SMTP().__enter__.return_value = mock_conn
        send_message_exception = Exception()
        mock_conn.send_message.side_effect = send_message_exception

        with self.assertRaises(Exception) as exc_info:
            smtp_send(mock_message)

        self.assertEqual(
            exc_info.exception,
            send_message_exception,
        )
        mock_SMTP.assert_called_with(
            "test.hostname",
            "1234",
            timeout=60,
        )
        mock_conn.starttls.assert_called()
        mock_conn.login.assert_called_with(
            "test.user",
            "test_password",
        )
        mock_conn.send_message.assert_called_with(mock_message)

    def test_smtp_send_handles_exception_from_starttls(self, mock_SMTP):
        mock_message = MagicMock()
        mock_conn = MagicMock()
        mock_SMTP().__enter__.return_value = mock_conn
        login_exception = Exception()
        mock_conn.starttls.side_effect = login_exception

        with self.assertRaises(Exception) as exc_info:
            smtp_send(mock_message)

        self.assertEqual(
            exc_info.exception,
            login_exception,
        )
        mock_SMTP.assert_called_with(
            "test.hostname",
            "1234",
            timeout=60,
        )
        mock_conn.starttls.assert_called()

    def test_smtp_send_handles_exception_from_login(self, mock_SMTP):
        mock_message = MagicMock()
        mock_conn = MagicMock()
        mock_SMTP().__enter__.return_value = mock_conn
        login_exception = Exception()
        mock_conn.login.side_effect = login_exception

        with self.assertRaises(Exception) as exc_info:
            smtp_send(mock_message)

        self.assertEqual(
            exc_info.exception,
            login_exception,
        )
        mock_SMTP.assert_called_with(
            "test.hostname",
            "1234",
            timeout=60,
        )
        mock_conn.starttls.assert_called()
        mock_conn.login.assert_called()
