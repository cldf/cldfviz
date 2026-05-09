"""
Plots a phylogeny as SVG.
"""
import argparse
import pathlib

from cldfviz.cli_util import (
    add_testable, add_language_filter, get_language_filter, add_open, write_output,
    get_multiparameter, add_multiparameter, add_tree, get_tree,
    add_secondary_dataset, get_secondary_dataset,
)
from cldfviz.glottolog import Glottolog
from cldfviz.colormap import weighted_colors
from cldfviz.tree import render, TreeData


def register(parser: argparse.ArgumentParser):  # pylint: disable=C0116
    add_testable(parser)
    add_tree(parser)
    add_language_filter(parser)
    Glottolog.add(parser)
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
    parser.add_argument('--height', type=int, default=None)
    parser.add_argument(
        '--styles',
        help="Python dict suitable to pass into `toytree.tree.draw` (or path to a text file "
             "containing such a dict). "
             "See https://toytree.readthedocs.io/en/latest/8-styling.html#",
        default='{}')
    add_secondary_dataset(parser, '--data-dataset')
    parser.add_argument(
        '--tree-label-property',
        help="Name of the language property used to identify languages in the tree.",
        default=None)
    add_multiparameter(parser)
    add_open(parser)


def run(args: argparse.Namespace):  # pylint: disable=C0116
    cldf = get_secondary_dataset(args, 'data_dataset')
    nwk, tree, treeds = get_tree(args, glottolog=Glottolog.from_args(args))

    if args.ascii_art:
        print(nwk.ascii_art())
        return

    data = None
    if args.parameters:
        mp, cms = get_multiparameter(args, cldf, None)
        values = {lang.id: weighted_colors(val, cms) for lang, val in mp.iter_languages()}
        data = TreeData(values=values, parameters=mp.parameters, colormaps=cms)

    glangs = {}
    if args.glottolog and args.glottolog_links:  # pragma: no cover
        glangs = {lg.id: lg.name for lg in args.glottolog.api.languoids()}
    if pathlib.Path(args.styles).exists():
        args.styles = pathlib.Path(args.styles).read_text(encoding='utf8')
    lf = get_language_filter(args)

    lid2tree = {}
    lid2name = {}
    if cldf:
        # We need to collect two mappings here:
        # 1. Language ID to node labels used in the tree.
        # 2. Language ID to names, in case we need to rename the leaf nodes.
        for lg in cldf.iter_rows('LanguageTable', 'id', 'glottocode', 'name'):
            lid2tree[lg['id']] = \
                lg[args.tree_label_property] if args.tree_label_property else lg['id']
            lid2name[lg['id']] = lg['name']

    if data and args.tree_label_property:
        # Re-key the values so that they can be picked up when adding markers to the tree.
        data.values = {lid2tree[lid]: vals for lid, vals in data.values.items() if lid2tree[lid]}

    kw = dict(  # pylint: disable=R1735
        legend=_get_legend(args, tree, treeds),
        width=args.width,
        height=args.height,
        styles=eval(args.styles),  # pylint: disable=W0123
        with_glottolog_links=args.glottolog_links,
        data=data,
        labels=_get_labels(args, cldf, treeds, lid2tree, lid2name),
    )
    if treeds:
        kw.update(
            tree_object=tree,
            glottolog_mapping={
                r['id']: (r['glottocode'], glangs.get(r['glottocode']) or '') for r in
                treeds.iter_rows('LanguageTable', 'id', 'glottocode') if r['glottocode']},
            leafs=[lg.id for lg in treeds.objects('LanguageTable') if lf(lg)] if lf else None,
        )
    write_output(args, render(nwk, **kw))


def _get_labels(args, cldf, treeds, lid2tree, lid2name):
    if args.name_as_label:
        if cldf:
            # If we have data, we assume that the tree nodes should get data language names.
            return {tid: lid2name[lid] for lid, tid in lid2tree.items()}
        if treeds:
            # If we have a tree from a tree dataset, "name-as-label" refers to language names in
            # this dataset.
            return {r['id']: r['name'] for r in treeds.iter_rows('LanguageTable', 'id', 'name')}
    return None


def _get_legend(args: argparse.Namespace, tree, treeds) -> str:
    if args.title:
        return args.title

    legend = tree.name if tree else ''
    if treeds:
        dcol = treeds.get(('TreeTable', 'description'))
        if dcol:
            legend += f"{' - ' if legend else ''}{tree.row[dcol.name]}"
    if tree and tree.tree_branch_length_unit:
        legend += f' with branches in {tree.tree_branch_length_unit}'
    return legend
