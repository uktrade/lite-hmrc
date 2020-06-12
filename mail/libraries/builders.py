import json

from django.utils import timezone

from mail.enums import SourceEnum, ExtractTypeEnum
from mail.libraries.lite_to_edifact_converter import licences_to_edifact
from mail.models import LicenceUpdate, Mail


def build_update_mail(licences) -> Mail:
    last_lite_update = LicenceUpdate.objects.last()
    run_number = last_lite_update.hmrc_run_number + 1 if last_lite_update else 1
    file_name, file_content = _build_licence_updates_file(licences, run_number)
    mail = Mail.objects.create(
        edi_filename=file_name,
        edi_data=file_content,
        extract_type=ExtractTypeEnum.LICENCE_UPDATE,
        raw_data="See Licence Payload",
    )
    licence_ids = json.dumps([str(licence.reference) for licence in licences])
    LicenceUpdate.objects.create(hmrc_run_number=run_number, source=SourceEnum.LITE, mail=mail, licence_ids=licence_ids)

    return mail


def _build_licence_updates_file(licences, run_number):
    now = timezone.now()
    file_name = (
        "ILBDOTI_live_CHIEF_licenceUpdate_"
        + str(run_number)
        + "_"
        + "{:04d}{:02d}{:02d}{:02d}{:02d}".format(now.year, now.month, now.day, now.hour, now.minute)
    )

    file_content = licences_to_edifact(licences)

    return file_name, file_content
