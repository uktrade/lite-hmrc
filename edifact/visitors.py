from lark import Discard, Token
from lark.visitors import Transformer, Visitor, v_args

from mail.enums import LicenceStatusEnum
from mail.libraries.helpers import get_good_id, get_licence_id, get_licence_status
from mail.libraries.usage_data_decomposition import id_owner
from mail.models import TransactionMapping


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
        licence_usage_transaction_header, _, _ = tree.children
        _, licence_ref, _ = licence_usage_transaction_header.children

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


class TransactionMapper(Visitor):
    def __init__(self, usage_data, *args, **kwargs):
        self.usage_data = usage_data
        super().__init__(*args, **kwargs)

    def visit(self, *args, **kwargs):
        raise NotImplementedError("This should only be called topdown")

    def licence_usage_transaction_header(self, tree):
        self.transaction_ref, self.licence_ref, _ = tree.children

    def licence_line_header(self, tree):
        line_num, *_ = tree.children

        TransactionMapping.objects.get_or_create(
            line_number=line_num,
            usage_data=self.usage_data,
            licence_reference=self.licence_ref,
            usage_transaction=self.transaction_ref,
        )


@v_args(inline=True)
class JsonPayload(Transformer):
    def file(self, *licence_usage_transactions):
        return {"licences": list(licence_usage_transactions)}

    def file_header(self, *args):
        return Discard

    def file_trailer(self, *args):
        return Discard

    def licence_usage_transaction(self, licence_usage_transaction_header, licence_lines):
        licence_reference, licence_status_code, completion_date = licence_usage_transaction_header

        action = get_licence_status(str(licence_status_code))
        if not action == LicenceStatusEnum.OPEN:
            return Discard

        licence_id = get_licence_id(str(licence_reference))
        licence_payload = {
            "action": str(action),
            "completion_date": completion_date,
            "id": licence_id,
        }
        licence_payload["goods"] = []
        for licence_line in licence_lines:
            line_num = licence_line.pop("line_num")
            licence_line = {
                **licence_line,
                "id": get_good_id(line_num, licence_reference),
            }
            licence_payload["goods"].append(licence_line)
        return licence_payload

    def licence_usage_transaction_header(self, licence_reference, licence_status_code, completion_date=""):
        return licence_reference, licence_status_code, completion_date

    def TRANSACTION_REF(self, *args):
        return Discard

    def licence_usage_transaction_trailer(self, *args):
        return Discard

    def licence_line(self, *licence_line_headers):
        return licence_line_headers

    def licence_line_header(self, line_num, quantity_used, value_used, currency=""):
        good_payload = {
            "line_num": str(line_num),
            "usage": str(quantity_used),
            "value": str(value_used),
            "currency": str(currency),
        }

        return good_payload

    def licence_usage(self, *args):
        return Discard

    def licence_line_trailer(self, *args):
        return Discard
