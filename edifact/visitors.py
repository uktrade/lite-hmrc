from lark import Discard, Token
from lark.visitors import Transformer, Visitor, v_args

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
