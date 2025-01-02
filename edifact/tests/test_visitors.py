import uuid

from django.test import TestCase
from lark import Token, Tree

from edifact.parsers import usage_data_parser
from edifact.visitors import RunNumberUpdater, SourceSplitter
from mail.enums import SourceEnum
from mail.models import LicenceIdMapping


class RunNumberUpdaterTests(TestCase):
    def test_updates_run_number(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\12ABC12AB1ABCD1AB1\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\fileTrailer\\1"""

        tree = usage_data_parser.parse(file)
        transformed = RunNumberUpdater(spire_run_number=12345).transform(tree)

        expected = Tree(
            Token("RULE", "file"),
            [
                Tree(Token("RULE", "file_header"), [Token("TIMESTAMP", "201901130300"), Token("RUN_NUMBER", "12345")]),
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
        )

        self.assertEqual(transformed, expected)


class SourceSplitterTests(TestCase):
    def test_only_returns_spire_lines(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/SPIRE\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\SPIREONE\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\licenceUsage\\LU04148/00002\\insert\\GBSIE2017/LITE\\O\\
8\\line\\1\\0\\0\\GBP
9\\usage\\O\\LITEONE\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
10\\end\\line\\3
11\\end\\licenceUsage\\5
12\\fileTrailer\\2"""

        LicenceIdMapping.objects.create(
            lite_id=uuid.uuid4(),
            reference="GBSIE2017/LITE",
        )

        tree = usage_data_parser.parse(file)
        transformed = SourceSplitter(SourceEnum.SPIRE).transform(tree)

        expected = Tree(
            Token("RULE", "file"),
            [
                Tree(Token("RULE", "file_header"), [Token("TIMESTAMP", "201901130300"), Token("RUN_NUMBER", "49543")]),
                Tree(
                    Token("RULE", "licence_usage_transaction"),
                    [
                        Tree(
                            Token("RULE", "licence_usage_transaction_header"),
                            [
                                Token("TRANSACTION_REF", "LU04148/00001"),
                                Token("LICENCE_REF", "GBOIE2017/SPIRE"),
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
                                        Token("DECLARATION_UCR", "SPIREONE"),
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
        )

        self.assertEqual(transformed, expected)

    def test_only_returns_lite_lines(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/SPIRE\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\SPIREONE\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\licenceUsage\\LU04148/00002\\insert\\GBSIE2017/LITE\\O\\
8\\line\\1\\0\\0\\GBP
9\\usage\\O\\LITEONE\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
10\\end\\line\\3
11\\end\\licenceUsage\\5
12\\fileTrailer\\2"""

        LicenceIdMapping.objects.create(
            lite_id=uuid.uuid4(),
            reference="GBSIE2017/LITE",
        )

        tree = usage_data_parser.parse(file)
        transformed = SourceSplitter(SourceEnum.LITE).transform(tree)

        expected = Tree(
            Token("RULE", "file"),
            [
                Tree(Token("RULE", "file_header"), [Token("TIMESTAMP", "201901130300"), Token("RUN_NUMBER", "49543")]),
                Tree(
                    Token("RULE", "licence_usage_transaction"),
                    [
                        Tree(
                            Token("RULE", "licence_usage_transaction_header"),
                            [
                                Token("TRANSACTION_REF", "LU04148/00002"),
                                Token("LICENCE_REF", "GBSIE2017/LITE"),
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
                                        Token("DECLARATION_UCR", "LITEONE"),
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
        )

        self.assertEqual(transformed, expected)
