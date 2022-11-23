"""
Visualize a dataset's data model as entity-relationship diagram of the corresponding CLDF SQL.
"""
import shlex
import shutil
import pathlib
import tempfile
import subprocess
import webbrowser

import requests
from pycldf.ext.sql import get_database
from clldutils.clilib import PathType
from clldutils.path import ensure_cmd

from cldfviz.cli_util import add_testable


def download_file(url, target):
    with requests.get('https://github.com/' + url, stream=True) as r:
        r.raise_for_status()
        with target.open('wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return target


def register(parser):
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
        '--format',
        choices=['compact.dot', 'compact.svg', 'large.dot', 'large.svg'],
        help="`large` diagrams include all fields of an entity, `compact` ones do not. Diagrams "
             "are available in SVG or Graphviz' DOT language.",
        default='large.svg')
    parser.add_argument(
        'output',
        help='Path to which to write the diagram file.',
        type=PathType(must_exist=False))


def run(args):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for url, target in [
            ('xerial/sqlite-jdbc/releases/download/3.39.4.1/sqlite-jdbc-3.39.4.1.jar',
             'sqlite.jar'),
            ('schemaspy/schemaspy/releases/download/v6.1.0/schemaspy-6.1.0.jar',
             'schemaspy.jar'),
        ]:
            attrib = target.replace('.', '_')
            if not getattr(args, attrib):
                setattr(args, attrib, download_file(url, tmp / target))
        get_database(args.dataset_locator, download_dir=tmp, fname=tmp / 'db.sqlite')

        # Note: This exact way of calling java must be kept to keep tests working.
        subprocess.check_call(shlex.split(
            "{} -jar {} -t sqlite-xerial -db {} -sso -s public -dp {} -o {} -cat % -vizjs".format(
                args.java,
                args.schemaspy_jar,
                tmp / 'db.sqlite',
                tmp,
                args.sqlite_jar.parent,
            )))
        shutil.copy(
            tmp / 'diagrams' / 'summary' / 'relationships.real.{}'.format(args.format), args.output)

    args.log.info('ER diagram in format {} written to {}'.format(args.format, args.output))
    if not args.test:
        webbrowser.open(args.output.resolve().as_uri())  # pragma: no cover
