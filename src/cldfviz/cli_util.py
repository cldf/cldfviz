"""
This module provides shared functionality for cli commands.

Often, functionality comes as two related functions `add_*` and `get_*`, where the `add_*`
function registers options which are exploited in the `get_*` function.
"""
import re
import json
import typing
import inspect
import pathlib
import argparse
import webbrowser

from clldutils.text import split_text_with_context
from clldutils.clilib import PathType, ParserError
from clldutils import path
import newick
from pyglottolog.objects import Glottocode
from pycldf import Dataset
from pycldf.ext import discovery
from pycldf.trees import TreeTable, Tree

from cldfviz.glottolog import Glottolog
from cldfviz.colormap import COLORMAPS, CATEGORICAL, CONTINUOUS, Colormap
from cldfviz.multiparameter import MultiParameter


def join_quoted(items: typing.Iterable) -> str:
    return ', '.join(['"{}"'.format(i) for i in items])


def add_jinja_template(parser, default):
    parser.add_argument(
        "--template",
        type=PathType(type='file'),
        default=default,
        help="Template file using Jinja2 syntax (see https://jinja.palletsprojects.com/). "
             "To create a custom template, you might want to start out with a copy of the "
             "default template.",
    )


def add_open(parser):
    parser.add_argument(
        "--open", action='store_true', default=False,
        help="Open the output file in the browser. (Requires specifying --output as well.)"
    )
    try:
        parser.add_argument(
            "-o", "--output", type=PathType(type="file", must_exist=False), default=False,
            help="(non-existing) path name to write the result to.",
        )
    except argparse.ArgumentError:  # pragma: no cover
        pass  # output option already added.


def open_output(args: argparse.Namespace):
    if args.output and args.open and not getattr(args, 'test', False):  # pragma: no cover
        webbrowser.open(args.output.resolve().as_uri(), new=1)


def write_output(args: argparse.Namespace, res: str):
    if args.output:
        args.output.write_text(res, encoding="utf8")
        print("Output written to {}".format(args.output))
        open_output(args)
    else:
        print(res)


def add_language_filter(parser):
    parser.add_argument(
        '--language-filters',
        default=None,
        help="JSON object specifying filter criteria for included languages. Keys must be "
             "names of columns in the datasets' LanguageTable, values are interpreted as "
             "regular expressions if they are strings or as literal values otherwise and will "
             "be matched against the value of a language for the specified column. Only "
             "languages matching all criteria are included in the analysis.",
    )


def get_language_filter(args):
    if args.language_filters is None:
        return

    def language_filter(lg):
        for k, v in json.loads(args.language_filters).items():
            val = lg.data[k]
            if isinstance(v, str):
                if isinstance(val, list):
                    if v not in val:
                        return False
                elif not re.search(v, val or ''):
                    return False
            else:
                if lg.data[k] != v:
                    return False
        return True
    return language_filter


def get_filtered_languages(args, ds) -> typing.Union[None, typing.List[str]]:
    language_filter = get_language_filter(args)
    if language_filter:
        res = []
        if 'LanguageTable' not in ds:  # pragma: no cover
            raise ValueError('Language filters only work on datasets with a LanguageTable')
        for lg in ds.objects('LanguageTable'):
            if language_filter(lg):
                res.append(lg.id)
        return res


def add_testable(parser):
    parser.add_argument('--test', action='store_true', default=False, help=argparse.SUPPRESS)


def add_listvalued(parser, *args, **kw):
    kw.setdefault('default', [])
    kw.setdefault('type', lambda s: split_text_with_context(s, ',', brackets={'{': '}'}))
    parser.add_argument(*args, **kw)


def import_module(dotted_name_or_path):
    import importlib
    p = pathlib.Path(dotted_name_or_path)
    if p.exists():
        return path.import_module(p.resolve())
    return importlib.import_module(dotted_name_or_path)


def import_subclass(dotted_name_or_path, cls):
    mod = import_module(dotted_name_or_path)
    for _, obj in inspect.getmembers(mod):
        if inspect.isclass(obj) and issubclass(obj, cls) and not obj.__subclasses__():
            return obj


def add_multiparameter(parser, with_language_filter=False, with_language_properties=False):
    """
    Adds necessary options to instantiate a `MultiParameter` object (with related colormaps).
    """
    if with_language_filter:
        add_language_filter(parser)
    add_listvalued(
        parser,
        '--parameters',
        help="Comma-separated Parameter IDs, specifying the values to plot.",
    )
    add_listvalued(
        parser,
        '--datatypes',
        help="Explicit datatypes for parameters",
    )
    add_listvalued(
        parser,
        '--colormaps',
        help="Comma-separated names of colormaps to use for the respective parameter. Choose from "
             "{} for categorical and from {} for continuous parameters."
             "".format(join_quoted(COLORMAPS[CATEGORICAL]), join_quoted(COLORMAPS[CONTINUOUS])),
    )
    parser.add_argument(
        '--missing-value',
        default=None,
        help="A color used to indicate missing values. If not specified missing values will be "
             "omitted. (Note: We define 'missing values' as rows in the ValueTable with a null "
             "value; so specifying --missing-value will **not** add null values for all languages "
             "in the dataset.)",
    )
    parser.add_argument(
        '--weight-col',
        help="Name of a column in ValueTable with numeric values to use as weight (for "
             "multi-valued parameters).",
        default=None,
    )
    if with_language_properties:
        add_listvalued(
            parser,
            '--language-properties',
            help="Comma-separated language properties, i.e. columns in the dataset's LanguageTable "
                 "to plot on the map.",
        )
        add_listvalued(
            parser,
            '--language-properties-colormaps',
            help="Comma-separated names of colormap to use for the respective language properties. "
                 "See help for --colormaps for choices",
        )


def get_multiparameter(args, ds: Dataset, glottolog: Glottolog, **ukw):
    with_language_filters = hasattr(args, 'language_filters')
    with_language_properties = hasattr(args, 'language_properties')

    kw = dict(
        datatypes=args.datatypes,
        glottolog=glottolog,
        include_missing=args.missing_value is not None,
        weight_col=getattr(args, 'weight_col', None),
    )
    if with_language_properties:
        kw['language_properties'] = args.language_properties
    if with_language_filters:
        kw['language_filter'] = get_language_filter(args)
    kw.update(ukw)

    data = MultiParameter(ds, args.parameters, **kw)

    if args.parameters and not args.colormaps:
        args.colormaps = [None] * len(args.parameters)

    if with_language_properties:
        if args.language_properties and not args.language_properties_colormaps:
            args.language_properties_colormaps = \
                [None] * len(args.language_properties)
        if '__language__' in data.parameters:
            assert len(data.parameters) == 1
            args.colormaps = args.colormaps or [None]
        args.colormaps.extend(args.language_properties_colormaps)

    assert len(args.colormaps) == len(data.parameters), '{}'.format(data.parameters.keys())
    try:
        cms = {
            pid: Colormap(
                data.parameters[pid],
                name=cm,
                novalue=args.missing_value)
            for pid, cm in zip(data.parameters, args.colormaps)}
    except (ValueError, KeyError) as e:
        raise ParserError(str(e))

    with_shapes = sum(1 for cm in cms.values() if cm.with_shapes)
    if with_shapes:
        if with_shapes > 1:
            raise ParserError('Only one colormap can specify shapes.')
        if len(data.parameters) > 2:
            raise ParserError('Shapes can only be specified for one of two parameters.')

    return data, cms


def add_secondary_dataset(parser, opt: str, help: typing.Optional[str] = None):
    """
    Some commands access data in multiple CLDF datasets.

    To be used with `get_secondary_dataset`.
    """
    parser.add_argument(
        opt,
        default=None,
        help="CLDF dataset locator. {}".format(help or '').strip(),
    )
    try:
        parser.add_argument(
            '--download-dir',
            type=PathType(type='dir'),
            help='An existing directory to use for downloading a dataset (if necessary).',
            default=None,
        )
    except argparse.ArgumentError:  # pragma: no cover
        pass  # output option already added.


def add_tree(parser):
    add_secondary_dataset(
        parser,
        '--tree-dataset',
        help='A tree from the TreeTable of this dataset is used.')
    parser.add_argument(
        '--tree',
        help="Tree specified as Glottocode (interpreted as the root of the Glottolog tree), "
             "Newick formatted string or path to a file containing the Newick formatted "
             "tree.")
    parser.add_argument(
        '--tree-id', default=None,
        help="Tree specified by ID in the TreeTable of a CLDF dataset."
    )
    parser.add_argument(
        '--glottocodes-as-tree-labels',
        action='store_true',
        default=False,
        help="If a tree in a TreeTable of a CLDF dataset is used, the nodes will be renamed "
             "using the corresponding Glottocodes."
    )


def get_secondary_dataset(args, opt: str):
    if getattr(args, opt):
        return discovery.get_dataset(getattr(args, opt), args.download_dir)


def get_tree(args, glottolog: typing.Optional[Glottolog] = None) \
        -> typing.Tuple[newick.Node, typing.Union[None, Tree], typing.Union[None, Dataset]]:
    """
    Note: While the `Tree` object which may be returned by this function allows access to the
    Newick string of the tree, the returned `Node` object should be used preferentially. This is
    because changes like renaming labels to Glottocodes are only done on this `Node` and **not**
    synced to `Tree.newick_string`!
    """
    ds = get_secondary_dataset(args, 'tree_dataset')
    tree = None
    if args.tree:
        if Glottocode.pattern.match(args.tree):
            assert glottolog
            nwk = glottolog.newick(args.tree)
        elif pathlib.Path(args.tree).exists():
            nwk = newick.read(args.tree)[0]
        else:
            nwk = newick.loads(args.tree)[0]
    else:
        for tree in TreeTable(ds):
            if (args.tree_id and tree.id == args.tree_id) or \
                    ((not args.tree_id) and tree.tree_type == 'summary'):
                nwk = tree.newick()
                break
        else:
            raise ValueError('No matching tree found')  # pragma: no cover
        # Rename tree nodes:
        if args.glottocodes_as_tree_labels:
            name_map = {
                r['id']: r['glottocode']
                for r in ds.iter_rows('LanguageTable', 'id', 'glottocode')}

            def rename(n):
                n.name = name_map.get(n.name)
                return n
            nwk.visit(rename)
    return nwk, tree, ds
