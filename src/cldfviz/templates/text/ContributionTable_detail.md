{# 
 Render a contribution
 #}
{{ ctx.name }} {% if ctx.cldf.contributor %}by {{ ctx.cldf.contributor }}{% endif %}


{% if ctx.cldf.description %}{{ ctx.cldf.description }}{% endif %}


{% if ctx.cldf.citation %}
Cite as:
<blockquote>
{{ ctx.cldf.citation }}
</blockquote>
{% endif %}