import datetime
from email.header import Header
from email.message import Message
from poplib import error_proto
from unittest.mock import MagicMock, patch

from dateutil.tz import tzlocal
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from parameterized import parameterized

from mail.libraries.email_message_dto import EmailMessageDto
from mail_servers.servers import MailServer
from mailboxes.enums import MailReadStatuses
from mailboxes.models import MailboxConfig
from mailboxes.tests.factories import MailboxConfigFactory, MailReadStatusFactory
from mailboxes.utils import (
    MailboxMessage,
    MarkStatus,
    get_message_header,
    get_message_id,
    get_unread_messages_iterator,
    get_message_number,
    get_read_messages,
    is_from_valid_sender,
)


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


class GetReadMessagesTests(TestCase):
    def test_get_read_messages(self):
        a_mailbox = MailboxConfigFactory()
        MailReadStatusFactory(
            mailbox=a_mailbox,
            status=MailReadStatuses.READ,
            message_id="a-read",
        )
        MailReadStatusFactory(
            mailbox=a_mailbox,
            status=MailReadStatuses.UNREAD,
            message_id="a-unread",
        )
        MailReadStatusFactory(
            mailbox=a_mailbox,
            status=MailReadStatuses.UNPROCESSABLE,
            message_id="a-unprocessable",
        )
        self.assertEqual(
            get_read_messages(a_mailbox),
            {"a-read", "a-unprocessable"},
        )

        b_mailbox = MailboxConfigFactory()
        MailReadStatusFactory(
            mailbox=b_mailbox,
            status=MailReadStatuses.READ,
            message_id="b-read",
        )
        MailReadStatusFactory(
            mailbox=b_mailbox,
            status=MailReadStatuses.UNREAD,
            message_id="b-unread",
        )
        MailReadStatusFactory(
            mailbox=b_mailbox,
            status=MailReadStatuses.UNPROCESSABLE,
            message_id="b-unprocessable",
        )
        self.assertEqual(
            get_read_messages(b_mailbox),
            {"b-read", "b-unprocessable"},
        )


class IsFromValidSenderTests(TestCase):
    @parameterized.expand(
        [
            "From: valid@example.com",  # /PS-IGNORE
            "valid@example.com",  # /PS-IGNORE
        ]
    )
    def test_is_from_valid_sender(self, valid_address):
        message = Message()
        from_header = Header(f"Sender <{valid_address.replace('From: ', '')}>")  # /PS-IGNORE
        message["From"] = from_header

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()

        mailbox_config = MailboxConfigFactory()

        message = MailboxMessage(
            pop3_connection,
            mailbox_config,
            "1",
        )
        self.assertTrue(is_from_valid_sender(message, [valid_address]))

    @parameterized.expand(
        [
            "From: valid@example.com",  # /PS-IGNORE
            "valid@example.com",  # /PS-IGNORE
        ]
    )
    def test_is_from_invalid_sender(self, valid_address):
        message = Message()
        from_header = Header("Invalid <not.valid@example.com>")  # /PS-IGNORE
        message["From"] = from_header

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()

        mailbox_config = MailboxConfigFactory()

        message = MailboxMessage(
            pop3_connection,
            mailbox_config,
            "1",
        )

        self.assertFalse(is_from_valid_sender(message, [valid_address]))


class MarkStatusTests(TestCase):
    def test_mark_status_read_status(self):
        mailbox_config = MailboxConfigFactory()

        message = Message()
        message["Message-Id"] = Header("<12345@example.com>")  # /PS-IGNORE

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()

        mailbox_message = MailboxMessage(
            pop3_connection,
            mailbox_config,
            "1",
        )

        mail_read_status = mailbox_config.mail_read_statuses.create(
            message_num="1",
            message_id="12345",
            status=MailReadStatuses.UNREAD,
        )

        mark_status = MarkStatus(mailbox_message, mail_read_status)
        mark_status(MailReadStatuses.READ)
        mail_read_status.refresh_from_db()
        self.assertEqual(
            mail_read_status.status,
            MailReadStatuses.READ,
        )


class MailboxMessageTests(TestCase):
    def test_message_header(self):
        msg = Message()
        header = Header("value")
        msg["header"] = header

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()
        mailbox_config = MailboxConfigFactory()
        message_number = "1"

        mailbox_message = MailboxMessage(pop3_connection, mailbox_config, message_number)
        pop3_connection.top.assert_not_called()

        self.assertIsInstance(mailbox_message.message_header, Message)
        self.assertEqual(mailbox_message.message_header["header"], "value")
        pop3_connection.top.assert_called_once_with(message_number, 0)

        msg = Message()
        header = Header("a different value")
        msg["header"] = header

        pop3_connection.top.return_value = MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        self.assertIsInstance(mailbox_message.message_header, Message)
        self.assertEqual(mailbox_message.message_header["header"], "value")
        pop3_connection.top.assert_called_once_with(message_number, 0)

    def test_message_id(self):
        mailbox_config = MailboxConfigFactory()

        message = Message()
        message["Message-Id"] = Header("<12345@example.com>")  # /PS-IGNORE

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()

        mailbox_message = MailboxMessage(
            pop3_connection,
            mailbox_config,
            "1",
        )
        self.assertEqual(
            mailbox_message.message_id,
            "12345",
        )
        pop3_connection.top.assert_called_once_with("1", 0)

        message = Message()
        message["Message-Id"] = Header("<67890@example.com>")  # /PS-IGNORE

        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()
        self.assertEqual(
            mailbox_message.message_id,
            "12345",
        )
        pop3_connection.top.assert_called_once_with("1", 0)

    def test_mail_data(self):
        mailbox_config = MailboxConfigFactory()

        message = Message()
        message["Message-Id"] = Header("<12345@example.com>")  # /PS-IGNORE

        pop3_connection = MagicMock()
        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()
        mail_data = MagicMock()
        pop3_connection.retr.return_value = mail_data

        mailbox_message = MailboxMessage(
            pop3_connection,
            mailbox_config,
            "1",
        )
        self.assertEqual(
            mailbox_message.mail_data,
            mail_data,
        )
        pop3_connection.retr.assert_called_with("1")

        message = Message()
        message["Message-Id"] = Header("<67890@example.com>")  # /PS-IGNORE

        pop3_connection.top.return_value = MagicMock(), message.as_bytes().split(b"\n"), MagicMock()
        different_mail_data = MagicMock()
        pop3_connection.retr.return_value = different_mail_data

        self.assertEqual(
            mailbox_message.mail_data,
            mail_data,
        )
        pop3_connection.retr.assert_called_with("1")


@override_settings(
    SPIRE_FROM_ADDRESS="from.spire@example.com",  # /PS-IGNORE
)
class GetMessageIteratorTests(TestCase):
    def test_get_unread_messages_iterator(self):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [
                b"1 11111",
                b"2 22222",
                b"3 33333",
            ],
            MagicMock(),
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        def _retr(which):
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return b"+OK", msg.as_bytes().split(b"\n"), len(msg.as_bytes())

        mock_pop3_connection.retr.side_effect = _retr

        iterator = get_unread_messages_iterator(mail_server)
        dtos, funcs = zip(*iterator)

        self.assertEqual(
            list(dtos),
            [
                EmailMessageDto(
                    run_number=1,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_1_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-1@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_1_datetime', b'', b''], 148)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=2,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_2_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-2@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_2_datetime', b'', b''], 148)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=3,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_3_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-3@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_3_datetime', b'', b''], 148)",  # /PS-IGNORE
                ),
            ],
        )

        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [
                "<MailReadStatus: message_id=message-id-1 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-2 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-3 status=UNREAD>",
            ],
            transform=repr,
        )

        funcs[1](MailReadStatuses.READ)
        funcs[2](MailReadStatuses.UNPROCESSABLE)
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [
                "<MailReadStatus: message_id=message-id-1 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-2 status=READ>",
                "<MailReadStatus: message_id=message-id-3 status=UNPROCESSABLE>",
            ],
            transform=repr,
        )
        self.assertEqual(
            bytes(mailbox.mail_read_statuses.all()[0].mail_data),
            b"Message-Id: <message-id-1@example.com>\nTo: to@example.com\nFrom: from.spire@example.com\nDate: 2021-04-23T12:38Z\nSubject: abc_xyz_nnn_yyy_1_datetime\n\n",  # /PS-IGNORE
        )
        self.assertEqual(
            bytes(mailbox.mail_read_statuses.all()[1].mail_data),
            b"Message-Id: <message-id-2@example.com>\nTo: to@example.com\nFrom: from.spire@example.com\nDate: 2021-04-23T12:38Z\nSubject: abc_xyz_nnn_yyy_2_datetime\n\n",  # /PS-IGNORE
        )
        self.assertEqual(
            bytes(mailbox.mail_read_statuses.all()[2].mail_data),
            b"Message-Id: <message-id-3@example.com>\nTo: to@example.com\nFrom: from.spire@example.com\nDate: 2021-04-23T12:38Z\nSubject: abc_xyz_nnn_yyy_3_datetime\n\n",  # /PS-IGNORE
        )

    def test_get_unread_messages_iterator_run_multiple_times(self):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [
                b"1 11111",
                b"2 22222",
                b"3 33333",
            ],
            MagicMock(),
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            msg["ChangingValue"] = Header("first-run")
            return MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        def _retr(which):
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            msg["ChangingValue"] = Header("first-run")
            return b"+OK", msg.as_bytes().split(b"\n"), len(msg.as_bytes())

        mock_pop3_connection.retr.side_effect = _retr

        iterator = get_unread_messages_iterator(mail_server)
        dtos, _ = zip(*iterator)

        self.assertEqual(
            list(dtos),
            [
                EmailMessageDto(
                    run_number=1,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_1_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-1@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_1_datetime', b'ChangingValue: first-run', b'', b''], 173)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=2,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_2_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-2@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_2_datetime', b'ChangingValue: first-run', b'', b''], 173)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=3,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_3_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-3@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_3_datetime', b'ChangingValue: first-run', b'', b''], 173)",  # /PS-IGNORE
                ),
            ],
        )
        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [
                "<MailReadStatus: message_id=message-id-1 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-2 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-3 status=UNREAD>",
            ],
            transform=repr,
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            msg["ChangingValue"] = Header("second-run")
            return MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        def _retr(which):
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            msg["ChangingValue"] = Header("second-run")
            return b"+OK", msg.as_bytes().split(b"\n"), len(msg.as_bytes())

        mock_pop3_connection.retr.side_effect = _retr

        iterator = get_unread_messages_iterator(mail_server)
        dtos, _ = zip(*iterator)

        self.assertEqual(
            list(dtos),
            [
                EmailMessageDto(
                    run_number=1,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_1_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-1@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_1_datetime', b'ChangingValue: second-run', b'', b''], 174)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=2,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_2_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-2@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_2_datetime', b'ChangingValue: second-run', b'', b''], 174)",  # /PS-IGNORE
                ),
                EmailMessageDto(
                    run_number=3,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_3_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-3@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_3_datetime', b'ChangingValue: second-run', b'', b''], 174)",  # /PS-IGNORE
                ),
            ],
        )
        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [
                "<MailReadStatus: message_id=message-id-1 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-2 status=UNREAD>",
                "<MailReadStatus: message_id=message-id-3 status=UNREAD>",
            ],
            transform=repr,
        )

    def test_get_unread_messages_iterator_invalid_senders(self):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [
                b"1 11111",
                b"2 22222",
                b"3 33333",
            ],
            MagicMock(),
        )

        lookup_from = {
            "1": "invalid@example.com",  # /PS-IGNORE
            "2": settings.SPIRE_FROM_ADDRESS,
            "3": "invalid@example.com",  # /PS-IGNORE
        }

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(lookup_from[which])
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        def _retr(which):
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(lookup_from[which])
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return b"+OK", msg.as_bytes().split(b"\n"), len(msg.as_bytes())

        mock_pop3_connection.retr.side_effect = _retr

        iterator = get_unread_messages_iterator(mail_server)
        dtos, _ = zip(*iterator)

        self.assertEqual(
            list(dtos),
            [
                EmailMessageDto(
                    run_number=2,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_2_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-2@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_2_datetime', b'', b''], 148)",  # /PS-IGNORE
                ),
            ],
        )

        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [
                "<MailReadStatus: message_id=message-id-2 status=UNREAD>",
            ],
            transform=repr,
        )

    def test_get_unread_messages_iterator_already_read(self):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mailbox_config = MailboxConfigFactory(username="test@example.com")  # /PS-IGNORE
        mailbox_config.mail_read_statuses.create(
            message_num=1,
            message_id="message-id-1",
            status=MailReadStatuses.READ,
        )
        mailbox_config.mail_read_statuses.create(
            message_num=3,
            message_id="message-id-3",
            status=MailReadStatuses.UNPROCESSABLE,
        )

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [
                b"1 11111",
                b"2 22222",
                b"3 33333",
            ],
            MagicMock(),
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return MagicMock(), msg.as_bytes().split(b"\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        def _retr(which):
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return b"+OK", msg.as_bytes().split(b"\n"), len(msg.as_bytes())

        mock_pop3_connection.retr.side_effect = _retr

        iterator = get_unread_messages_iterator(mail_server)
        dtos, _ = zip(*iterator)

        self.assertEqual(
            list(dtos),
            [
                EmailMessageDto(
                    run_number=2,
                    sender=settings.SPIRE_FROM_ADDRESS,
                    receiver="to@example.com",  # /PS-IGNORE
                    date=datetime.datetime(2021, 4, 23, 12, 38, tzinfo=tzlocal()),
                    subject="abc_xyz_nnn_yyy_2_datetime",
                    body=b"",
                    attachment=[None, None],
                    raw_data=f"(b'+OK', [b'Message-Id: <message-id-2@example.com>', b'To: to@example.com', b'From: {settings.SPIRE_FROM_ADDRESS}', b'Date: 2021-04-23T12:38Z', b'Subject: abc_xyz_nnn_yyy_2_datetime', b'', b''], 148)",  # /PS-IGNORE
                ),
            ],
        )

    def test_get_unread_messages_iterator_retr_failure(self):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [b"1 11111"],
            MagicMock(),
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return MagicMock(), msg.as_bytes().split(b"\n\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        mock_pop3_connection.retr.side_effect = error_proto()

        iterator = get_unread_messages_iterator(mail_server)
        self.assertEqual(list(iterator), [])

        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            [],
            transform=repr,
        )

    @patch("mailboxes.utils.to_mail_message_dto")
    def test_get_unread_messages_iterator_message_dto_failure(self, mock_to_mail_message_dto):
        self.assertEqual(MailboxConfig.objects.count(), 0)

        mail_server = MagicMock(spec=MailServer)
        type(mail_server).user = "test@example.com"  # /PS-IGNORE

        mock_pop3_connection = mail_server.connect_to_pop3().__enter__()
        mock_pop3_connection.list.return_value = (
            MagicMock(),
            [b"1 11111"],
            MagicMock(),
        )

        def _top(which, howmuch):
            self.assertEqual(howmuch, 0)
            msg = Message()
            msg["Message-Id"] = Header(f"<message-id-{which}@example.com>")  # /PS-IGNORE
            msg["To"] = Header("to@example.com")  # /PS-IGNORE
            msg["From"] = Header(settings.SPIRE_FROM_ADDRESS)
            msg["Date"] = Header("2021-04-23T12:38Z")
            msg["Subject"] = Header(f"abc_xyz_nnn_yyy_{which}_datetime")
            return MagicMock(), msg.as_bytes().split(b"\n\n"), MagicMock()

        mock_pop3_connection.top.side_effect = _top

        mock_pop3_connection.retr.return_value = MagicMock(), [b"UNCONVERTABLE"], MagicMock()

        mock_to_mail_message_dto.side_effect = ValueError()

        iterator = get_unread_messages_iterator(mail_server)
        self.assertEqual(list(iterator), [])

        mailbox = MailboxConfig.objects.get(username="test@example.com")  # /PS-IGNORE
        self.assertQuerySetEqual(
            mailbox.mail_read_statuses.order_by("message_id"),
            ["<MailReadStatus: message_id=message-id-1 status=UNPROCESSABLE>"],  # /PS-IGNORE
            transform=repr,
        )
