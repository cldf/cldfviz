from cldfviz.multiparameter import MultiParameter


def test_MultiParameter(metadatafree_dataset, StructureDataset, glottolog):
    _ = MultiParameter(
        metadatafree_dataset, ['param1'], glottolog={lg.id: lg for lg in glottolog.languoids()})
    mp = MultiParameter(StructureDataset, ['B', 'C'])
    for lang, values in mp.iter_languages():
        assert lang.name == 'Bengali'
        assert values['B'][0].v == 'B-1'
        assert values['B'][0].code == '1'
        break
    mp = MultiParameter(StructureDataset, ['B'], language_property='Family_name')
    assert 'Family_name' in mp.parameters
    mp = MultiParameter(StructureDataset, [])
    assert 'language' in mp.parameters
