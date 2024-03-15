import json

from datetime import datetime

from mail.libraries.chiefprotocol import format_line
from mail.libraries.chieftypes import LicenceDataLine, ForeignTrader, Trader

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


def sanitize_foreign_trader(line):
    tokens = line.split("\\")
    foreign_trader = ForeignTrader(*tokens)
    foreign_trader.name = "End-user name"
    foreign_trader.address1 = "address line1"
    foreign_trader.address2 = "address line2"
    foreign_trader.address3 = "address line3"
    foreign_trader.address4 = "address line4"
    foreign_trader.address5 = "address line5"
    foreign_trader.postcode = "postcode"
    foreign_trader.country = "AU"

    return format_line(foreign_trader)


def sanitize_product_line(line):
    tokens = line.split("\\")
    line_item = LicenceDataLine(*tokens)
    line_item.goods_description = "PRODUCT NAME"

    return format_line(line_item)


edi_data_sanitizer = {
    "trader": sanitize_trader,
    "foreignTrader": sanitize_foreign_trader,
    "line": sanitize_product_line,
}


def sanitize_edi_data(lines):
    output_lines = []
    for line in lines.split("\n"):
        line_type = line.split("\\")[1]
        output_line = edi_data_sanitizer.get(line_type, lambda x: x)(line)

        output_lines.append(output_line)

    return "\n".join(output_lines)


def sanitize_raw_data(value):
    today = datetime.strftime(datetime.today().date(), "%d %B %Y")
    return f"{today}: raw_data contents anonymised"


def sanitize_sent_data(value):
    today = datetime.strftime(datetime.today().date(), "%d %B %Y")
    return f"{today}: sent_data contents anonymised"


def sanitize_payload_data(value):
    today = datetime.strftime(datetime.today().date(), "%d %B %Y")
    data = json.loads(value)
    anonymised = {
        "reference": data.get("reference", "reference not available"),
        "action": data.get("action", "action not available"),
        "details": f"{today}, other details anonymised",
    }
    return json.dumps(anonymised)
