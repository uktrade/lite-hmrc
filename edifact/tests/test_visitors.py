import uuid

from django.test import TestCase
from lark import Token, Tree
from parameterized import parameterized

from edifact.parsers import usage_data_parser
from edifact.visitors import Edifact, JsonPayload, RunNumberUpdater, SourceSplitter, TransactionMapper
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
                Tree(
                    Token("RULE", "file_header"),
                    [
                        Token("SOURCE_SYSTEM", "CHIEF"),
                        Token("DESTINATION_SYSTEM", "SPIRE"),
                        Token("DATA_ID", "usageData"),
                        Token("CREATION_DATE_TIME", "201901130300"),
                        Token("RUN_NUMBER", "12345"),
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
                                Token("TRANSACTION_REF", "LU04148/00002"),
                                Token("ACTION", "insert"),
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
    FILES = [
        (
            """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\49543\\
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
""",
            {
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
            },
        ),
        (
            """1\\fileHeader\\CHIEF\\SPIRE\\usageData\\202010010315\\1111\\
2\\licenceUsage\\LU01111/00027\\insert\\GBSIEL/2020/0000006/P\\O\\
3\\line\\1\\1.000\\2.00\\
4\\usage\\O\\24AAAAAAAAAAAAAAAA\\XXXX\\20200926\\1.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
5\\end\\line\\3
6\\end\\licenceUsage\\5
7\\licenceUsage\\LU01111/00032\\insert\\GBSIEL/2020/0000008/P\\O\\
8\\line\\1\\3.000\\4.00\\
9\\usage\\O\\24AAAAAAAAAAAAAAAB\\XXXX\\20200925\\100.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
10\\end\\line\\3
11\\end\\licenceUsage\\5
12\\licenceUsage\\LU01111/00039\\insert\\GBSIEL/2020/0000001/P\\O\\
13\\line\\1\\5.000\\6.00\\
14\\usage\\O\\24AAAAAAAAAAAAAAAC\\XXXX\\20200927\\34800.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
15\\end\\line\\3
16\\end\\licenceUsage\\5
17\\licenceUsage\\LU01111/00054\\insert\\GBSIEL/2020/0001111/P\\O\\
18\\line\\1\\7.000\\8.00\\
19\\usage\\O\\24AAAAAAAAAAAAAAAD\\XXXX\\20200930\\1.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
20\\end\\line\\3
21\\end\\licenceUsage\\5
22\\licenceUsage\\LU01111/00070\\insert\\GBSIEL/2021/0000003/P\\O\\
23\\line\\2\\9.000\\10.00\\
24\\usage\\O\\24AAAAAAAAAAAAAAAE\\XXXX\\20200930\\6.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
25\\end\\line\\3
26\\end\\licenceUsage\\5
27\\licenceUsage\\LU01111/00094\\insert\\GBSIEL/2021/0000006/P\\O\\
28\\line\\1\\11.000\\12.00\\
29\\usage\\O\\24AAAAAAAAAAAAAAAF\\XXXX\\20200930\\80.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
30\\usage\\O\\24AAAAAAAAAAAAAAAG\\XXXX\\20200930\\100.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
31\\end\\line\\4
32\\end\\licenceUsage\\6
33\\licenceUsage\\LU01111/00120\\insert\\GBSIEL/2020/0000007/P\\O\\
34\\line\\1\\13.000\\14.00\\
35\\usage\\O\\24AAAAAAAAAAAAAAAH\\XXXX\\20200929\\1.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
36\\end\\line\\3
37\\end\\licenceUsage\\5
38\\licenceUsage\\LU01111/00126\\insert\\GBSIEL/2020/0001006/P\\O\\
39\\line\\1\\15.000\\16.00\\
40\\usage\\O\\24AAAAAAAAAAAAAAAI\\XXXX\\20200924\\6.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
41\\end\\line\\3
42\\line\\4\\17.000\\18.00\\
43\\usage\\O\\24AAAAAAAAAAAAAAAJ\\XXXX\\20200924\\2.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
44\\end\\line\\3
45\\end\\licenceUsage\\8
46\\licenceUsage\\LU01111/00133\\insert\\GBSIEL/2020/0001446/P\\O\\
47\\line\\1\\19.000\\20.00\\
48\\usage\\O\\24AAAAAAAAAAAAAAAK\\XXXX\\20200925\\2.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
49\\end\\line\\3
50\\end\\licenceUsage\\5
51\\licenceUsage\\LU01111/00181\\insert\\GBSIEL/2021/0001327/P\\O\\
52\\line\\1\\21.000\\22.00\\
53\\usage\\O\\24AAAAAAAAAAAAAAAL\\XXXX\\20200930\\90.000\\\\\\GB111111111111\\\\NA\\\\\\\\\\
54\\end\\line\\3
55\\end\\licenceUsage\\5
56\\licenceUsage\\LU01111/00263\\insert\\GBSIEL/2021/0000043/P\\O\\
57\\line\\1\\23.000\\24.00\\
58\\usage\\O\\24AAAAAAAAAAAAAAAM\\XXXX\\20200930\\3.000\\\\\\GB111111111111\\\\GB\\\\\\\\\\
59\\end\\line\\3
60\\end\\licenceUsage\\5
61\\fileTrailer\\11""",
            {
                "licences": [
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "1.000", "value": "2.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "3.000", "value": "4.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "5.000", "value": "6.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "7.000", "value": "8.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "9.000", "value": "10.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "11.000", "value": "12.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "13.000", "value": "14.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [
                            {"usage": "15.000", "value": "16.00", "currency": "", "id": None},
                            {"usage": "17.000", "value": "18.00", "currency": "", "id": None},
                        ],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "19.000", "value": "20.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "21.000", "value": "22.00", "currency": "", "id": None}],
                    },
                    {
                        "action": "open",
                        "completion_date": "",
                        "id": None,
                        "goods": [{"usage": "23.000", "value": "24.00", "currency": "", "id": None}],
                    },
                ]
            },
        ),
    ]

    @parameterized.expand(FILES)
    def test_json_payload(self, file, expected):
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

        tree = usage_data_parser.parse(file)
        payload = JsonPayload().transform(tree)
        self.assertEqual(payload, expected)


class EditfactTests(TestCase):
    def test_edifact(self):
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
22\\end\\line\\4
23\\end\\licenceUsage\\6
24\\fileTrailer\\4"""

        tree = usage_data_parser.parse(file)
        edifact = Edifact().transform(tree)

        self.assertEqual(file, edifact)
