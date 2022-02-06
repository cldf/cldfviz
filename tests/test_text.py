from cldfviz.text import render


def test_custom_templates(StructureDataset, tmp_path):
    tmpl = tmp_path / 'tmpl'
    tmpl.mkdir()
    tmpl.joinpath('LanguageTable_detail.md').write_text("stuff", encoding='utf8')
    assert 'stuff' in render('[](LanguageTable#cldf:Juang_SM)', StructureDataset, template_dir=tmpl)


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


