{# 
 Template macros
 #}
{% macro sourceref(src, year_brackets=None, with_internal_ref_link=False) -%}
{% if with_internal_ref_link %}[{% endif %}{{ src.refkey(year_brackets=year_brackets) }}{% if with_internal_ref_link %}
](#{% if with_internal_ref_link is string %}{{ with_internal_ref_link }}{% else %}source-{{ src.id }}{% endif %}){% endif %}
{%- endmacro %}

{% macro reference(ref, year_brackets=None, pages=True, with_internal_ref_link=False) -%}
{{ sourceref(ref.source, year_brackets=year_brackets, with_internal_ref_link=with_internal_ref_link) }}{% if ref.description %}
: {{ ref.description }}{% endif %}
{%- endmacro %}

{% macro references(refs, brackets=True, pages=True, with_internal_ref_link=False) -%}
{% if refs %}{% if brackets %}
 ({% endif %}{% for ref in refs %}
{{ reference(ref, pages=pages, with_internal_ref_link=with_internal_ref_link) }}{% if loop.last == False %}, {% endif %}{% endfor %}{% if brackets %}
){% endif %}{% endif %}
{%- endmacro %}

{% macro form(f, with_language=False) -%}
{% if f.cldf.form is string %}
    {% set form_string = "_" + f.cldf.form + "_" %}
{% else %}
    {% set form_strings = [] %}
    {% for form in f.cldf.form %}
        {% set form_strings = form_strings.append("_" + form + "_") %}
    {% endfor %}
    {% set form_string = form_strings|join("/") %}
{% endif %}
{% if f.cldf.parameterReference is not string %} 
    {% set translations = [] %}
    {% for par in f.parameters %}
        {% set translations = translations.append(par.name) %}
    {% endfor %}
    {% set trans_string = translations|join(", ") %}
{% else %}
    {% set trans_string = f.parameter.name %}
{% endif %}
{% if with_language %}{{ f.language.name }} {% endif %}{{form_string}} ‘{{ trans_string }}’
{%- endmacro %}

{% macro alignments(cogs, cognatesetReference) -%}
{% set vars = namespace(header=False) %}
{% for cog in cogs %}
{% if cog.cldf.cognatesetReference == cognatesetReference %}
{% if not vars.header %}

| Form | Language | {% for seg in cog.cldf.alignment %}- | {% endfor %}

| :-- | :-- | {% for seg in cog.cldf.alignment %} :-- | {% endfor %}

{% set vars.header = True %}
{% endif %}
| _{{ cog.form.cldf.form }}_ | {{ cog.form.language.name }} | {% for seg in cog.cldf.alignment %}{{ seg }} | {% endfor %}

{% endif %}
{% endfor %}
{%- endmacro %}

{% macro source(src, with_anchor=False, with_link=False) -%}
{% if with_anchor %}<a id="source-{{ src.id }}"> </a>{% endif %}{{ src.text() }}{% if with_link %}
{% if src.get("doi") %}
 [DOI: {{ src["doi"] }}](https://doi.org/{{ src["doi"] }}){% else %}{% if src.get("url") %}
 [{{ src["url"] }}]({{ src["url"] }}){% endif %}
{% endif %}
{% endif %}
{%- endmacro %}
