import warnings


def test_render(StructureDataset, tmp_path):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')
        from pycldf.trees import TreeTable

        from cldfviz.tree import render

    out = tmp_path / 'tree.svg'
    _ = render(
        list(TreeTable(StructureDataset))[0],
        out,
        glottolog_mapping={
            'Santali_NM': ('abcd1234', 'Abcd'),
            'Marathi_IA': ('efgh1234', None),
        },
        legend='The Tree',
        with_glottolog_links=True,
    )
    assert out.exists()
    svg = out.read_text(encoding='utf8')
    assert 'The Tree' in svg
    assert 'Abcd' in svg
