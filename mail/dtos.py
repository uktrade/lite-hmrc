from collections import namedtuple
import logging

log = logging.getLogger(__name__)

EmailMessageDto = namedtuple("EmailMessageDto", "run_number, sender, subject, body, attachment")
