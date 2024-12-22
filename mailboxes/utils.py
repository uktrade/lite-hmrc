import logging
from email.headerregistry import Address
from email.parser import BytesHeaderParser
from email.utils import parseaddr

logger = logging.getLogger(__name__)


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
