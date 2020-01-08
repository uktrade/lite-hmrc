from collections import namedtuple
import json

EmailMessageDto = namedtuple(
    "EmailMessageDto", "run_number, sender, receiver, subject, body, attachment"
)


def to_json(emailMsgDto: EmailMessageDto):
    """
    Converts EmailMessageDto to JSON str
    :param emailMsgDto: an object of type EmailMessageDto
    :return: str in JSON format
    """
    if emailMsgDto is None:
        raise TypeError("given EmailMessageDto is invalid!")

    if emailMsgDto.attachment is None or not isinstance(
        emailMsgDto.attachment[1], bytes
    ):
        raise TypeError("Invalid attribute 'attachment'")

    emailMsgDto.attachment[1] = emailMsgDto.attachment[1].decode("ascii")
    _dict = {
        "run_number": emailMsgDto.run_number,
        "sender": emailMsgDto.sender,
        "subject": emailMsgDto.subject,
        "receiver": emailMsgDto.receiver,
        "body": emailMsgDto.body,
        "attachment": {
            "name": emailMsgDto.attachment[0],
            "data": emailMsgDto.attachment[1],
        },
    }
    return json.dumps(_dict)
