import typing
import decimal
import functools
import itertools
import collections

import attr
import pycldf
from pycldf import orm
from pyglottolog.languoids import Languoid

from cldfviz.glottolog import Glottolog

CONTINUOUS = 1
CATEGORICAL = 2


class Language:
    def __init__(self, obj, glottolog: typing.Optional[Glottolog] = None):
        glottolog = glottolog or {}
        if isinstance(obj, str):
            obj = glottolog[obj]
            self.id = obj.id
            self.name = obj.name
            self.lat = obj.lat
            self.lon = obj.lon
        elif isinstance(obj, orm.Language):
            self.id = obj.id
            self.name = obj.name
            self.lat = obj.cldf.latitude
            self.lon = obj.cldf.longitude
            if self.lat is None and obj.cldf.glottocode in glottolog:
                # FIXME: If a language is mapped to multiple glottocodes, we could try to take the
                # midpoint of these as coordinate. (If longitudes have different signs, transform
                # back and forth appropriately, i.e. lon < 0 => lon = 360 - abs(lon))
                # shapely.geometry.MultiPoint([(0, 0), (1, 1)]).convex_hull.centroid
                self.lat = glottolog[obj.cldf.glottocode].lat
                self.lon = glottolog[obj.cldf.glottocode].lon
        else:
            raise TypeError(obj)
        self.lat = float(self.lat) if self.lat is not None else self.lat
        self.lon = float(self.lon) if self.lon is not None else self.lon


@attr.s
class Parameter:
    id = attr.ib()
    name = attr.ib()
    type = attr.ib(default=CATEGORICAL)
    domain = attr.ib(default=attr.Factory(dict))
    value_to_code = attr.ib(default=attr.Factory(dict))

    @classmethod
    def from_object(cls, obj):
        return cls(id=obj.id, name=getattr(obj.cldf, 'name', obj.id))


@functools.total_ordering
@attr.s(order=False, eq=False)
class Value:
    v = attr.ib()
    pid = attr.ib()
    lid = attr.ib()
    code = attr.ib()
    float = attr.ib(default=None)

    def __attrs_post_init__(self):
        try:
            self.float = float(self.v)
        except (ValueError, TypeError):
            self.float = None

    def __eq__(self, other):
        return (self.lid, self.pid, self.v) == (other.lid, other.pid, other.v)

    def __lt__(self, other):
        return (self.lid, self.pid, self.v) < (other.lid, other.pid, other.v)

    @classmethod
    def from_row(cls, row, codes):
        return cls(
            v=row.get('codeReference') or row['value'],
            lid=row['languageReference'],
            pid=row['parameterReference'],
            code=codes[row['parameterReference']][row['codeReference']]
            if row['parameterReference'] in codes and row['codeReference'] else None,
        )


class MultiParameter:
    """
    Extracts relevant data about a set of parameters from a CLDF dataset.

    :ivar parameters: `OrderedDict` mapping parameter IDs to :class:`Parameter` instances.
    """
    def __init__(self,
                 ds: pycldf.Dataset,
                 pids: typing.Iterable[str],
                 datatypes: typing.Iterable[str] = None,
                 include_missing: bool = False,
                 glottolog: typing.Optional[typing.Dict[str, typing.Union[dict, Languoid]]] = None,
                 language_properties: typing.Optional[typing.Iterable[str]] = None,
                 language_filter: typing.Optional[typing.Callable[[orm.Object], bool]] = None):
        self.include_missing = include_missing
        language_properties = language_properties or []

        if 'LanguageTable' in ds:
            langs = {lg.id: Language(lg, glottolog=glottolog)
                     for lg in ds.objects('LanguageTable')
                     if language_filter is None or language_filter(lg)}
        else:
            langs = {gc: Language(gc, glottolog=glottolog)
                     for gc in set(r['languageReference'] for r in
                                   ds.iter_rows('ValueTable', 'languageReference'))
                     if gc in glottolog}

        langs = {k: v for k, v in langs.items() if v and v.lat is not None}
        params = {p.id: Parameter.from_object(p)
                  for p in ds.objects('ParameterTable')} if 'ParameterTable' in ds else {}
        # For each pid, we add a parameter:
        self.parameters = collections.OrderedDict(
            [(pid, params.get(pid, Parameter(id=pid, name=pid))) for pid in pids])
        # For each language-property we add a parameter:
        for language_property in language_properties:
            self.parameters[language_property] = Parameter(
                id=language_property, name=language_property)
        if not self.parameters:
            # No parameters and no language property specified: Just plot language locations.
            self.parameters['__language__'] = Parameter(id='__language__', name='language')

        codes = collections.defaultdict(collections.OrderedDict)
        if 'CodeTable' in ds:
            for row in ds.iter_rows('CodeTable', 'id', 'parameterReference', 'name'):
                if row['parameterReference'] in self.parameters:
                    codes[row['parameterReference']][row['id']] = row['name']
        language_rows = []
        for i, language_property in enumerate(language_properties):
            if i == 0:
                language_rows = list(ds.iter_rows('LanguageTable', 'id', 'name'))
            if not all(isinstance(v[language_property], (int, float, decimal.Decimal))
                       for v in language_rows if v[language_property] is not None):
                codes[language_property] = collections.OrderedDict([
                    (p, p) for p in sorted(
                        set(r[language_property] for r in language_rows
                            if r[language_property] is not None))
                ])
        self.languages = collections.OrderedDict()
        self.values = []
        colmap = ['languageReference', 'parameterReference', 'value']
        if codes:
            colmap.append('codeReference')
        if pids:
            seen = {pid: False for pid in pids}
            comp = 'ValueTable' if ds.module == 'StructureDataset' else 'FormTable'
            for val in ds.iter_rows(comp, *colmap):
                seen[val['parameterReference']] = True
                if ((val['value'] is not None) or self.include_missing) and \
                        val['parameterReference'] in self.parameters:
                    lang = langs.get(val['languageReference'])
                    if lang:
                        self.languages[val['languageReference']] = lang
                        self.values.append(Value.from_row(val, codes))
                        self.parameters[val['parameterReference']] \
                            .value_to_code[str(val['value'])] = \
                            val.get('codeReference') or val['Value']
            if not all(seen[pid] for pid in pids):
                raise ValueError('Invalid parameter ID')
        for language_property in language_properties:
            for lang in language_rows:
                if (lang['id'] in langs) and lang[language_property] is not None:
                    if lang['id'] in langs:
                        self.languages.setdefault(lang['id'], langs[lang['id']])
                        self.values.append(Value(
                            v=lang[language_property],
                            pid=language_property,
                            lid=lang['id'],
                            code=language_property))
        if not self.values:
            # No parameters and no language property specified: Just plot language locations.
            if 'LanguageTable' not in ds:
                for lid, lang in langs.items():
                    self.languages.setdefault(lid, lang)
                    self.values.append(Value(
                        v='y',
                        pid='__language__',
                        lid=lid,
                        code='language'))
            else:
                for lang in ds.iter_rows('LanguageTable', 'id', 'name'):
                    if lang['id'] in langs:
                        self.languages.setdefault(lang['id'], langs[lang['id']])
                        self.values.append(Value(
                            v='y',
                            pid='__language__',
                            lid=lang['id'],
                            code='language'))

        for i, p in enumerate(self.parameters.values()):
            if p.id in codes:
                p.domain = codes[p.id]
            else:
                vals = [v for v in self.values if v.pid == p.id]
                if all(v.float is not None for v in vals) and \
                        (len(set(v.v for v in vals)) > 8 or  # noqa: W504
                         (datatypes and datatypes[i] == 'number')):
                    p.type = CONTINUOUS
                    p.domain = (min(v.float for v in vals), max(v.float for v in vals))
                else:
                    p.domain = collections.OrderedDict([
                        (v, v) for v in sorted(set(vv.v for vv in vals), key=lambda vv: str(vv))])

    def __str__(self):  # pragma: no cover
        return str(self.parameters)

    def iter_languages(self) \
            -> typing.Iterator[typing.Tuple[Language, typing.Dict[str, typing.List[Value]]]]:
        for lid, values in itertools.groupby(sorted(self.values), lambda v: v.lid):
            values = {pid: list(vals) for pid, vals in itertools.groupby(values, lambda v: v.pid)}
            values = collections.OrderedDict(
                [(pid, values.get(pid, [])) for pid in self.parameters])
            if self.include_missing or all(bool(v) for v in values.values()):
                yield self.languages[lid], values
