import re
import urllib.parse

from pycldf import orm
import jinja2
import jinja2.meta
from clldutils.misc import nfilter

import cldfviz

__all__ = ['iter_templates', 'render']

MD_LINK_PATTERN = re.compile(r'\[(?P<label>[^]]*)]\((?P<url>[^)]+)\)')
TEMPLATE_DIR = cldfviz.PKG_DIR.joinpath('templates', 'text')


def get_env(template_dir=None):
    loader = jinja2.FileSystemLoader(
        searchpath=[str(d) for d in nfilter([template_dir, TEMPLATE_DIR])])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)

    def paragraphs(s):
        return '\n\n'.join(s.split('\n'))

    env.filters['paragraphs'] = paragraphs
    return env


def iter_templates():
    env = get_env()
    for p in sorted(TEMPLATE_DIR.iterdir(), key=lambda pp: pp.name):
        m = re.match(r"{#(.+?)#}", p.read_text(encoding='utf8'), flags=re.MULTILINE | re.DOTALL)
        doc = m.group(1) if m else None
        template_source = env.loader.get_source(env, p.name)
        parsed_content = env.parse(template_source)
        vars = jinja2.meta.find_undeclared_variables(parsed_content)
        yield p, doc, [v for v in vars if v != 'ctx']


def render_template(env, fname_or_component, ctx, index=False, fmt='md', func_dict=None):
    func_dict = func_dict or {}
    # Determine the template to use ...
    tmpl_fname = ctx.pop(
        '__template__',  # ... by looking for an explicit name ...
        # ... and falling back to the "most suitable" one.
        '{}_{}.{}'.format(fname_or_component, 'index' if index else 'detail', fmt),
    )
    jinja_template = env.get_template(tmpl_fname)
    jinja_template.globals.update(func_dict)
    return jinja_template.render(**ctx)


def pad_ex(obj, gloss):
    out_obj = []
    out_gloss = []
    for o, g in zip(obj, gloss):
        diff = len(o) - len(g)
        if diff < 0:
            o += " "*-diff  # noqa E225
        else:
            g += " " * diff
        out_obj.append(o)
        out_gloss.append(g)
    return "  ".join(out_obj).strip(), "  ".join(out_gloss).strip()


def render(doc, cldf, template_dir=None):
    table_map = {}
    for table in cldf.tables:
        fname = str(table.url)
        if (fname, 'id') in cldf:
            try:
                table_map[fname] = cldf.get_tabletype(table)
            except ValueError:
                table_map[fname] = None
    table_map[cldf.bibname] = 'Source'
    return ''.join(iter_md(get_env(template_dir=template_dir), doc, cldf, table_map))


def iter_md(env, md, cldf, table_map, func_dict=None):
    func_dict = func_dict or {"pad_ex": pad_ex}
    datadict = {}
    datadict[cldf.bibname] = {src.id: src for src in cldf.sources}

    reverse_table_map = {v: k for k, v in table_map.items()}
    current = 0
    for m in MD_LINK_PATTERN.finditer(md):
        yield md[current:m.start()]
        current = m.end()
        url = urllib.parse.urlparse(m.group('url'))
        fname = url.path.split('/')[-1]
        if fname in reverse_table_map:
            fname = reverse_table_map[fname]
        if url.fragment.startswith('cldf:') and fname in table_map:
            if fname not in datadict:
                objs = cldf.objects(table_map[fname]) \
                    if table_map[fname] else cldf.iter_rows(fname, 'id')
                datadict[fname] = {r.id if isinstance(r, orm.Object) else r['id']: r for r in objs}

            type_ = table_map[fname]
            _, _, oid = url.fragment.partition(':')
            tmpl_context = {
                k: True if v[0] == '' else v[0] for k, v in
                urllib.parse.parse_qs(url.query, keep_blank_values=True).items()}
            for k in tmpl_context:
                if k.startswith('with_') and (tmpl_context[k] in ['0', 'false', 'False']):
                    tmpl_context[k] = False
            tmpl_context['ctx'] = list(datadict[fname].values()) \
                if oid == '__all__' else datadict[fname][oid]
            tmpl_context['cldf'] = cldf
            yield render_template(
                env, type_ or fname, tmpl_context, index=oid == '__all__', func_dict=func_dict)
        else:
            yield md[m.start():m.end()]
    yield md[current:]
