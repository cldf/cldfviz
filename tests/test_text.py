import pytest

from pycldf import Generic
from jinja2 import BaseLoader, TemplateNotFound

from cldfviz.text import *


def test_iter_templates():
    assert len(list(iter_templates())) > 17


def test_regular_md(StructureDataset):
    assert render('[Glottolog](https://glottolog.org)', StructureDataset) == \
           '[Glottolog](https://glottolog.org)'


def test_custom_templates(StructureDataset, tmp_path):
    tmpl = tmp_path / 'tmpl'
    tmpl.mkdir()
    tmpl.joinpath('LanguageTable_detail.md').write_text(
        '{{ "stuff" | paragraphs }}', encoding='utf8')
    assert 'stuff' in render('[](LanguageTable#cldf:Juang_SM)', StructureDataset, template_dir=tmpl)

    class Loader(BaseLoader):
        def get_source(self, environment, template):
            path = tmpl / template
            return path.read_text(encoding='utf8'), path, lambda: 1
    assert 'stuff' in render('[](LanguageTable#cldf:Juang_SM)', StructureDataset, loader=Loader())


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
<pre>
The  t-e&lt;in&gt;xt  
The  GL-&lt;FOC&gt;OSS  
‘the translation’</pre>
"""
    assert render('[ex](ExampleTable#cldf:igt)', StructureDataset, escape=False) == """\

> (igt) Ho (Peterson 2017)
<pre>
The  t-e<in>xt  
The  GL-<FOC>OSS  
‘the translation’</pre>
"""
    assert render('[ex](ExampleTable#cldf:ptonly)', StructureDataset) == """\

> (ptonly) Ho
<pre>
<i>Only primary text</i>  
‘and translation’</pre>
"""
    res = render(
        """[](ExampleTable?with_internal_ref_link#cldf:igt)
[](sources.bib#cldf:__all__)""",
        StructureDataset)
    assert "The Title" in res
    res = render(
        """[](ExampleTable?with_internal_ref_link#cldf:igt)
[](sources.bib?cited_only=1#cldf:__all__)""",
        StructureDataset)
    assert "The Title" not in res
    assert "Fitting the pieces" in res


def test_render_entry(Dictionary):
    assert render('[ex](EntryTable#cldf:entry-1)', Dictionary) \
        == '‘Motschegiebschn’, *noun*: lady bug\n'
    assert render('[ex](EntryTable#cldf:entry-2)', Dictionary) \
        == '‘Bemme’, *noun*: 1. sandwich 2. tire of a bicycle\n'
    assert render('[ex](EntryTable#cldf-pref:entry-2)', dict(pref=Dictionary)) \
           == '‘Bemme’, *noun*: 1. sandwich 2. tire of a bicycle\n'


def test_render_metadata(StructureDataset):
    assert render('[](p/StructureDataset-metadata.json#cldf:"dc:identifier")', StructureDataset) == \
        'https://doi.org/10.1515/jsall-2017-0008'
    assert render(
        """[](Metadata#cldf:tables[?"dc:conformsTo"=='http://cldf.clld.org/v1.0/terms.rdf#LanguageTable'].url | [0])""",
        StructureDataset) == 'languages.csv'


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


def test_reference_list(StructureDataset):
    text = """# [](ParameterTable?__template__=property.md&name=name#cldf:B)

See [](Source?ref&with_internal_ref_link#cldf:Peterson2017) and [ex](http://example.com)

[References](Source?cited_only#cldf:__all__)
"""
    res = render(text, StructureDataset)
    assert "Gender/Noun classes" in res
    assert 'Peterson 2017' in res
    assert "Fitting the pieces together" in res


def test_keep_label(StructureDataset):
    text = "[xyz](Source?ref&with_internal_ref_link&keep_label#cldf:Peterson2017)"
    assert 'xyz' in render(text, StructureDataset)
