{# 
 Render the list of contributions of a dataset.
 #}
{% for contrib in ctx %}
- {{ contrib.name }}{% if contrib.cldf.contributor %} by {{ contrib.cldf.contributor }}{% endif %}
{% endfor %}