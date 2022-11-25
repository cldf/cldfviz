import copy
import typing
import pathlib
import xml.etree.cElementTree as ElementTree

import toytree
import toyplot.svg
from pycldf.trees import Tree

__all__ = ['render']


def render(tree: Tree,
           output: pathlib.Path,
           glottolog_mapping: typing.Optional[typing.Dict[str, typing.Tuple[str, str]]] = None,
           legend: typing.Optional[str] = None,
           width: typing.Optional[int] = 500,
           styles: typing.Optional[dict] = None,
           with_glottolog_links: bool = False) -> pathlib.Path:
    glottolog_mapping = glottolog_mapping or {}

    def rename(n):
        if n.name in glottolog_mapping:
            n.name = "{}--{}".format(n.name, glottolog_mapping[n.name][0])
        if not n.is_leaf:
            n.name = None

    nwk = tree.newick(strip_comments=True)
    if with_glottolog_links:
        nwk.visit(rename)

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
    canvas, axes, mark = toytree.tree(nwk.newick + ";").draw(**style)
    if legend:
        axes.label.text = legend
    toyplot.svg.render(canvas, str(output))
    if with_glottolog_links:
        add_glottolog_links(output, glottolog_mapping)
    return output


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
