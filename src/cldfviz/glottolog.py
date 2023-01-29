"""
We provide a Glottolog object that abstracts whether the data is accessed via pyglottolog.Glottolog
from glottolog/glottolog-like data or via pycldf.Dataset from glottolog/glottolog-cldf-like
data.
"""
import argparse
import collections

import attr
from pycldf import Dataset
from pycldf.ext import discovery
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING
from clldutils.clilib import PathType
import newick

try:
    import pyglottolog
except ImportError:  # pragma: no cover
    pyglottolog = None

__all__ = ['Glottolog', 'Languoid']


@attr.s
class Languoid:
    id = attr.ib()
    name = attr.ib()
    lat = attr.ib()
    lon = attr.ib()

    @classmethod
    def from_dict(cls, d):
        return cls(id=d['id'], name=d['name'], lat=d['latitude'], lon=d['longitude'])

    @classmethod
    def from_languoid(cls, lang):
        return cls(id=lang.id, name=lang.name, lat=lang.latitude, lon=lang.longitude)


class Glottolog(collections.UserDict):
    def __init__(self, api_or_dataset):
        self.api = api_or_dataset
        super().__init__()
        if isinstance(self.api, Dataset):
            for row in self.api.iter_rows('LanguageTable', 'id', 'name', 'latitude', 'longitude'):
                self[row['id']] = Languoid.from_dict(row)
        else:
            for lang in self.api.languoids():
                self[lang.id] = Languoid.from_languoid(lang)

    @staticmethod
    def add(parser):
        add_catalog_spec(parser, 'glottolog', default=IGNORE_MISSING)
        parser.add_argument(
            '--glottolog-cldf',
            default=None,
            help="Dataset locator for the glottolog-cldf dataset.")
        try:
            parser.add_argument(
                '--download-dir',
                type=PathType(type='dir'),
                help='An existing directory to use for downloading a dataset (if necessary).',
                default=None,
            )
        except argparse.ArgumentError:
            pass

    @classmethod
    def from_args(cls, args):
        if args.glottolog_cldf:
            return cls(discovery.get_dataset(args.glottolog_cldf, download_dir=args.download_dir))
        if args.glottolog:
            if hasattr(args.glottolog, 'api'):
                # cldfbench has already initialized a pyglottolog.Glottolog instance!
                return cls(args.glottolog.api)
            if args.glottolog != IGNORE_MISSING:
                assert pyglottolog
                return cls(pyglottolog.Glottolog(args.glottolog))

    def newick(self, gc):
        if isinstance(self.api, Dataset):
            for row in self.api.iter_rows(
                    'ValueTable', 'languageReference', 'parameterReference', 'value'):
                if row['languageReference'] == gc and \
                        row['parameterReference'] == 'subclassification':
                    return newick.loads(row['value'])[0]
        else:
            return self.api.languoid(gc).newick_node(template="{l.id}")
