import logging

from background_task import background

from mail.libraries.routing_controller import check_and_route_emails

MANAGE_INBOX_TASK_QUEUE = "manage_inbox_queue"


@background(queue=MANAGE_INBOX_TASK_QUEUE, schedule=0)
def manage_inbox():
    logging.info("Polling inbox for updates")

    try:
        check_and_route_emails()
    except Exception as exc:  # noqa
        logging.error(f"An unexpected error occurred when polling inbox for updates -> {type(exc).__name__}: {exc}")
