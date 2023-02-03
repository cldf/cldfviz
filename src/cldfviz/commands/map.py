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

from cldfviz.map import Map, MarkerFactory
from cldfviz.cli_util import (
    add_testable, import_subclass, get_multiparameter, join_quoted, add_multiparameter,
)
from cldfviz.glottolog import Glottolog

FORMATS = {}
for cls in Map.__subclasses__():
    for fmt in cls.__formats__:
        FORMATS[fmt] = cls


def register(parser):
    add_testable(parser)
    add_dataset(parser)
    Glottolog.add(parser)

    add_multiparameter(parser, with_language_filter=True, with_language_properties=True)

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
        '--no-legend',
        action='store_true',
        default=False,
        help="Don't add a legend to the map (e.g. because it would be too big).",
    )
    parser.add_argument(
        '--no-open',
        action='store_true',
        default=False,
        help="Don't open the created file.",
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

    data, cms = get_multiparameter(
        args, ds, Glottolog.from_args(args), exclude_lang=lambda lg: lg.lat is None)
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
        if args.test or args.no_open:
            return
        fig.open()  # pragma: no cover
