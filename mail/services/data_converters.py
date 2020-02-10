from conf.constants import VALID_SENDERS
from mail.enums import ReceptionStatusEnum, ExtractTypeEnum
from mail.models import Mail
from mail.services.helpers import (
    convert_sender_to_source,
    new_hmrc_run_number,
    process_attachment,
    get_licence_ids,
    new_spire_run_number,
)


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
    return data


def convert_data_for_licence_update_reply(dto):
    data = {}
    data["response_filename"], data["response_data"] = process_attachment(
        dto.attachment
    )
    data["status"] = ReceptionStatusEnum.REPLY_RECEIVED
    mail = Mail.objects.get(
        status=ReceptionStatusEnum.REPLY_PENDING,
        extract_type=ExtractTypeEnum.LICENCE_UPDATE,
    )
    return data, mail


def convert_data_for_usage_update(dto):
    data = {"usage_update": {}}
    data["edi_filename"], data["edi_data"] = process_attachment(dto.attachment)
    data["usage_update"]["spire_run_number"] = (
        new_spire_run_number(int(dto.run_number))
        if convert_sender_to_source(dto.sender) in VALID_SENDERS
        else None
    )
    data["usage_update"]["hmrc_run_number"] = dto.run_number
    data["usage_update"]["license_ids"] = get_licence_ids(data["edi_data"])
    return data


def convert_data_for_usage_update_reply(dto):
    data = {}
    data["response_filename"], data["response_data"] = process_attachment(
        dto.attachment
    )
    data["status"] = ReceptionStatusEnum.REPLY_RECEIVED
    mail = Mail.objects.get(
        status=ReceptionStatusEnum.REPLY_PENDING,
        extract_type=ExtractTypeEnum.USAGE_UPDATE,
    )
    return data, mail
