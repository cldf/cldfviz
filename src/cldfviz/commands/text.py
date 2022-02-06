"""

"""
from clldutils.clilib import PathType
from pycldf.cli_util import get_dataset, add_dataset
from termcolor import colored

from cldfviz.text import *


def register(parser):
    add_dataset(parser)
    parser.add_argument('-l', '--list', help='list templates', default=False, action='store_true')
    parser.add_argument('--text-string', default=None)
    parser.add_argument('--text-file', type=PathType(type='file', must_exist=True), default=None)
    parser.add_argument('--templates', type=PathType(type='dir'), default=None)


def run(args):
    ds = get_dataset(args)

    if args.list:
        print(colored('Available templates:', attrs=['bold', 'underline']) + '\n')
        for p, doc, vars in iter_templates():
            component, _, type_ = p.stem.partition('_')
            if (component == 'Source' and ds.sources) or component in ds:
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

    assert args.text_string or args.text_file
    print(render(
        args.text_string or args.text_file.read_text(encoding='utf8'), ds, args.templates))
