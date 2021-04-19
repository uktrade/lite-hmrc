from mail.enums import LicenceActionEnum, LITE_HMRC_LICENCE_TYPE_MAPPING


class FileHeader:
    def __init__(self, data_identifier, run_number, time_stamp):
        self.data_identifier = data_identifier
        self.run_number = run_number
        self.time_stamp = time_stamp

    def __str__(self):
        return "\\".join(
            ["1", "fileHeader", "SPIRE", "CHIEF", self.data_identifier, self.time_stamp, str(self.run_number), "Y"]
        )


class LicenceTransactionHeader:
    def __init__(self, line_no, licence, action, old_payload=None):
        licence_payload = licence.data
        self.line_no = line_no
        self.tx_reference = licence.reference.split("/", 1)[1].replace("/", "")
        self.action = action
        self.licence_type = LITE_HMRC_LICENCE_TYPE_MAPPING.get(licence_payload.get("type"), "INVALID_TYPE")
        if old_payload:
            self.licence_reference = licence.old_reference
            self.start_date = old_payload.get("start_date").replace("-", "")
            self.end_date = old_payload.get("end_date").replace("-", "")
        else:
            self.licence_reference = licence.reference
            self.start_date = licence_payload.get("start_date").replace("-", "")
            self.end_date = licence_payload.get("end_date").replace("-", "")

    def __str__(self):
        new_line = "\n" if self.line_no > 1 else ""
        return new_line + "\\".join(
            [
                str(self.line_no),
                "licence",
                self.tx_reference,
                self.action,
                self.licence_reference,
                self.licence_type,
                "E",
                self.start_date,
                self.end_date,
            ]
        )
