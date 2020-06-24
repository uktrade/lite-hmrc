import logging

from background_task import background
from django.db import transaction

from mail.enums import ReceptionStatusEnum, ReplyStatusEnum
from mail.libraries.builders import build_update_mail
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.routing_controller import update_mail, send
from mail.models import LicencePayload, Mail

LICENCE_UPDATES_TASK_QUEUE = "licences_updates_queue"


@background(queue=LICENCE_UPDATES_TASK_QUEUE, schedule=0)
def send_licence_updates_to_hmrc():
    logging.info("Sending LITE licence updates to HMRC")

    if not _is_email_slot_free():
        logging.info("There is currently an update in progress or an email is in flight")
        return

    try:
        with transaction.atomic():
            licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

            if not licences.exists():
                logging.info("There are currently no licences to send")
                return

            mail = build_update_mail(licences)
            mail_dto = build_request_mail_message_dto(mail)
            licence_references = list(licences.values_list("reference", flat=True))
            logging.info(f"Created Mail [{mail.id}] from licences [{licence_references}]")

            send(mail_dto)
            update_mail(mail, mail_dto)
            licences.update(is_processed=True)
    except Exception as exc:  # noqa
        logging.error(
            f"An unexpected error occurred when sending LITE licence updates to HMRC -> {type(exc).__name__}: {exc}"
        )
    else:
        logging.info(f"Successfully sent LITE licences updates in Mail [{mail.id}] to HMRC")


def _is_email_slot_free() -> bool:
    pending_mail = _get_pending_mail()
    if pending_mail:
        logging.error(f"The following Mail is pending: {pending_mail}")
        return False

    rejected_mail = _get_rejected_mail()
    if rejected_mail:
        logging.error(f"The following Mail has been rejected: {pending_mail}")
        return False

    return True


def _get_pending_mail() -> []:
    return list(Mail.objects.exclude(status=ReceptionStatusEnum.REPLY_SENT).values_list("id", flat=True))


def _get_rejected_mail() -> []:
    return list(
        Mail.objects.filter(
            status=ReceptionStatusEnum.REPLY_SENT, response_data__icontains=ReplyStatusEnum.REJECTED,
        ).values_list("id", flat=True)
    )
