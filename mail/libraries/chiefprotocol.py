# The CHIEF message protocol(s). "TIS" means technical interface specification.
# DES235: TIS LINE FILE DIALOGUE AND SYNTAX
# DES236: TIS – Licence Maintenance and Usage
#
# TIS spec jargon:
# - M: mandatory (required)
# - O: optional
# - C: conditional
# - A: absent (must not be present)

import datetime
from typing import Any, Tuple, Optional, Sequence


class LicenceDataMessage:
    def __init__(self, licences: Optional[Any] = None):
        self._lines = []
        self.licences = licences or []

    def finalize(self, src_system: str, dest_system: str, time_stamp: datetime.datetime, run_number: int) -> str:
        lines = [self._header(src_system, dest_system, time_stamp, run_number)]

        for licence in self.licences:
            lines.extend(self._licence(licence))

        num_transactions = sum(row[0] == "licence" for row in lines)
        lines.append(self._trailer(num_transactions))

        return format_lines(lines)

    def _header(self, src_system: str, dest_system: str, time_stamp: datetime.datetime, run_number: int) -> Tuple:
        # Setting this to Y will override the hmrc run number with the run number in this file.
        # This is usually set to N in almost all cases
        reset_run_number_indicator = "N"

        return (
            "fileHeader",
            src_system,
            dest_system,
            "licenceData",
            time_stamp.strftime("%Y%m%d%H%M"),  # YYYYMMDDhhmm
            run_number,
            reset_run_number_indicator,
        )

    def _trailer(self, num_transactions: int):
        # File trailer includes the number of licences, but +1 for each "update"
        # because this code represents those as "cancel" followed by "insert".
        return ("fileTrailer", num_transactions)

    def _licence(self, licence: Any):
        return [("end", "licence")]


def resolve_line_numbers(lines: Sequence[tuple]) -> list:
    """Add line numbers for a CHIEF message.

    For "end" lines, we keep track of the number of lines since the matching
    opening line type, and add that number to the end of the line.
    """
    starts = {}
    result = []

    for lineno, line in enumerate(lines, start=1):
        line_type = line[0]
        # Track the most recent line number for each line type.
        starts[line_type] = lineno

        if line_type == "end":
            # End lines are like ("end", <start-type>). Find the number of
            # lines since the <start-type> line, add that to the end line
            # like ("end", <start-type>, <distance>).
            start_type = line[1]
            distance = (lineno - starts[start_type]) + 1
            line += (distance,)

        # Prepend every line with the line number.
        line = (lineno,) + line
        result.append(line)

    return result


def format_line(line: Tuple) -> str:
    """Format a line, with `None` values as the empty string."""
    field_sep = "\\"  # A single back-slash character.

    return field_sep.join("" if v is None else str(v) for v in line)


def format_lines(lines: Sequence[tuple]) -> str:
    """Format the sequence of line tuples as 1 complete string."""
    lines = resolve_line_numbers(lines)
    formatted_lines = [format_line(line) for line in lines]
    line_sep = "\n"

    return line_sep.join(formatted_lines) + line_sep
