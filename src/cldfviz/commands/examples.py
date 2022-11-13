"""
Build an HTML file to display exmaples in a CLDF dataset.
"""
from clldutils.clilib import PathType
from pycldf.cli_util import get_dataset, add_dataset
import jinja2

import cldfviz


def register(parser):
    add_dataset(parser)
    parser.add_argument(
        "-o", "--output", type=PathType(type="file", must_exist=False), default=False
    )


def run(args):
    ds = get_dataset(args)

    examples = list(ds.objects("ExampleTable"))
    loader = jinja2.FileSystemLoader(
        searchpath=[str(cldfviz.PKG_DIR / "templates" / "examples")]
    )
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    res = env.get_template("examples.html").render(ds=ds, examples=examples)
    if args.output:
        args.output.write_text(res, encoding="utf8")
        print("HTML written to {}".format(args.output))
    else:
        print(res)
