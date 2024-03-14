import json

from mail.libraries.chiefprotocol import format_line
from mail.libraries.chieftypes import Trader, ForeignTrader

# Methods to anonymise fields specified in model config yaml file
#


def sanitize_trader(line):
    tokens = line.split("\\")
    trader = Trader(*tokens)
    trader.turn = ""
    trader.rpa_trader_id = "GB123456789000"
    trader.name = "Exporter name"
    trader.start_date = ""
    trader.end_date = ""
    trader.address1 = "address line1"
    trader.address2 = "address line2"
    trader.address3 = "address line3"
    trader.address4 = "address line4"
    trader.address5 = "address line5"
    trader.postcode = "postcode"

    return format_line(trader)


def sanitize_raw_data(value):
    return "The content of the field raw_data is replaced with this static text"


def sanitize_edi_data(lines):
    output_lines = []
    for line in lines.split("\n"):
        line_type = line.split("\\")[1]
        if line_type == "trader":
            line = sanitize_trader(line)

        output_lines.append(line)

    return "\n".join(output_lines)


def sanitize_sent_data(value):
    return "The content of the field sent_data is replaced with this static text"


def sanitize_payload_data(value):
    return json.dumps({"data": "The licence payload json is replaced with this static text"})
