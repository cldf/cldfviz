{# 
  Render an example object as IGT (if possible). 
  `with_primaryText`
  `with_internal_ref_link`
#}
{% import 'util.md' as util %}
> ({{ ctx.id }}) {{ ctx.related('languageReference').name }}{{ util.references(ctx.references, with_internal_ref_link=with_internal_ref_link) }}
{% if (ctx.cldf.analyzedWord == [] and ctx.cldf.primaryText != None) or with_primaryText %}
> _{{ ctx.cldf.primaryText }}_
{% endif %}
>
{% if ctx.cldf.analyzedWord != [] %}
> |{% for word in ctx.cldf.analyzedWord %} {{ word }} |{% endfor %}

> |{% for word in ctx.cldf.analyzedWord %} --- |{% endfor %}

> |{% for word in ctx.cldf.gloss %} {{ word }} |{% endfor %}

{% endif %}
>
{% if ctx.cldf.translatedText != None %}> ‘{{ ctx.cldf.translatedText }}’{% endif %}
