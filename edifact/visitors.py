import itertools

from lark import Discard, Token
from lark.visitors import Interpreter, Transformer, v_args

from mail.enums import LicenceStatusEnum
from mail.libraries.helpers import get_good_id, get_licence_id, get_licence_status
from mail.libraries.usage_data_decomposition import id_owner
from mail.models import TransactionMapping


def flatten(lists):
    if not isinstance(lists, (list, tuple)):
        return [lists]
    return list(itertools.chain.from_iterable(flatten(l) for l in lists))


class RunNumberUpdater(Transformer):
    def __init__(self, spire_run_number, *args, **kwargs):
        self.spire_run_number = spire_run_number
        super().__init__(*args, **kwargs)

    def RUN_NUMBER(self, token):
        return Token("RUN_NUMBER", str(self.spire_run_number))


@v_args(tree=True)
class SourceSplitter(Transformer):
    def __init__(self, desired_source, *args, **kwargs):
        self.desired_source = desired_source
        super().__init__(*args, **kwargs)

    def licence_usage_transaction(self, tree):
        licence_usage_transaction_header = tree.children[0]
        licence_ref = licence_usage_transaction_header.children[2]

        source = id_owner(licence_ref)
        if not source == self.desired_source:
            return Discard

        return tree

    def file(self, tree):
        tree = tree.copy()
        transaction_count = len(list(tree.find_data("licence_usage_transaction")))
        file_trailer = tree.children[-1]
        file_trailer.children[0] = Token("LICENCE_USAGE_COUNT", str(transaction_count))
        return tree


class TransactionMapper(Interpreter):
    def __init__(self, usage_data, *args, **kwargs):
        self.usage_data = usage_data
        super().__init__(*args, **kwargs)

    def licence_usage_transaction(self, tree):
        (transaction_ref, licence_ref), line_num, _ = self.visit_children(tree)
        TransactionMapping.objects.get_or_create(
            line_number=line_num,
            usage_data=self.usage_data,
            licence_reference=licence_ref,
            usage_transaction=transaction_ref,
        )

    def licence_usage_transaction_header(self, tree):
        transaction_ref = str(tree.children[0])
        licence_ref = str(tree.children[2])

        return transaction_ref, licence_ref

    def licence_line(self, tree):
        values = self.visit_children(tree)

        return values[0]

    def licence_line_header(self, tree):
        line_num, *_ = tree.children

        return line_num[0]


@v_args(inline=True)
class JsonPayload(Transformer):
    def _stringify(self, value):
        if value is None:
            return ""
        return str(value)

    def file(self, *licence_usage_transactions):
        return {"licences": list(licence_usage_transactions)}

    def file_header(self, *args):
        return Discard

    def file_trailer(self, *args):
        return Discard

    def licence_usage_transaction(self, licence_payload, *licence_lines):
        if not licence_payload:
            return Discard

        licence_reference = licence_payload.pop("licence_reference")
        licence_payload["goods"] = []
        for licence_line in flatten(licence_lines):
            line_num = licence_line.pop("line_num")
            licence_line = {
                **licence_line,
                "id": get_good_id(line_num, licence_reference),
            }
            licence_payload["goods"].append(licence_line)

        return licence_payload

    def licence_usage_transaction_header(self, action, licence_reference, licence_status_code, completion_date=""):
        action = get_licence_status(licence_status_code)
        if not action == LicenceStatusEnum.OPEN:
            return None

        licence_id = get_licence_id(str(licence_reference))
        licence_payload = {
            "action": self._stringify(action),
            "completion_date": self._stringify(completion_date),
            "id": licence_id,
            "licence_reference": licence_reference,
        }

        return licence_payload

    def TRANSACTION_REF(self, *args):
        return Discard

    def licence_usage_transaction_trailer(self, *args):
        return Discard

    def licence_line(self, *licence_line_headers):
        return licence_line_headers

    def licence_line_header(self, line_num, quantity_used, value_used, currency=""):
        good_payload = {
            "line_num": self._stringify(line_num),
            "usage": self._stringify(quantity_used),
            "value": self._stringify(value_used),
            "currency": self._stringify(currency),
        }

        return good_payload

    def licence_usage(self, *args):
        return Discard

    def licence_line_trailer(self, *args):
        return Discard


@v_args(inline=True)
class Edifact(Transformer):
    def _to_line(self, fields):
        return "\\".join(field if field else "" for field in fields)

    def file(self, *args):
        lines = flatten(args)
        lines = [f"{line_number}\\{line}" for line_number, line in enumerate(lines, start=1)]
        lines = "\n".join(lines)
        return lines

    def file_header(self, *args):
        return self._to_line(["fileHeader", *args])

    def file_trailer(self, *args):
        return self._to_line(["fileTrailer", *args])

    def licence_usage_transaction_header(self, *args):
        return self._to_line(["licenceUsage", *args])

    def licence_usage_transaction(self, *args):
        return flatten(args)

    def licence_usage_transaction_trailer(self, *args):
        return self._to_line(["end", "licenceUsage", *args])

    def licence_line_header(self, *args):
        return self._to_line(["line", *args])

    def licence_line(self, *args):
        return flatten(args)

    def licence_line_trailer(self, *args):
        return self._to_line(["end", "line", *args])

    def licence_usage(self, *args):
        return self._to_line(["usage", *args])
