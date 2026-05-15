"""
Functionality to render CLDF Trees as SVG using the tyotree library.
"""
import copy
import pathlib
import textwrap
import dataclasses
from xml.etree import ElementTree
from typing import Optional, Union, Callable

import toytree
import toyplot.svg
from pycldf.trees import Tree
from newick import RESERVED_PUNCTUATION, Node
from clldutils.svg import pie, icon

from cldfviz.colormap import get_shape_and_color, SVG_SHAPE_MAP, Colormap, WeightedColorsType
from cldfviz.multiparameter import Parameter, ParameterDictType

__all__ = ['render', 'TreeData']

NodeNameType = str
GlottocodeType = str
GlottologNameType = str
GlottologMappingType = dict[NodeNameType, tuple[GlottocodeType, GlottologNameType]]
LabelsType = Union[Callable[[NodeNameType], str], dict[NodeNameType, str]]


def clean_node_label(s: Union[str, None]) -> Union[str, None]:
    """Create a node label suitable for inclusion in SVG."""
    if s:  # Automatically generated label mappings may map to `None`.
        for c in RESERVED_PUNCTUATION:
            s = s.replace(c, '_')
        return s.replace(' ', '_')
    return s


@dataclasses.dataclass
class TreeData:
    """Data to be plotted against the tree."""
    values: dict[str, WeightedColorsType]
    parameters: ParameterDictType
    colormaps: dict[Union[str, None], Colormap]


class SVGTree:
    """Functionality to create SVG programmatically."""
    def __init__(self, svg):
        self.svg = svg
        self.parent_map: dict = {c: p for p in svg.iter() for c in p}

    @classmethod
    def from_toyplot(  # pylint: disable=R0913,R0917
        cls, tree_object, nwk: Node, data: TreeData, width, height, legend, styles
    ):
        """Initialize a SVGTree with the content rendered by toytree."""
        style = dict(  # pylint: disable=R1735
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
        canvas, axes, _ = toytree.tree(nwk.newick + ";", tree_format=1).draw(**style)
        if legend:
            axes.label.text = legend
        return cls(toyplot.svg.render(canvas, None))

    @property
    def height(self) -> float:
        """The height of the SVG doc."""
        return float(self.svg.attrib['height'].replace('px', ''))

    @height.setter
    def height(self, val):
        self.svg.attrib['height'] = str(val) + 'px'
        view_box = self.svg.attrib['viewBox'].split()
        view_box[3] = str(val)
        self.svg.attrib['viewBox'] = ' '.join(view_box)

    @property
    def width(self) -> float:
        """The width of the SVG doc."""
        return float(self.svg.attrib['width'].replace('px', ''))

    @width.setter
    def width(self, val):
        self.svg.attrib['width'] = str(val) + 'px'
        view_box = self.svg.attrib['viewBox'].split()
        view_box[2] = str(val)
        self.svg.attrib['viewBox'] = ' '.join(view_box)

    @staticmethod
    def element(tag, parent, text=None, **attrs) -> ElementTree.Element:
        """Create an SVG element."""
        ee = ElementTree.SubElement(parent, tag)
        ee.attrib = {k.rstrip('_').replace('_', '-'): str(v) for k, v in attrs.items()}
        if text:
            ee.text = text
        return ee

    @staticmethod
    def marker(parent, weighted_colors):
        """Add a marker to the SVG doc."""
        res = get_shape_and_color(weighted_colors)
        if res:
            g = ElementTree.SubElement(parent, 'g')
            g.attrib['transform'] = 'scale(0.5)'
            parent = g
            p = ElementTree.fromstring(icon(res[1].replace('#', SVG_SHAPE_MAP[res[0]])))
        else:
            ratios, colors = [c[0] for c in weighted_colors], [c[1] for c in weighted_colors]
            p = ElementTree.fromstring(pie(ratios, colors, width=20, stroke_circle=True))
        parent.extend(p.findall('./{http://www.w3.org/2000/svg}path'))
        parent.extend(p.findall('./{http://www.w3.org/2000/svg}circle'))

    def visit_leafs(self, visitor: Callable, *args, **kw):
        """Apply visitor to all leaf nodes."""
        for t in self.svg.findall('.//g[@class="toytree-TipLabels"]/g/text'):
            visitor(self, t, self.parent_map[t], *args, **kw)

    def __bytes__(self):
        return ElementTree.tostring(self.svg, encoding='utf8', xml_declaration=True)

    def __str__(self):
        return bytes(self).decode('utf8')

    @staticmethod
    def prepare_nwk(  # pylint: disable=R0913,R0917
            nwk,
            leafs,
            glottolog_mapping: GlottologMappingType,
            labels: LabelsType,
            data,
            with_glottolog_links: bool,
    ):
        """
        This function prepares the newick representation of the tree in such a way that
        post-processing the toytree output becomes possible.
        """
        if leafs:
            if callable(leafs):
                leafs = [n.name for n in nwk.walk() if n.name and leafs(n)]
            nwk.prune_by_names(leafs, inverse=True)

        if data:
            nwk.prune_by_names(list(data.values.keys()), inverse=True)

        if with_glottolog_links:
            def apply_glottolog_mapping(n):
                if n.name in glottolog_mapping:
                    n.name = f"{n.name}--{glottolog_mapping[n.name][0]}"
                if not n.is_leaf:
                    n.name = None
            nwk.visit(apply_glottolog_mapping)

        if labels and (not data):
            def apply_labels(n):
                n.name = clean_node_label(labels(n) if callable(labels) else labels[n.name]) \
                    if n.name else n.name
            nwk.visit(apply_labels)

        def pad(n):
            if n.name and n.is_leaf:
                # FIXME: pad to fit longest label  # pylint: disable=fixme
                n.name = n.name + '#############'
        nwk.visit(pad)

    def add_glottolog_links(self, glottolog_mapping: GlottologMappingType):
        """Add Glottolog links next to the leaf names."""
        def _add_glottolog_links(svg, t, _, gcodes):
            "Post-process the SVG to turn leaf names with Glottocodes into links"""
            if t.text:
                lid, _, gcode = t.text.strip().partition('--')
                if gcode:
                    se = svg.element('text', t, **copy.copy(t.attrib))
                    gname = gcodes[lid][1]
                    if gname:
                        se.text = f'{lid} - {gname} [{gcode}]'
                    else:
                        se.text = f'{lid} - [{gcode}]'
                    se.attrib['fill'] = '#0000ff'
                    t.tag = 'a'
                    t.attrib = {
                        'href': f'https://glottolog.org/resource/languoid/id/{gcode}',
                        # 'title': 'The glottolog name',
                    }
                    t.text = None
        self.visit_leafs(_add_glottolog_links, glottolog_mapping)

    def add_marker(self, data: TreeData, labels: LabelsType):
        """Add value marker next to the leaf name."""
        def _add_marker(svg, t, parent: ElementTree.Element, data: TreeData, labels):
            """Prepend leaf labels with markers."""
            t.text = t.text.rstrip('#') if t.text else t.text
            if t.text in data.values:
                t.attrib['x'] = str(float(t.attrib['x']) + 15)

                g = ElementTree.SubElement(parent, 'g')
                g.attrib = {'transform': "translate(0,-10)"}
                svg.marker(g, data.values[t.text])
                if t.text in (labels or {}):
                    t.text = labels[t.text]
        self.visit_leafs(_add_marker, data, labels)


def render(  # pylint: disable=R0913,R0917
        nwk: Union[Node, Tree],
        tree_object: Optional[Tree] = None,
        output: Optional[pathlib.Path] = None,
        glottolog_mapping: Optional[GlottologMappingType] = None,
        legend: Optional[str] = None,
        width: Optional[int] = 500,
        height: Optional[int] = None,
        styles: Optional[dict] = None,
        with_glottolog_links: bool = False,
        labels: Optional[Union[Callable[[Node], str], dict[NodeNameType, str]]] = None,
        leafs: Optional[Union[Callable[[Node], bool], list[NodeNameType]]] = None,
        data: Optional[TreeData] = None,
) -> Union[pathlib.Path, str]:
    """Render a tree to SVG."""
    glottolog_mapping = glottolog_mapping or {}
    if isinstance(nwk, Tree):
        tree_object = nwk
        nwk = tree_object.newick(strip_comments=True)

    SVGTree.prepare_nwk(nwk, leafs, glottolog_mapping, labels, data, with_glottolog_links)
    res = SVGTree.from_toyplot(tree_object, nwk, data, width, height, legend, styles)

    if with_glottolog_links:
        res.add_glottolog_links(glottolog_mapping)

    if data:
        res.add_marker(data, labels)
        add_legend(res, data)
    else:
        res.visit_leafs(
            lambda s, t, p: setattr(t, 'text', t.text.rstrip('#') if t.text else t.text))

    if output:
        output.write_bytes(bytes(res))
        return output
    return str(res)


@dataclasses.dataclass
class ParameterLegend:
    """Data and method to create a legend for a single parameter."""
    index: int
    pid: str
    parameter: Parameter
    legend: ElementTree.Element
    svg: SVGTree

    def _row(self, y: int, weighted_colors, label, **attrs) -> int:
        def _shorten(text, width):
            return textwrap.shorten(str(text), width, placeholder='…')

        row_ = self.svg.element('g', self.legend, transform=f"translate(10,{y})")
        if weighted_colors:
            self.svg.marker(row_, weighted_colors)
        self.svg.element(
            'text', row_,
            x=30 if weighted_colors else 0, y=15,
            text=_shorten(label, 25 if weighted_colors else 30), stroke_width=0, **attrs)
        return y + 25

    def _continuous_variable_legend(self, y: int, colormap) -> int:
        min_, max_ = self.parameter.domain
        row_ = self.svg.element('g', self.legend, transform=f"translate(10,{y})")
        self.svg.element('text', row_, x=0, y=15, text=str(min_), stroke_width=0)
        self.svg.element(
            'text', row_, x=180, y=15, text=str(max_), text_anchor='end', stroke_width=0)
        y += 25
        row_ = self.svg.element('g', self.legend, transform=f"translate(10,{y})")
        for i in range(10):
            self.svg.element(
                'rect',
                row_,
                x=i * 18,
                y=0,
                width='18', height='18',
                fill=colormap(min_ + i * (max_ - min_) / 10))
        return y + 25

    def _categorical_variable_legend(
            self, y: int, pid_with_color: Optional[str], data: Optional[TreeData]) -> int:
        for v, label in self.parameter.domain.items():
            weighted_colors = [
                (1, data.colormaps[self.pid](v) if j == self.index else '#ffffff')
                for j in range(len(data.parameters))]
            if pid_with_color == self.pid:
                weighted_colors = [(1, data.colormaps[self.pid](v))]
            y = self._row(y, weighted_colors, label)
        return y

    def add_legend(self, y: int, data: Optional[TreeData], pid_with_color: Optional[str]) -> int:
        """Add a legend for a single parameter."""
        if self.index != 0:
            self.svg.element('line', self.legend, x1=5, y1=y, x2=195, y2=y, stroke='black')
            y += 3
        else:
            y += 5
        y = self._row(y, None, self.parameter.name, font_weight='bold')
        if isinstance(self.parameter.domain, tuple):
            return self._continuous_variable_legend(y, data.colormaps[self.pid])
        return self._categorical_variable_legend(y, pid_with_color, data)


def add_legend(svg: SVGTree, data: Optional[TreeData]):
    """If data is plotted on the tree, we add a legend describing the parameters."""
    y = 0
    legend = svg.element(
        'g', svg.svg, transform=f"translate({svg.width - 20},45)", style="font-size: 12px")
    rect = svg.element('rect', legend, x=0, y=0, width='200', height=svg.height, rx=5, fill='white')
    pid_with_color = None
    if any(cm.with_shapes for cm in data.colormaps.values()):
        for pid, cm in data.colormaps.items():
            if not cm.with_shapes:
                pid_with_color = pid
                break

    for i, (pid, parameter) in enumerate(data.parameters.items()):
        pl = ParameterLegend(i, pid, parameter, legend, svg)
        y = pl.add_legend(y, data, pid_with_color)

    rect.attrib['height'] = str(y)

    svg.width = svg.width + 220
    svg.height = max([svg.height, 45 + y])
