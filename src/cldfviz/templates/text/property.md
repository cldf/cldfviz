{# 
 Render a single property/attribute of a data object.
 #}
{% set prop = property if property is defined else "name" %}
{% set res = ctx["cldf"][prop] or ctx["data"][prop] or ctx[prop] %}
{{ res | paragraphs }}
