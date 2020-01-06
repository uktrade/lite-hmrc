import unittest

from mail.dtos import *

class TestDtos(unittest.TestCase):
    def setUp(self):
        pass

    def test_EmailMessageDto(self):
        emailMessageDto = EmailMessageDto(run_number=101, sender='test@example.com', body='body', subject='subject',
                                          attachment={})
        self.assertEqual(101, emailMessageDto.run_number, 'Run-number did not match')
        self.assertEqual('test@example.com', emailMessageDto.sender, 'sender email did not match')

