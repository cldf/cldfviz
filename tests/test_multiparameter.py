import pytest
from pycldf import Dataset

from cldfviz.multiparameter import MultiParameter, Language, Value, CONTINUOUS


def test_Language(glottolog, StructureDataset):
    from pycldf import orm
    for row in StructureDataset['LanguageTable']:
        row['Glottocode'] = 'abcd1234'
        row['Latitude'] = None
        lang = Language(orm.Language(StructureDataset, row), glottolog)
        assert lang.lat == pytest.approx(10.0)
        break

    with pytest.raises(TypeError):
        _ = Language({})


def test_MultiParameter(metadatafree_dataset, StructureDataset, glottolog, tmp_path):
    with pytest.raises(ValueError):
        _ = MultiParameter(StructureDataset, ['A'])

    _ = MultiParameter(metadatafree_dataset, ['param1'], glottolog=glottolog)
    mp = MultiParameter(StructureDataset, ['B', 'C'])
    for lang, values in mp.iter_languages():
        assert lang.name == 'Bengali'
        assert values['C'][0].v == 'C-1'
        assert values['C'][0].code == '1'
        break
    mp = MultiParameter(StructureDataset, ['B'], language_properties=['Family_name'])
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
    assert list(mp.parameters.values())[0].type == CONTINUOUS
    mp = MultiParameter(ds, [], glottolog=glottolog)
    assert len(mp.languages) == 2


def test_Value():
    v1 = Value(v=1, pid=1, lid=1, code=1)
    assert v1 == Value(v=1, pid=1, lid=1, code=2)
    assert Value(v=2, pid=2, lid=1, code=2) < Value(v=1, pid=1, lid=2, code=1)
