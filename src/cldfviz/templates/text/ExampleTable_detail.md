{# 
  Render an example object as IGT (if possible). 
  `with_primaryText`
  `with_internal_ref_link`
  `example_id`
  `as_monospace`
#}
{% import 'util.md' as util %}

{% if not as_monospace %}
> ({{ example_id or ctx.id }}) {{ ctx.related('languageReference').name }}{{ util.references(ctx.references, with_internal_ref_link=with_internal_ref_link) }}
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

{% else %}
{% set pad_len = (example_id or ctx.id)|length+3 %}
    ({{ example_id or ctx.id }}) {{ ctx.related('languageReference').name }}{{ util.references(ctx.references, with_internal_ref_link=with_internal_ref_link) }}
{% if (ctx.cldf.analyzedWord == [] and ctx.cldf.primaryText != None) or with_primaryText %}
    {{ " "*pad_len + ctx.cldf.primaryText }}
{% endif %}
{% if ctx.cldf.analyzedWord != [] %}
{% set obj, gloss = pad_ex(ctx.cldf.analyzedWord, ctx.cldf.gloss) %}
    {{ " "*pad_len + obj }}
    {{ " "*pad_len + gloss }}
{% endif %}
{% if ctx.cldf.translatedText != None %}
    {{" "*pad_len}}‘{{ ctx.cldf.translatedText }}’{% endif %}
{% endif %}