import logging
from datetime import timedelta

from background_task import background
from background_task.models import Task
from django.utils import timezone
from rest_framework import status

from conf.settings import (
    LITE_API_URL,
    HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
    LITE_API_REQUEST_TIMEOUT,
    MAX_ATTEMPTS,
)
from mail.libraries.usage_data_decomposition import build_json_payload_from_data_blocks, split_edi_data_by_id
from mail.models import UsageUpdate
from mail.requests import put

USAGE_FIGURES_QUEUE = "usage_figures_queue"
TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)


def schedule_licence_usage_figures_for_lite_api(lite_usage_update_id):
    logging.info(f"Scheduling UsageUpdate '{lite_usage_update_id}' for LITE API")
    task = Task.objects.filter(queue=USAGE_FIGURES_QUEUE, task_params=f'[["{lite_usage_update_id}"], {{}}]')

    if task.exists():
        logging.info(f"UsageUpdate '{lite_usage_update_id}' has already been scheduled")
    else:
        send_licence_usage_figures_to_lite_api(lite_usage_update_id)
        logging.info(f"UsageUpdate '{lite_usage_update_id}' has been scheduled")


@background(queue=USAGE_FIGURES_QUEUE, schedule=0)
def send_licence_usage_figures_to_lite_api(lite_usage_update_id):
    logging.info(f"Preparing LITE UsageUpdate [{lite_usage_update_id}] for LITE API")

    try:
        lite_usage_update = UsageUpdate.objects.get(id=lite_usage_update_id)
        licences = lite_usage_update.get_licence_ids()
    except UsageUpdate.DoesNotExist:  # noqa
        _handle_exception(
            f"LITE UsageUpdate [{lite_usage_update_id}] does not exist.", lite_usage_update_id,
        )
    else:
        logging.info(f"Sending LITE UsageUpdate [{lite_usage_update_id}] figures for Licences [{licences}] to LITE API")

        try:
            build_lite_payload(lite_usage_update)
            response = put(
                f"{LITE_API_URL}/licences/hmrc-integration/",
                lite_usage_update.lite_payload,
                hawk_credentials=HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
                timeout=LITE_API_REQUEST_TIMEOUT,
            )
        except Exception as exc:  # noqa
            _handle_exception(
                f"An unexpected error occurred when sending LITE UsageUpdate [{lite_usage_update_id}] to LITE API -> "
                f"{type(exc).__name__}: {exc}",
                lite_usage_update_id,
            )
        else:
            if response.status_code != status.HTTP_200_OK:
                _handle_exception(
                    f"An unexpected response was received when sending LITE UsageUpdate [{lite_usage_update_id}] to "
                    f"LITE API -> status=[{response.status_code}], message=[{response.text}]",
                    lite_usage_update_id,
                )

            lite_usage_update.lite_sent_at = timezone.now()
            lite_usage_update.save()
            logging.info(f"Successfully sent LITE UsageUpdate [{lite_usage_update_id}] to LITE API")


def build_lite_payload(lite_usage_update):
    _, data = split_edi_data_by_id(lite_usage_update.mail.edi_data)
    payload = build_json_payload_from_data_blocks(data)
    payload["transaction_id"] = str(lite_usage_update.id)
    lite_usage_update.lite_payload = payload
    lite_usage_update.save()


def schedule_max_tried_task_as_new_task(lite_usage_update_id):
    """
    Used to schedule a max-tried task as a new task (starting from attempts=0);
    Abstracted from 'send_licence_usage_figures_to_lite_api' to enable unit testing of a recursive operation
    """

    logging.warning(
        f"Maximum attempts of {MAX_ATTEMPTS} for LITE UsageUpdate [{lite_usage_update_id}] has been reached"
    )

    schedule_datetime = timezone.now() + timedelta(seconds=TASK_BACK_OFF)
    logging.info(
        f"Scheduling new task for LITE UsageUpdate [{lite_usage_update_id}] to commence at [{schedule_datetime}]"
    )
    send_licence_usage_figures_to_lite_api(lite_usage_update_id, schedule=TASK_BACK_OFF)  # noqa


def _handle_exception(message, lite_usage_update_id):
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
            schedule_max_tried_task_as_new_task(lite_usage_update_id)

    # Raise an exception
    # this will cause the task to be marked as 'Failed' and retried if there are retry attempts left
    raise Exception(error_message)
