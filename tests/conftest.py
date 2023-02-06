import shutil
import pathlib

from pycldf import Dataset
import pytest
from cldfcatalog.repository import get_test_repo
from pyglottolog import Glottolog


@pytest.fixture
def glottolog_dir(tmp_path):
    repo = get_test_repo(str(tmp_path), tags=['v1', 'v2'])
    d = pathlib.Path(repo.working_dir)
    for dd in ['languoids', 'references']:
        shutil.copytree(pathlib.Path(__file__).parent / 'glottolog' / dd, d / dd)
    return d


@pytest.fixture
def glottolog(glottolog_dir):
    from cldfviz.glottolog import Glottolog as AnyGlottolog
    return AnyGlottolog(Glottolog(glottolog_dir))


@pytest.fixture
def md_path_factory():
    def mdpath(dirname):
        return pathlib.Path(__file__).parent / dirname / '{}-metadata.json'.format(
            dirname.split('_')[0])
    return mdpath


@pytest.fixture
def StructureDataset():
    return Dataset.from_metadata(
        pathlib.Path(__file__).parent / 'StructureDataset' / 'StructureDataset-metadata.json')


@pytest.fixture
def Wordlist():
    return Dataset.from_metadata(
        pathlib.Path(__file__).parent / 'Wordlist' / 'Wordlist-metadata.json')


@pytest.fixture
def Dictionary():
    return Dataset.from_metadata(
        pathlib.Path(__file__).parent / 'Dictionary' / 'Dictionary-metadata.json')


@pytest.fixture
def Generic():
    return Dataset.from_metadata(
        pathlib.Path(__file__).parent / 'Generic' / 'Generic-metadata.json')


@pytest.fixture
def MetadataFreeStructureDataset(tmp_path):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
6,abcd1237,param1,val3
1,abcd1235,param1,val1
2,abcd1234,param1,val2
3,book1243,param1,val3
5,book1243,param2,val3
4,isol1234,param1,val4""", encoding='utf8')
    return values


@pytest.fixture
def metadatafree_dataset(MetadataFreeStructureDataset):
    return Dataset.from_data(MetadataFreeStructureDataset)
