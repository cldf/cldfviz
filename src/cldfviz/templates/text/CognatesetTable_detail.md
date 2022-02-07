{# 
 Render a Cognateset.
 
 name
 description
 source, comment
 
 - cognates
 or table of cognates with alingnments!
 #}
{% import 'util.md' as util %}
{{ ctx.name }}

{% if ctx.cldf.description %}{{ ctx.cldf.description }}{% endif %}

{% if ctx.references %}Source: {{ util.references(ctx.references, brackets=False) }}{% endif %}

{{ util.alignments(ctx.cognates, ctx.id) }}