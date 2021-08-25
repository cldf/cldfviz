import typing
import decimal
import functools
import itertools
import collections

import attr
import pycldf
from pyglottolog.languoids import Languoid

CONTINUOUS = 1
CATEGORICAL = 2


@attr.s
class Language:
    id = attr.ib()
    name = attr.ib()
    lat = attr.ib()
    lon = attr.ib()

    @classmethod
    def from_object(cls, obj, glottolog=None):
        lonlat = obj.lonlat
        glang = (glottolog or {}).get(getattr(obj.cldf, 'glottocode', obj.id))
        if (not lonlat) and glang and glang.latitude is not None:
            lonlat = (glang.longitude, glang.latitude)
        if lonlat and lonlat[0] is not None:
            return cls(
                id=obj.id,
                name=getattr(obj.cldf, 'name', obj.id),
                lon=float(lonlat[0]),
                lat=float(lonlat[1]))

    @classmethod
    def from_glottolog(cls, lid, glottolog):
        if glottolog:
            glang = glottolog.get(lid)
            if glang and glang.latitude is not None:
                return cls(id=glang.id, name=glang.name, lat=glang.latitude, lon=glang.longitude)


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
                 include_missing: bool = False,
                 glottolog: typing.Optional[typing.Dict[str, Languoid]] = None,
                 language_properties: typing.Optional[typing.Iterable[str]] = None):
        self.include_missing = include_missing
        language_properties = language_properties or []
        langs = {lg.id: Language.from_object(lg, glottolog=glottolog)
                 for lg in ds.objects('LanguageTable')} if 'LanguageTable' in ds else {}
        langs = {k: v for k, v in langs.items() if v}
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
            comp = 'ValueTable' if ds.module == 'StructureDataset' else 'FormTable'
            for val in ds.iter_rows(comp, *colmap):
                if ((val['value'] is not None) or self.include_missing) and \
                        val['parameterReference'] in self.parameters:
                    lang = langs.get(val['languageReference'])
                    if not lang:
                        lang = Language.from_glottolog(val['languageReference'], glottolog)
                    if lang:
                        self.languages[val['languageReference']] = lang
                        self.values.append(Value.from_row(val, codes))
                        self.parameters[val['parameterReference']] \
                            .value_to_code[str(val['value'])] = \
                            val.get('codeReference') or val['Value']
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
            for lang in ds.iter_rows('LanguageTable', 'id', 'name'):
                if lang['id'] in langs:
                    self.languages.setdefault(lang['id'], langs[lang['id']])
                    self.values.append(Value(
                        v='y',
                        pid='__language__',
                        lid=lang['id'],
                        code='language'))

        for p in self.parameters.values():
            if p.id in codes:
                p.domain = codes[p.id]
            else:
                vals = [v for v in self.values if v.pid == p.id]
                if all(v.float is not None for v in vals) and len(set(v.v for v in vals)) > 8:
                    p.type = CONTINUOUS
                    p.domain = (min(v.float for v in vals), max(v.float for v in vals))
                else:
                    p.domain = collections.OrderedDict([
                        (v, v) for v in sorted(set(vv.v for vv in vals), key=lambda vv: str(vv))])

    def iter_languages(self) \
            -> typing.Iterator[typing.Tuple[Language, typing.Dict[str, typing.List[Value]]]]:
        for lid, values in itertools.groupby(sorted(self.values), lambda v: v.lid):
            values = {pid: list(vals) for pid, vals in itertools.groupby(values, lambda v: v.pid)}
            values = collections.OrderedDict(
                [(pid, values.get(pid, [])) for pid in self.parameters])
            if self.include_missing or all(bool(v) for v in values.values()):
                yield self.languages[lid], values
