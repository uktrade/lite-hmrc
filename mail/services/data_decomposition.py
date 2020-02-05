import json

from mail.enums import SourceEnum
from mail.services.helpers import id_owner


def split_edi_data_by_id(usage_data):
    lines = usage_data.split("\n")
    spire_blocks = []
    lite_blocks = []
    block = []
    licence_owner = None
    for line in lines:
        if "licenceUsage" in line and "end" not in line:
            licence_id = line.split(r"\{}".format(""))[4]
            licence_owner = id_owner(licence_id)

        data_line = line.split(r"\{}".format(""), 1)[1]
        block.append(data_line)

        if "fileTrailer" in line:
            spire_blocks.append(block)
            break
        if "fileHeader" in line:
            spire_blocks.append(block)
            block = []

        if "licenceUsage" in line and "end" in line:
            if licence_owner == SourceEnum.SPIRE:
                spire_blocks.append(block)
            else:
                lite_blocks.append(block)
            block = []

    return spire_blocks, lite_blocks


def build_spire_file_from_data_blocks(data_blocks: list):
    spire_file = ""
    i = 1
    for block in data_blocks:
        for line in block:
            spire_file += str(i) + "\\" + line + "\n"
            i += 1

    spire_file = spire_file[:-1]
    return spire_file


# Keys for good payload
"""
[line number (some int)] = -1
[line start (always usage)] = 0
[usage_type] = 1
[declaration-ucr] = 2
[declaration-part-number] = 3
[control-date] = 4
[quantity-used] = 5
[value-used] = 6
[trader-id / TURN] = 7
[claim-ref] = 8
[origin-country (not used for exports)] = 9
[customs-mic] = 10
[customs-message] = 11
[consignee-name] = 12
"""
# Sample block
"""
[
    "licenceUsage\\LU04148/00005\\insert\\GBOGE2011/56789\\O\\",
    "line\\1\\0\\0\\",
    "usage\\O\\9GB000004988000-4750437112345\\G\\20190111\\0\\0\\\\000104\\\\\\\\",
    "usage\\O\\9GB000004988000-4750436912345\\Y\\20190111\\0\\0\\\\000104\\\\\\\\",
    "end\\line\\4",
    "end\\licenceUsage\\6",
]
"""


def build_json_payload_from_data_blocks(data_blocks: list):
    payload = []

    for block in data_blocks:
        licence_payload = {
            "id": "",
            "goods": [],
        }

        for line in block:
            good_payload = {
                "usage_type": "",
                "declaration_ucr": "",
                "declaration_part_number": "",
                "control_date": "",
                "quantity_used": "",
                "value_used": "",
                "currency": "",
                "trader_id": "",
                "claim_ref": "",
                "origin_country": "",
                "customs_mic": "",
                "customs_message": "",
                "consignee_name": "",
            }

            skip_currency = False
            if "licenceUsage" in line and "end" not in line:
                licence_payload["id"] = line.split("\\")[3]

            if "usage" in line:
                line_array = line.split("\\")
                line_array.pop(0)
                key_number = 0

                for key in good_payload.keys():
                    if key == "value_used" and (
                        line_array[key_number] == "0" or line_array[key_number] == ""
                    ):
                        skip_currency = True
                    if key == "currency" and skip_currency:
                        good_payload[key] = ""
                        skip_currency = False
                        continue
                    good_payload[key] = line_array[key_number]
                    key_number += 1

                licence_payload["goods"].append(good_payload)

        payload.append(licence_payload)

    return json.dumps({"licences": payload})
