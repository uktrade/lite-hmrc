from email.header import Header
from email.message import Message
from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from mailboxes.utils import get_message_header, get_message_id


class GetMessageHeaderTests(SimpleTestCase):
    def test_get_message_header(self):
        msg = Message()
        header = Header("value")
        msg["header"] = header

        pop3_connection = MagicMock()
        pop3_connection().top.return_value = MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        returned_header, msg_num = get_message_header(pop3_connection(), "4 12345")
        pop3_connection().top.assert_called_with("4", 0)
        self.assertIsInstance(returned_header, Message)
        self.assertEqual(returned_header["header"], "value")
        self.assertEqual(msg_num, "4")


class GetMessageId(SimpleTestCase):
    @override_settings(
        SPIRE_FROM_ADDRESS="spire.from.address@example.com",  # /PS-IGNORE
        HMRC_TO_DIT_REPLY_ADDRESS="hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
    )
    def test_get_message_id_not_from_valid_email(self):
        message = Message()
        from_header = Header("from@example.com")  # /PS-IGNORE
        message["From"] = from_header
        reply_to_header = Header("reply-to@example.com")  # /PS-IGNORE
        message["Reply-To"] = reply_to_header

        message_id, message_number = get_message_id(message, "4")

        self.assertIsNone(message_id)
        self.assertEqual(message_number, "4")

    @override_settings(
        SPIRE_FROM_ADDRESS="spire.from.address@example.com",  # /PS-IGNORE
        HMRC_TO_DIT_REPLY_ADDRESS="hmrc.to.dit.reply.address@example.com",  # /PS-IGNORE
    )
    def test_get_message_id_not_from_valid_email(self):
        message = Message()
        from_header = Header("Spire <spire.from.address@example.com>")  # /PS-IGNORE
        message["From"] = from_header
        reply_to_header = Header("HMRC <hmrc.to.dit.reply.address@example.com>")  # /PS-IGNORE
        message["Reply-To"] = reply_to_header
        message_id_header = Header("<123456@example.com>")  # /PS-IGNORE
        message["Message-ID"] = message_id_header

        message_id, message_number = get_message_id(message, "4")

        self.assertEqual(message_id, "123456")
        self.assertEqual(message_number, "4")
