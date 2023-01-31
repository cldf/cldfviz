"""
Build an HTML file to display examples in a CLDF dataset.
"""
from pycldf.cli_util import add_dataset, get_dataset
from pycldf.sources import Sources

from cldfviz.cli_util import add_open, write_output, add_jinja_template
from cldfviz.template import render_jinja_template, TEMPLATE_DIR


def register(parser):
    add_dataset(parser)
    mod = __name__.split('.')[-1]
    add_jinja_template(parser, TEMPLATE_DIR / mod / '{}.html'.format(mod))
    add_open(parser)


def run(args):
    ds = get_dataset(args)
    res = render_jinja_template(
        args.template,
        ds=ds,
        examples=list(ds.objects("ExampleTable")),
        split_ref=Sources.parse)
    write_output(args, res)
