import logging
import os

from background_task import background
from django.conf import settings
logger = logging.getLogger(__name__)

@background(queue="test_queue", schedule=0)
def emit_test_file():
    test_file_path = os.path.join(settings.BASE_DIR, ".background-tasks-is-ready")
    with open(test_file_path, "w") as test_file:
        test_file.write("OK")
