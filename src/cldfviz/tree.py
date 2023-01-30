import copy
import typing
import pathlib
import xml.etree.cElementTree as ElementTree

import toytree
import toyplot.svg
from pycldf.trees import Tree
from newick import RESERVED_PUNCTUATION, Node

__all__ = ['render']


def clean_node_label(s):
    for c in RESERVED_PUNCTUATION + ' ':
        s = s.replace(c, '_')
    return s


def render(tree: Tree,
           output: typing.Optional[pathlib.Path] = None,
           glottolog_mapping: typing.Optional[typing.Dict[str, typing.Tuple[str, str]]] = None,
           legend: typing.Optional[str] = None,
           width: typing.Optional[int] = 500,
           styles: typing.Optional[dict] = None,
           with_glottolog_links: bool = False,
           labels: typing.Optional[typing.Union[typing.Callable[[Node], str], dict]] = None,
           leafs: typing.Optional[typing.Union[typing.Callable[[Node], bool], list]] = None,
           ) -> typing.Union[pathlib.Path, str]:
    glottolog_mapping = glottolog_mapping or {}

    def rename(n):
        if n.name in glottolog_mapping:
            n.name = "{}--{}".format(n.name, glottolog_mapping[n.name][0])
        if not n.is_leaf:
            n.name = None

    def rename2(n):
        n.name = clean_node_label(labels(n) if callable(labels) else labels[n.name]) \
            if n.name else n.name

    nwk = tree.newick(strip_comments=True)
    if leafs:
        if callable(leafs):
            leafs = [n.name for n in nwk.walk() if n.name and leafs(n)]
        nwk.prune_by_names(leafs, inverse=True)
    if with_glottolog_links:
        nwk.visit(rename)
    if labels:
        nwk.visit(rename2)

    style = dict(
        width=width,
        height=sum(1 for n in nwk.walk() if n.is_leaf) * 15 + 50,
        node_hover=True,
        tip_labels_align=True,
        tip_labels_style={
            "fill": "#262626",
            "font-size": "11px",
            "-toyplot-anchor-shift": "5px",
            "line-height": "14px",
        },
        scalebar=bool(tree.tree_branch_length_unit) or bool(legend),
    )
    style.update(styles or {})
    canvas, axes, mark = toytree.tree(nwk.newick + ";", tree_format=1).draw(**style)
    if legend:
        axes.label.text = legend
    res = ElementTree.tostring(toyplot.svg.render(canvas, None)).decode('utf8')
    if with_glottolog_links:
        res = add_glottolog_links(res, glottolog_mapping)
    if output:
        output.write_text(res, encoding='utf8')
        return output
    return res


def add_glottolog_links(svg, gcodes, out=None):
    "Post-process the SVG to turn leaf names with Glottocodes into links"""
    ns = '{http://www.w3.org/2000/svg}'
    svg = ElementTree.fromstring(svg)
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
    return ElementTree.tostring(svg).decode('utf8')
