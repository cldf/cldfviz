import re
import json
import inspect
import pathlib
import argparse

from clldutils.text import split_text_with_context
from clldutils import path


def add_language_filter(parser):
    parser.add_argument(
        '--language-filters',
        default=None,
        help="JSON object specifying filter criteria for included languages. Keys must be "
             "names of columns in the datasets' LanguageTable, values are interpreted as "
             "regular expressions if they are strings or as literal values otherwise and will "
             "be matched against the value of a language for the specified column. Only "
             "languages matching all criteria are included in the analysis.",
    )


def get_language_filter(args):
    if args.language_filters is None:
        return

    def language_filter(lg):
        for k, v in json.loads(args.language_filters).items():
            if isinstance(v, str):
                if not re.search(v, lg.data[k] or ''):
                    return False
            else:
                if lg.data[k] != v:
                    return False
        return True
    return language_filter


def add_testable(parser):
    parser.add_argument('--test', action='store_true', default=False, help=argparse.SUPPRESS)


def add_listvalued(parser, *args, **kw):
    kw.setdefault('default', [])
    kw.setdefault('type', lambda s: split_text_with_context(s, ',', brackets={'{': '}'}))
    parser.add_argument(*args, **kw)


def import_module(dotted_name_or_path):
    import importlib
    p = pathlib.Path(dotted_name_or_path)
    if p.exists():
        return path.import_module(p.resolve())
    return importlib.import_module(dotted_name_or_path)


def import_subclass(dotted_name_or_path, cls):
    mod = import_module(dotted_name_or_path)
    for _, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, cls) and not obj.__subclasses__():
            return obj
