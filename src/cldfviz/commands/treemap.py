"""
Plot values for a parameter of the dataset against a Glottolog family tree.

FIXME:
Make configurable:
- output file
- output format
- tree (from file? from string?)
- tree labels (which property from LanguageTable?)
- value labels and order

Make this work with
- combined parameters
- metadata-free datasets (i.e. values.csv only, metadata from Glottolog)
"""
import io
import pathlib
import webbrowser
import collections

from pycldf.cli_util import add_dataset, get_dataset
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING

try:
    import pandas as pd
    from Bio import Phylo
    import lingtreemaps
except ImportError:
    lingtreemaps = None


class DF:
    def __init__(self):
        self.df = None
        self.acc = collections.defaultdict(list)

    def __enter__(self):
        return self

    def add(self, item):
        if self.df is None:
            self.df = pd.DataFrame(columns=list(item))
        for k, v in item.items():
            self.acc[k].append(v)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.acc.items():
            self.df[k] = v


def df_from_dicts(dicts):
    with DF() as df:
        for d in dicts:
            df.add(d)
    return df.df


def newick_safe_name(s):
    return s.replace(' ', '_').replace('(', '').replace(')', '').replace("'", '')


def register(parser):
    add_dataset(parser)
    add_catalog_spec(parser, 'glottolog', default=IGNORE_MISSING)
    parser.add_argument('parameter')
    parser.add_argument('root')


def run(args):
    if lingtreemaps is None:
        args.log.error(
            'install cldfviz with lingtreemaps, running "pip install cldfviz[lingtreemaps]"')
        return
    ds = get_dataset(args)

    # 1. Get the Glottolog family tree, and its set of node names (Glottocodes).
    tree = args.glottolog.api.languoid(args.root).newick_node(template="{l.id}")
    nodes = set()
    tree.visit(lambda n: nodes.add(n.name))

    # 2. Get the set of matching languages in the dataset.
    id2name = {}
    gc2name = {}
    languages = []
    for lang in ds.iter_rows('LanguageTable', 'id', 'glottocode', 'name', 'latitude', 'longitude'):
        if lang['glottocode'] in nodes:  # The language is in the tree.
            name = newick_safe_name(lang['name'])
            languages.append(dict(ID=name, Latitude=lang['latitude'], Longitude=lang['longitude']))
            id2name[lang['id']] = name
            gc2name[lang['glottocode']] = name

    # 3. Get the set of values.
    if 'CodeTable' in ds:
        codes = {
            c['id']: c['name']
            for c in ds.iter_rows('CodeTable', 'id', 'name', 'parameterReference')
            if c['parameterReference'] == args.parameter}
    else:
        codes = None
    values = []
    for val in ds.iter_rows('ValueTable', 'parameterReference', 'languageReference', 'codeReference', 'value'):
        if val['parameterReference'] == args.parameter and val['languageReference'] in id2name:
            #
            # FIXME: rename value to code.name?
            #
            values.append(dict(
                Clade=id2name[val['languageReference']],
                Value=val['value'] if not codes else codes[val['codeReference']]))

    # 4. Prune the tree to only the languages in the dataset.
    tree.prune_by_names(list(gc2name), inverse=True)

    # 5. Rename the tree nodes
    def rename(n):
        if n.name in gc2name:
            n.name = gc2name[n.name]
        return n
    tree.visit(rename)

    # We have to restrict languages and values to what is now a leaf node!
    # I.e. when a language and one of its dialects is in the dataset, we remove the language.
    nodes = set()
    tree.visit(lambda n: nodes.add(n.name if n.is_leaf else None))
    leafs = set(n for n in nodes if n is not None)
    tree.prune_by_names(list(leafs - {v['Clade'] for v in values}))
    languages = df_from_dicts([l for l in languages if l['ID'] in leafs])
    values = df_from_dicts([v for v in values if v['Clade'] in leafs])

    if 1:
        print(tree)
        print(languages)
        print(values)

    #
    # Input: parameterReference,
    #
    fname = pathlib.Path('ut001.svg')
    kwargs = dict(filename=str(fname), file_format='svg')
    #kwargs.update(**lingtreemaps.load_conf('conf.yaml'))
    lingtreemaps.plot(languages, Phylo.read(io.StringIO(tree.newick), 'newick'), values, **kwargs)
    # open plot in browser?

    webbrowser.open(fname.resolve().as_uri())
