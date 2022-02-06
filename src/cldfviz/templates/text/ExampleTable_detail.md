{# 
  Render an example object as IGT (if possible). 
#}
{% import 'util.md' as util %}
<blockquote>
({{ ctx.id }}) {{ ctx.related('languageReference').name }}{{ util.references(ctx.references) }}
{% if ctx.cldf.analyzedWord == [] and ctx.cldf.primaryText != None %}
_{{ ctx.cldf.primaryText }}_
{% endif %}

{% if ctx.cldf.analyzedWord != [] %}
|{% for word in ctx.cldf.analyzedWord %} {{ word }} |{% endfor %}

|{% for word in ctx.cldf.analyzedWord %} --- |{% endfor %}

|{% for word in ctx.cldf.gloss %} {{ word }} |{% endfor %}
{% endif %}


{% if ctx.cldf.translatedText != None %}‘{{ ctx.cldf.translatedText }}’{% endif %}

</blockquote>
