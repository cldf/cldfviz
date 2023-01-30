"""
Render CLDF Markdown to common markdown.

The CLDF Markdown text can be read
- from a parameter, via `--text-string`
- from a file, specified as `--text-file`
- from a media item associated with a CLDF dataset via `--media-id`.
"""
import re
import pathlib
import argparse

from clldutils.clilib import PathType, ParserError
from clldutils.markup import MarkdownImageLink
from pycldf.ext import discovery
from pycldf.ext.markdown import DatasetMapping
from pycldf.media import MediaTable
from termcolor import colored

from cldfviz.text import iter_templates, render, iter_cldfviz_links
from cldfviz.cli_util import add_testable
from . import map, tree


def get_dataset(locator):
    prefix = None
    if ':' in locator and not locator.startswith('http'):
        prefix, _, locator = locator.partition(':')
        if not DatasetMapping.key_pattern.fullmatch(prefix):
            raise ParserError('Invalid dataset prefix: {}'.format(prefix))  # pragma: no cover
    return prefix, locator


def register(parser):
    add_testable(parser)
    parser.add_argument('datasets', type=get_dataset, nargs='+')
    parser.add_argument('-l', '--list', help='list templates', default=False, action='store_true')
    parser.add_argument(
        '--media-id', default=None)
    parser.add_argument(
        '--text-string', default=None)
    parser.add_argument(
        '--text-file', type=PathType(type='file', must_exist=True), default=None)
    parser.add_argument('--templates', type=PathType(type='dir'), default=None)
    parser.add_argument('--output', type=PathType(type='file', must_exist=False), default=None)
    parser.add_argument('--download-dir', type=PathType(type='dir'), default=None)


def run(args):
    dss = {
        prefix: discovery.get_dataset(locator, args.download_dir)
        for prefix, locator in args.datasets}

    if args.list:
        print(colored('Available templates:', attrs=['bold', 'underline']) + '\n')
        for p, doc, vars in iter_templates():
            component, _, type_ = p.stem.partition('_')
            if (component == 'Source' and any(ds.sources for ds in dss.values())) or \
                    any(component in ds for ds in dss.values()):
                print(colored('{} {}'.format(component, type_), attrs=['bold']))
                print('Usage: ' + colored('[<label>]({}{}#cldf:{})'.format(
                    component,
                    '?var1&var2' if vars else '',
                    '__all__' if type_ == 'index' else '<object-ID>'), color='blue'))
                if vars:
                    print('Variables: ' + colored(', '.join(vars), color='blue'))
                if doc:
                    print(doc)
        return

    assert args.text_string or args.text_file or args.media_id
    text = args.text_string
    if (not text) and args.text_file:
        text = args.text_file.read_text(encoding='utf8')
    if not text:
        prefix, _, mid = args.media_id.partition(':')
        if not mid:
            mid, prefix = prefix, None
        for media in MediaTable(dss[prefix]):
            if media.id == mid:
                assert media.mimetype == 'text/markdown'
                # FIXME: Also check for conformsTo == CLDF Markdown column?
                text = media.read()
                break

    res = render(text, dss, args.templates)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(res, encoding='utf8')
        args.log.info('{} written'.format(args.output))

    create_images(
        args,
        res,
        dss,
        args.output.parent if args.output else
        (pathlib.Path('.') if args.text_string or (not args.text_file) else args.text_file.parent))

    def clean(ml):
        if re.match(r'cldfviz\.(map|tree)', ml.parsed_url.fragment):
            ml.update_url(query='')
        return ml

    res = MarkdownImageLink.replace(res, clean)

    if not args.output:
        print(res)


def create_images(oargs, md, dss, base_dir):
    for prefix, ds in dss.items():
        for ml in iter_cldfviz_links(md):
            if prefix is None or (ml.parsed_url.fragment.partition('-')[2] == prefix):
                p = base_dir.joinpath(ml.parsed_url.path)
                p.parent.mkdir(parents=True, exist_ok=True)
                args = [str(ds.tablegroup._fname)]
                kw = ml.parsed_url_query
                kw['output'] = [str(p)]
                for k, v in kw.items():
                    if v[0]:
                        args.extend(['--' + k, v[0]])
                    else:
                        args.append('--' + k)

                if 'tree' in ml.parsed_url.fragment:
                    cmd = tree
                elif 'map' in ml.parsed_url.fragment:
                    kw['format'] = [p.suffix[1:].lower()]
                    cmd = map
                else:
                    raise NotImplementedError(ml.parsed_url.fragment)  # pragma: no cover

                p = argparse.ArgumentParser()
                cmd.register(p)
                args = p.parse_args(args)
                if oargs.test:
                    args.test = True
                args.log = oargs.log
                cmd.run(args)
