import json

from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.enums import SourceEnum
from mail.services.data_decomposition import (
    split_edi_data_by_id,
    build_spire_file_from_data_blocks,
    build_json_payload_from_data_blocks,
)
from mail.services.helpers import id_owner


class FileDeconstruction(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        self.spire_data_expected = [
            ["fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\9876\\"],
            [
                "licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000001328000-PE112345\\R\\20190112\\0\\0\\\\000262\\\\\\\\",
                "usage\\O\\9GB000001328000-PE112345\\L\\20190112\\0\\0\\\\000262\\\\\\\\",
                "usage\\O\\9GB000001328000-PE112345\\K\\20190112\\0\\0\\\\000262\\\\\\\\",
                "end\\line\\5",
                "end\\licenceUsage\\7",
            ],
            [
                "licenceUsage\\LU04148/00002\\insert\\GBOGE2014/23456\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000003133000-445251012345\\Z\\20190112\\0\\0\\\\000962\\\\\\\\",
                "end\\line\\3",
                "end\\licenceUsage\\5",
            ],
            [
                "licenceUsage\\LU04148/00003\\insert\\GBOGE2018/34567\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000001328000-PE112345\\A\\20190112\\0\\0\\\\000442\\\\\\\\",
                "end\\line\\3",
                "end\\licenceUsage\\5",
            ],
            [
                "licenceUsage\\LU04148/00004\\insert\\GBSIE2018/45678\\O\\",
                "line\\1\\3\\0\\",
                "usage\\O\\9GB00000133000-774170812345\\D\\20190112\\3\\0\\\\009606\\\\\\\\",
                "end\\line\\3",
                "end\\licenceUsage\\5",
            ],
            ["fileTrailer\\7"],
        ]
        self.lite_data_expected = [
            [
                "licenceUsage\\LU04148/00005\\insert\\GBOGE2011/56789\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000004988000-4750437112345\\G\\20190111\\0\\0\\\\000104\\\\\\\\",
                "usage\\O\\9GB000004988000-4750436912345\\Y\\20190111\\0\\0\\\\000104\\\\\\\\",
                "end\\line\\4",
                "end\\licenceUsage\\6",
            ],
            [
                "licenceUsage\\LU04148/00006\\insert\\GBOGE2017/98765\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000002816000-273993\\L\\20190109\\0\\0\\\\000316\\\\\\\\",
                "end\\line\\3",
                "end\\licenceUsage\\5",
            ],
            [
                "licenceUsage\\LU04148/00007\\insert\\GBOGE2015/87654\\O\\",
                "line\\1\\0\\0\\",
                "usage\\O\\9GB000003133000-784920212345\\E\\20190111\\0\\0\\\\000640\\\\\\\\",
                "usage\\O\\9GB000003133000-784918012345\\D\\20190111\\0\\0\\\\000640\\\\\\\\",
                "end\\line\\4",
                "end\\licenceUsage\\6",
            ],
        ]
        self.expected_file_for_spire = (
            "1\\fileHeader\\CHIEF\\SPIRE\\usageData\\201901130300\\9876\\\n"
            "2\\licenceUsage\\LU04148/00001\\insert\\GBOIE2017/12345B\\O\\\n"
            "3\\line\\1\\0\\0\\\n"
            "4\\usage\\O\\9GB000001328000-PE112345\\R\\20190112\\0\\0\\\\000262\\\\\\\\\n"
            "5\\usage\\O\\9GB000001328000-PE112345\\L\\20190112\\0\\0\\\\000262\\\\\\\\\n"
            "6\\usage\\O\\9GB000001328000-PE112345\\K\\20190112\\0\\0\\\\000262\\\\\\\\\n"
            "7\\end\\line\\5\n"
            "8\\end\\licenceUsage\\7\n"
            "9\\licenceUsage\\LU04148/00002\\insert\\GBOGE2014/23456\\O\\\n"
            "10\\line\\1\\0\\0\\\n"
            "11\\usage\\O\\9GB000003133000-445251012345\\Z\\20190112\\0\\0\\\\000962\\\\\\\\\n"
            "12\\end\\line\\3\n"
            "13\\end\\licenceUsage\\5\n"
            "14\\licenceUsage\\LU04148/00003\\insert\\GBOGE2018/34567\\O\\\n"
            "15\\line\\1\\0\\0\\\n"
            "16\\usage\\O\\9GB000001328000-PE112345\\A\\20190112\\0\\0\\\\000442\\\\\\\\\n"
            "17\\end\\line\\3\n"
            "18\\end\\licenceUsage\\5\n"
            "19\\licenceUsage\\LU04148/00004\\insert\\GBSIE2018/45678\\O\\\n"
            "20\\line\\1\\3\\0\\\n"
            "21\\usage\\O\\9GB00000133000-774170812345\\D\\20190112\\3\\0\\\\009606\\\\\\\\\n"
            "22\\end\\line\\3\n"
            "23\\end\\licenceUsage\\5\n"
            "24\\fileTrailer\\7"
        )
        expected_lite_payload = {
            "licences": [
                {
                    "id": "GBOGE2011/56789",
                    "goods": [
                        {
                            "usage_type": "O",
                            "declaration_ucr": "9GB000004988000-4750437112345",
                            "declaration_part_number": "G",
                            "control_date": "20190111",
                            "quantity_used": "0",
                            "value_used": "0",
                            "currency": "",
                            "trader_id": "",
                            "claim_ref": "000104",
                            "origin_country": "",
                            "customs_mic": "",
                            "customs_message": "",
                            "consignee_name": "",
                        },
                        {
                            "usage_type": "O",
                            "declaration_ucr": "9GB000004988000-4750436912345",
                            "declaration_part_number": "Y",
                            "control_date": "20190111",
                            "quantity_used": "0",
                            "value_used": "0",
                            "currency": "",
                            "trader_id": "",
                            "claim_ref": "000104",
                            "origin_country": "",
                            "customs_mic": "",
                            "customs_message": "",
                            "consignee_name": "",
                        },
                    ],
                },
                {
                    "id": "GBOGE2017/98765",
                    "goods": [
                        {
                            "usage_type": "O",
                            "declaration_ucr": "9GB000002816000-273993",
                            "declaration_part_number": "L",
                            "control_date": "20190109",
                            "quantity_used": "0",
                            "value_used": "0",
                            "currency": "",
                            "trader_id": "",
                            "claim_ref": "000316",
                            "origin_country": "",
                            "customs_mic": "",
                            "customs_message": "",
                            "consignee_name": "",
                        },
                    ],
                },
                {
                    "id": "GBOGE2015/87654",
                    "goods": [
                        {
                            "usage_type": "O",
                            "declaration_ucr": "9GB000003133000-784920212345",
                            "declaration_part_number": "E",
                            "control_date": "20190111",
                            "quantity_used": "0",
                            "value_used": "0",
                            "currency": "",
                            "trader_id": "",
                            "claim_ref": "000640",
                            "origin_country": "",
                            "customs_mic": "",
                            "customs_message": "",
                            "consignee_name": "",
                        },
                        {
                            "usage_type": "O",
                            "declaration_ucr": "9GB000003133000-784918012345",
                            "declaration_part_number": "D",
                            "control_date": "20190111",
                            "quantity_used": "0",
                            "value_used": "0",
                            "currency": "",
                            "trader_id": "",
                            "claim_ref": "000640",
                            "origin_country": "",
                            "customs_mic": "",
                            "customs_message": "",
                            "consignee_name": "",
                        },
                    ],
                },
            ]
        }
        self.expected_lite_json_payload = json.dumps(expected_lite_payload)
        """
        [line number (some int)] = 0
        [line start (always usage)] = 1
        [usage_type] = 2
        [declaration-ucr] = 3
        [declaration-part-number] = 4
        [control-date] = 5
        [quantity-used] = 6
        [value-used] = 7
        [trader-id / TURN] = 8
        [claim-ref] = 9
        [origin-country (not used for exports)] = 10
        [customs-mic] = 11
        [customs-message] = 12
        [consignee-name] = 13
        """

    @tag("1882", "id-ident")
    def test_determine_spire_licence_id_and_lite_licence_ids(self):
        spire_id_1 = "GBSIE2018/45678"
        spire_id_2 = "GBOIE2017/12345B"
        lite_id = "GBOGE2011/56789"
        self.assertEqual(id_owner(spire_id_1), SourceEnum.SPIRE)
        self.assertEqual(id_owner(spire_id_2), SourceEnum.SPIRE)
        self.assertEqual(id_owner(lite_id), SourceEnum.LITE)

    @tag("1882", "splitting-file")
    def test_usage_data_split_according_to_licence_ids(self):
        usage_data = self.licence_usage_file_body
        spire_data, lite_data = split_edi_data_by_id(usage_data)

        self.assertEqual(spire_data, self.spire_data_expected)
        self.assertEqual(lite_data, self.lite_data_expected)

    @tag("1882", "rebuilding-file-spire")
    def test_spire_file_rebuild(self):
        spire_file = build_spire_file_from_data_blocks(self.spire_data_expected)

        self.assertEqual(spire_file, self.expected_file_for_spire)

    @tag("1882", "build-json-lite")
    def test_lite_json_payload_create(self):
        lite_payload = build_json_payload_from_data_blocks(self.lite_data_expected)

        self.assertEqual(lite_payload, self.expected_lite_json_payload)
