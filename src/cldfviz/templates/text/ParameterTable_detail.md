{# 
  Render a parameter. 
#}
**{{ ctx.name }}**

{% if ctx.codes %}
Codes:
{% for code in ctx.codes %}
- {{ code.name }}{% if code.description != None %}: {{ code.description }}{% endif %}
{% endfor %}
{% endif %}

{% if ctx.cldf.description %}
Description:
{{ ctx.cldf.description }}
{% endif %}
