import time
import urllib.parse

from smtplib import SMTPException
from typing import List, MutableMapping, Tuple

from celery import Task, shared_task
from celery.utils.log import get_task_logger
from contextlib import contextmanager
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.status import HTTP_207_MULTI_STATUS, HTTP_208_ALREADY_REPORTED

from mail import requests as mail_requests
from mail.enums import ReceptionStatusEnum, SourceEnum
from mail.libraries.builders import build_email_message, build_licence_data_mail, build_licence_rejected_email_message
from mail.libraries.data_processors import build_request_mail_message_dto
from mail.libraries.email_message_dto import EmailMessageDto
from mail.libraries.lite_to_edifact_converter import EdifactValidationError
from mail.libraries.routing_controller import check_and_route_emails, update_mail
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
LOCK_EXPIRE = 60 * 10  # secs (10 min)
CELERY_SEND_LICENCE_UPDATES_TASK_NAME = "mail.celery_tasks.send_licence_details_to_hmrc"
CELERY_MANAGE_INBOX_TASK_NAME = "mail.celery_tasks.manage_inbox"


class SMTPConnectionBusy(SMTPException):
    pass


@contextmanager
def cache_lock(lock_id):
    timeout_at = time.monotonic() + LOCK_EXPIRE - 3
    # cache.add fails if the key already exists.
    # return True if lock is acquired, False otherwise
    status = cache.add(lock_id, "lock_acquired", LOCK_EXPIRE)
    try:
        yield status
    finally:
        if time.monotonic() < timeout_at and status:
            cache.delete(lock_id)


class SendEmailBaseTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        message = """
        Maximum attempts for send_email_task exceeded - the task has failed and needs manual inspection.
        Args: %s
        """ % (
            args,
        )

        # Log the final failure message
        logger.critical(message)


@shared_task(
    autoretry_for=(SMTPConnectionBusy, SMTPException),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
    base=SendEmailBaseTask,
)
def send_email_task(message):
    """
    Main purpose of this task is to send email.

    We use SMTP to send emails. As we process messages we have a requirement to
    send emails from multiple places, because of this we may open multiple SMTP connections.
    This results in error if the number of concurrent connections exceed maximum allowed value.

    To manage this reliably we are restricting access to this shared resource using a lock.
    This is achieved by deferring all email sending functionality to this task.
    Before sending email it first tries to acquire a lock.
      - If there are no active connections then it acquires lock and sends email.
        In some cases we need to update state which is handled in subtask linked to this task.
      - If there is active connection (lock acquisition fails) then it raises an exception
        which triggers a retry.
        If all retries fail then manual intervention may be required (unlikely)
    """

    global_lock_id = "global_send_email_lock"

    with cache_lock(global_lock_id) as lock_acquired:
        if not lock_acquired:
            logger.exception("Another SMTP connection is active, will be retried after backing off")
            raise SMTPConnectionBusy()

        logger.info("Lock acquired, proceeding to send email")

        try:
            smtp_send(message)
        except SMTPException:
            logger.exception("An unexpected error occurred when sending email -> %s")
            raise

        logger.info("Email sent successfully")


# Notify Users of Rejected Mail
@shared_task
def notify_users_of_rejected_licences(mail_id, mail_response_subject):
    """If a reply is received with rejected licences this task notifies users of the rejection"""

    logger.info("Notifying users of rejected licences found in mail with subject %s", mail_response_subject)

    message_dto = EmailMessageDto(
        run_number=None,
        sender=settings.EMAIL_USER,
        receiver=",".join(settings.NOTIFY_USERS),
        date=timezone.now(),
        subject="Licence rejected by HMRC",
        body=f"Mail (Id: {mail_id}) with subject {mail_response_subject} has rejected licences",
        attachment=None,
        raw_data=None,
    )
    message = build_licence_rejected_email_message(message_dto)

    send_email_task.apply_async(
        args=(message,),
        serializer="pickle",
    )

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


@shared_task
def finalise_sending_spire_licence_details(mail_id, message_dto):
    """Subtask that performs follow-up tasks after completing the primary purpose
    of sending an email"""

    mail = Mail.objects.get(id=mail_id)
    message_dto = EmailMessageDto(*message_dto)

    update_mail(mail, message_dto)


@shared_task
def finalise_sending_lite_licence_details(mail_id, message_dto, licence_payload_ids):
    """Subtask that performs follow-up tasks after completing the primary purpose
    of sending an email"""

    mail = Mail.objects.get(id=mail_id)
    message_dto = EmailMessageDto(*message_dto)

    update_mail(mail, message_dto)

    licence_payloads = LicencePayload.objects.filter(id__in=licence_payload_ids, is_processed=False)
    references = [item.reference for item in licence_payloads]

    licence_payloads.update(is_processed=True)

    logger.info("Licence payloads with references %s marked as processed", references)


class SendLicenceDetailsBaseTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        message = """
        Maximum attempts for send_licence_details_to_hmrc task exceeded - the task has failed and needs manual inspection.

        Args: %s
        """ % (
            args,
        )
        logger.error(message)


@shared_task(
    autoretry_for=(EdifactValidationError,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
    base=SendLicenceDetailsBaseTask,
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

            message = build_email_message(mail_dto)
            licence_payload_ids = [str(licence.id) for licence in licences]
            send_email_task.apply_async(
                args=(message,),
                serializer="pickle",
                link=finalise_sending_lite_licence_details.si(mail.id, mail_dto, licence_payload_ids),
            )

    except EdifactValidationError:
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
