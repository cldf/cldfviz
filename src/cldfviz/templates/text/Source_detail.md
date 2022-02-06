{# 
  Render a source object as linearization according to the unified stylesheet for Linguistics.
  Pass `with_anchor` to pre-pend an HTML anchor suitable as link target.
#}
{% if with_anchor is defined %}<a id="source-{{ ctx.id }}"> </a>{% endif %}{{ ctx.text() }}