import logging
from conf.constants import VALID_SENDERS
from mail.enums import ReceptionStatusEnum
from mail.services.helpers import (
    convert_sender_to_source,
    new_hmrc_run_number,
    process_attachment,
    get_licence_ids,
    new_spire_run_number,
)

logger = logging.getLogger("data_converters")


def convert_data_for_licence_update(dto):
    data = {"licence_update": {}}
    data["licence_update"]["source"] = convert_sender_to_source(dto.sender)
    data["licence_update"]["hmrc_run_number"] = (
        new_hmrc_run_number(int(dto.run_number))
        if convert_sender_to_source(dto.sender) in VALID_SENDERS
        else None
    )
    data["licence_update"]["source_run_number"] = dto.run_number
    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)
    data["licence_update"]["license_ids"] = get_licence_ids(data["edi_data"])
    _print_nice(data)
    return data


def convert_data_for_licence_update_reply(dto):
    data = {
        "response_filename": process_attachment(dto.attachment)[0],
        "response_data": process_attachment(dto.attachment)[1],
        "status": ReceptionStatusEnum.REPLY_RECEIVED,
    }
    # mail = Mail.objects.get(
    #     status=ReceptionStatusEnum.REPLY_PENDING,
    #     extract_type=ExtractTypeEnum.LICENCE_UPDATE,
    # )
    # if mail:
    #     logger.debug("Found mail in {} of extract type {} ".
    #                  format(ReceptionStatusEnum.REPLY_PENDING, ExtractTypeEnum.LICENCE_UPDATE))
    # else:
    #     logger.warn("Can not find any mail in REPLY_PENDING of extract type LICENCE_UPDATE")
    return data


def convert_data_for_usage_update(dto):
    data = {
        "usage_update": {},
        "edi_filename": process_attachment(dto.attachment)[0],
        "edi_data": process_attachment(dto.attachment)[1],
    }
    data["usage_update"]["spire_run_number"] = (
        new_spire_run_number(int(dto.run_number))
        if convert_sender_to_source(dto.sender) in VALID_SENDERS
        else None
    )
    data["usage_update"]["hmrc_run_number"] = dto.run_number
    data["usage_update"]["license_ids"] = get_licence_ids(data["edi_data"])
    return data


def convert_data_for_usage_update_reply(dto):
    data = {
        "response_filename": process_attachment(dto.attachment)[0],
        "response_data": process_attachment(dto.attachment)[1],
        "status": ReceptionStatusEnum.REPLY_RECEIVED,
    }
    return data


def _print_nice(data):
    output = ""
    for k, v in data.items():
        output += "{}->[{}] ".format(k, str(v))
