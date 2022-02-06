{# 
 Render Cognate objects.
 Pass `cognatesetReference=...` to filter cognates of a specific cognateset. This will lead to
 displaying also alignments if available.
 #}
{% import 'util.md' as util %}
{% if cognatesetReference is defined %}
{{ util.alignments(ctx, cognatesetReference) }}
{% else %}
{% for cog in ctx %}
- {{ util.form(cog.form) }}_  {{ cog.form.language.name }}
{% endfor %}
{% endif %}