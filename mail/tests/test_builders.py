from unittest import mock

from django.conf import settings
from django.test import testcases

from mail.libraries import builders
from mail.libraries.email_message_dto import EmailMessageDto


class BuildEmailMessageTest(testcases.TestCase):
    maxDiff = None

    @mock.patch("django.core.mail.message.formatdate")
    @mock.patch("django.core.mail.message.make_msgid")
    def test_build_email_message(self, mock_make_msgid, mock_formatdate):
        attachment = "30 \U0001d5c4\U0001d5c6/\U0001d5c1 \u5317\u4EB0"
        email_message_dto = EmailMessageDto(
            run_number=1,
            sender=settings.HMRC_ADDRESS,
            receiver=settings.SPIRE_ADDRESS,
            date="Mon, 17 May 2021 14:20:18 +0100",
            body=None,
            subject="Some subject",
            attachment=["some filename", attachment],
            raw_data="",
        )

        # Message-Id is normally a random value + MTA hostname.
        mock_make_msgid.return_value = "<xyz@local>"
        mock_formatdate.return_value = "Mon, 17 May 2021 14:20:18 +0100"

        django_email = builders.build_email_message(email_message_dto)
        mime_multipart = django_email.message()
        mime_multipart.set_boundary("===============8537751789001939036==")

        self.assertEqual(
            mime_multipart.as_string(),
            (
                'Content-Type: multipart/mixed; boundary="===============8537751789001939036=="\n'
                "MIME-Version: 1.0\n"
                "Subject: Some subject\n"
                f"From: {settings.EMAIL_USER}\n"
                f"To: {settings.SPIRE_ADDRESS}\n"
                "Date: Mon, 17 May 2021 14:20:18 +0100\n"
                "Message-ID: <xyz@local>\n"
                "\n"
                "--===============8537751789001939036==\n"
                'Content-Type: text/plain; charset="iso-8859-1"\n'
                "MIME-Version: 1.0\n"
                "Content-Transfer-Encoding: quoted-printable\n\n"
                "\n\n\n"
                "--===============8537751789001939036==\n"
                "Content-Type: application/octet-stream\n"
                "MIME-Version: 1.0\n"
                "Content-Transfer-Encoding: base64\n"
                'Content-Disposition: attachment; filename="some filename"\n'
                "Content-Transfer-Encoding: 7bit\n"
                "\n"
                "30 km/h Bei Jing \n"
                "--===============8537751789001939036==--\n"
            ),
        )
