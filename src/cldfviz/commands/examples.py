"""
Build an HTML file to display examples in a CLDF dataset.
"""
from pycldf.cli_util import add_dataset, get_dataset
from pycldf.sources import Sources

from cldfviz.cli_util import add_open, write_output
from cldfviz.template import render_jinja_template


def register(parser):
    add_dataset(parser)
    add_open(parser)


def run(args):
    ds = get_dataset(args)
    res = render_jinja_template(
        "examples.html",
        ds=ds,
        examples=list(ds.objects("ExampleTable")),
        split_ref=Sources.parse)
    write_output(args, res)
