import functools
import itertools
import collections

import attr

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
        if lonlat:
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

    @classmethod
    def from_object(cls, obj):
        return cls(id=obj.id, name=getattr(obj.cldf, 'name', obj.id))


@functools.total_ordering
@attr.s(order=False)
class Value:
    v = attr.ib()
    pid = attr.ib()
    lid = attr.ib()
    code = attr.ib()
    float = attr.ib(default=None)

    def __attrs_post_init__(self):
        try:
            self.float = float(self.v)
        except ValueError:
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
            if row['parameterReference'] in codes else None,
        )


class MultiParameter:
    def __init__(self, ds, pids, include_missing=False, glottolog=None, language_property=None):
        #
        # FIXME: If no pids, look for language_col, if none either, make synthetic "has_language"
        # parameter.
        #
        langs = {lg.id: Language.from_object(lg, glottolog=glottolog)
                 for lg in ds.objects('LanguageTable')} if 'LanguageTable' in ds else {}
        params = {p.id: Parameter.from_object(p)
                  for p in ds.objects('ParameterTable')} if 'ParameterTable' in ds else {}
        self.parameters = collections.OrderedDict(
            [(pid, params.get(pid, Parameter(id=pid, name=pid))) for pid in pids])
        if language_property:
            self.parameters[language_property] = Parameter(
                id=language_property, name=language_property)
        elif not pids:
            # No parameters and no language property specified: Just plot language locations.
            self.parameters['language'] = Parameter(id='language', name='language')

        codes = collections.defaultdict(collections.OrderedDict)
        if 'CodeTable' in ds:
            for row in ds.iter_rows('CodeTable', 'id', 'parameterReference', 'name'):
                if row['parameterReference'] in self.parameters:
                    codes[row['parameterReference']][row['id']] = row['name']
        if language_property:
            codes[language_property] = collections.OrderedDict([
                (p, p) for p in sorted(set(r[language_property] for r in ds['LanguageTable']))
            ])
        self.languages = collections.OrderedDict()
        self.values = []
        colmap = ['languageReference', 'parameterReference', 'value']
        if codes:
            colmap.append('codeReference')
        for val in ds.iter_rows('ValueTable', *colmap):
            if (val['value'] is not None) and val['parameterReference'] in self.parameters:
                lang = langs.get(val['languageReference'])
                if not lang:
                    lang = Language.from_glottolog(val['languageReference'], glottolog)
                if lang:
                    self.languages[val['languageReference']] = lang
                    self.values.append(Value.from_row(val, codes))
        if language_property:
            for lang in ds.iter_rows('LanguageTable', 'id', 'name'):
                self.languages.setdefault(lang['id'], langs[lang['id']])
                self.values.append(Value(
                    v=lang[language_property],
                    pid=language_property,
                    lid=lang['id'],
                    code=language_property))
        elif not pids:
            # No parameters and no language property specified: Just plot language locations.
            for lang in ds.iter_rows('LanguageTable', 'id', 'name'):
                self.languages.setdefault(lang['id'], langs[lang['id']])
                self.values.append(Value(
                    v='y',
                    pid='language',
                    lid=lang['id'],
                    code='language'))

        for p in self.parameters.values():
            if p.id in codes:
                p.domain = codes[p.id]
            else:
                vals = [v for v in self.values if v.pid == p.id]
                if all(v.float is not None for v in vals):
                    p.type = CONTINUOUS
                    p.domain = (min(v.float for v in vals), max(v.float for v in vals))
                else:
                    p.domain = collections.OrderedDict([
                        (v, v) for v in sorted(set(vv.v for vv in vals), key=lambda vv: str(vv))])

        self.include_missing = include_missing

    def iter_languages(self):
        for lid, values in itertools.groupby(sorted(self.values), lambda v: v.lid):
            values = {pid: list(vals) for pid, vals in itertools.groupby(values, lambda v: v.pid)}
            values = collections.OrderedDict([(pid, values.get(pid, [])) for pid in self.parameters])
            if self.include_missing or all(bool(v) for v in values.values()):
                yield self.languages[lid], values