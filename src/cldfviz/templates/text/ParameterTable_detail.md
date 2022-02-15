{# 
  Render a parameter. 
  `with_codes`
#}
**{{ ctx.name }}**

{% if ctx.cldf.description %}
Description:
{{ ctx.cldf.description }}
{% endif %}

{% if ctx.codes and (with_codes or with_codes is not defined) %}
Codes:
{% for code in ctx.codes %}
- {{ code.name }}{% if code.description != None %}: {{ code.description }}{% endif %}

{% endfor %}
{% endif %}
