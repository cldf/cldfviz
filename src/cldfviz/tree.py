import sys
import copy
import typing
import pathlib
import textwrap
import xml.etree.cElementTree as ElementTree

import toytree
import toyplot.svg
from pycldf.trees import Tree
from newick import RESERVED_PUNCTUATION, Node
from clldutils.svg import pie, icon

from cldfviz.colormap import get_shape_and_color, SVG_SHAPE_MAP

__all__ = ['render']


def clean_node_label(s):
    if s:  # Automatically generated label mappings may map to `None`.
        for c in RESERVED_PUNCTUATION:
            s = s.replace(c, '_')
        return s.replace(' ', '_')
    return s


class SVGTree:
    def __init__(self, svg):
        self.svg = svg
        self.parent_map = {c: p for p in svg.iter() for c in p}

    @property
    def height(self):
        return float(self.svg.attrib['height'].replace('px', ''))

    @height.setter
    def height(self, val):
        self.svg.attrib['height'] = str(val) + 'px'
        viewBox = self.svg.attrib['viewBox'].split()
        viewBox[3] = str(val)
        self.svg.attrib['viewBox'] = ' '.join(viewBox)

    @property
    def width(self):
        return float(self.svg.attrib['width'].replace('px', ''))

    @width.setter
    def width(self, val):
        self.svg.attrib['width'] = str(val) + 'px'
        viewBox = self.svg.attrib['viewBox'].split()
        viewBox[2] = str(val)
        self.svg.attrib['viewBox'] = ' '.join(viewBox)

    @staticmethod
    def element(tag, parent, text=None, **attrs):
        ee = ElementTree.SubElement(parent, tag)
        ee.attrib = {k.rstrip('_').replace('_', '-'): str(v) for k, v in attrs.items()}
        if text:
            ee.text = text
        return ee

    @staticmethod
    def marker(parent, weighted_colors):
        res = get_shape_and_color(weighted_colors)
        if res:
            g = ElementTree.SubElement(parent, 'g')
            g.attrib['transform'] = 'scale(0.5)'
            parent = g
            p = ElementTree.fromstring(icon(res[1].replace('#', SVG_SHAPE_MAP[res[0]])))
        else:
            ratios, colors = [c[0] for c in weighted_colors], [c[1] for c in weighted_colors]
            p = ElementTree.fromstring(pie(ratios, colors, width=20, stroke_circle=True))
        parent.extend(p.findall('./{}path'.format('{http://www.w3.org/2000/svg}')))
        parent.extend(p.findall('./{}circle'.format('{http://www.w3.org/2000/svg}')))

    def visit_leafs(self, visitor, *args, **kw):
        for t in self.svg.findall('.//g[@class="toytree-TipLabels"]/g/text'):
            visitor(self, t, self.parent_map[t], *args, **kw)

    def __bytes__(self):
        kw = dict(encoding='utf8')
        if sys.version_info >= (3, 8):
            kw['xml_declaration'] = True
        return ElementTree.tostring(self.svg, **kw)

    def __str__(self):
        return bytes(self).decode('utf8')


def render(nwk: typing.Union[Node, Tree],
           tree_object: typing.Optional[Tree] = None,
           output: typing.Optional[pathlib.Path] = None,
           glottolog_mapping: typing.Optional[typing.Dict[str, typing.Tuple[str, str]]] = None,
           legend: typing.Optional[str] = None,
           width: typing.Optional[int] = 500,
           height: typing.Optional[int] = None,
           styles: typing.Optional[dict] = None,
           with_glottolog_links: bool = False,
           labels: typing.Optional[typing.Union[typing.Callable[[Node], str], dict]] = None,
           leafs: typing.Optional[typing.Union[typing.Callable[[Node], bool], list]] = None,
           data=None,
           ) -> typing.Union[pathlib.Path, str]:
    glottolog_mapping = glottolog_mapping or {}
    if isinstance(nwk, Tree):
        tree_object = nwk
        nwk = tree_object.newick(strip_comments=True)

    def rename(n):
        if n.name in glottolog_mapping:
            n.name = "{}--{}".format(n.name, glottolog_mapping[n.name][0])
        if not n.is_leaf:
            n.name = None

    def rename2(n):
        n.name = clean_node_label(labels(n) if callable(labels) else labels[n.name]) \
            if n.name else n.name

    if leafs:
        if callable(leafs):
            leafs = [n.name for n in nwk.walk() if n.name and leafs(n)]
        nwk.prune_by_names(leafs, inverse=True)
    if data:
        nwk.prune_by_names(list(data.values.keys()), inverse=True)
    if with_glottolog_links:
        nwk.visit(rename)
    if labels and (not data):
        nwk.visit(rename2)

    def pad(n):
        if n.name and n.is_leaf:
            n.name = n.name + '#############'  # FIXME: pad to fit longest label
    nwk.visit(pad)

    style = dict(
        width=width,
        height=height or sum(1 for n in nwk.walk() if n.is_leaf) * (23 if data else 15) + 150,
        node_hover=True,
        tip_labels_align=True,
        tip_labels_style={
            "fill": "#262626",
            "font-size": "11px",
            "-toyplot-anchor-shift": "15px",
            "line-height": "14px",
        },
        scalebar=bool(getattr(tree_object, 'tree_branch_length_unit', None)) or bool(legend),
    )
    style.update(styles or {})
    canvas, axes, mark = toytree.tree(nwk.newick + ";", tree_format=1).draw(**style)
    if legend:
        axes.label.text = legend
    res = SVGTree(toyplot.svg.render(canvas, None))
    if with_glottolog_links:
        res.visit_leafs(add_glottolog_links, glottolog_mapping)

    if data:
        res.visit_leafs(add_marker, data, labels)
        add_legend(res, data)
    else:
        res.visit_leafs(
            lambda s, t, p: setattr(t, 'text', t.text.rstrip('#') if t.text else t.text))

    if output:
        output.write_bytes(bytes(res))
        return output
    return str(res)


def add_glottolog_links(svg, t, _, gcodes):
    "Post-process the SVG to turn leaf names with Glottocodes into links"""
    if t.text:
        lid, _, gcode = t.text.strip().partition('--')
        if gcode:
            se = svg.element('text', t, **copy.copy(t.attrib))
            gname = gcodes[lid][1]
            if gname:
                se.text = '{} - {} [{}]'.format(lid, gname, gcode)
            else:
                se.text = '{} - [{}]'.format(lid, gcode)
            se.attrib['fill'] = '#0000ff'
            t.tag = 'a'
            t.attrib = {
                'href': 'https://glottolog.org/resource/languoid/id/{}'.format(gcode),
                # 'title': 'The glottolog name',
            }
            t.text = None


def add_marker(svg, t, parent, data, labels):
    t.text = t.text.rstrip('#') if t.text else t.text
    if t.text in data.values:
        t.attrib['x'] = str(float(t.attrib['x']) + 15)

        g = ElementTree.SubElement(parent, 'g')
        g.attrib = dict(transform="translate(0,-10)")
        svg.marker(g, data.values[t.text])
        if t.text in (labels or {}):
            t.text = labels[t.text]


def add_legend(svg, data):
    def shorten(text, width):
        return textwrap.shorten(str(text), width, placeholder='…')

    def row(legend, y, weighted_colors, label, **attrs):
        row_ = svg.element('g', legend, transform="translate(10,{})".format(y))
        if weighted_colors:
            svg.marker(row_, weighted_colors)
        svg.element(
            'text', row_,
            x=30 if weighted_colors else 0, y=15,
            text=shorten(label, 25 if weighted_colors else 30), stroke_width=0, **attrs)

    y = 0
    legend = svg.element(
        'g', svg.svg,
        transform="translate({},{})".format(svg.width - 20, 45), style="font-size: 12px")
    rect = svg.element('rect', legend, x=0, y=0, width='200', height=svg.height, rx=5, fill='white')
    pid_with_color = None
    if any(cm.with_shapes for cm in data.colormaps.values()):
        for pid, cm in data.colormaps.items():
            if not cm.with_shapes:
                pid_with_color = pid
                break

    for i, (pid, parameter) in enumerate(data.parameters.items()):
        if i != 0:
            svg.element('line', legend, x1=5, y1=y, x2=195, y2=y, stroke='black')
            y += 3
        else:
            y += 5

        row(legend,
            y,
            None,
            parameter.name,
            font_weight='bold')
        y += 25
        if isinstance(parameter.domain, tuple):
            min_, max_ = parameter.domain
            row_ = svg.element('g', legend, transform="translate(10,{})".format(y))
            svg.element('text', row_, x=0, y=15, text=str(min_), stroke_width=0)
            svg.element(
                'text', row_, x=180, y=15, text=str(max_), text_anchor='end', stroke_width=0)
            y += 25
            row_ = svg.element('g', legend, transform="translate(10,{})".format(y))
            for i in range(10):
                svg.element(
                    'rect',
                    row_,
                    x=i * 18,
                    y=0,
                    width='18', height='18',
                    fill=data.colormaps[pid](min_ + i * (max_ - min_) / 10))
            y += 25
        else:
            for v, label in parameter.domain.items():
                weighted_colors = [
                    (1, data.colormaps[pid](v) if j == i else '#ffffff')
                    for j in range(len(data.parameters))]
                if pid_with_color == pid:
                    weighted_colors = [(1, data.colormaps[pid](v))]
                row(legend, y, weighted_colors, label)
                y += 25
    rect.attrib['height'] = str(y)

    svg.width = svg.width + 220
    svg.height = max([svg.height, 45 + y])
