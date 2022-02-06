{# 
  Render a borrowing, aka loanword.
#}
{% import 'util.md' as util %}
{{ util.form(ctx.targetForm) }}{% if ctx.sourceForm %}
 (from {{ ctx.sourceForm.language.name }}{% if ctx.sourceForm.cldf.form != ctx.targetForm.cldf.form or ctx.sourceForm.parameter != ctx.targetForm.parameter %}
 _{{ ctx.sourceForm.cldf.form }}_{% endif %}{% if ctx.sourceForm.parameter != ctx.targetForm.parameter %}
 ‘{{ ctx.sourceForm.meaning }}’{% endif %}){% endif %}{{ util.references(ctx.references) }}