import datetime
from dataclasses import dataclass


@dataclass
class EmailMessageDto:
    run_number: str
    sender: str
    receiver: str
    date: datetime.datetime
    subject: str
    body: str
    attachment: list
    raw_data: str


@dataclass
class UsageData(EmailMessageDto):
    pass


@dataclass
class UsageReply(EmailMessageDto):
    pass


@dataclass
class LicenceReply(EmailMessageDto):
    pass


@dataclass
class LicenceData(EmailMessageDto):
    pass


@dataclass
class HmrcEmailMessageDto:
    run_number: str
    message_id: str
    sender: str
    receiver: str
    subject: str
    body: str
    attachment: list
    raw_data: str
