"""
Visualize a dataset's data model as entity-relationship diagram of the corresponding CLDF SQL.
"""
import shutil
import pathlib
import argparse
import tempfile
import subprocess

import requests
from pycldf.ext.sql import get_database
from clldutils.clilib import PathType
from clldutils.path import ensure_cmd

from cldfviz.cli_util import add_testable, add_open, write_output


def _download_file(url: str, target: pathlib.Path) -> pathlib.Path:
    with requests.get('https://github.com/' + url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with target.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return target


def _copy_file(dest: pathlib.Path, target: pathlib.Path) -> pathlib.Path:
    shutil.copy(dest, target)
    return target


def register(parser: argparse.ArgumentParser):  # pylint: disable=C0116
    add_testable(parser)
    parser.add_argument('dataset_locator')
    parser.add_argument(
        '--java',
        type=ensure_cmd,
        help='Path to the Java runtime.',
        default='java')
    parser.add_argument(
        '--schemaspy-jar',
        type=PathType(type='file'),
        help='Path to a suitable version of the SchemaSpy jar file.',
        default=None)
    parser.add_argument(
        '--sqlite-jar',
        type=PathType(type='file'),
        help='Path to a suitable version of the Xerial SQLite JDBC Driver jar file.',
        default=None)
    parser.add_argument(
        '--db',
        type=PathType(type='file'),
        help='Path to CLDF SQLite file. This provides a shortcut, bypassing SQLite creation.',
        default=None,
    )
    parser.add_argument(
        '--format',
        choices=['compact.dot', 'compact.svg', 'large.dot', 'large.svg'],
        help="`large` diagrams include all fields of an entity, `compact` ones do not. Diagrams "
             "are available in SVG or Graphviz' DOT language.",
        default='large.svg')
    add_open(parser)


def run(args):  # pylint: disable=C0116
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for url, target in [
            ('xerial/sqlite-jdbc/releases/download/3.39.4.1/sqlite-jdbc-3.39.4.1.jar',
             'sqlite.jar'),
            ('schemaspy/schemaspy/releases/download/v6.2.4/schemaspy-6.2.4.jar',
             'schemaspy.jar'),
        ]:
            attrib = target.replace('.', '_')
            if not getattr(args, attrib):
                setattr(args, attrib, _download_file(url, tmp / target))
            else:
                setattr(args, attrib, _copy_file(getattr(args, attrib), tmp / target))
        if args.db:
            _copy_file(args.db, tmp / 'db.sqlite')  # pragma: no cover
        else:
            get_database(args.dataset_locator, download_dir=tmp, fname=tmp / 'db.sqlite')

        # Note: This exact way of calling java must be kept to keep tests working.
        out = subprocess.check_output([
            args.java, "-jar", args.schemaspy_jar,
            "-t", "sqlite-xerial",
            "-db", tmp / 'db.sqlite',
            "-sso", "-s", "public",
            "-dp", tmp,
            "-o", args.sqlite_jar.parent,
            "-cat", "%", "-vizjs"
        ])
        for line in out.decode('utf8').split('\n'):  # pragma: no cover
            args.log.debug(line)
        res = tmp\
            .joinpath('diagrams', 'summary', f'relationships.real.{args.format}')\
            .read_text(encoding='utf8')

    write_output(args, res)
