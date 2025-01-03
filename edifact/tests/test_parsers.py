from django.test import TestCase
from lark import Token, Tree
from parameterized import parameterized

from edifact.parsers import usage_data_parser

files = [
    (
        """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\12ABC12AB1ABCD1AB1\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\fileTrailer\\1
""",
        Tree(
            Token("RULE", "file"),
            [
                Tree(
                    Token("RULE", "file_header"),
                    [
                        Token("SOURCE_SYSTEM", "CHIEF"),
                        Token("DESTINATION_SYSTEM", "SPIRE"),
                        Token("DATA_ID", "usageData"),
                        Token("CREATION_DATE_TIME", "201901130300"),
                        Token("RUN_NUMBER", "49543"),
                    ],
                ),
                Tree(
                    Token("RULE", "licence_usage_transaction"),
                    [
                        Tree(
                            Token("RULE", "licence_usage_transaction_header"),
                            [
                                Token("TRANSACTION_REF", "LU04148/00001"),
                                Token("ACTION", "insert"),
                                Token("LICENCE_REF", "GBOIE2017/12345B"),
                                Token("LICENCE_STATUS", "O"),
                            ],
                        ),
                        Tree(
                            Token("RULE", "licence_line"),
                            [
                                Tree(
                                    Token("RULE", "licence_line_header"),
                                    [
                                        Token("LINE_NUM", "1"),
                                        Token("QUANTITY_USED", "0"),
                                        Token("VALUE_USED", "0"),
                                        Token("CURRENCY", "GBP"),
                                    ],
                                ),
                                Tree(
                                    Token("RULE", "licence_usage"),
                                    [
                                        Token("USAGE_TYPE", "O"),
                                        Token("DECLARATION_UCR", "12ABC12AB1ABCD1AB1"),
                                        Token("DECLARATION_PART_NUM", "XXXX"),
                                        Token("CONTROL_DATE", "20191130"),
                                        Token("QUANTITY_USED", "1.000"),
                                        Token("VALUE_USED", "2.00"),
                                        Token("TRADER_ID", "GB123456789012"),
                                        Token("ORIGIN_COUNTRY", "GB"),
                                    ],
                                ),
                                Tree(Token("RULE", "licence_line_trailer"), [Token("RECORD_COUNT", "3")]),
                            ],
                        ),
                        Tree(Token("RULE", "licence_usage_transaction_trailer"), [Token("RECORD_COUNT", "5")]),
                    ],
                ),
                Tree(Token("RULE", "file_trailer"), [Token("LICENCE_USAGE_COUNT", "1")]),
            ],
        ),
    ),
    (
        """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBSIE2022/12345B\\D\\20241001
3\\line\\2\\1.000\\0.000\\
4\\end\\line\\2
5\\line\\1\\1.000\\0.00\\
6\\end\\line\\2
7\\end\\licenceUsage\\6
8\\fileTrailer\\1
""",
        Tree(
            Token("RULE", "file"),
            [
                Tree(
                    Token("RULE", "file_header"),
                    [
                        Token("SOURCE_SYSTEM", "CHIEF"),
                        Token("DESTINATION_SYSTEM", "SPIRE"),
                        Token("DATA_ID", "usageData"),
                        Token("CREATION_DATE_TIME", "201901130300"),
                        Token("RUN_NUMBER", "49543"),
                    ],
                ),
                Tree(
                    Token("RULE", "licence_usage_transaction"),
                    [
                        Tree(
                            Token("RULE", "licence_usage_transaction_header"),
                            [
                                Token("TRANSACTION_REF", "LU04148/00001"),
                                Token("ACTION", "insert"),
                                Token("LICENCE_REF", "GBSIE2022/12345B"),
                                Token("LICENCE_STATUS", "D"),
                                Token("COMPLETION_DATE", "20241001"),
                            ],
                        ),
                        Tree(
                            Token("RULE", "licence_line"),
                            [
                                Tree(
                                    Token("RULE", "licence_line_header"),
                                    [
                                        Token("LINE_NUM", "2"),
                                        Token("QUANTITY_USED", "1.000"),
                                        Token("VALUE_USED", "0.000"),
                                    ],
                                ),
                                Tree(Token("RULE", "licence_line_trailer"), [Token("RECORD_COUNT", "2")]),
                            ],
                        ),
                        Tree(
                            Token("RULE", "licence_line"),
                            [
                                Tree(
                                    Token("RULE", "licence_line_header"),
                                    [
                                        Token("LINE_NUM", "1"),
                                        Token("QUANTITY_USED", "1.000"),
                                        Token("VALUE_USED", "0.00"),
                                    ],
                                ),
                                Tree(Token("RULE", "licence_line_trailer"), [Token("RECORD_COUNT", "2")]),
                            ],
                        ),
                        Tree(Token("RULE", "licence_usage_transaction_trailer"), [Token("RECORD_COUNT", "6")]),
                    ],
                ),
                Tree(Token("RULE", "file_trailer"), [Token("LICENCE_USAGE_COUNT", "1")]),
            ],
        ),
    ),
]


class UsageDataEdifactParserTests(TestCase):
    @parameterized.expand(files)
    def test_parsing_usage_data(self, file, expected):
        tree = usage_data_parser.parse(file)
        self.assertEqual(tree, expected)
