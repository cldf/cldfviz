import shutil
import pathlib

import pytest
from cldfcatalog.repository import get_test_repo


@pytest.fixture
def glottolog_dir(tmpdir):
    repo = get_test_repo(str(tmpdir), tags=['v1', 'v2'])
    d = pathlib.Path(repo.working_dir)
    for dd in ['languoids', 'references']:
        shutil.copytree(str(pathlib.Path(__file__).parent / 'glottolog' / dd), str(d / dd))
    return d
