from django.test import TestCase

from mail.enums import ExtractTypeEnum, ReceptionStatusEnum
from mail.libraries.mailbox_service import find_mail_of
from mail.tests.factories import MailFactory


class FindMailOfTests(TestCase):
    def test_finding_mail(self):
        mail = MailFactory(status=ReceptionStatusEnum.REPLY_SENT, extract_type=ExtractTypeEnum.LICENCE_DATA)

        found_mail = find_mail_of(
            [ExtractTypeEnum.LICENCE_DATA, ExtractTypeEnum.LICENCE_REPLY],
            ReceptionStatusEnum.REPLY_SENT,
        )

        self.assertEqual(mail, found_mail)

    def test_mail_not_found(self):
        MailFactory(status=ReceptionStatusEnum.REPLY_SENT, extract_type=ExtractTypeEnum.LICENCE_DATA)

        found_mail = find_mail_of(
            [ExtractTypeEnum.USAGE_DATA, ExtractTypeEnum.USAGE_REPLY],
            ReceptionStatusEnum.REPLY_SENT,
        )

        self.assertIsNone(found_mail)
