"""
Plot values for parameters in a CLDF StructureDataset on a map.

Usage examples:
- plot languages of a dataset:
  cldfbench cldfviz.map PATH/TO/DATASET --language-labels
- plot values of one parameter:
  cldfbench cldfviz.map PATH/TO/DATASET --parameters PID
- plot values of a column in the dataset's LanguageTable:
  cldfbench cldfviz.map PATH/TO/DATASET --language-property Macroarea
"""
import pathlib

from pycldf.cli_util import get_dataset, add_dataset
from clldutils.clilib import PathType
from cldfbench.cli_util import add_catalog_spec

from cldfviz.colormap import Colormap, COLORMAPS
from cldfviz.multiparameter import MultiParameter, CONTINUOUS, CATEGORICAL
from cldfviz.map import Map
from cldfviz.cli_util import add_testable

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
    parser.add_argument(
        '--parameters',
        default=[],
        type=lambda s: s.split(','),
        help="Comma-separated Parameter IDs, specifying the values to plot on the map. If not "
             "specified, all languages in the dataset will be plotted.",
    )
    parser.add_argument(
        '--colormaps',
        default=[],
        type=lambda s: s.split(','),
        help="Comma-separated names of colormaps to use for the respective parameter. Choose from "
             "{} for categorical and from {} for continuous parameters.".format(
            join_quoted(COLORMAPS[CATEGORICAL]), join_quoted(COLORMAPS[CONTINUOUS])),
    )
    parser.add_argument(
        '--language-property',
        help="Plot values of a language property, i.e. a column in the dataset's LanguageTable.",
        default=None,
    )
    parser.add_argument(
        '--language-property-colormap',
        default='tol',
        help="Name of colormap to use for the language property. See help for --colormaps for "
             "choices",
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
        ds, args.parameters, glottolog=glottolog, language_property=args.language_property)
    if args.colormaps:
        if args.language_property:
            args.colormaps.append(args.language_property_colormap)
        assert len(args.colormaps) == len(data.parameters)
    else:
        args.colormaps = [None] * len(data.parameters)
    cms = {pid: Colormap(data.parameters[pid].domain, name=cm)
           for pid, cm in zip(data.parameters, args.colormaps)}

    with FORMATS[args.format](data.languages.values(), args) as fig:
        for lang, values in data.iter_languages():
            fig.add_language(lang, values, cms)

        fig.add_legend(data.parameters, cms)

        args.log.info('Output written to: {}'.format(args.output))
        if not args.test:
            fig.open()  # pragma: no cover
