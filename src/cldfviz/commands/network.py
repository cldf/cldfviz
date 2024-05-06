"""
Convert a parameter network to a suitable format for visualization/analysis.

- DOT/GV for interoperability with the GraphViz tools
- GraphML for interoperability with networkx/igraph/Gephi

Image formats like SVG can then be created by piping the output to the `dot` program.
"""
import re
import json
import pathlib
import functools
import xml.etree
import collections

try:
    from networkx import Graph
    from networkx.algorithms.components import node_connected_component
except ImportError:  # pragma: no cover
    Graph = None

from pycldf.cli_util import get_dataset, add_dataset


def string_or_path(s):
    return pathlib.Path(s).read_text(encoding='utf8') if pathlib.Path(s).exists() else s


def register(parser):
    add_dataset(parser)
    parser.add_argument(
        '--format',
        choices=['dot', 'graphml'],
        help="Output format",
        default='dot')
    parser.add_argument(
        '--edge-filters',
        default=None,
        help="JSON object specifying filter criteria for included edges. Keys must be "
             "names of columns in the datasets' ParameterNetwork, values are interpreted as "
             "regular expressions if they are strings or as literal values otherwise and will "
             "be matched against the value of an edge for the specified column. Only "
             "edges matching all criteria are included in the analysis.",
    )
    parser.add_argument(
        '--node-attributes',
        help="Python dict (passed as string or name to a file) to supply node attributes. Use "
             "lambda functions accepting a pycldf.orm.Parameter instance as sole argument to "
             "compute values on the fly.",
        type=string_or_path,
        default='{}')
    parser.add_argument(
        '--edge-attributes',
        help="Python dict (passed as string or name to a file) to supply edge attributes. Use "
             "lambda functions accepting a pycldf.orm.ParameterNetworkEdge instance as sole "
             "argument to compute values on the fly.",
        type=string_or_path,
        default='{}')
    parser.add_argument(
        '--parameter',
        help="To single out individual components of multi-component networks, a node contained "
             "in the desired component can be specified by ID or Name.",
        default=None,
    )


def run(args):
    if Graph is None:  # pragma: no cover
        args.log.error(
            'install cldfviz with network support, running "pip install cldfviz[network]"')
        return

    def edge_filter(row):
        for k, v in json.loads(args.edge_filters or '{}').items():
            val = row.data[k]
            if isinstance(v, list):
                if val not in v:
                    return False
            elif isinstance(v, str):
                if not re.search(v, str(val) or ''):
                    return False
            else:
                if row.data[k] != v:
                    return False
        return True

    ds = get_dataset(args)
    pnodes = collections.OrderedDict((p.id, p) for p in ds.objects('ParameterTable'))

    # Edges filtered by --edge-filters:
    edges = [edge for edge in ds.objects('ParameterNetwork') if edge_filter(edge)]

    if args.parameter:
        # Now compute edges filtered for one component:
        g = Graph()
        for e in edges:
            g.add_edge(e.cldf.sourceParameterReference, e.cldf.targetParameterReference)
        for pid, p in pnodes.items():
            if args.parameter == p.cldf.name or args.parameter == pid:
                nodes = node_connected_component(g, pid)
                edges = [e for e in edges if e.cldf.sourceParameterReference in nodes]
                break
        else:  # pragma: no cover
            raise ValueError('Invalid parameter specified.')

    nids = ({e.cldf.sourceParameterReference for e in edges} |  # noqa: W504
            {e.cldf.targetParameterReference for e in edges})
    nodes = [v for k, v in pnodes.items() if k in nids]

    def compute_attrs(spec, obj):
        attrs, drop = collections.OrderedDict(), False
        for k, v in spec.items():
            if callable(v):
                v = v(obj)
                if k == 'drop' and v:
                    # Special key "drop" and the return value is True, skip the edge.
                    drop = True
                    break
            if k != 'drop':
                attrs[k] = v
        return attrs, drop

    # Compute attributes:
    eattrs = functools.partial(compute_attrs, eval(args.edge_attributes))
    edges = [(edge, eattrs(edge)) for edge in edges]
    edges = [(edge, attrs) for edge, (attrs, drop) in edges if not drop]
    nattrs = functools.partial(compute_attrs, eval(args.node_attributes))
    nodes = [(node, nattrs(node)[0]) for node in nodes]

    if args.format == 'dot':
        print(dot(nodes, edges))
    elif args.format == 'graphml':
        print(graphml(nodes, edges))
    else:  # pragma: no cover
        raise ValueError('unsupported format')


def dot(nodes, edges):
    def dot_id(v):
        """
        We convert everything to a string, then escape as needed.
        """
        return '"{}"'.format(str(v).replace('"', r'\"'))

    def format_attrs(attrs):
        pairs = ['"{}"={}'.format(k, dot_id(v)) for k, v in attrs.items() if v is not None]
        return ' [{}]'.format(';'.join(pairs)) if pairs else ''

    def iter_lines():
        yield 'digraph {'
        for node, attrs in nodes:
            attrs.setdefault('label', node.cldf.name)
            yield '"{}"{}'.format(node.id, format_attrs(attrs))

        for edge, attrs in edges:
            if not edge.cldf.edgeIsDirected:
                attrs.setdefault('dir', 'none')
            yield '"{}" -> "{}"{}'.format(
                edge.cldf.sourceParameterReference,
                edge.cldf.targetParameterReference,
                format_attrs(attrs))
        yield '}'
    return '\n'.join(iter_lines())


def graphml(nodes, edges, edgedefault="undirected"):
    ns = 'http://graphml.graphdrawing.org/xmlns'

    def qname(lname):
        return '{' + ns + '}' + lname

    def infer_type(values):
        #  boolean, int, long, float, double, or string.
        for value in values:
            if isinstance(value, bool):
                return 'boolean', lambda s: str(s).lower()
            if isinstance(value, int):
                return 'long', lambda s: str(s)
            if isinstance(value, float):
                return 'double', lambda s: str(s)
        return 'string', lambda s: str(s)

    def iter_attributes(attrs):
        if attrs:
            values = collections.defaultdict(list)
            for attr in attrs:
                for k, v in attr.items():
                    values[k].append(v)
            for key, vals in values.items():
                yield key, infer_type(vals)

    def subelement(parent, tag, **attrs):
        return xml.etree.ElementTree.SubElement(
            parent, qname(tag), **{qname(k): v for k, v in attrs.items()})

    def create_key(e, prefix, name, type):
        id_ = '{}.{}'.format(prefix, name)
        subelement(e, 'key', **{'id': id_, 'for': 'node', 'attr.name': name, 'attr.type': type})
        return id_

    root = xml.etree.ElementTree.Element(qname('graphml'))
    graph = subelement(root, 'graph', id='graph', edgedefault=edgedefault)
    converters = {}
    for aname, (atype, conv) in iter_attributes([a for _, a in nodes]):
        converters[create_key(graph, 'n', aname, atype)] = conv
    for aname, (atype, conv) in iter_attributes([a for _, a in edges]):
        converters[create_key(graph, 'e', aname, atype)] = conv

    for node, attrs in nodes:
        n = subelement(graph, 'node', id=node.id)
        for k, v in attrs.items():
            key = 'n.{}'.format(k)
            if v is not None:
                t = subelement(n, 'data', key=key)
                t.text = converters[key](v)

    for edge, attrs in edges:
        n = subelement(graph, 'edge',
                       source=edge.cldf.sourceParameterReference,
                       target=edge.cldf.targetParameterReference)
        for k, v in attrs.items():
            key = 'e.{}'.format(k)
            if v is not None:
                t = subelement(n, 'data', key=key)
                t.text = converters[key](v)

    if hasattr(xml.etree.ElementTree, 'indent'):  # new in Python 3.9.
        xml.etree.ElementTree.indent(root)
    return xml.etree.ElementTree.tostring(
        root,
        encoding='utf8',
        default_namespace='http://graphml.graphdrawing.org/xmlns',
        xml_declaration=True).decode('utf8')
