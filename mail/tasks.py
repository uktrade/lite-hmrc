import logging
import os

from background_task import background
from django.conf import settings

from mail.libraries.routing_controller import check_and_route_emails

logger = logging.getLogger(__name__)


MANAGE_INBOX_TASK_QUEUE = "manage_inbox_queue"
NOTIFY_USERS_TASK_QUEUE = "notify_users_queue"
LICENCE_DATA_TASK_QUEUE = "licences_updates_queue"
TASK_BACK_OFF = 3600  # Time, in seconds, to wait before scheduling a new task (used after MAX_ATTEMPTS is reached)


# Manage Inbox
@background(queue=MANAGE_INBOX_TASK_QUEUE, schedule=0)
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


@background(queue="test_queue", schedule=0)
def emit_test_file():
    test_file_path = os.path.join(settings.BASE_DIR, ".background-tasks-is-ready")
    with open(test_file_path, "w") as test_file:
        test_file.write("OK")
