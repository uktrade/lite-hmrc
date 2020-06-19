import logging
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from background_task import background
from background_task.models import Task
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from mail.requests import put

from conf.settings import (
    EMAIL_USER,
    NOTIFY_USERS,
    LITE_API_URL,
    HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
    LITE_API_REQUEST_TIMEOUT,
    MAX_ATTEMPTS,
)
from mail.enums import ReceptionStatusEnum, ReplyStatusEnum
from mail.libraries.builders import build_update_mail
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.mailbox_service import send_email
from mail.libraries.routing_controller import update_mail, check_and_route_emails, send
from mail.models import LicencePayload, Mail, UsageUpdate
from mail.servers import MailServer

LICENCE_UPDATES_TASK_QUEUE = "licences_updates_queue"
MANAGE_INBOX_TASK_QUEUE = "manage_inbox_queue"
NOTIFY_USERS_TASK_QUEUE = "notify_users_queue"
USAGE_FIGURES_QUEUE = "usage_figures_queue"
TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)


@background(queue=LICENCE_UPDATES_TASK_QUEUE, schedule=0)
def send_lite_licence_updates_to_hmrc():
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


@background(queue=MANAGE_INBOX_TASK_QUEUE, schedule=0)
def manage_inbox_queue():
    logging.info("Polling inbox for updates")

    try:
        check_and_route_emails()
    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when polling inbox for updates -> {type(exc).__name__}: {exc}")


@background(queue=NOTIFY_USERS_TASK_QUEUE, schedule=0)
def notify_users_of_rejected_mail(mail_id, mail_response_date):
    logging.info(f"Notifying users of rejected Mail [{mail_id}, {mail_response_date}]")

    try:
        multipart_msg = MIMEMultipart()
        multipart_msg["From"] = EMAIL_USER
        multipart_msg["To"] = ",".join(NOTIFY_USERS)
        multipart_msg["Subject"] = f"Mail rejected"
        body = MIMEText(f"Mail [{mail_id}] received at [{mail_response_date}] was rejected")
        multipart_msg.attach(body)

        server = MailServer()
        smtp_connection = server.connect_to_smtp()
        send_email(smtp_connection, multipart_msg)
        server.quit_smtp_connection()
    except Exception as exc:  # noqa
        error_message = (
            f"An unexpected error occurred when notifying users of rejected Mail "
            f"[{mail_id}, {mail_response_date}] -> {type(exc).__name__}: {exc}"
        )

        # Raise an exception
        # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
        raise Exception(error_message)
    else:
        logging.info(f"Successfully notified users of rejected Mail [{mail_id}, {mail_response_date}]")


@background(queue=USAGE_FIGURES_QUEUE, schedule=0)
def send_licence_usage_figures_to_lite_api(lite_usage_update_id):
    logging.info(f"Preparing LITE UsageUpdate [{lite_usage_update_id}] for LITE API")

    try:
        lite_usage_update = UsageUpdate.objects.get(id=lite_usage_update_id)
    except UsageUpdate.DoesNotExist:  # noqa
        _handle_lite_usage_figures_exception(
            f"LITE UsageUpdate [{lite_usage_update_id}] does not exist.", lite_usage_update_id,
        )
    else:
        licences = list(lite_usage_update.licence_ids)
        logging.info(f"Sending LITE UsageUpdate [{lite_usage_update_id}] figures for Licences [{licences}] to LITE API")

        try:
            response = put(
                f"{LITE_API_URL}/licences/hmrc-integration/",
                lite_usage_update.lite_payload,
                hawk_credentials=HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
                timeout=LITE_API_REQUEST_TIMEOUT,
            )
        except Exception as exc:  # noqa
            _handle_lite_usage_figures_exception(
                f"An unexpected error occurred when sending LITE UsageUpdate [{lite_usage_update_id}] to LITE API -> "
                f"{type(exc).__name__}: {exc}",
                lite_usage_update_id,
            )
        else:
            if response.status_code != status.HTTP_200_OK:
                _handle_lite_usage_figures_exception(
                    f"An unexpected response was received when sending LITE UsageUpdate [{lite_usage_update_id}] to "
                    f"LITE API -> status=[{response.status_code}], message=[{response.text}]",
                    lite_usage_update_id,
                )

            logging.info(f"Successfully sent LITE UsageUpdate [{lite_usage_update_id}] to LITE API")


def _handle_lite_usage_figures_exception(message, lite_usage_update_id):
    logging.warning(message)
    error_message = f"Failed to send LITE UsageUpdate [{lite_usage_update_id}] to LITE API"

    try:
        task = Task.objects.get(queue=USAGE_FIGURES_QUEUE, task_params=f'[["{lite_usage_update_id}"], {{}}]')
    except Task.DoesNotExist:
        logging.error(f"No task was found for UsageUpdate [{lite_usage_update_id}]")
    else:
        # Get the task's current attempt number by retrieving the previous attempts and adding 1
        current_attempt = task.attempts + 1

        # Schedule a new task if the current task has been attempted MAX_ATTEMPTS times;
        # HMRC Integration tasks need to be resilient and keep retrying post-failure indefinitely.
        # This logic will make MAX_ATTEMPTS attempts to send licence changes according to the Django Background Task
        # Runner scheduling, then wait TASK_BACK_OFF seconds before starting the process again.
        if current_attempt >= MAX_ATTEMPTS:
            logging.warning(
                f"Maximum attempts of {MAX_ATTEMPTS} for LITE UsageUpdate [{lite_usage_update_id}] has been reached"
            )

            schedule_datetime = timezone.now() + timedelta(seconds=TASK_BACK_OFF)
            logging.info(
                f"Scheduling new task for LITE UsageUpdate [{lite_usage_update_id}] to commence at "
                f"[{schedule_datetime}]"
            )
            send_licence_usage_figures_to_lite_api(lite_usage_update_id, schedule=TASK_BACK_OFF)  # noqa
        else:
            error_message += f"; attempt number [{current_attempt}]"

    # Raise an exception
    # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
    raise Exception(error_message)


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
