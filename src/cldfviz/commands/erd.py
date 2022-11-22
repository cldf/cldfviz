"""

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
    parser.add_argument('dataset_locator')
    add_testable(parser)
    parser.add_argument('--java', type=ensure_cmd, default='java')
    parser.add_argument('--schemaspy-jar', type=PathType(type='file'), default=None)
    parser.add_argument('--sqlite-jar', type=PathType(type='file'), default=None)
    parser.add_argument(
        '--format',
        choices=['compact.dot', 'compact.svg', 'large.dot', 'large.svg'],
        default='large.svg')
    parser.add_argument('output', type=PathType(must_exist=False))


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

        subprocess.check_call(shlex.split(
            "{} -jar {} -t sqlite-xerial -db {} -sso -s public -o {} -dp {} -cat % -vizjs".format(
                args.java,
                args.schemaspy_jar,
                tmp / 'db.sqlite',
                tmp,
                args.sqlite_jar.parent,
            )))
        shutil.copy(
            tmp / 'diagrams' / 'summary' / 'relationships.real.{}'.format(args.format), args.output)

    webbrowser.open(args.output.resolve().as_uri())
