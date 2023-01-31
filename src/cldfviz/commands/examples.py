"""
Build an HTML file to display examples in a CLDF dataset.
"""
from pycldf.cli_util import add_dataset, get_dataset
from pycldf.sources import Sources
from clldutils.misc import nfilter

from cldfviz.cli_util import (
    add_open, write_output, add_jinja_template, add_language_filter, get_filtered_languages,
)
from cldfviz.media import get_objects_and_media, get_media_url
from cldfviz.template import render_jinja_template, TEMPLATE_DIR


def register(parser):
    add_dataset(parser)
    add_language_filter(parser)
    mod = __name__.split('.')[-1]
    add_jinja_template(parser, TEMPLATE_DIR / mod / '{}.html'.format(mod))
    add_open(parser)


def run(args):
    ds = get_dataset(args)
    valid_langs = get_filtered_languages(args, ds)

    examples = []
    for example, media in get_objects_and_media(
            ds, 'ExampleTable', 'exampleReference',
            filter=lambda e: (valid_langs is None) or e.cldf.languageReference in valid_langs):
        examples.append((
            example,
            nfilter(get_media_url(f) for f in media if f.mimetype.type == 'audio')))

    res = render_jinja_template(args.template, ds=ds, examples=examples, split_ref=Sources.parse)
    write_output(args, res)
