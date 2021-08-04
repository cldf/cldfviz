from cldfbench.__main__ import main

from cldfviz.map import WITH_CARTOPY


def test_map(glottolog_dir, tmp_path, StructureDataset):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2""", encoding='utf8')
    main([
        'cldfviz.map',
        '--glottolog', str(glottolog_dir),
        '--output', str(tmp_path / 'testmap'),
        '--format', 'html',
        '--parameters', 'param1',
        '--test',
        str(values)])
    assert tmp_path.joinpath('testmap.html').exists()

    main([
        'cldfviz.map',
        '--glottolog', str(glottolog_dir),
        '--output', str(tmp_path / 'testmap.html'),
        '--format', 'html',
        '--parameters', 'B,C',
        '--colormaps', 'viridis,tol',
        '--language-property', 'Family_name',
        '--pacific-centered',
        '--test',
        str(StructureDataset.directory / 'StructureDataset-metadata.json')])
    assert tmp_path.joinpath('testmap.html').exists()

    if WITH_CARTOPY:
        main([
            'cldfviz.map',
            '--glottolog', str(glottolog_dir),
            '--output', str(tmp_path / 'testmap'),
            '--format', 'png',
            '--parameters', 'param1',
            '--test',
            str(values)])
        assert tmp_path.joinpath('testmap.png').exists()
        main([
            'cldfviz.map',
            '--glottolog', str(glottolog_dir),
            '--output', str(tmp_path / 'testmap'),
            '--format', 'jpg',
            '--title', 'The Title',
            '--language-labels',
            '--parameters', 'B,C',
            '--colormaps', 'viridis,tol',
            '--language-property', 'Family_name',
            '--pacific-centered',
            '--test',
            str(StructureDataset.directory / 'StructureDataset-metadata.json')])
        assert tmp_path.joinpath('testmap.jpg').exists()
