import logging
from email.headerregistry import Address
from email.parser import BytesHeaderParser
from email.utils import parseaddr

from django.conf import settings

logger = logging.getLogger(__name__)


def get_message_header(pop3_connection, listing_msg):
    msg_num = listing_msg.split()[0]

    # retrieves the header information
    # 0 indicates the number of lines of message to be retrieved after the header
    _, msg_header, _ = pop3_connection.top(msg_num, 0)

    parser = BytesHeaderParser()
    header = parser.parsebytes(b"".join(msg_header))

    return header, msg_num


def get_message_id(msg_header, msg_num):
    spire_from_address = settings.SPIRE_FROM_ADDRESS.encode("utf-8")
    hmrc_dit_reply_address = settings.HMRC_TO_DIT_REPLY_ADDRESS.encode("utf-8")

    if spire_from_address not in msg_header.as_bytes() and hmrc_dit_reply_address not in msg_header.as_bytes():
        logger.warning(
            "Found mail with message_num %s that is not from SPIRE (%s) or HMRC (%s), skipping ...",
            msg_num,
            spire_from_address,
            hmrc_dit_reply_address,
        )
        return None, msg_num

    _, message_id = parseaddr(str(msg_header["message-id"]))
    message_id = Address(addr_spec=message_id).username

    logging.info("Extracted Message-Id as %s for the message_num %s", message_id, msg_num)
    return message_id, msg_num
