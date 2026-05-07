"""
We provide a Glottolog object that abstracts whether the data is accessed via pyglottolog.Glottolog
from glottolog/glottolog-like data or via pycldf.Dataset from glottolog/glottolog-cldf-like
data.
"""
import argparse
import collections
import dataclasses
from typing import Optional

from pycldf import Dataset
from pycldf.ext import discovery
from cldfbench.cli_util import add_catalog_spec, IGNORE_MISSING
import newick

try:
    import pyglottolog
except ImportError:  # pragma: no cover
    pyglottolog = None

from cldfviz.util import add_download_dir

__all__ = ['Glottolog', 'Languoid']


@dataclasses.dataclass
class Languoid:
    """Glottolog languoid data for plotting on a map."""
    id: str
    name: str
    lat: Optional[float]
    lon: Optional[float]

    @classmethod
    def from_dict(cls, d):
        """Factory for glottolog-cldf .iter_rows access."""
        return cls(id=d['id'], name=d['name'], lat=d['latitude'], lon=d['longitude'])

    @classmethod
    def from_languoid(cls, lang):
        """Factory for pyglottolog API access."""
        return cls(id=lang.id, name=lang.name, lat=lang.latitude, lon=lang.longitude)


class Glottolog(collections.UserDict):
    """Wrapper, unifying access to Glottolog data either via pyglottolog or glottolog-cldf."""
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
    def add(parser: argparse.ArgumentParser):
        """Add cli option."""
        add_catalog_spec(parser, 'glottolog', default=IGNORE_MISSING)
        parser.add_argument(
            '--glottolog-cldf',
            default=None,
            help="Dataset locator for the glottolog-cldf dataset.")
        add_download_dir(parser)

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> Optional['Glottolog']:
        """Instantiate object from cli options."""
        if args.glottolog_cldf:
            return cls(discovery.get_dataset(args.glottolog_cldf, download_dir=args.download_dir))
        if args.glottolog:
            if hasattr(args.glottolog, 'api'):
                # cldfbench has already initialized a pyglottolog.Glottolog instance!
                return cls(args.glottolog.api)
            if args.glottolog != IGNORE_MISSING:
                assert pyglottolog
                return cls(pyglottolog.Glottolog(args.glottolog))
        return None  # pragma: no cover

    def newick(self, gc: str) -> Optional[newick.Node]:
        """Get the newick representation of the subclassification starting at gc."""
        if isinstance(self.api, Dataset):
            for row in self.api.iter_rows(
                    'ValueTable', 'languageReference', 'parameterReference', 'value'):
                if row['languageReference'] == gc and \
                        row['parameterReference'] == 'subclassification':
                    return newick.loads(row['value'])[0]
            return None  # pragma: no cover
        return self.api.languoid(gc).newick_node(template="{l.id}")
