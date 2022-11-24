"""
Plots a phylogeny as SVG.
"""
import copy
import pathlib
import webbrowser

from clldutils.clilib import PathType
from pycldf.cli_util import add_dataset, get_dataset
from cldfbench.cli_util import add_catalog_spec

from cldfviz.cli_util import add_testable
import xml.etree.cElementTree as ElementTree

from pycldf.trees import TreeTable

import toytree
import toyplot.svg


def register(parser):
    add_testable(parser)
    add_dataset(parser)
    add_catalog_spec(parser, 'glottolog')
    parser.add_argument('--glottolog-links', action='store_true', default=False)
    parser.add_argument('--title', default=None)
    parser.add_argument('--width', type=int, default=500)
    parser.add_argument('--tree-id', default=None)
    parser.add_argument(
        '--styles',
        help="Python dict suitable to pass into `toytree.tree.draw`. "
             "See https://toytree.readthedocs.io/en/latest/8-styling.html#",
        default='{}')
    parser.add_argument(
        'output',
        type=PathType(must_exist=False),
        help="Path to which to write the SVG file.",
    )


def run(args):  # pragma: no cover
    cldf = get_dataset(args)

    for tree in TreeTable(cldf):
        if args.tree_id is None or (args.tree_id == tree.id):
            if args.title:
                legend = args.title
            else:
                legend = tree.name
                dcol = cldf['TreeTable', 'description']
                if dcol:
                    legend += ' - {}'.format(tree.row[dcol.name])

                if tree.tree_branch_length_unit:
                    legend += ' with branches in {}'.format(tree.tree_branch_length_unit)
            glangs =  {}
            if args.glottolog and args.glottolog_links:
                glangs = {lg.id: lg.name for lg in args.glottolog.api.languoids()}
            render_tree(
                tree.newick(strip_comments=True),
                args.output,
                {
                    r['id']: (r['glottocode'], glangs.get(r['glottocode']) or '')
                    for r in cldf.iter_rows('LanguageTable', 'id', 'glottocode') if r['glottocode']},
                legend,
                args.width,
                eval(args.styles),
                args.glottolog_links,
            )
    if not args.test:  # pragma: no cover
        webbrowser.open(args.output.resolve().as_uri())


def render_tree(nwk,
                output: pathlib.Path,
                gcodes: dict,
                legend: str,
                width: int,
                styles,
                links):

    def rename(n):
        if n.name in gcodes:
            n.name = "{}--{}".format(n.name, gcodes[n.name][0])
        if not n.is_leaf:
            n.name = None

    if links:
        nwk.visit(rename)

    ntaxa = sum(1 for n in nwk.walk() if n.is_leaf)
    tree = toytree.tree(nwk.newick + ";")

    style = dict(
        width=width,
        height=ntaxa * 15 + 50,
        node_hover=True,
        tip_labels_align=True,
        tip_labels_style={
            "fill": "#262626",
            "font-size": "11px",
            "-toyplot-anchor-shift": "5px",
            "line-height": "14px",
        },
        scalebar=True
    )
    style.update(styles)
    canvas, axes, mark = tree.draw(**style)
    axes.label.text = legend
    toyplot.svg.render(canvas, str(output))
    if links:
        add_glottolog_links(output, gcodes)


def add_glottolog_links(in_, gcodes, out=None):
    "Post-process the SVG to turn leaf names with Glottocodes into links"""
    ns = '{http://www.w3.org/2000/svg}'
    svg = ElementTree.fromstring(in_.read_text(encoding='utf8'))
    for t in svg.findall('*.//{0}g[@class="toytree-TipLabels"]/{0}g/{0}text'.format(ns)):
        lid, _, gcode = t.text.strip().partition('--')
        if gcode:
            se = ElementTree.SubElement(t, '{0}text'.format(ns))
            gname = gcodes[lid][1]
            if gname:
                se.text = '{} - {} [{}]'.format(lid, gname, gcode)
            else:
                se.text = '{} - [{}]'.format(lid, gcode)
            se.attrib = copy.copy(t.attrib)
            se.attrib['fill'] = '#0000ff'
            t.tag = '{0}a'.format(ns)
            t.attrib = {
                'href': 'https://glottolog.org/resource/languoid/id/{}'.format(gcode),
                'title': 'The glottolog name',
            }
            t.text = None
    (out or in_).write_bytes(ElementTree.tostring(svg))
