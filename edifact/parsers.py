from pathlib import Path

from django.conf import settings
from lark import Lark

GRAMMARS_PATH = Path(settings.BASE_DIR) / "edifact" / "grammars"


def generate_parser(grammar_file):
    full_file_path = GRAMMARS_PATH / grammar_file
    return Lark.open(full_file_path, start="file", parser="lalr")


usage_data_parser = generate_parser("usage_data.lark")
