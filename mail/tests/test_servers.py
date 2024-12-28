from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from mail.servers import smtp_send


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
        mock_conn = mock_SMTP()
        mock_conn.send_message.return_value = mock_result

        result = smtp_send(mock_message)

        mock_SMTP.assert_called_with(
            "test.hostname",
            "1234",
            timeout=60,
        )
        mock_conn = mock_SMTP()
        mock_conn.starttls.assert_called()
        mock_conn.login.assert_called_with(
            "test.user",
            "test_password",
        )
        mock_conn.send_message.assert_called_with(mock_message)
        mock_conn.quit.assert_called()
        self.assertEqual(result, mock_result)

    def test_smtp_send_handles_exception_from_send_message(self, mock_SMTP):
        mock_message = MagicMock()
        mock_conn = mock_SMTP()
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
        mock_conn = mock_SMTP()
        mock_conn.starttls.assert_called()
        mock_conn.login.assert_called_with(
            "test.user",
            "test_password",
        )
        mock_conn.send_message.assert_called_with(mock_message)
        mock_conn.quit.assert_called()
