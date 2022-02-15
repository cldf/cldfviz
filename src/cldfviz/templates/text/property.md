{# 
 Render a single property/attribute of a data object.
 #}
{% set prop = property if property is defined else "name" %}
{{ ctx[prop] }}