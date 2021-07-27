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
    return Glottolog(glottolog_dir)


@pytest.fixture
def metadatafree_dataset(tmp_path):
    values = tmp_path / 'values.csv'
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2""", encoding='utf8')
    return Dataset.from_data(values)


@pytest.fixture
def StructureDataset():
    return Dataset.from_metadata(
        pathlib.Path(__file__).parent / 'StructureDataset' / 'StructureDataset-metadata.json')
