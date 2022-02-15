{# 
 Render a code of a categorical parameter.
 #}
{{ ctx.cldf.name or ctx.id }}{% if ctx.cldf.description %} ({{ ctx.cldf.description }}){% endif %}