{# 
 Render a list of all parameters in a dataset.
 #}
{% for p in ctx %}
- {{ lang.cldf.name }}
{% endfor %}
