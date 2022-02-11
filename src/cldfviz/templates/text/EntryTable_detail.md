{#
  Render a Dictionary entry along with its meaning descriptions.
#}
‘{{ ctx.cldf["headword"] }}’, *{{ ctx.cldf["partOfSpeech"] }}*:
{%- if ctx.senses|length == 1 %}
 {{ ctx.senses[0].cldf["description"] }}
{% else %}
{% for sense in ctx.senses %}{{ " " }}{{ loop.index }}. {{ sense.cldf["description"] }}{% endfor %}{{ "" }}
{% endif %}
