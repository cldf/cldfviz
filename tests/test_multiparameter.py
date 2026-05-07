import argparse

import pytest
from pycldf import Dataset

from cldfviz.multiparameter import (
    MultiParameter, Language, Value, ParameterType, Parameter, ParameterData, LanguageData)
from cldfviz.cli_util import get_language_filter


def test_Language(glottolog, StructureDataset):
    from pycldf import orm
    for row in StructureDataset['LanguageTable']:
        row['Glottocode'] = 'abcd1234'
        row['Latitude'] = None
        lang = Language._from_object(orm.Language(StructureDataset, row), glottolog)
        assert lang.lat == pytest.approx(10.0)
        break


@pytest.mark.parametrize(
    'lfilter,exclude,expected',
    [
        (lambda x: True, lambda x: False, 29),
        (lambda x: True, lambda x: True, 0),
        (lambda x: False, lambda x: False, 0),
        (lambda x: x.id == 'Mundari_NM', lambda x: False, 1),
    ]
)
def test_Language_from_dataset(glottolog, StructureDataset, lfilter, exclude, expected):
    assert len(Language.from_dataset(StructureDataset, glottolog, lfilter, exclude)) == expected


@pytest.mark.parametrize(
    'values,codes,datatype,expected',
    [
        ([], {'pid': 1}, None, 1),
        ([Value('1', 'pid', 'lid', None, 1.0)], {}, 'number', (1.0, 1.0)),
        (
            [Value('1', 'pid', 'lid'), Value('2', 'pid', 'lid'), Value('2', 'pid', 'lid')],
            {},
            None,
            {'2': '2', '1': '1'}),
    ]
)
def test_Parameter_set_domain(values, codes, datatype, expected):
    p = Parameter(id='pid', name='param')
    p.set_domain(values, codes, datatype)
    assert p.domain == expected


def test_ParameterData(glottolog, StructureDataset):
    ldata = LanguageData.from_dataset(
        StructureDataset, ['Latitude'], glottolog=glottolog)
    pdata = ParameterData.from_dataset(StructureDataset, [], ldata)
    assert not pdata.codes

    ldata = LanguageData.from_dataset(
        StructureDataset, ['Family_name'], glottolog=glottolog)
    pdata = ParameterData.from_dataset(StructureDataset, [], ldata)
    assert (list(pdata.codes['Family_name'].keys())[-1] ==
            'Dravidian'), "Values not ordered by decreasing frequency!"


def test_MultiParameter(metadatafree_dataset, StructureDataset, glottolog, tmp_path):
    with pytest.raises(ValueError):
        _ = MultiParameter(StructureDataset, ['A'])

    _ = MultiParameter(metadatafree_dataset, ['param1'], glottolog=glottolog)
    mp = MultiParameter(StructureDataset, ['B', 'C'])
    for lang, values in mp.iter_languages():
        assert lang.name == 'Bengali'
        assert values['C'][0].v == 'C-1', values['C']
        assert values['C'][0].code == '1'
        break
    mp = MultiParameter(
        StructureDataset,
        ['B'],
        language_filter=get_language_filter(argparse.Namespace(language_filters='{"Filtered":"False"}')),
        language_properties=['Family_name'])
    assert len(mp.languages) == 26
    assert 'Family_name' in mp.parameters
    mp = MultiParameter(StructureDataset, [])
    assert '__language__' in mp.parameters

    values = tmp_path / 'values.csv'
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,1
2,abcd1235,param1,2
3,abcd1235,param1,3
4,abcd1235,param1,4
5,abcd1235,param1,5
6,abcd1235,param1,6
7,abcd1235,param1,7
8,abcd1235,param1,8
9,abcd1235,param1,9
10,abcd1234,param1,10""", encoding='utf8')
    ds = Dataset.from_data(values)
    mp = MultiParameter(ds, ['param1'], glottolog=glottolog)
    assert list(mp.parameters.values())[0].type == ParameterType.CONTINUOUS
    mp = MultiParameter(ds, [], glottolog=glottolog)
    assert len(mp.languages) == 2


def test_Value():
    v1 = Value(v=1, pid=1, lid=1, code=1)
    assert v1 == Value(v=1, pid=1, lid=1, code=2)
    assert Value(v=2, pid=2, lid=1, code=2) < Value(v=1, pid=1, lid=2, code=1)
