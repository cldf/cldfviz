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
<blockquote>
(igt) Ho (Peterson 2017)

| The | t-ext |
| --- | --- |
| The | GL-OSS |

‘the translation’
</blockquote>"""
    assert render('[ex](ExampleTable#cldf:ptonly)', StructureDataset) == """\
<blockquote>
(ptonly) Ho
_Only primary text_



‘and translation’
</blockquote>"""


def test_render_source(StructureDataset):
    assert "Peterson, John. 2017." in render('[P](sources.bib#cldf:Peterson2017)', StructureDataset)
    assert "- " in render('[P](sources.bib#cldf:__all__)', StructureDataset)


def test_render_language(StructureDataset):
    res = render('[P](LanguageTable?with_glottolog_link#cldf:Juang_SM)', StructureDataset)
    assert 'glottolog.org' in res

    res = render('[P](LanguageTable#cldf:Juang_SM)', StructureDataset)
    assert 'glottolog.org' not in res


def test_render_parameter(StructureDataset):
    res = render('[](ParameterTable#cldf:C)', StructureDataset)
    assert "Codes" in res


