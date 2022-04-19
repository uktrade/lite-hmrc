LITE_HMRC_LICENCE_TYPE_MAPPING = {
    "siel": "SIE",
    "sicl": "SIE",
    "sitl": "SIE",
    "oiel": "OIE",
    "ogel": "OGE",
    "ogcl": "OGE",
    "ogtl": "OGE",
}


class LicenceActionEnum:
    INSERT = "insert"
    CANCEL = "cancel"
    UPDATE = "update"

    choices = [
        (INSERT, "Insert"),
        (CANCEL, "Cancel"),
        (UPDATE, "Update"),
    ]


class LicenceTypeEnum:
    SIEL = "siel"
    SICL = "sicl"
    SITL = "sitl"
    OIEL = "oiel"
    OICL = "oicl"
    OGEL = "ogel"
    OGCL = "ogcl"
    OGTL = "ogtl"

    choices = [
        (SIEL, "Standard Individual Export Licence"),
        (SICL, "Standard Individual Trade Control Licence"),
        (SITL, "Standard Individual Transhipment Licence"),
        (OIEL, "Open Individual Export Licence"),
        (OICL, "Open Individual Trade Control Licence"),
        (OGEL, "Open General Export Licence"),
        (OGCL, "Open General Trade Control Licence"),
        (OGTL, "Open General Transhipment Licence"),
    ]

    STANDARD_LICENCES = [SIEL, SICL, SITL]
    OPEN_LICENCES = [OIEL, OICL]
    OPEN_GENERAL_LICENCES = [OGEL, OGCL, OGTL]


class ReplyStatusEnum:
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"

    choices = [
        (ACCEPTED, "Accepted"),
        (REJECTED, "Rejected"),
        (PENDING, "Pending"),
    ]


class ReceptionStatusEnum:
    PENDING = "pending"
    REPLY_PENDING = "reply_pending"
    REPLY_RECEIVED = "reply_received"
    REPLY_SENT = "reply_sent"

    choices = [
        (PENDING, "Pending"),
        (REPLY_PENDING, "Reply Pending"),
        (REPLY_RECEIVED, "Reply Received"),
        (REPLY_SENT, "Reply Sent"),
    ]


class ExtractTypeEnum:
    USAGE_DATA = "usage_data"
    USAGE_REPLY = "usage_reply"
    LICENCE_REPLY = "licence_reply"
    LICENCE_DATA = "licence_data"

    choices = [
        (USAGE_DATA, "Usage Data"),
        (USAGE_REPLY, "Usage Reply"),
        (LICENCE_REPLY, "Licence Reply"),
        (LICENCE_DATA, "Licence Data"),
    ]

    email_keys = [
        ("usageData", USAGE_DATA),
        ("usageReply", USAGE_REPLY),
        ("licenceReply", LICENCE_REPLY),
        ("licenceData", LICENCE_DATA),
    ]


class SourceEnum:
    SPIRE = "SPIRE"
    LITE = "LITE"
    HMRC = "HMRC"

    choices = [
        (SPIRE, "SPIRE"),
        (LITE, "LITE"),
        (HMRC, "HMRC"),
    ]


class UnitMapping:
    number = 30
    gram = 21
    kilogram = 23
    meters_squared = 45
    meters = 57
    litre = 94
    meters_cubed = 2
    intangible = 30

    choices = [
        (number, "NAR"),
        (gram, "GRM"),
        (kilogram, "KGM"),
        (meters_squared, "MTK"),
        (meters, "MTR"),
        (litre, "LTR"),
        (meters_cubed, "MTQ"),
        (intangible, "ITG"),
    ]

    @classmethod
    def convert(cls, unit) -> int:
        for k, v in cls.choices:
            if unit == v:
                return k


class MailReadStatuses:
    READ = "READ"
    UNREAD = "UNREAD"
    UNPROCESSABLE = "UNPROCESSABLE"

    choices = [(READ, "Read"), (UNREAD, "Unread"), (UNPROCESSABLE, "Unprocessable")]


class LicenceStatusEnum:
    OPEN = "open"
    EXHAUST = "exhaust"
    SURRENDER = "surrender"
    EXPIRE = "expire"
    CANCEL = "cancel"

    choices = [(OPEN, "open"), (EXHAUST, "exhaust"), (SURRENDER, "surrender"), (EXPIRE, "expire"), (CANCEL, "cancel")]
