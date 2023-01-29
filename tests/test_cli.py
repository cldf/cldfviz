import logging
import pathlib
import warnings

import pytest
import requests_mock
import pycldf

from cldfbench.__main__ import main

from cldfviz.map import WITH_CARTOPY, MarkerFactory, leaflet, mpl


@pytest.fixture
def ds_arg(StructureDataset):
    return str(StructureDataset.directory / 'StructureDataset-metadata.json')


def test_audiowordlist(Wordlist, capsys, tmp_path):
    tmp_path.joinpath('1.wav').write_text('x', encoding='utf8')
    main([
        'cldfviz.audiowordlist',
        str(Wordlist.directory / 'Wordlist-metadata.json'),
        'ID=island',
        '--media-dir', str(tmp_path),
    ])
    out, _ = capsys.readouterr()
    assert '1.wav' in out

    main([
        'cldfviz.audiowordlist', str(Wordlist.directory / 'Wordlist-metadata.json'), 'ID=island'])
    out, _ = capsys.readouterr()
    assert 'example.org' in out

    main([
        'cldfviz.audiowordlist',
        '--output', str(tmp_path / 'o.html'),
        str(Wordlist.directory / 'Wordlist-metadata.json'),
        'ID=island'])
    out, _ = capsys.readouterr()
    assert tmp_path.joinpath('o.html').exists()

    ds = pycldf.Wordlist.in_dir(tmp_path)
    ds.add_columns(
        'FormTable',
        {'name': 'Media_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference'})
    ds.add_component('MediaTable')
    ds.write(
        FormTable=[dict(ID='1', Language_ID='l1', Parameter_ID='p1', Form='abc', Media_ID='m1')],
        MediaTable=[dict(ID='m1', Media_Type='audio/x-wav', Download_URL='http://example.org')],
    )
    main([
        'cldfviz.audiowordlist',
        str(tmp_path / 'Wordlist-metadata.json'),
        'p1'])
    out, _ = capsys.readouterr()
    assert 'abc' in out


def test_tree(ds_arg, tmp_path, capsys):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')

        main(['cldfviz.tree', ds_arg, str(tmp_path / 'test.svg'), '--ascii-art'])
        out, _ = capsys.readouterr()
        assert 'Marathi' in out

        styles = tmp_path / 's.json'
        styles.write_text('{}', encoding='utf8')
        o = tmp_path / 'test2.svg'
        main(['cldfviz.tree', ds_arg, str(o), '--test', '--styles', str(styles)])
        assert o.exists()

        main(['cldfviz.tree', ds_arg, str(o), '--test', '--title', 'The Title'])
        assert 'The Title' in o.read_text(encoding='utf8')


def test_treemap(ds_arg, tmp_path, glottolog_dir, metadatafree_dataset):
    if WITH_CARTOPY:
        tp = tmp_path / 'tree.nwk'
        tp.write_text(
            "((Santali_NM:1,Mundari_NM:1.1),(Hindi_IA:2,Sadri_IA:1.9)):3", encoding='utf8')
        main(['cldfviz.treemap', ds_arg, 'B', '--test',
              '--ltm-filename', str(tmp_path / 'B.pdf'),
              '--tree', str(tp),
              '--tree-label-property', 'ID'])
        assert tmp_path.joinpath('B.pdf').exists()
        main(['cldfviz.treemap', ds_arg, 'B', '--test',
              '--ltm-filename', str(tmp_path / 'B.pdf'),
              '--tree', '"((Santali_NM:1,Mundari_NM:1.1),(Hindi_IA:2,Sadri_IA:1.9)):3"',
              '--tree-label-property', 'ID'])
        assert tmp_path.joinpath('B.pdf').exists()
        main(['cldfviz.treemap', ds_arg, 'B', '--test',
              '--ltm-filename', str(tmp_path / 'B.pdf'),
              '--tree-dataset', ds_arg,
              '--tree-id', '1',
              '--tree-label-property', 'ID'])
        assert tmp_path.joinpath('B.pdf').exists()
        main(['cldfviz.treemap', ds_arg, 'B', '--test',
              '--ltm-filename', str(tmp_path / 'B.pdf'),
              '--tree-dataset', ds_arg,
              '--tree-id', '1',
              '--glottocodes-as-tree-labels'])
        assert tmp_path.joinpath('B.pdf').exists()
        main(['cldfviz.treemap', str(tmp_path / 'values.csv'), 'param1', '--test',
              '--ltm-filename', str(tmp_path / 'B.pdf'),
              '--tree', 'abcd1234', '--glottolog', str(glottolog_dir)],
             log=logging.getLogger(__name__))
        assert tmp_path.joinpath('B.pdf').exists()


def test_examples(ds_arg, tmp_path, capsys):
    main(['cldfviz.examples', ds_arg, '-o', str(tmp_path / 'ex.html')])
    assert tmp_path.joinpath('ex.html').exists()

    main(['cldfviz.examples', ds_arg])
    out, _ = capsys.readouterr()
    assert '<h1>Examples' in out


def test_erd(ds_arg, tmp_path, mocker):
    with pytest.raises(SystemExit):
        main(['cldfviz.erd', '-h'])

    with requests_mock.Mocker() as m:
        class Subprocess:
            @staticmethod
            def check_call(cmd, *args, **kw):
                out = None
                for i, token in enumerate(cmd):
                    if token == '-o':
                        out = cmd[i + 1]
                        break
                o = pathlib.Path(out) / 'diagrams' / 'summary' / 'relationships.real.large.svg'
                o.parent.mkdir(parents=True)
                o.write_text('a', encoding='utf8')

        mocker.patch('cldfviz.commands.erd.subprocess', Subprocess())
        o = tmp_path / 'res.svg'
        m.get(requests_mock.ANY, text='abc')
        main(['cldfviz.erd', ds_arg, str(o), '--test'])
        assert o.exists()


def test_text(ds_arg, capsys, Wordlist):
    main(['cldfviz.text', '--text-string', '"[](Source?with_the_works=false#cldf:__all__)"', ds_arg])
    assert 'Peterson, John' in capsys.readouterr()[0]
    main(['cldfviz.text', '-l', ds_arg])
    assert 'CodeTable' in capsys.readouterr()[0]

    main([
        'cldfviz.text', str(Wordlist.directory / 'Wordlist-metadata.json'), '--media-id', '2'])
    out, _ = capsys.readouterr()
    assert 'The Text' in out


def test_text_invalid(StructureDataset):
    with pytest.raises(ValueError):
        main([
            'cldfviz.text', '--text-string', '"a"', str(StructureDataset.directory / 'sources.bib')])


def test_text_multi_ds(ds_arg, capsys):
    main([
        'cldfviz.text',
        '--text-string', '"[](ParameterTable#cldf-p1:B) [](ParameterTable#cldf-p2:D)"',
        'p1:' + ds_arg,
        'p2:' + ds_arg,
    ])
    out = capsys.readouterr()[0]
    assert 'Gender' in out and 'Oblique' in out


def test_text_with_map(ds_arg, capsys, tmp_path):
    tmpl = tmp_path / 'templ.md'
    tmpl.write_text('![](map.html?parameters=B&pacific-centered#cldfviz.map-pref)')
    main(
        ['cldfviz.text', '--text-file', str(tmpl), '--test', '--output', str(tmp_path / 'test.md'), 'pref:' + ds_arg],
        log=logging.getLogger(__name__))
    assert tmp_path.joinpath('map.html').exists()


class MF(MarkerFactory):
    def __init__(self, ds, args, param):
        MarkerFactory.__init__(self, ds, args, param)
        assert param == 'test'

    def __call__(self, map, language, values, colormaps):
        if self.args.format == 'html':
            return leaflet.LeafletMarkerSpec(css='.leaflet-tooltip {}')
        return mpl.MPLMarkerSpec(text='text')


def test_map(glottolog_dir, tmp_path, capsys, ds_arg, md_path_factory):
    values = tmp_path.joinpath('values.csv')
    values.write_text("""\
ID,Language_ID,Parameter_ID,Value
1,abcd1235,param1,val1
2,abcd1234,param1,val2
3,book1243,param1,val3
5,book1243,param2,val3
4,isol1234,param1,val4""", encoding='utf8')
    sd = ds_arg

    def run(data=None, **kw):
        for k, v in dict(
            glottolog=glottolog_dir,
            output=tmp_path / 'testmap',
            format='html',
            test=None,
        ).items():
            kw.setdefault(k, v)
        args = ['cldfviz.map']
        for k, v in kw.items():
            args.append('--{}'.format(k.replace('_', '-')))
            if v is not None:
                args.append(str(v))
        args.append(str(data or values))
        main(args, log=logging.getLogger(__name__))

    run(parameters='param1')
    assert tmp_path.joinpath('testmap.html').exists()

    run(parameters='param1',
        colormaps='{"val1": "#a00", "val2": "#0a0", "val3": "#00a", "val4": "#000"}')
    assert tmp_path.joinpath('testmap.html').exists()

    with pytest.raises(SystemExit):  # Shapes in colormap, but just one parameter.
        run(parameters='param1',
            colormaps='{"val1": "circle", "val2": "#0a0", "val3": "#00a", "val4": "#000"}')

    with pytest.raises(SystemExit):  # Explicit color map for non-categorical parameter.
        run(parameters='B',
            colormaps='{"v":"#aaaaaa"}',
            data=sd)

    with pytest.raises(SystemExit):  # Shapes in color maps for both parameters.
        run(parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},'
                      '{"0":"circle","1":"diamond","2":"square"}',
            data=sd)

    run(parameters='C,D',
        colormaps='{"0":"circle","1":"diamond","2":"square"},tol',
        data=sd)

    with pytest.raises(SystemExit):
        # Non-matching colormap values:
        run(parameters='param1', colormaps='{"x": "y"}')
    out, _ = capsys.readouterr()
    assert 'ERROR' in out

    run(parameters='B,C',
        colormaps='viridis,tol',
        language_properties='Family_name',
        pacific_centered=None,
        data=str(md_path_factory('StructureDataset_listvalued_glottocode')))
    assert tmp_path.joinpath('testmap.html').exists()

    run(data=sd,
        parameters='C',
        language_filters='{"Name":"Kharia"}')
    assert 'Santali' not in tmp_path.joinpath('testmap.html').read_text(encoding='utf8')

    run(data=sd,
        parameters='C',
        language_filters='{"Filtered":true}')
    html = tmp_path.joinpath('testmap.html').read_text(encoding='utf8')
    assert 'Kharia' in html and 'Telugu' not in html

    run(marker_factory='cldfviz.map', data=sd)
    run(marker_factory='{},test'.format(__file__), data=sd)

    if WITH_CARTOPY:
        run(format='png', parameters='param1')
        assert tmp_path.joinpath('testmap.png').exists()
        run(format='jpg',
            title='The Title',
            language_labels=None,
            parameters='B,C',
            colormaps='viridis,tol',
            language_properties='Family_name',
            pacific_centered=None,
            output=tmp_path / 'testmap.jpg',
            data=sd)
        assert tmp_path.joinpath('testmap.jpg').exists()

        run(format='png', projection='Robinson', parameters='param1', with_stock_img=None)
        run(format='png', projection='Robinson', parameters='param1', extent='"-150,150,50,-50"')
        run(format='png', projection='Robinson', parameters='param1', zorder='{"v":5}')
        run(format='png', parameters='param1,param2', no_borders=None)
        run(format='png', marker_factory='cldfviz.map', data=sd)
        run(format='png', marker_factory='{},test'.format(__file__), data=sd)
        run(format='png',
            data=sd,
            parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},tol')
        run(format='png',
            data=sd,
            parameters='C,D',
            colormaps='{"0":"circle","1":"diamond","2":"square"},tol',
            projection='Mollweide')
        # Test multi-valued parameter (triggering piechart icons!):
        run(format='png', data=sd, parameters='Z,C', projection='Mollweide', pacific_centered=None)
