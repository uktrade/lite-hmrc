from django.test import TestCase
from lark import Token, Tree

from edifact.parsers import usage_data_parser


class UsageDataEdifactParserTests(TestCase):
    def test_parsing_usage_data(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\
3\\end\\licenceUsage\\0
4\\fileTrailer\\1"""

        tree = usage_data_parser.parse(file)

        self.assertEqual(
            tree,
            Tree(
                Token("RULE", "file"),
                [
                    Tree(
                        Token("RULE", "file_header"), [Token("TIMESTAMP", "201901130300"), Token("RUN_NUMBER", "49543")]
                    ),
                    Tree(
                        Token("RULE", "licence_usage_transaction"),
                        [
                            Tree(
                                Token("RULE", "licence_usage_transaction_header"),
                                [
                                    Token("TRANSACTION_REF", "LU04148/00001"),
                                    Token("LICENCE_REF", "GBOIE2017/12345B"),
                                    Token("LICENCE_STATUS", "O"),
                                ],
                            ),
                            Tree(Token("RULE", "licence_usage_transaction_trailer"), [Token("RECORD_COUNT", "0")]),
                        ],
                    ),
                    Tree(Token("RULE", "file_trailer"), [Token("LICENCE_USAGE_COUNT", "1")]),
                ],
            ),
        )
