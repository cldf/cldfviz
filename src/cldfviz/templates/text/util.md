{# 
 Template macros
 #}
{% macro reference(ref, year_brackets=None, pages=True, with_internal_ref_link=False) -%}
{% if with_internal_ref_link %}[{% endif %}{{ ref.source.refkey(year_brackets=year_brackets) }}{% if with_internal_ref_link %}
](#{% if with_internal_ref_link is string %}{{ with_internal_ref_link }}{% else %}source-{{ ref.source.id }}{% endif %}){% endif %}{% if ref.description %}
: {{ ref.description }}{% endif %}
{%- endmacro %}

{% macro references(refs, brackets=True, pages=True, with_internal_ref_link=False) -%}
{% if refs %}{% if brackets %}
 ({% endif %}{% for ref in refs %}
{{ reference(ref, pages=pages, with_internal_ref_link=with_internal_ref_link) }}{% if loop.last == False %}, {% endif %}{% endfor %}{% if brackets %}
){% endif %}{% endif %}
{%- endmacro %}

{% macro form(f, with_language=False) -%}
{% if with_language %}{{ f.language.name }} {% endif %}_{{ f.cldf.form }}_ ‘{{ f.parameter.name if f.parameter else f.cldf.parameterReference }}’
{%- endmacro %}

{% macro alignments(cogs, cognatesetReference) -%}
{% set vars = namespace(header=False) %}
{% for cog in cogs %}
{% if cog.cldf.cognatesetReference == cognatesetReference %}
{% if not vars.header %}

| Form | Language | {% for seg in cog.cldf.alignment %}- | {% endfor %}

| --- | --- | {% for seg in cog.cldf.alignment %} --- | {% endfor %}

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
