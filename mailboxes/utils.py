import logging
from email.headerregistry import Address
from email.parser import BytesHeaderParser
from email.utils import parseaddr

from django.conf import settings

logger = logging.getLogger(__name__)


def get_message_number(listing_message):
    listing_msg = listing_message.decode(settings.DEFAULT_ENCODING)
    msg_num, _, _ = listing_msg.partition(" ")
    return msg_num


def get_message_header(pop3_connection, msg_num):
    # retrieves the header information
    # 0 indicates the number of lines of message to be retrieved after the header
    _, msg_header, _ = pop3_connection.top(msg_num, 0)

    parser = BytesHeaderParser()
    header = parser.parsebytes(b"".join(msg_header))

    return header


def get_message_id(msg_header):
    _, message_id = parseaddr(str(msg_header["message-id"]))
    message_id = Address(addr_spec=message_id).username
    return message_id


def is_from_valid_sender(msg_header, valid_addresses):
    _, from_address = parseaddr(str(msg_header["From"]))
    valid_addresses = [address.replace("From: ", "") for address in valid_addresses]

    return from_address in valid_addresses
