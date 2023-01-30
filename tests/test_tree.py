import warnings

import pytest


@pytest.mark.parametrize(
    'opts,expect',
    [
        (
            dict(
                glottolog_mapping={
                    'Santali_NM': ('abcd1234', 'Abcd'),
                    'Marathi_IA': ('efgh1234', None),
                },
                legend='The Tree',
                with_glottolog_links=True),
            lambda svg: 'The Tree' in svg and 'Abcd' in svg),
        (
            dict(labels=lambda n: '(' + n.name + ')'),
            lambda svg: '_Santali_NM_' in svg),
        (
            dict(leafs=lambda n: n.name != 'Santali_NM'),
            lambda svg: 'Santali_NM' not in svg),
    ]
)
def test_render(StructureDataset, opts, expect):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')
        from pycldf.trees import TreeTable
        from cldfviz.tree import render

    assert expect(render(list(TreeTable(StructureDataset))[0], **opts))


def test_render_to_file(StructureDataset, tmp_path):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')
        from pycldf.trees import TreeTable
        from cldfviz.tree import render

    o = tmp_path / 'test.svg'
    render(list(TreeTable(StructureDataset))[0], output=o)
    assert o.exists()
