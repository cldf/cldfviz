"""
Plot values for a parameter of the dataset against a Glottolog family tree.

FIXME:
Make configurable:
- tree (from file? from string? from phlorest phylogeny!)
  - get the summary tree from a CLDF Phylogeny dataset
  - match nodes by Glottocode
- tree labels (which property from LanguageTable?)
- value labels and order
- config file?

Make this work with
- metadata-free datasets (i.e. values.csv only, metadata from Glottolog)

"""
import io
import pathlib
import webbrowser
import collections

import newick
from pyglottolog.objects import Glottocode
from pycldf.cli_util import add_dataset, get_dataset
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING

try:
    import pandas as pd
    from Bio import Phylo
    import yaml
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


def yaml_type(s):
    return yaml.load(io.StringIO(s), yaml.SafeLoader)


def iter_ltm_options():
    h = []
    if lingtreemaps:
        for line in pathlib.Path(lingtreemaps.__file__).parent\
                .joinpath('data', 'default_config.yaml').read_text(encoding='utf8').split('\n'):
            line = line.strip()
            if line.startswith('#'):
                h.append(line[1:].strip())
            elif line:
                opt, _, default = line.partition(':')
                opt, val, help = opt.strip(), yaml_type(default.strip()), ' '.join(h)
                if opt == 'filename':
                    help = "The filename. If unspecified, the parameter ID will be used."
                yield opt, val, help
                h = []


def register(parser):
    add_dataset(parser)
    add_catalog_spec(parser, 'glottolog', default=IGNORE_MISSING)
    parser.add_argument('parameter')
    parser.add_argument(
        'tree',
        help="Tree specified as Glottocode (interpreted as the root of the Glottolog tree), "
             "Newick formatted string or path to a file containing the Newick formatted "
             "tree.")
    parser.add_argument(
        '--tree-label-property',
        help="Name of the language property used to identify languages in the tree.",
        default='glottocode')
    for opt, default, help in iter_ltm_options():
        parser.add_argument(
            '--ltm-{}'.format(opt.replace('_', '-')),
            default=default,
            type=yaml_type,
            help=help)


def run(args):
    if lingtreemaps is None:
        args.log.error(
            'install cldfviz with lingtreemaps, running "pip install cldfviz[lingtreemaps]"')
        return


    ds = get_dataset(args)

    # 1. Get the tree ...
    if Glottocode.pattern.match(args.tree):
        tree = args.glottolog.api.languoid(args.tree).newick_node(template="{l.id}")
    elif pathlib.Path(args.tree).exists():
        tree = newick.read(args.tree)[0]
    else:
        tree = newick.loads(args.tree)
    # ... and its set of node labels.
    nodes = {n.name for n in tree.walk()}

    # 2. Get the set of matching languages in the dataset.
    id2name = {}
    treelabel2name = {}
    languages = []
    for lang in ds.iter_rows('LanguageTable', 'id', 'glottocode', 'name', 'latitude', 'longitude'):
        treelabel = lang[args.tree_label_property]
        if treelabel in nodes:  # The language is in the tree.
            name = newick_safe_name(lang['name'])
            languages.append(dict(ID=name, Latitude=lang['latitude'], Longitude=lang['longitude']))
            id2name[lang['id']] = name
            treelabel2name[treelabel] = name

    # 3. Get the set of values.
    if 'CodeTable' in ds:
        codes = collections.OrderedDict([
            (c['id'], c['name'])
            for c in ds.iter_rows('CodeTable', 'id', 'name', 'parameterReference')
            if c['parameterReference'] == args.parameter])
    else:
        codes = None
    values = []
    for val in ds.iter_rows('ValueTable', 'parameterReference', 'languageReference', 'codeReference', 'value'):
        if val['parameterReference'] == args.parameter and val['languageReference'] in id2name:
            values.append(dict(
                Clade=id2name[val['languageReference']],
                Value=val['value'] if not codes else codes[val['codeReference']]))
    # Sort values by value/code. ltm will just use this order.
    values = sorted(values, key=lambda v: v['Value'] if not codes else list(codes.values()).index(v['Value']))

    # 4. Prune the tree to only the languages in the dataset.
    tree.prune_by_names(list(treelabel2name), inverse=True)

    # 5. Rename the tree nodes
    def rename(n):
        if n.name in treelabel2name:
            n.name = treelabel2name[n.name]
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

    kwargs = {k.replace('ltm_', ''): v for k, v in args.__dict__.items() if k.startswith('ltm_')}
    kwargs['filename'] = kwargs['filename'] or args.parameter
    fname = pathlib.Path(
        kwargs['filename'] if '.' in kwargs['filename'] else '{filename}.{file_format}'.format(**kwargs))
    lingtreemaps.plot(languages, Phylo.read(io.StringIO(tree.newick), 'newick'), values, **kwargs)
    args.log.info('Output written to: {}'.format(fname))
    webbrowser.open(fname.resolve().as_uri())
