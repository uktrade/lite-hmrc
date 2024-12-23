from email.header import Header
from email.message import Message
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings
from parameterized import parameterized

from mailboxes.utils import get_message_header, get_message_id, get_message_number, is_from_valid_sender


class GetMessageHeaderTests(SimpleTestCase):
    def test_get_message_header(self):
        msg = Message()
        header = Header("value")
        msg["header"] = header

        pop3_connection = MagicMock()
        pop3_connection().top.return_value = MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        returned_header = get_message_header(pop3_connection(), "4")
        pop3_connection().top.assert_called_with("4", 0)
        self.assertIsInstance(returned_header, Message)
        self.assertEqual(returned_header["header"], "value")


class GetMessageIdTests(SimpleTestCase):
    @override_settings(
        SPIRE_FROM_ADDRESS="spire.from.address@example.com",  # /PS-IGNORE
        HMRC_TO_DIT_REPLY_ADDRESS="hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
    )
    def test_get_message_id_not_from_valid_email(self):
        message = Message()
        message_id_header = Header("<123456@example.com>")  # /PS-IGNORE
        message["Message-ID"] = message_id_header

        message_id = get_message_id(message)

        self.assertEqual(message_id, "123456")


class GetMessageNumberTests(SimpleTestCase):
    def test_get_message_number(self):
        self.assertEqual(get_message_number(b"22 12345"), "22")


class IsFromValidSenderTests(SimpleTestCase):
    @parameterized.expand(
        [
            "From: spire.from.address@example.com",  # /PS-IGNORE
            "From: hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
            "spire.from.address@example.com",  # /PS-IGNORE
            "hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
        ]
    )
    def test_is_from_valid_sender(self, valid_address):
        message = Message()
        from_header = Header(f"Sender <{valid_address.replace('From: ', '')}>")  # /PS-IGNORE
        message["From"] = from_header

        self.assertTrue(is_from_valid_sender(message, [valid_address]))

    @parameterized.expand(
        [
            "From: spire.from.address@example.com",  # /PS-IGNORE
            "From: hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
            "spire.from.address@example.com",  # /PS-IGNORE
            "hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
        ]
    )
    def test_is_from_invalid_sender(self, valid_address):
        message = Message()
        from_header = Header("Invalid <not.valid@example.com>")  # /PS-IGNORE
        message["From"] = from_header

        self.assertFalse(is_from_valid_sender(message, [valid_address]))
