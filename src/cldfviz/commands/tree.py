"""
Plots a phylogeny as SVG.
"""
import webbrowser

from clldutils.clilib import PathType
from pycldf.cli_util import add_dataset, get_dataset
from pycldf.trees import TreeTable
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING

from cldfviz.cli_util import add_testable
from cldfviz.tree import render


def register(parser):
    add_testable(parser)
    add_dataset(parser)
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
    parser.add_argument('--title', default=None)
    parser.add_argument('--width', type=int, default=500)
    parser.add_argument(
        '--tree-id',
        help="ID in TreeTable of the dataset, identifying the tree to plot.",
        default=None)
    parser.add_argument(
        '--styles',
        help="Python dict suitable to pass into `toytree.tree.draw`. "
             "See https://toytree.readthedocs.io/en/latest/8-styling.html#",
        default='{}')
    parser.add_argument(
        'output',
        type=PathType(must_exist=False),
        help="Path to which to write the SVG file.",
    )


def run(args):
    cldf = get_dataset(args)

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
            render(
                tree,
                args.output,
                glottolog_mapping={
                    r['id']: (r['glottocode'], glangs.get(r['glottocode']) or '') for r in
                    cldf.iter_rows('LanguageTable', 'id', 'glottocode') if r['glottocode']},
                legend=legend,
                width=args.width,
                styles=eval(args.styles),
                with_glottolog_links=args.glottolog_links,
            )
            break
    if not args.test:  # pragma: no cover
        webbrowser.open(args.output.resolve().as_uri())
