{# 
 Render a table of all languages in a dataset.
 #}
{% for lang in ctx %}
{% if loop.first %}

| Name |{% if ('LanguageTable', 'glottocode') in cldf %} Glottocode |{% endif %}{% if ('LanguageTable', 'ISO639P3code') in cldf %} ISO 639-3 |{% endif %}

| :-- |{% if ('LanguageTable', 'glottocode') in cldf %} :-- |{% endif %}{% if ('LanguageTable', 'ISO639P3code') in cldf %} :-- |{% endif %}

{% endif %}
| {{ lang.cldf.name }} |{% if ('LanguageTable', 'glottocode') in cldf %} {{ lang.cldf.glottocode }} |{% endif %}{% if ('LanguageTable', 'ISO639P3code') in cldf %} {{ lang.cldf.ISO639P3code }} |{% endif %}

{% endfor %}
