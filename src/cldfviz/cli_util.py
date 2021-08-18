import inspect
import pathlib
import argparse
import importlib

from clldutils.text import split_text_with_context
from clldutils import path


def add_testable(parser):
    parser.add_argument('--test', action='store_true', default=False, help=argparse.SUPPRESS)


def add_listvalued(parser, *args, **kw):
    kw.setdefault('default', [])
    kw.setdefault('type', lambda s: split_text_with_context(s, ',', brackets={'{': '}'}))
    parser.add_argument(*args, **kw)


def import_module(dotted_name_or_path):
    p = pathlib.Path(dotted_name_or_path)
    if p.exists():
        return path.import_module(p.resolve())
    return importlib.import_module(dotted_name_or_path)  # pragma: no cover


def import_subclass(dotted_name_or_path, cls):
    mod = import_module(dotted_name_or_path)
    for _, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, cls) and not obj.__subclasses__():
            return obj
