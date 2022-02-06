{# 
 Template macros
 #}
{% macro reference(ref, year_brackets=None, pages=True) -%}
{{ ref.source.refkey(year_brackets=year_brackets) }}{% if ref.description %}: {{ ref.description }}{% endif %}
{%- endmacro %}

{% macro references(refs, brackets=True, pages=True) -%}
{% if refs %}{% if brackets %}
 ({% endif %}{% for ref in refs %}
{{ reference(ref, pages=pages) }}{% if loop.last == False %}, {% endif %}{% endfor %}{% if brackets %}
){% endif %}{% endif %}
{%- endmacro %}

{% macro form(f) -%}
_{{ f.cldf.form }}_ ‘{{ f.parameter.name if f.parameter else f.cldf.parameterReference }}’
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
