import shlex
import logging
import pathlib
import warnings
import functools

import pytest
import requests_mock
import pycldf

from cldfbench.__main__ import main

from cldfviz.map import WITH_CARTOPY, MarkerFactory, leaflet, mpl


def lmain(*args, **kw):
    kw.setdefault('log', logging.getLogger(__name__))
    return main(*args, **kw)


def runcli(command, cli):
    return lmain([command] + shlex.split(cli))


@pytest.fixture
def ds_arg(StructureDataset):
    return str(StructureDataset.directory / 'StructureDataset-metadata.json')


def test_audiowordlist(Wordlist, capsys, tmp_path):
    def run(opts):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore', category=DeprecationWarning, module='importlib._bootstrap')
            warnings.filterwarnings(
                'ignore', category=DeprecationWarning, module='joblib.backports')
            functools.partial(runcli, 'cldfviz.audiowordlist')(opts)
        out, _ = capsys.readouterr()
        return out

    tmp_path.joinpath('1.wav').write_text('x', encoding='utf8')
    assert '1.wav' in run('{} ID=island --media-dir {}'.format(Wordlist.directory, tmp_path))

    assert 'example.org' in run('{} ID=island'.format(Wordlist.directory))

    run('{} ID=island --output {}'.format(Wordlist.directory, tmp_path / 'o.html'))
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
    assert 'abc' in run('{} p1'.format(tmp_path / 'Wordlist-metadata.json'))


def test_tree_misc(ds_arg, tmp_path, capsys):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')

        styles = tmp_path / 's.json'
        styles.write_text('{}', encoding='utf8')
        o = tmp_path / 'test2.svg'
        lmain(['cldfviz.tree', '--tree-dataset', ds_arg, '--output', str(o), '--test', '--styles', str(styles)])
        assert o.exists()


@pytest.mark.parametrize(
    'args,expect',
    [
        (
            '--tree-dataset DATASET --ascii-art --tree-id 1',
            lambda out: 'Marathi' in out),
        (
            '--tree-dataset DATASET --title "The Title"',
            lambda out: 'The Title' in out),
        (
            '--tree-dataset DATASET --name-as-label',
            lambda out: 'Korku_NM' not in out and ('Korku' in out)),
        (
            '--tree "((khr:1,sat:1.1),(unr:2,bfw:1.9)):3" --tree-label-property ISO639P3code '
            '--name-as-label --data-dataset DATASET --parameters C',
            lambda out: 'Kharia' in out),
        (
            '--tree-dataset DATASET --name-as-label --data-dataset DATASET --parameters C',
            lambda out: 'Enclitic PL' in out and ('Korku_NM' not in out) and ('Korku' in out)),
        (
            '--tree-dataset DATASET --data-dataset DATASET --parameters C '
            '--colormaps \'{"0":"circle","1":"triangle_up","2":"triangle_down"}\'',
            lambda out: 'Enclitic PL' in out),
        (
            '--tree-dataset DATASET --data-dataset DATASET --parameters C,D '
            '--colormaps \'{"0":"circle","1":"triangle_up","2":"triangle_down"},tol\'',
            lambda out: 'Enclitic PL' in out),
        (
            '--tree "((Santali_NM:1,Mundari_NM:1.1),(Hindi_IA:2,Sadri_IA:1.9)):3" '
            '--data-dataset DATASET --parameters C,B',
            lambda out: 'Hindi_IA' in out),
    ]
)
def test_tree(ds_arg, tmp_path, capsys, args, expect):
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='importlib._bootstrap')

        runcli('cldfviz.tree', '--test ' + args.replace('DATASET', ds_arg))
        out, _ = capsys.readouterr()
        assert expect(out)


@pytest.mark.skipif(not WITH_CARTOPY, reason="Cannot run without cartopy.")
@pytest.mark.parametrize(
    'with_full_dataset,opts,expect',
    [
        (
            True,
            'B --tree "((Santali_NM:1,Mundari_NM:1.1),(Hindi_IA:2,Sadri_IA:1.9)):3" '
            '--language-filters \'{"Name":".+"}\' --tree-label-property ID',
            lambda svg: True),
        (
            True,
            'B --tree "((Santali_NM:1,Mundari_NM:1.1),(Hindi_IA:2,Sadri_IA:1.9)):3" '
            '--tree-label-property ID',
            lambda svg: True),
        (
            True,
            'B --tree-dataset DATASET --tree-id 1 --tree-label-property ID',
            lambda svg: True),
        (
            True,
            'B --tree-dataset DATASET --tree-id 1 --glottocodes-as-tree-labels',
            lambda svg: True),
        (
            False,
            'param1 --tree abcd1234 --glottolog GLOTTOLOG',
            lambda svg: True),
        (
            False,
            'param1 --tree "((abcd1234:2,abcd1235:2.5)book1243:3):2;" --glottolog GLOTTOLOG',
            lambda svg: True),
        (
            False,
            'param1 --tree "((abcd1234:2,abcd1235:2.5):2,book1243:3):2;" --glottolog GLOTTOLOG',
            lambda svg: True),
    ]
)
def test_treemap(
        tmp_path, glottolog_dir, MetadataFreeStructureDataset, StructureDataset,
        with_full_dataset, opts, expect):
    out = tmp_path / 'test.svg'
    opts = opts.replace('DATASET', str(StructureDataset.directory))
    opts = opts.replace('GLOTTOLOG', str(glottolog_dir))
    print(opts)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=UserWarning, module='geopandas.plotting')
        runcli(
            'cldfviz.treemap',
            '{} --output {} --test {}'.format(
                StructureDataset.directory if with_full_dataset else MetadataFreeStructureDataset,
                out,
                opts))
    assert expect(out.read_text(encoding='utf8'))


def test_examples(ds_arg, tmp_path, capsys):
    main(['cldfviz.examples', ds_arg, '-o', str(tmp_path / 'ex.html')])
    assert tmp_path.joinpath('ex.html').exists()

    main(['cldfviz.examples', ds_arg])
    out, _ = capsys.readouterr()
    assert '<ol class="example">' in out


def test_erd(ds_arg, tmp_path, mocker):
    with pytest.raises(SystemExit):
        main(['cldfviz.erd', '-h'])

    with requests_mock.Mocker() as m:
        class Subprocess:
            @staticmethod
            def check_output(cmd, *args, **kw):
                out = None
                for i, token in enumerate(cmd):
                    if token == '-o':
                        out = cmd[i + 1]
                        break
                o = pathlib.Path(out) / 'diagrams' / 'summary' / 'relationships.real.large.svg'
                o.parent.mkdir(parents=True)
                o.write_text('a', encoding='utf8')
                return ''.encode('utf8')

        mocker.patch('cldfviz.commands.erd.subprocess', Subprocess())
        jar = tmp_path / 'jar'
        jar.write_text('abc', encoding='utf8')
        o = tmp_path / 'res.svg'
        m.get(requests_mock.ANY, text='abc')
        main(['cldfviz.erd', ds_arg, '--output', str(o), '--test', '--sqlite-jar', str(jar)])
        assert o.exists()


@pytest.mark.parametrize(
    'ds,opts,expect',
    [
        (
            'StructureDataset',
            '--text-string "[](Source?with_the_works=false#cldf:__all__)"',
            lambda out: 'Peterson, John' in out),
        (
            'StructureDataset',
            '-l',
            lambda out: 'CodeTable' in out),
        (
            'StructureDataset',
            '--text-string "[ex](ExampleTable#cldf:igt)" --no-escape',
            lambda out: '<in>' in out),
        (
            'Wordlist',
            '--media-id 2',
            lambda out: 'The Text' in out),
    ]
)
def test_text(capsys, Wordlist, StructureDataset, ds, opts, expect):
    runcli('cldfviz.text', '{} --test {}'.format(
        (Wordlist if ds == 'Wordlist' else StructureDataset).directory, opts))
    assert expect(capsys.readouterr()[0])


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


def test_text_with_images(ds_arg, capsys, tmp_path):
    tmpl = tmp_path / 'templ.md'
    tmpl.write_text('![](map.html?parameters=B&pacific-centered#cldfviz.map-pref)')
    lmain(
        ['cldfviz.text', '--text-file', str(tmpl), '--test', '--output', str(tmp_path / 'test.md'), 'pref:' + ds_arg])
    assert tmp_path.joinpath('map.html').exists()

    main(['cldfviz.text', ds_arg, '--text-string', '![](tree.svg#cldfviz.tree)', '--test', '--output', str(tmp_path / 'test.md')])
    assert tmp_path.joinpath('tree.svg').exists()


class MF(MarkerFactory):
    def __init__(self, ds, args, param):
        MarkerFactory.__init__(self, ds, args, param)
        assert param == 'test'

    def __call__(self, map, language, values, colormaps):
        if self.args.format == 'html':
            return leaflet.LeafletMarkerSpec(tooltip='abcdefg', css='.leaflet-tooltip {}')
        return mpl.MPLMarkerSpec(text='abcdefg')


def test_map_misc(tmp_path, capsys, ds_arg, md_path_factory, MetadataFreeStructureDataset):
    def run(ds, opts):
        return functools.partial(runcli, 'cldfviz.map')(str(ds) + ' ' + opts)

    with pytest.raises(SystemExit):  # Shapes in colormap, but just one parameter.
        run(MetadataFreeStructureDataset,
            '--parameters param1 '
            '--colormaps \'{"val1": "circle", "val2": "#0a0", "val3": "#00a", "val4": "#000"}\'')

    with pytest.raises(SystemExit):  # Explicit color map for non-categorical parameter.
        run(ds_arg, '--parameters B --colormaps \'{"v":"#aaaaaa"}\'')

    with pytest.raises(SystemExit):  # Shapes in color maps for both parameters.
        run(ds_arg,
            '--parameters C,D '
            '--colormaps \'{"0":"circle","1":"diamond","2":"square"},'
            '{"0":"circle","1":"diamond","2":"square"}\'')

    with pytest.raises(SystemExit):  # Shapes in color maps, but more than 2 parameters.
        run(ds_arg,
            '--parameters C,D,E '
            '--colormaps \'{"0":"circle","1":"diamond","2":"square"},tol,tol\'')

    with pytest.raises(SystemExit):
        # Non-matching colormap values:
        run(MetadataFreeStructureDataset, '--parameters param1 --colormaps \'{"x": "y"}\'')
    out, _ = capsys.readouterr()
    assert 'ERROR' in out

    if WITH_CARTOPY:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore', category=DeprecationWarning, module='cartopy.crs')
            # For JPG, there's a slightly different code path.
            run(ds_arg, '--format jpg --parameters C --output {}'.format(tmp_path / 'test.jpg'))


@pytest.mark.skipif(not WITH_CARTOPY, reason="Cannot run without cartopy.")
@pytest.mark.parametrize(
    'with_full_dataset,opts,expect_html,expect_svg',
    [
        (False, '--parameters param1', None, None),
        (
            False,
            '--parameters param1 '
            '--colormaps=\'{"val1":"#a00","val2":"#0a0","val3":"#00a","val4":"#000"}\'',
            None, None),
        (
            True,
            '--parameters C --overlay-geojson ecoregions',
            lambda html: 'ECO_NAME' in html, None),
        (
            True,
            '--parameters C --colormaps \'{"0":"circle","1":"diamond","2":"square"}\'',
            None, None),
        (
            True,
            '--parameters C,D --colormaps \'{"0":"circle","1":"diamond","2":"square"},tol\'',
            None, None),
        (
            'StructureDataset_listvalued_glottocode',
            '--parameters B,C --colormaps viridis,tol --language-properties Family_name '
            '--pacific-centered',
            None, None),
        (
            True,
            '--parameters C --language-filters \'{"Name":"Kharia"}\'',
            lambda html: 'Kharia' in html and 'Telugu' not in html, None),
        (
            True,
            '--parameters C --language-filters \'{"Filtered":1}\'',
            lambda html: 'Kharia' in html and 'Maithili' not in html, None),
        (
            True,
            '--parameters C --language-filters \'{"ListFiltered":"a"}\'',
            lambda html: 'Kharia' in html and 'Ho' not in html, None),
        (
            True,
            '--marker-factory cldfviz.map',
            None, None),
        (
            True,
            '--marker-factory {},test'.format(__file__),
            None, None),
        (
            False,
            '--parameters param1',
            None, lambda svg: 'param1' in svg),
        (
            True,
            '--title "The Title" --language-labels --parameters B,C --colormaps viridis,tol '
            '--language-properties Family_name --pacific-centered',
            None, lambda svg: 'The Title' in svg,
        ),
        (
            False,
            '--projection Robinson --parameters param1 --with-stock-img',
            None, None),
        (
            False,
            '--projection Robinson --parameters param1 --extent "50,150,50,-50"',
            None, None),
        (
            False,
            '--projection Robinson --parameters param1 --zorder \'{"v":5}\'',
            None, None),
        (
            False,
            '--parameters param1,param2 --no-borders',
            None, None),
        (
            True,
            '--parameters C,D --colormaps \'{"0":"circle","1":"diamond","2":"square"},tol\' '
            '--projection Mollweide',
            None, None),
        (
            True,
            '--parameters Z,C --projection Mollweide --pacific-centered',
            None, None),
    ]
)
def test_map(
        MetadataFreeStructureDataset, StructureDataset, md_path_factory,
        glottolog_dir, tmp_path, with_full_dataset, opts, expect_html, expect_svg):
    if isinstance(with_full_dataset, str):
        data = md_path_factory(with_full_dataset)
    else:
        data = StructureDataset.directory / 'StructureDataset-metadata.json' \
            if with_full_dataset else MetadataFreeStructureDataset

    def run(fmt):
        out = tmp_path / 'testmap.{}'.format(fmt)
        args = '{} --test --format {} --output {} --glottolog {} '.format(
            data, fmt, out, glottolog_dir)
        runcli('cldfviz.map', args + opts)
        assert out.exists()
        return out.read_text(encoding='utf8')

    html = run('html')
    if expect_html:
        assert expect_html(html)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            'ignore', category=DeprecationWarning, module='cartopy.crs')
        svg = run('svg')
    if expect_svg:
        assert expect_svg(svg)
