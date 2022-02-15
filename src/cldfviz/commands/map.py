"""
Plot values for parameters in a CLDF StructureDataset on a map.

Usage examples:
- plot languages of a dataset:
  cldfbench cldfviz.map PATH/TO/DATASET --language-labels
- plot values of one parameter:
  cldfbench cldfviz.map PATH/TO/DATASET --parameters PID
- plot values of a column in the dataset's LanguageTable:
  cldfbench cldfviz.map PATH/TO/DATASET --language-property Macroarea

Colormaps: Colormaps can be specified by name - chosing from the ones available - or explicitly,
by providing a mapping from values (as found in the value column of ValueTable) to colors (see
below), serialized as JSON object, e.g. `--colormaps '{"x": "#a00", "y": "#0a0"}'`.

Colors: Colors can be specified as
- hex-triplets ("#a00", "AA0000")
- name (see https://www.w3.org/TR/css-color-4/#named-colors)
"""
import pathlib

from pycldf.cli_util import get_dataset, add_dataset
from clldutils.clilib import PathType, ParserError
from cldfbench.cli_util import add_catalog_spec

from cldfviz.colormap import Colormap, COLORMAPS
from cldfviz.multiparameter import MultiParameter, CONTINUOUS, CATEGORICAL
from cldfviz.map import Map, MarkerFactory
from cldfviz.cli_util import add_testable, add_listvalued, import_subclass

FORMATS = {}
for cls in Map.__subclasses__():
    for fmt in cls.__formats__:
        FORMATS[fmt] = cls


def join_quoted(items):
    return ', '.join(['"{}"'.format(i) for i in items])


def register(parser):
    add_testable(parser)
    add_dataset(parser)
    add_catalog_spec(parser, 'glottolog')
    add_listvalued(
        parser,
        '--parameters',
        help="Comma-separated Parameter IDs, specifying the values to plot on the map. If not "
             "specified, all languages in the dataset will be plotted.",
    )
    add_listvalued(
        parser,
        '--colormaps',
        help="Comma-separated names of colormaps to use for the respective parameter. Choose from "
             "{} for categorical and from {} for continuous parameters."
             "".format(join_quoted(COLORMAPS[CATEGORICAL]), join_quoted(COLORMAPS[CONTINUOUS])),
    )
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
    parser.add_argument(
        '--output',
        type=PathType(type='file', must_exist=False),
        help="Filesystem path to write the resulting map to. If no suffix is specified, it will "
             "be appended according to FORMAT; if given, suffix must match FORMAT.",
        default=pathlib.Path('map'))
    parser.add_argument(
        '--format',
        default='html',
        metavar='FORMAT',
        choices=list(FORMATS),
    )
    parser.add_argument(
        '--markersize',
        help="Size of map markers in pixels",
        type=int,
        default=10,
    )
    parser.add_argument(
        '--marker-factory',
        help="A python module providing a subclass of `cldfviz.map.MarkerFactory`.",
        default=None,
    )
    parser.add_argument(
        '--title',
        default=None,
        help="Title for the map plot",
    )
    parser.add_argument(
        '--pacific-centered',
        action='store_true',
        default=False,
        help="Center maps of the whole world at the pacific, thus not cutting large language "
             "families in half."
    )
    parser.add_argument(
        '--language-labels',
        action='store_true',
        default=False,
        help="Display language names on the map",
    )
    parser.add_argument(
        '--missing-value',
        default=None,
        help="A color used to indicate missing values. If not specified missing values will be "
             "omitted.",
    )
    parser.add_argument(
        '--no-legend',
        action='store_true',
        default=False,
        help="Don't add a legend to the map (e.g. because it would be too big).",
    )

    for cls in Map.__subclasses__():
        cls.add_options(
            parser, help_suffix='(Only for FORMATs {})'.format(join_quoted(cls.__formats__)))


def run(args):
    ds = get_dataset(args)
    if not args.output.suffix:
        args.output = args.output.parent / "{}.{}".format(args.output.name, args.format)
    else:
        assert args.output.suffix[1:] == args.format

    glottolog = {lg.id: lg for lg in args.glottolog.api.languoids() if lg.latitude is not None} \
        if args.glottolog else {}
    data = MultiParameter(
        ds,
        args.parameters,
        glottolog=glottolog,
        include_missing=args.missing_value is not None,
        language_properties=args.language_properties)
    if args.parameters and not args.colormaps:
        args.colormaps = [None] * len(args.parameters)
    if args.language_properties and not args.language_properties_colormaps:
        args.language_properties_colormaps = \
            [None] * len(args.language_properties)
    if '__language__' in data.parameters:
        assert len(data.parameters) == 1
        args.colormaps = [None]
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

    if args.marker_factory:
        comps = args.marker_factory.split(',')
        cls = import_subclass(comps[0], MarkerFactory)
        args.marker_factory = cls(ds, args, *comps[1:])

    try:
        map = FORMATS[args.format](data.languages.values(), args)
    except ValueError as e:  # pragma: no cover
        raise ParserError(str(e))

    with map as fig:
        for lang, values in data.iter_languages():
            fig.api_add_language(lang, values, cms)

        if not args.no_legend:
            fig.api_add_legend(data.parameters, cms)

        args.log.info('Writing output to: {}'.format(args.output))
        args.log.info('For non-html maps this may take a while.')
        if not args.test:
            fig.open()  # pragma: no cover
