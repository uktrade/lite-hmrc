import uuid

from django.test import TestCase
from lark import Token, Tree

from edifact.parsers import usage_data_parser
from edifact.visitors import JsonPayload, RunNumberUpdater, SourceSplitter, TransactionMapper
from mail.enums import SourceEnum
from mail.models import GoodIdMapping, LicenceIdMapping, LicencePayload, TransactionMapping
from mail.tests.factories import UsageDataFactory


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


class TransactionMapperTests(TestCase):
    def test_creates_transaction_mappings(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\12ABC12AB1ABCD1AB1\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\fileTrailer\\1"""

        self.assertFalse(TransactionMapping.objects.exists())

        usage_data = UsageDataFactory()

        tree = usage_data_parser.parse(file)

        TransactionMapper(usage_data).visit_topdown(tree)

        self.assertEqual(
            TransactionMapping.objects.count(),
            1,
        )
        transaction_mapping = TransactionMapping.objects.get()
        self.assertEqual(transaction_mapping.line_number, 1)
        self.assertEqual(transaction_mapping.usage_data, usage_data)
        self.assertEqual(transaction_mapping.licence_reference, "GBOIE2017/12345B")
        self.assertEqual(transaction_mapping.usage_transaction, "LU04148/00001")

    def test_transaction_mappings_already_exists(self):
        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\
3\\line\\1\\0\\0\\GBP
4\\usage\\O\\12ABC12AB1ABCD1AB1\\XXXX\\20191130\\1.000\\2.00\\\\GB123456789012\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\fileTrailer\\1"""

        usage_data = UsageDataFactory()
        TransactionMapping.objects.create(
            line_number=1,
            usage_data=usage_data,
            licence_reference="GBOIE2017/12345B",
            usage_transaction="LU04148/00001",
        )

        tree = usage_data_parser.parse(file)

        TransactionMapper(usage_data).visit_topdown(tree)

        self.assertEqual(
            TransactionMapping.objects.count(),
            1,
        )
        transaction_mapping = TransactionMapping.objects.get()
        self.assertEqual(transaction_mapping.line_number, 1)
        self.assertEqual(transaction_mapping.usage_data, usage_data)
        self.assertEqual(transaction_mapping.licence_reference, "GBOIE2017/12345B")
        self.assertEqual(transaction_mapping.usage_transaction, "LU04148/00001")


class JsonPayloadTests(TestCase):
    def test_json_payload(self):
        LicencePayload.objects.create(reference="GBOGE2011/56789", lite_id="00000000-0000-0000-0000-000000000001")
        LicencePayload.objects.create(reference="GBOGE2017/98765", lite_id="00000000-0000-0000-0000-000000000002")
        LicencePayload.objects.create(reference="GBOGE2015/87654", lite_id="00000000-0000-0000-0000-000000000003")

        GoodIdMapping.objects.create(
            licence_reference="GBOGE2011/56789",
            line_number=2,
            lite_id="00000000-0000-0000-0000-000000000001",
        )
        GoodIdMapping.objects.create(
            licence_reference="GBOGE2015/87654",
            line_number=1,
            lite_id="00000000-0000-0000-0000-000000000002",
        )

        file = """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
2\\licenceUsage\\LU04148/00005\\insert\\GBOGE2011/56789\\O\\
3\\line\\2\\17\\0\\
4\\usage\\O\\9GB000004988000-4750437112345\\G\\20190111\\0\\0\\\\000104\\\\\\\\\\\\\\
5\\usage\\O\\9GB000004988000-4750436912345\\Y\\20190111\\0\\0\\\\000104\\\\\\\\\\\\\\
6\\end\\line\\4
7\\end\\licenceUsage\\6
8\\licenceUsage\\LU04148/00006\\insert\\GBOGE2017/98765\\O\\
9\\line\\1\\0\\0\\
10\\usage\\O\\9GB000002816000-273993\\L\\20190109\\0\\0\\\\000316\\\\\\\\\\\\\\
11\\end\\line\\3
12\\end\\licenceUsage\\5
13\\licenceUsage\\LU04148/00007\\insert\\GBOGE2015/87654\\O\\
14\\line\\1\\1000000\\0\\GBP
15\\usage\\O\\9GB000003133000-784920212345\\E\\20190111\\0\\0\\\\000640\\\\\\\\\\\\\\
16\\usage\\O\\9GB000003133000-784918012345\\D\\20190111\\0\\0\\\\000640\\\\\\\\\\\\\\
17\\end\\line\\4
18\\end\\licenceUsage\\6
19\\licenceUsage\\LU04148/00008\\insert\\GBOGE2015/87654\\E\\
20\\line\\1\\9999\\0\\GBP
21\\usage\\O\\9GB000003333333-784920212345\\E\\20190111\\0\\0\\\\000640\\\\\\\\\\\\\\
23\\end\\line\\4
24\\end\\licenceUsage\\6
25\\fileTrailer\\4
"""

        tree = usage_data_parser.parse(file)
        payload = JsonPayload().transform(tree)

        expected_payload = {
            "licences": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "action": "open",
                    "completion_date": "",
                    "goods": [
                        {
                            "id": "00000000-0000-0000-0000-000000000001",
                            "usage": "17",
                            "value": "0",
                            "currency": "",
                        }
                    ],
                },
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "action": "open",
                    "completion_date": "",
                    "goods": [{"id": None, "usage": "0", "value": "0", "currency": ""}],
                },
                {
                    "id": "00000000-0000-0000-0000-000000000003",
                    "action": "open",
                    "completion_date": "",
                    "goods": [
                        {
                            "id": "00000000-0000-0000-0000-000000000002",
                            "usage": "1000000",
                            "value": "0",
                            "currency": "GBP",
                        }
                    ],
                },
            ]
        }

        self.assertEqual(payload, expected_payload)
