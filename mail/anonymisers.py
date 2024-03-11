import json

# Methods to anonymise fields specified in model config yaml file
#


def sanitize_raw_data(value):
    return "The content of the field raw_data is replaced with this static text"


def sanitize_edi_data(value):
    return "The content of the field edi_data is replaced with this static text"


def sanitize_sent_data(value):
    return "The content of the field sent_data is replaced with this static text"


def sanitize_payload_data(value):
    return json.dumps({"data": "The licence payload json is replaced with this static text"})
