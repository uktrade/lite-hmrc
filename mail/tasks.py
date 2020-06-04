import logging

from background_task import background
from background_task.models import Task
from django.db import transaction

from mail.models import LicencePayload


@background(schedule=0, repeat=Task.HOURLY//3, repeat_until=None)
def email_licences():
    with transaction.atomic():
        licences = LicencePayload.objects.filter(is_processed=False).select_for_update(nowait=True)

        email, licences_with_errors = prepare_email(licences)

        try:
            send_email(email)
        except Exception as exc:  # noqa
            logging.warning(f"An unexpected error occurred sending email -> {type(exc).__name__}: {exc}")

        licences.exclude(id__in=licences_with_errors).update(is_processed=True)


def prepare_email(licences):
    email = ""
    licences_with_errors = []

    for licence in licences:
        try:
            email += process_licence(licence)
        except Exception as exc: # noqa
            logging.warning(f"An unexpected error occurred when processing licence -> {type(exc).__name__}: {exc}")
            licences_with_errors += licence.id

    return email, licences_with_errors


def process_licence(licence):
    return str(licence)


def send_email(email):
    pass
