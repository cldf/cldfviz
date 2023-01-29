import argparse

import pytest

from cldfviz.glottolog import *


@pytest.fixture
def glottolog_cldf(glottolog_dir, tmp_path):
    from pycldf import StructureDataset
    import pyglottolog

    ds = StructureDataset.in_dir(tmp_path / 'glottolog-cldf')
    ds.add_component('LanguageTable')
    langs, vals = [], []
    for lang in pyglottolog.Glottolog(glottolog_dir).languoids():
        langs.append(dict(
            ID=lang.id, Name=lang.name, Latitude=lang.latitude, Longitude=lang.longitude))
        vals.append(dict(
            ID=lang.id,
            Language_ID=lang.id,
            Parameter_ID='subclassification',
            Value=lang.newick_node(template="{l.id}").newick,
        ))
    ds.write(LanguageTable=langs, ValueTable=vals)
    return tmp_path / 'glottolog-cldf'


def test_Glottolog_glottolog_cldf(glottolog_cldf):
    parser = argparse.ArgumentParser()
    Glottolog.add(parser)
    args = parser.parse_args(['--glottolog-cldf', str(glottolog_cldf)])
    gl = Glottolog.from_args(args)
    assert 'abcd1234' in gl
    assert len(gl) == 8
    assert gl.newick('abcd1234')


def test_Glottolog_pyglottolog(glottolog_dir):
    parser = argparse.ArgumentParser()
    Glottolog.add(parser)
    args = parser.parse_args(['--glottolog', str(glottolog_dir)])
    gl = Glottolog.from_args(args)
    assert 'abcd1234' in gl
    assert len(gl) == 8
    assert gl.newick('abcd1234')
