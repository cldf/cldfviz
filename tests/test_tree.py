import warnings


def test_render(StructureDataset, tmp_path):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')
        from pycldf.trees import TreeTable
        from cldfviz.tree import render

    treeobj = list(TreeTable(StructureDataset))[0]
    out = tmp_path / 'tree.svg'
    _ = render(
        treeobj,
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

    _ = render(
        treeobj,
        out,
        legend='The Tree',
        labels={n.name: '(' + n.name + ')' for n in treeobj.newick().walk() if n.name},
    )
    assert '_Santali_NM_' in out.read_text(encoding='utf8')

    _ = render(
        treeobj,
        out,
        legend='The Tree',
        leafs=[n.name for n in treeobj.newick().walk() if n.name and n.name != 'Santali_NM'],
    )
    assert 'Santali_NM' not in out.read_text(encoding='utf8')
