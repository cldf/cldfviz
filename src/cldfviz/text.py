import re

from pycldf import Dataset
from pycldf.ext.markdown import CLDFMarkdownText
import jinja2
import jinja2.meta
from clldutils.misc import nfilter
from clldutils.markup import MarkdownLink, MarkdownImageLink

import cldfviz

__all__ = ['iter_templates', 'render', 'iter_cldfviz_links']

TEMPLATE_DIR = cldfviz.PKG_DIR.joinpath('templates', 'text')


def _add_filters(env):
    def paragraphs(s):
        return '\n\n'.join(s.split('\n'))

    env.filters['paragraphs'] = paragraphs


def get_env(template_dir=None, fallback_template_dir=None):
    loader = jinja2.FileSystemLoader(
        searchpath=[str(d) for d in nfilter([template_dir, fallback_template_dir, TEMPLATE_DIR])])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    _add_filters(env)
    return env


def iter_templates():
    env = get_env()
    for p in sorted(TEMPLATE_DIR.iterdir(), key=lambda pp: pp.name):
        m = re.match(r"{#(.+?)#}", p.read_text(encoding='utf8'), flags=re.MULTILINE | re.DOTALL)
        doc = m.group(1) if m else None
        parsed_content = env.parse(env.loader.get_source(env, p.name))
        vars = jinja2.meta.find_undeclared_variables(parsed_content)
        yield p, doc, [v for v in vars if v != 'ctx']


def pad_ex(obj, gloss):
    out_obj = []
    out_gloss = []
    for o, g in zip(obj, gloss):
        g = g or ""
        diff = len(o) - len(g)
        if diff < 0:
            o += " "*-diff  # noqa E225
        else:
            g += " " * diff
        out_obj.append(o)
        out_gloss.append(g)
    return "  ".join(out_obj).strip(), "  ".join(out_gloss).strip()


def render(doc, cldf_dict, template_dir=None, loader=None, func_dict=None):
    """
    Render CLDF Markdown using customizable jinja2 templates.

    Features:

    - Reference list: Include a list of cited references using the link \
      `[](Source?cited_only#cldf:__all__)`

    :param doc:
    :param cldf_dict:
    :param template_dir:
    :param loader:
    :param func_dict:
    :return:
    """
    func_dict = func_dict or {}
    func_dict.update({"pad_ex": pad_ex})

    if isinstance(cldf_dict, Dataset):
        cldf_dict = {None: cldf_dict}

    folder_env = get_env(template_dir=template_dir)
    if loader is None:
        env = folder_env
    else:
        env = jinja2.Environment(
            loader=jinja2.ChoiceLoader([loader, folder_env.loader]),
            trim_blocks=True,
            lstrip_blocks=True)
        _add_filters(env)

    proc = TemplateRenderer(
        env, func_dict, doc, cldf_dict,
        # download_dir!
    )
    return proc.render()


def iter_cldfviz_links(md):
    for match in MarkdownImageLink.pattern.finditer(md):
        ml = MarkdownImageLink.from_match(match)
        if re.match(r'cldfviz\.(map|tree)', ml.parsed_url.fragment):
            yield ml


class TemplateRenderer(CLDFMarkdownText):
    def __init__(self, env, func_dict, *args, **kw):
        super().__init__(*args, **kw)
        self.env = env
        self.func_dict = func_dict
        self.with_partial_local_reflist = False
        self.cited = None

    def render_template(self, fname_or_component, ctx, index=False, fmt='md'):
        # Determine the template to use ...
        tmpl_fname = ctx.pop(
            '__template__',  # ... by looking for an explicit name ...
            # ... and falling back to the "most suitable" one.
            '{}_{}.{}'.format(fname_or_component, 'index' if index else 'detail', fmt),
        )
        jinja_template = self.env.get_template(tmpl_fname)
        jinja_template.globals.update(self.func_dict)
        return jinja_template.render(**ctx)

    def get_tmpl_context(self, ml):
        tmpl_context = {k: True if v[0] == '' else v[0] for k, v in ml.parsed_url_query.items()}
        for k in tmpl_context:
            if k.startswith('with_') and (tmpl_context[k] in ['0', 'false', 'False']):
                tmpl_context[k] = False
        tmpl_context['ctx'] = self.get_object(ml)
        tmpl_context['cldf'] = self.dataset_mapping[ml.prefix]
        return tmpl_context

    def render_link(self, ml):
        ref_link = ml.all and \
            'cited_only' in ml.parsed_url_query and \
            ml.component(self.dataset_mapping[ml.prefix]) == 'Source'

        if self.cited:
            # We're in the second pass!
            if ref_link:
                ctx = self.get_tmpl_context(ml)
                ctx['ctx'] = [s for s in self.get_object(ml) if s.id in self.cited]
                ctx["with_anchor"] = True
                return self.render_template('Source', ctx, index=True)
            return ml

        if ref_link:  # So we need a second pass.
            self.with_partial_local_reflist = True
            return ml

        return self.render_template(
            ml.component(self.dataset_mapping[ml.prefix]) or ml.table_or_fname,
            self.get_tmpl_context(ml),
            index=ml.all)

    def render(self, simple_link_detection=True, markdown_kw=None):
        md = super().render(simple_link_detection=simple_link_detection, markdown_kw=markdown_kw)
        if self.with_partial_local_reflist:
            # Second pass!
            # 1. Determine which sources have been referenced:
            self.cited = set(
                MarkdownLink.from_match(ml).url.split('-', maxsplit=1)[-1]
                for ml in MarkdownLink.pattern.finditer(md)
                if MarkdownLink.from_match(ml).url.startswith('#source-'))

            # 2. Insert the pruned list of sources:
            md = super().render(
                simple_link_detection=simple_link_detection, markdown_kw=markdown_kw)
        return md
