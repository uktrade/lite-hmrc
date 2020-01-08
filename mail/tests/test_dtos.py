import unittest
import json

from mail.dtos import *


class TestDtos(unittest.TestCase):
    def setUp(self):
        pass

    def test_EmailMessageDto(self):
        emailMessageDto = EmailMessageDto(
            run_number=101,
            sender="test@example.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=[],
        )
        self.assertEqual(101, emailMessageDto.run_number, "Run-number did not match")
        self.assertEqual(
            "test@example.com", emailMessageDto.sender, "sender email did not match"
        )
        self.assertEqual(
            "receiver@example.com",
            emailMessageDto.receiver,
            "receiver email did not match",
        )

    def test_toJson(self):
        emailMessageDto = EmailMessageDto(
            run_number=101,
            sender="test@example.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=["filename", "a line".encode("ascii", "replace")],
        )
        dtoInJson = to_json(emailMessageDto)
        dtoInDict = json.loads(dtoInJson)
        self.assertEqual(dtoInDict["run_number"], 101)
        self.assertEqual(dtoInDict["body"], "body")
        self.assertEqual(dtoInDict["attachment"]["name"], "filename")
        self.assertEqual(dtoInDict["attachment"]["data"], "a line")

    def test_toJson_raiseTypeError(self):
        emailMessageDto = EmailMessageDto(
            run_number=101,
            sender="test@example.com",
            receiver="receiver@example.com",
            body="body",
            subject="subject",
            attachment=["filename", "contents not encoded"],
        )
        with self.assertRaises(TypeError) as context:
            to_json(emailMessageDto)
        self.assertEqual("Invalid attribute 'attachment'", str(context.exception))
