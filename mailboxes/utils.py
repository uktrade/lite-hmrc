import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_message_id(pop3_connection, listing_msg):
    """
    Takes a single line from pop3 LIST command and extracts
    the message num. Uses the message number further to extract header information
    from which the actual Message-ID is extracted.

    :param pop3_connection: pop3 connection instance
    :param listing_msg: a line returned from the pop3.list command, e.g. b"2 5353"
    :return: the message-id and message_num extracted from the input, for the above example: b"2"
    """
    msg_num = listing_msg.split()[0]

    # retrieves the header information
    # 0 indicates the number of lines of message to be retrieved after the header
    msg_header = pop3_connection.top(msg_num, 0)

    spire_from_address = settings.SPIRE_FROM_ADDRESS.encode("utf-8")
    hmrc_dit_reply_address = settings.HMRC_TO_DIT_REPLY_ADDRESS.encode("utf-8")

    if spire_from_address not in msg_header[1] and hmrc_dit_reply_address not in msg_header[1]:
        logger.warning(
            "Found mail with message_num %s that is not from SPIRE (%s) or HMRC (%s), skipping ...",
            msg_num,
            spire_from_address,
            hmrc_dit_reply_address,
        )
        return None, msg_num

    message_id = None
    for index, item in enumerate(msg_header[1]):
        hdr_item_fields = item.decode("utf-8").split(" ")
        # message id is of the form b"Message-ID: <963d810e-c573-ef26-4ac0-151572b3524b@email-domail.co.uk>"  /PS-IGNORE

        if len(hdr_item_fields) == 2:
            if hdr_item_fields[0].lower() == "message-id:":
                value = hdr_item_fields[1].replace("<", "").replace(">", "")
                message_id = value.split("@")[0]
        elif len(hdr_item_fields) == 1:
            if hdr_item_fields[0].lower() == "message-id:":
                value = msg_header[1][index + 1].decode("utf-8")
                value = value.replace("<", "").replace(">", "").strip(" ")
                message_id = value.split("@")[0]

    logging.info("Extracted Message-Id as %s for the message_num %s", message_id, msg_num)
    return message_id, msg_num
