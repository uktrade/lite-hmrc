import time
import urllib.parse
from smtplib import SMTPException
from typing import List, MutableMapping, Tuple
from contextlib import contextmanager
from django.core.cache import cache

from celery import Task, shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from mail.libraries.email_message_dto import EmailMessageDto
from rest_framework.status import HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED

from mail import requests as mail_requests
from mail.enums import ReceptionStatusEnum, SourceEnum
from mail.libraries.builders import build_email_message, build_email_rejected_licence_message, build_licence_data_mail
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.routing_controller import check_and_route_emails, send, update_mail
from mail.libraries.usage_data_decomposition import build_json_payload_from_data_blocks, split_edi_data_by_id
from mail.models import LicenceIdMapping, LicencePayload, Mail, UsageData
from mail.servers import smtp_send

logger = get_task_logger(__name__)


# Send Usage Figures to LITE API
def get_lite_api_url():
    """The URL for the licence usage callback, from the LITE_API_URL setting.

    If the configured URL has no path, use `/licences/hmrc-integration/`.
    """
    url = settings.LITE_API_URL
    components = urllib.parse.urlparse(url)

    if components.path in ("", "/"):
        components = components._replace(path="/licences/hmrc-integration/")
        url = urllib.parse.urlunparse(components)

    return url


def parse_response(response) -> Tuple[MutableMapping, List[str], List[str]]:
    response = response.json()
    licences = response["licences"]

    accepted_licences = [
        LicenceIdMapping.objects.get(lite_id=licence.get("id")).reference
        for licence in licences["accepted"]
        if licence.get("id")
    ]
    rejected_licences = [
        LicenceIdMapping.objects.get(lite_id=licence.get("id")).reference
        for licence in licences["rejected"]
        if licence.get("id")
    ]

    return response, accepted_licences, rejected_licences


def save_response(lite_usage_data: UsageData, accepted_licences, rejected_licences, response):
    lite_usage_data.lite_accepted_licences = accepted_licences
    lite_usage_data.lite_rejected_licences = rejected_licences
    lite_usage_data.lite_sent_at = timezone.now()
    lite_usage_data.lite_response = response

    if not lite_usage_data.has_spire_data:
        lite_usage_data.mail.status = ReceptionStatusEnum.REPLY_RECEIVED
        lite_usage_data.mail.save()

    lite_usage_data.save()


def _log_error(message, lite_usage_data_id):
    logger.error("Failed to send LITE UsageData [{%s}] to LITE API -> {%s}", lite_usage_data_id, message)


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180
LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes
CELERY_SEND_LICENCE_UPDATES_TASK_NAME = "mail.celery_tasks.send_licence_details_to_hmrc"
CELERY_MANAGE_INBOX_TASK_NAME = "mail.celery_tasks.manage_inbox"


# Notify Users of Rejected Mail
@shared_task(
    autoretry_for=(SMTPException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def notify_users_of_rejected_licences(mail_id, mail_response_subject):
    """If a reply is received with rejected licences this task notifies users of the rejection"""

    logger.info("Notifying users of rejected licences found in mail with subject %s", mail_response_subject)

    try:
        send_smtp_task.apply_async(kwargs={"mail_id": mail_id, "mail_response_subject": mail_response_subject})

    except SMTPException:
        logger.exception(
            "An unexpected error occurred when notifying users of rejected licences, Mail Id: %s, subject: %s",
            mail_id,
            mail_response_subject,
        )
        raise

    logger.info("Successfully notified users of rejected licences found in mail with subject %s", mail_response_subject)


class SendUsageDataBaseTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        message = (
            """
        Maximum attempts for send_licence_usage_figures_to_lite_api task exceeded - the task has failed and needs manual inspection.
        See mail.apps.MailConfig for a potential retry mechanism.

        Args: %s
        """
            % args
        )
        logger.error(message)


@shared_task(
    autoretry_for=(SMTPException,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def send_licence_details_to_hmrc():
    """Sends LITE issued licence details to HMRC"""

    logger.info(f"Sending LITE issued licence updates to HMRC")

    # We can only send next message after current message is fully processed.
    # Once it is fully processed it's status is marked as 'reply_sent'.
    #
    # So check if there are any in-progress messages before we proceed.
    if Mail.objects.exclude(status=ReceptionStatusEnum.REPLY_SENT).count():
        logger.info(
            "Currently we are either waiting for a reply or next one is ready to be sent out,\n"
            "so we cannot send this update yet and need to wait till that is completed."
        )
        return

    try:
        with transaction.atomic():
            # It is unlikely LicencePayload is being updated concurrently so even though it
            # blocking it is not going to be an issue to acquire lock
            licences = LicencePayload.objects.filter(is_processed=False).select_for_update()
            if not licences.exists():
                logger.info("There are currently no licences in the payload to send to HMRC")
                return

            mail = build_licence_data_mail(licences, SourceEnum.LITE)
            mail_dto = build_request_mail_message_dto(mail)
            licence_references = [licence.reference for licence in licences]
            logger.info(
                "Created licenceData mail with subject %s for licences [%s]", mail_dto.subject, licence_references
            )

            send(mail_dto, mail)

            # Mark the payloads as processed
            licences.update(is_processed=True)
            logger.info("Licence references [%s] marked as processed", licence_references)

    except SMTPException:
        logger.exception("An unexpected error occurred when sending LITE licence updates to HMRC -> %s")
        raise

    logger.info(
        "Successfully sent LITE issued licence (%s) updates in mail (%s) to HMRC", licence_references, mail.edi_filename
    )
    return True


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=True,
    base=SendUsageDataBaseTask,
)
def send_licence_usage_figures_to_lite_api(lite_usage_data_id):
    """Sends HMRC Usage figure updates to LITE"""

    logger.info("Preparing LITE UsageData [%s] for LITE API", lite_usage_data_id)

    try:
        lite_usage_data = UsageData.objects.get(id=lite_usage_data_id)
        licences = UsageData.licence_ids
    except UsageData.DoesNotExist:
        _log_error(
            f"LITE UsageData [{lite_usage_data_id}] does not exist.",
            lite_usage_data_id,
        )
        raise

    # Extract usage details of Licences issued from LITE
    _, data = split_edi_data_by_id(lite_usage_data.mail.edi_data, lite_usage_data)
    payload = build_json_payload_from_data_blocks(data)

    # We only process usage data for active licences so below error is unlikely
    if len(payload["licences"]) == 0:
        logger.error("Licences is blank in payload for %s", lite_usage_data, exc_info=True)
        return

    payload["usage_data_id"] = lite_usage_data_id
    lite_api_url = get_lite_api_url()
    logger.info("Sending LITE UsageData [%s] figures for Licences [%s] to LITE API", lite_usage_data_id, licences)

    try:
        lite_usage_data.lite_payload = payload
        lite_usage_data.save()

        response = mail_requests.put(
            lite_api_url,
            lite_usage_data.lite_payload,
            hawk_credentials=settings.HAWK_LITE_HMRC_INTEGRATION_CREDENTIALS,
            timeout=settings.LITE_API_REQUEST_TIMEOUT,
        )
    except Exception as exc:  # noqa
        _log_error(
            f"An unexpected error occurred when sending LITE UsageData [{lite_usage_data_id}] to LITE API -> "
            f"{type(exc).__name__}: {exc}",
            lite_usage_data_id,
        )
        raise

    if response.status_code not in [HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED]:
        _log_error(
            f"An unexpected response was received when sending LITE UsageData [{lite_usage_data_id}] to "
            f"LITE API -> status=[{response.status_code}], message=[{response.text}]",
            lite_usage_data_id,
        )
        raise

    if response.status_code == HTTP_207_MULTI_STATUS:
        try:
            response, accepted_licences, rejected_licences = parse_response(response)
        except Exception as exc:  # noqa
            _log_error(
                f"An unexpected error occurred when parsing the response for LITE UsageData "
                f"[{lite_usage_data_id}] -> {type(exc).__name__}: {exc}",
                lite_usage_data_id,
            )
            raise
        save_response(lite_usage_data, accepted_licences, rejected_licences, response)

    logger.info("Successfully sent LITE UsageData [%s] for licences [%s] to LITE API", lite_usage_data_id, licences)


# Scan Inbox for SPIRE and HMRC Emails
@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def manage_inbox():
    """Main task which scans inbox for SPIRE and HMRC emails"""

    logger.info("Polling inbox for updates")
    try:
        check_and_route_emails()
    except Exception as exc:  # noqa
        logger.error(
            "An unexpected error occurred when polling inbox for updates -> %s",
            type(exc).__name__,
            exc_info=True,
        )
        raise exc


@contextmanager
def cache_lock(lock_id):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists
    status = cache.add(lock_id, "lock_acquired", LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.delete(lock_id)


class SendSmtpFailureTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        mail_id = kwargs.get("mail_id", "Unknown")
        message = f"""
            Task failed permanently after all retries: send_smtp_task
            Mail ID: {mail_id}
            Exception: {exc}
            Args: {args}
            Kwargs: {kwargs}
            Task ID: {task_id}
            Exception Info: {einfo}
        """

        # Log the final failure message
        logger.critical(message)


@shared_task(bind=True, max_retries=MAX_ATTEMPTS, retry_backoff=3, base=SendSmtpFailureTask)
def send_smtp_task(self, mail_id=None, email_message_data=None, mail_response_subject=None):
    global_lock_id = "global_send_email_lock"

    # From task notify_users_of_rejected_licences
    if mail_id and mail_response_subject:
        message = build_email_rejected_licence_message(mail_id, mail_response_subject)
    else:
        deserialized_email_message_dto = EmailMessageDto(**email_message_data)
        message = build_email_message(deserialized_email_message_dto)

    with cache_lock(global_lock_id) as acquired:
        if acquired:
            logger.info("Global lock acquired, sending email")
            smtp_send(message)
            logger.info(f"Mail with Response Subject:{message['Subject']}; successfully sent.")

            # send_licence_details_to_hmrc and _collect_and_send -> update_mail were moved here if sucessfully sent
            if mail_id and email_message_data:
                mail = Mail.objects.filter(id=mail_id).first()
                update_mail(mail, deserialized_email_message_dto)
        else:
            logger.info("Another send_smtp_task is currently in progress, will retry...")
            raise self.retry()
