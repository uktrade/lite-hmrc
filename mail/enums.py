# Temporary values, THESE ARE NOT CORRECT OR FINAL


class ReceptionStatusEnum:
    PENDING = "pending"
    ACCEPTED = "accepted"
    REPLY_PENDING = "reply_pending"
    REPLY_SENT = "reply_sent"

    choices = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (REPLY_PENDING, "Reply Pending"),
        (REPLY_SENT, "Reply Sent"),
    ]

    @classmethod
    def human_readable(cls, status):
        for k, v in cls.choices:
            if status == k:
                return v

    @classmethod
    def as_list(cls):
        return [{"status": choice[0]} for choice in cls.choices]


class ExtractTypeEnum:
    USAGE_UPDATE = "usage_update"
    LICENCE_UPDATE = "licence_update"

    choices = [(USAGE_UPDATE, "Usage update"), (LICENCE_UPDATE, "Licence Update")]

    email_keys = [
        ("usageData", USAGE_UPDATE),
    ]

    @classmethod
    def human_readable(cls, status):
        for k, v in cls.choices:
            if status == k:
                return v

    @classmethod
    def as_list(cls):
        return [{"extract_type": choice[0]} for choice in cls.choices]


class SourceEnum:
    SPIRE = "SPIRE"
    LITE = "LITE"

    choices = [(SPIRE, "SPIRE"), (LITE, "LITE")]

    @classmethod
    def as_list(cls):
        return [{"status": choice[0]} for choice in cls.choices]
