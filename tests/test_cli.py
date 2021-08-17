import pytest

from cldfbench.__main__ import main

from cldfviz.map import WITH_CARTOPY


def test_map(glottolog_dir, tmp_path, StructureDataset, capsys):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2
3,book1243,param1,val3
5,book1243,param2,val3
4,isol1234,param1,val4""", encoding='utf8')
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
        '--output', str(tmp_path / 'testmap'),
        '--format', 'html',
        '--parameters', 'param1',
        '--colormaps', '{"val1": "#a00", "val2": "#0a0", "val3": "#00a", "val4": "#000"}',
        '--test',
        str(values)])
    assert tmp_path.joinpath('testmap.html').exists()

    with pytest.raises(SystemExit):
        main([
            'cldfviz.map',
            '--glottolog', str(glottolog_dir),
            '--output', str(tmp_path / 'testmap'),
            '--format', 'html',
            '--parameters', 'param1',
            '--colormaps', '{"x": "y"}',
            '--test',
            str(values)])
    out, _ = capsys.readouterr()
    assert 'ERROR' in out

    main([
        'cldfviz.map',
        '--glottolog', str(glottolog_dir),
        '--output', str(tmp_path / 'testmap.html'),
        '--format', 'html',
        '--parameters', 'B,C',
        '--colormaps', 'viridis,tol',
        '--language-properties', 'Family_name',
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
            '--language-properties', 'Family_name',
            '--pacific-centered',
            '--test',
            str(StructureDataset.directory / 'StructureDataset-metadata.json')])
        assert tmp_path.joinpath('testmap.jpg').exists()

        main([
            'cldfviz.map',
            '--glottolog', str(glottolog_dir),
            '--output', str(tmp_path / 'testmap'),
            '--format', 'png',
            '--projection', 'Robinson',
            '--parameters', 'param1',
            '--with-stock-img',
            '--test',
            str(values)])

        with pytest.raises(SystemExit):
            main([
                'cldfviz.map',
                '--glottolog', str(glottolog_dir),
                '--output', str(tmp_path / 'testmap'),
                '--format', 'png',
                '--projection', 'Robinson',
                '--parameters', 'param1,param2',
                '--test',
                str(values)])
