from collections import namedtuple


EmailMessageDto = namedtuple(
    "EmailMessageDto", "run_number, sender, subject, body, attachment"
)
