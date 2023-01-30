"""
Plots a phylogeny as SVG.
"""
import pathlib

from pycldf.cli_util import add_dataset, get_dataset
from pycldf.trees import TreeTable
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING

from cldfviz.cli_util import (
    add_testable, add_language_filter, get_language_filter, add_open, write_output,
)
from cldfviz.tree import render


def register(parser):
    add_testable(parser)
    add_dataset(parser)
    add_language_filter(parser)
    add_catalog_spec(parser, 'glottolog', default=IGNORE_MISSING)
    parser.add_argument(
        '--glottolog-links',
        help="Turn language labels into links to Glottolog (where possible).",
        action='store_true',
        default=False)
    parser.add_argument(
        '--ascii-art',
        help="Only print tree as ASCII graphic to the terminal.",
        action='store_true',
        default=False)
    parser.add_argument(
        '--name-as-label',
        action='store_true',
        default=False)
    parser.add_argument('--title', default=None)
    parser.add_argument('--width', type=int, default=500)
    parser.add_argument(
        '--tree-id',
        help="ID in TreeTable of the dataset, identifying the tree to plot.",
        default=None)
    parser.add_argument(
        '--styles',
        help="Python dict suitable to pass into `toytree.tree.draw` (or path to a text file "
             "containing such a dict). "
             "See https://toytree.readthedocs.io/en/latest/8-styling.html#",
        default='{}')
    add_open(parser)


def run(args):
    cldf = get_dataset(args)
    res = None

    for tree in TreeTable(cldf):
        if args.tree_id is None or (args.tree_id == tree.id):
            if args.ascii_art:
                print(tree.newick(strip_comments=True).ascii_art())
                return
            if args.title:
                legend = args.title
            else:
                legend = tree.name
                dcol = cldf.get(('TreeTable', 'description'))
                if dcol:
                    legend += ' - {}'.format(tree.row[dcol.name])

                if tree.tree_branch_length_unit:
                    legend += ' with branches in {}'.format(tree.tree_branch_length_unit)
            glangs = {}
            if args.glottolog and args.glottolog_links:  # pragma: no cover
                glangs = {lg.id: lg.name for lg in args.glottolog.api.languoids()}
            if pathlib.Path(args.styles).exists():
                args.styles = pathlib.Path(args.styles).read_text(encoding='utf8')
            lf = get_language_filter(args)
            res = render(
                tree,
                glottolog_mapping={
                    r['id']: (r['glottocode'], glangs.get(r['glottocode']) or '') for r in
                    cldf.iter_rows('LanguageTable', 'id', 'glottocode') if r['glottocode']},
                legend=legend,
                width=args.width,
                styles=eval(args.styles),
                with_glottolog_links=args.glottolog_links,
                labels={
                    r['id']: r['name']
                    for r in cldf.iter_rows('LanguageTable', 'id', 'name')
                } if args.name_as_label else None,
                leafs=[lg.id for lg in cldf.objects('LanguageTable') if lf(lg)] if lf else None,
            )
            break
    else:
        raise ValueError('no matching tree found!')  # pragma: no cover
    write_output(args, res)
