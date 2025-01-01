from django.test import TestCase
from lark import Token, Tree

from edifact.parsers import usage_data_parser


class UsageDataEdifactParserTests(TestCase):
    def test_parsing_usage_data(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\fileTrailer\\0"""

        self.assertEqual(
            usage_data_parser.parse(file),
            Tree(
                Token("RULE", "file"),
                [Token("TIMESTAMP", "201901130300"), Token("RUN_NUMBER", "49543"), Token("LICENCE_USAGE_COUNT", "0")],
            ),
        )
