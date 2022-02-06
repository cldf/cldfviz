{# 
  Render all sources of a dataset as bullet list. 
  Pass `with_anchor` to pre-pend an HTML anchor suitable as link target to each source.
#}
{% for src in ctx %}
- {% if with_anchor is defined %}<a id="source-{{ src.id }}"> </a>{% endif %}{{ src.text() }}
{% endfor %}