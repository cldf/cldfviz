import pytest

from pycldf import Generic

from cldfviz.text import *


def test_iter_templates():
    assert len(list(iter_templates())) > 17


def test_regular_md(StructureDataset):
    assert render('[Glottolog](https://glottolog.org)', StructureDataset) == \
           '[Glottolog](https://glottolog.org)'


def test_custom_templates(StructureDataset, tmp_path):
    tmpl = tmp_path / 'tmpl'
    tmpl.mkdir()
    tmpl.joinpath('LanguageTable_detail.md').write_text("stuff", encoding='utf8')
    assert 'stuff' in render('[](LanguageTable#cldf:Juang_SM)', StructureDataset, template_dir=tmpl)


def test_non_standard_table(tmp_path):
    ds = Generic.in_dir(tmp_path)
    ds.add_table('data.csv', 'id', 'name', 'description')
    ds.write(tmp_path / 'md.json', **{'data.csv': [dict(id='1', name='The Name', description='')]})
    tmpl = tmp_path / 'tmpl'
    tmpl.mkdir()
    tmpl.joinpath('data.csv_detail.md').write_text("{{ ctx['name'] }}", encoding='utf8')
    assert 'The Name' in render('[](data.csv#cldf:1)', ds, template_dir=tmpl)


def test_render_example(StructureDataset):
    assert render('[ex](ExampleTable#cldf:igt)', StructureDataset) == """\
> (igt) Ho (Peterson 2017)
>
> | The | t-ext |
> | --- | --- |
> | The | GL-OSS |
>
> ‘the translation’"""
    assert render('[ex](ExampleTable#cldf:ptonly)', StructureDataset) == """\
> (ptonly) Ho
> _Only primary text_
>
>
> ‘and translation’"""


@pytest.mark.parametrize(
    'comp,query,oid,ds,expected',
    [
        ('BorrowingTable', None, 'dutch_eiland', 'wl', 'Old Frisian'),
        ('CodeTable', None, 'C-0', 'sd', 'affixal'),
        ('CognateTable', None, 'Tena-1_one-1-1', 'wl', 'List and'),
        ('CognateTable', 'cognatesetReference=1', '__all__', 'wl', 'hʊk'),
        ('CognatesetTable', None, '1', 'wl', 'One-1'),
        ('ContributionTable', None, '12', 'wl', 'Dutch'),
        ('FormTable', None, '2', 'wl', 'eiland'),
        ('FormTable', None, '1', 'gn', 'a lot, '),
        ('FormTable', 'with_language', '2', 'wl', 'Dutch'),
        ('LanguageTable', None, 'Juang_SM', 'sd', lambda s: 'glottolog.org' not in s),
        ('LanguageTable', 'with_glottolog_link', 'Juang_SM', 'sd', 'glottolog.org'),
        ('ParameterTable', None, 'C', 'sd', 'Codes'),
        ('Source', None, 'Peterson2017', 'sd', 'Peterson, John. 2017.'),
        ('Source', None, '__all__', 'sd', '- '),
        ('Source', 'with_link', 'Peterson2017', 'sd', '[DOI:'),
    ]
)
def test_templates(Wordlist, Generic, StructureDataset, comp, query, oid, ds, expected):
    if ds == 'wl':
        dataset = Wordlist
    elif ds == 'gn':
        dataset = Generic
    else:
        dataset = StructureDataset
    res = render(
        '[]({}{}#cldf:{})'.format(comp, '?{}'.format(query) if query else '', oid), dataset)
    if callable(expected):
        assert expected(res)
    else:
        print(res)
        assert expected in res
