import enum
import decimal
import functools
import itertools
import collections
from collections.abc import Iterable, Generator
import dataclasses
from typing import Optional, Callable, Any, Union

import pycldf
from pycldf import orm

from cldfviz.glottolog import Glottolog

PidType = str
CodesDictType = dict[PidType, collections.OrderedDict[str, str]]
ValueDictType = collections.OrderedDict[PidType, list['Value']]
PSEUDO_PARAM_LANGUAGE = '__language__'


class ParameterType(enum.Enum):
    """Types of parameters - categorized by domain."""
    CONTINUOUS = 1
    CATEGORICAL = 2


@dataclasses.dataclass(frozen=True)
class Language:
    """Language metadata to facilitate plotting on a map."""
    id: str
    name: str
    lat: Optional[float]
    lon: Optional[float]

    @staticmethod
    def _optional_float(f):
        return float(f) if f is not None else None

    @classmethod
    def _from_glottocode(cls, glottocode: str, glottolog: Glottolog):
        obj = glottolog[glottocode]
        return cls(obj.id, obj.name, cls._optional_float(obj.lat), cls._optional_float(obj.lon))

    @classmethod
    def _from_object(cls, obj: orm.Language, glottolog: Optional[Glottolog] = None):
        lat = obj.cldf.latitude
        lon = obj.cldf.longitude
        if lat is None and obj.cldf.glottocode in glottolog:
            # FIXME: If a language is mapped to multiple glottocodes, we could try to take the
            # midpoint of these as coordinate. (If longitudes have different signs, transform
            # back and forth appropriately, i.e. lon < 0 => lon = 360 - abs(lon))
            # shapely.geometry.MultiPoint([(0, 0), (1, 1)]).convex_hull.centroid
            lat = glottolog[obj.cldf.glottocode].lat
            lon = glottolog[obj.cldf.glottocode].lon
        return cls(obj.id, obj.name, cls._optional_float(lat), cls._optional_float(lon))

    @staticmethod
    def from_dataset(
            ds: pycldf.Dataset,
            glottolog: Optional[Glottolog] = None,
            language_filter: Optional[Callable[[orm.Language], bool]] = None,
            exclude_lang: Optional[Callable[['Language'], bool]] = None,
    ) -> dict[str, 'Language']:
        """Retrieve a filtered set of languages from a dataset."""
        if 'LanguageTable' in ds:
            langs = {
                lg.id: Language._from_object(lg, glottolog=glottolog)
                for lg in ds.objects('LanguageTable')
                if language_filter is None or language_filter(lg)}
        else:
            glottocodes = {
                r['languageReference'] for r in ds.iter_rows('ValueTable', 'languageReference')}
            langs = {
                gc: Language._from_glottocode(gc, glottolog)
                for gc in glottocodes if glottolog and gc in glottolog}
        return {
            k: v for k, v in langs.items() if v and (exclude_lang is None or not exclude_lang(v))}


@dataclasses.dataclass
class Parameter:
    """Relevant parameter metadata to facilitate plotting of values and a legend."""
    id: str
    name: str
    type: ParameterType = ParameterType.CATEGORICAL
    domain: Union[dict[str, str], tuple[float, float]] = dataclasses.field(default_factory=dict)
    value_to_code: dict = dataclasses.field(default_factory=dict)

    @classmethod
    def from_object(cls, obj):
        return cls(id=obj.id, name=getattr(obj.cldf, 'name', obj.id))

    def set_domain(self, values: Iterable['Value'], codes: CodesDictType, datatype: Optional[str]):
        if self.id in codes:  # A categorical parameter.
            self.domain = codes[self.id]
            return
        vals = [v for v in values if v.pid == self.id]
        distinct_vals = {v.v for v in vals}
        if all(v.float_val is not None for v in vals) and \
                (len(distinct_vals) > 8 or datatype == 'number'):
            self.type = ParameterType.CONTINUOUS
            self.domain = (min(v.float_val for v in vals), max(v.float_val for v in vals))
            return
        counts = collections.Counter([vv.v for vv in vals])
        self.domain = collections.OrderedDict([
            (v, v) for v in sorted(distinct_vals, key=lambda vv: -counts[vv])])


ParameterDictType = collections.OrderedDict[str, Parameter]


@functools.total_ordering
@dataclasses.dataclass(order=False, eq=False)
class Value:
    v: str
    pid: str
    lid: str
    code: Optional[str]
    float_val: float = None
    weight: Optional[float] = None

    def __post_init__(self):
        try:
            self.float_val = float(self.v)
        except (ValueError, TypeError):
            self.float_val = None

    def __eq__(self, other):
        return (self.lid, self.pid, self.v) == (other.lid, other.pid, other.v)

    def __lt__(self, other):
        return (self.lid, self.pid, self.v) < (other.lid, other.pid, other.v)

    @classmethod
    def from_row(cls, row, codes: CodesDictType, weight_col=None):
        return cls(
            v=row.get('codeReference') or row['value'],
            lid=row['languageReference'],
            pid=row['parameterReference'],
            code=codes[row['parameterReference']][row['codeReference']]
            if row['parameterReference'] in codes and row['codeReference'] else None,
            weight=row[weight_col] if weight_col else None,
        )


@dataclasses.dataclass
class ValueData:
    languages: collections.OrderedDict = dataclasses.field(default_factory=collections.OrderedDict)
    values: list = dataclasses.field(default_factory=list)

    @classmethod
    def from_dataset(
            cls,
            ds: pycldf.Dataset,
            pdata: 'ParameterData',
            ldata: 'LanguageData',
            include_missing: bool,
            weight_col: Optional[str],
    ):
        res = cls()
        res._add_parameter_values(ds, pdata, ldata.languages, include_missing, weight_col)
        res._add_language_property_values(
            ldata.language_properties, ldata.languages, ldata.language_rows)
        res._add_language_values(ds, ldata.languages)
        return res

    def _add_parameter_values(
            self,
            ds,
            pdata,
            langs,
            include_missing,
            weight_col,
    ):
        if not pdata.pids:
            return
        colmap = ['languageReference', 'parameterReference', 'value']
        if pdata.codes:
            colmap.append('codeReference')
        seen = {pid: False for pid in pdata.pids}
        comp = 'ValueTable' if ds.module == 'StructureDataset' else 'FormTable'
        for val in ds.iter_rows(comp, *colmap):
            seen[val['parameterReference']] = True
            if ((val['value'] is not None) or include_missing) and \
                    val['parameterReference'] in pdata.parameters:
                lang = langs.get(val['languageReference'])
                if lang:
                    self.languages[val['languageReference']] = lang
                    self.values.append(Value.from_row(val, pdata.codes, weight_col=weight_col))
                    pdata.parameters[val['parameterReference']] \
                        .value_to_code[str(val['value'])] = \
                        val.get('codeReference') or val['Value']
        if not all(seen[pid] for pid in pdata.pids):
            raise ValueError('Invalid parameter ID')

    def _add_language_property_values(
            self,
            language_properties,
            langs,
            language_rows,
    ):
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

    def _add_language_values(self, ds: pycldf.Dataset, langs: dict[str, Language]):
        if self.values:
            return

        def make_value(lid):
            return Value(v='y', pid=PSEUDO_PARAM_LANGUAGE, lid=lid, code='language')

        if 'LanguageTable' not in ds:
            for lid, lang in langs.items():
                self.languages.setdefault(lid, lang)
                self.values.append(make_value(lid))
            return
        for lang in ds.iter_rows('LanguageTable', 'id', 'name'):
            if lang['id'] in langs:
                self.languages.setdefault(lang['id'], langs[lang['id']])
                self.values.append(make_value(lang['id']))


@dataclasses.dataclass
class LanguageData:
    language_properties: list[str]
    languages: dict[str, Language]
    language_rows: list[collections.OrderedDict[str, Any]]

    @classmethod
    def from_dataset(cls, ds, language_properties, language_filter, exclude_lang, glottolog):
        langs = Language.from_dataset(ds, glottolog, language_filter, exclude_lang)
        language_rows = []
        if language_properties:
            language_rows = [
                r for r in ds.iter_rows('LanguageTable', 'id', 'name')
                if r['id'] in langs]
        return cls(language_properties or [], langs, language_rows)


@dataclasses.dataclass
class ParameterData:
    pids: Iterable[str]
    parameters: ParameterDictType = dataclasses.field(default_factory=dict)
    codes: CodesDictType = dataclasses.field(
        default_factory=lambda: collections.defaultdict(collections.OrderedDict))

    @classmethod
    def from_dataset(cls, ds, pids, ldata):
        res = cls(pids=pids)
        res._add_parameters(ds, ldata.language_properties)
        res._add_codes(ds, ldata.language_properties, ldata.language_rows)
        return res

    def set_domains(self, values, datatypes):
        for i, p in enumerate(self.parameters.values()):
            p.set_domain(values, self.codes, datatypes[i] if datatypes else None)

    def _add_parameters(
            self,
            ds: pycldf.Dataset,
            language_properties: Iterable[str],
    ):
        params = {}
        if 'ParameterTable' in ds:
            params = {p.id: Parameter.from_object(p) for p in ds.objects('ParameterTable')}

        # For each pid, we add a parameter:
        self.parameters = collections.OrderedDict(
            [(pid, params.get(pid, Parameter(id=pid, name=pid))) for pid in self.pids])
        # For each language-property we add a parameter:
        for language_property in language_properties or []:
            self.parameters[language_property] = Parameter(
                id=language_property, name=language_property)
        if not self.parameters:
            # No parameters and no language property specified: Just plot language locations.
            self.parameters[PSEUDO_PARAM_LANGUAGE] = Parameter(
                id=PSEUDO_PARAM_LANGUAGE, name='language')

    def _add_codes(
            self,
            ds: pycldf.Dataset,
            language_properties: Iterable[str],
            language_rows: list[dict[str, Any]],
    ):
        if 'CodeTable' in ds:
            for row in ds.iter_rows('CodeTable', 'id', 'parameterReference', 'name'):
                if row['parameterReference'] in self.parameters:
                    self.codes[row['parameterReference']][row['id']] = row['name']

        for i, language_property in enumerate(language_properties):
            vals = [v[language_property] for v in language_rows if v[language_property] is not None]

            if all(isinstance(v, (int, float, decimal.Decimal)) for v in vals):
                # Numeric values indicate a continuous parameter.
                continue

            counts = collections.Counter(vals)
            # For categorical parameters we add codes ordered from most frequent to least frequent.
            # This will make sure that when plotting values in order, the less frequent ones will not
            # be covered by more frequent ones.
            self.codes[language_property] = collections.OrderedDict([
                (v, v) for v in sorted(set(vals), key=lambda x: -counts[x])
            ])


class MultiParameter:
    """
    Extracts relevant data about a set of parameters from a CLDF dataset.

    :ivar parameters: `OrderedDict` mapping parameter IDs to :class:`Parameter` instances.
    """
    def __init__(self,
                 ds: pycldf.Dataset,
                 pids: Iterable[str],
                 datatypes: Iterable[str] = None,
                 include_missing: bool = False,
                 glottolog: Optional[Glottolog] = None,
                 language_properties: Optional[Iterable[str]] = None,
                 language_filter: Optional[Callable[[orm.Object], bool]] = None,
                 weight_col=None,
                 exclude_lang: Optional[Callable[[Language], bool]] = None):
        self.include_missing = include_missing

        ldata = LanguageData.from_dataset(
            ds, language_properties, language_filter, exclude_lang, glottolog)
        pdata = ParameterData.from_dataset(ds, pids, ldata)
        data = ValueData.from_dataset(ds, pdata, ldata, include_missing, weight_col)

        self.languages = data.languages
        self.values = data.values

        pdata.set_domains(data.values, datatypes)
        self.parameters = pdata.parameters

    def __str__(self):  # pragma: no cover
        return str(self.parameters)

    def iter_languages(self) -> Generator[tuple[Language, ValueDictType], None, None]:
        """Yields languages and associated values."""
        for lid, values in itertools.groupby(sorted(self.values), lambda v: v.lid):
            values = {pid: list(vals) for pid, vals in itertools.groupby(values, lambda v: v.pid)}
            values = collections.OrderedDict(
                [(pid, values.get(pid, [])) for pid in self.parameters])
            if self.include_missing or all(bool(v) for v in values.values()):
                yield self.languages[lid], values
