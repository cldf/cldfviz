{# 
 Render a cognate.
 #}
{% import 'util.md' as util %}
{{ util.form(ctx.form, with_language=True) }}{{ util.references(ctx.references) }}
