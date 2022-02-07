{# 
  Render a source object as linearization according to the unified stylesheet for Linguistics.
  Pass `with_anchor` to pre-pend an HTML anchor suitable as link target.
  Pass `with_link` to append a markdown link if the source has DOI or URL.
#}
{% import 'util.md' as util %}
{{ util.source(ctx, with_anchor=with_anchor, with_link=with_link) }}