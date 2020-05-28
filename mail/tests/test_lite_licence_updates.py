from django.test import tag

from conf.test_client import LiteHMRCTestClient
from mail.services.lite_file_constructor import json_to_edifact


class LITELicenceTests(LiteHMRCTestClient):
    def setUp(self):
        super().setUp()

        # Sample structures
        # 1[line-number]\fileHeader[file-header]\SPIRE[source]\CHIEF[receiver]\licenceData[type of file]\202001171413[datetime]\96797[run-number]
        # Header
        # 2[line-number]\licence[record-type]\191877[transaction-reference (unique for file)]\insert[action]\GBOGE2017/00219[licence-reference]\OGE[licence-type]\E[usage]\20170629[start-date]\20770101[end-date]
        #   Permitted Trader (org or orgs). Blank if Open general
        #   3[line-number]\trader[record-type]\613815356001[TURN]\000219[RPATraderID]\start-date]\[end-date]\TEST CO LIMITED[name]\BELMONT ROAD[address-1]\MAIDENHEAD[address2]\SL6 6TB[addres-3]\[address-4]\[address-5]\[postcode]
        #   Country(s) (only code or group can be given)
        #   16[line-number]\country[record-type]\[CHIEF-country-code]\G012[CHIEF-country-group]\D[use]
        #   91line-number]\country[record-type]\CW[CHIEF-country-code]\[CHIEF-country-group]\D[use]
        #   92line-number]\country[record-type]\DZ[CHIEF-country-code]\[CHIEF-country-group]\D[use]
        #   93line-number]\country[record-type]\ER[CHIEF-country-code]\[CHIEF-country-group]\D[use]
        #   94line-number]\country[record-type]\GM[CHIEF-country-code]\[CHIEF-country-group]\D[use]
        #   95line-number]\country[record-type]\GP[CHIEF-country-code]\[CHIEF-country-group]\D[use]
        #   Foreign Trader
        #   78[line-number]/foreignTrader[record-type]/[address-1]/[address-2]/[address-3]/[address-4]/[address-5]/[postcode]/[coutnry]
        #   Requirements
        #   126[line-number]\restrictions[record-type]\Provisos may apply please see licence[restrictions]
        #   Licence line(s)
        #   127[line-number]\line[record-type]\1[line-number]\[commodity]\[supplement-1]\[supplement-2]\[commodity-group]\Open Licence goods - see actual licence for information[goods-description]\[something]
        #   67[line-number]\line[record-type]\4[line-number]\[commodity]\[supplement-1]\[supplement-2]\[commodity-group]\[goods-description]\[controlled-by]\[quantity-unit]\[quantity-issued]\[sub-period]
        #                                                                                       8\line\2\\\\\SARBE6-406GBE611 ASSEMBLY\Q\\30\\5
        # Trailer
        # 7[line-number]\end[record-type]\licence[start-record-type]\6[record-count]

    @tag("1882", "json-to-edifact")
    def test_json_payload_converted_to_edifact_file(self):
        payload = {
            "licences": [
                {
                    "licence": {
                        "licence_reference": "1234/56789",
                        "action": "insert",
                        "licence_type": "OGE",
                        "usage": "Export",
                        "start_date": "3124563",
                        "end_date": "12341212",
                    },
                    "traders": [
                        {
                            "turn": "613815356001",
                            "rpa_trader_id": "000219",
                            "start_date": "",
                            "end_date": "",
                            "name": "TEST CO LIMITED",
                            "address_1": "BELMONT ROAD",
                            "address_2": "",
                            "address_3": "",
                            "address_4": "",
                            "address_5": "",
                            "postcode": "al45jh",
                        },
                    ],
                    "countries": [],
                    "country_group": "G012",
                    "use": "D",
                    "foreign_traders": [
                        {
                            "name": "",
                            "address_1": "",
                            "address_2": "",
                            "address_3": "",
                            "address_4": "",
                            "address_5": "",
                            "postcode": "",
                        }
                    ],
                    "restrictions": "Provisos may apply please see licence",
                    "commodities": [
                        {
                            "commodity": "123878",
                            "supplement_1": None,
                            "supplement_2": None,
                            "commodity_group": None,
                            "goods_description": "description",
                            "controlled_by": "quantity",
                            "currency": "",
                            "quantity_unit": "GRM",
                            "value_issued": "",
                            "quantity_issued": "12345",
                            "sub_period": "",
                            "sub_period_quantity": "",
                            "sub_period_value": "",
                            "afc_rate": "",
                            "afc_quantity_unit": "",
                            "afc_currency": "",
                        }
                    ],
                },
            ]
        }
        edifact_file = json_to_edifact(payload)
        self.assertEqual(True, False)
