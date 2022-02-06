{# 
  Renders the name of a language object.
  Pass parameter `with_glottolog_link` to append the Glottocode as link to Glottolog.
#}
{{ ctx.cldf.name }}{% if ctx.cldf.glottocode != None and with_glottolog_link is defined %}[{{ ctx.cldf.glottocode }}](https://glottolog.org/resource/languoid/id/{{ ctx.cldf.glottocode }}){% endif %}
