"""
Functionality implementing rendering of CLDF Markdown.
"""
import re
import html
import pathlib
import functools
from typing import Union, Optional, Callable, Any
from collections.abc import Iterable, Generator

from pycldf import Dataset
from pycldf.ext.markdown import CLDFMarkdownText, CLDFMarkdownLink
import jinja2
import jinja2.meta
from clldutils.misc import nfilter
from clldutils.markup import MarkdownLink, MarkdownImageLink

import cldfviz

__all__ = ['iter_templates', 'render', 'iter_cldfviz_links']

PathType = Union[pathlib.Path, str]
TEMPLATE_DIR = cldfviz.PKG_DIR.joinpath('templates', 'text')


def source_markdown(src, with_link=False):
    """Render a Source object as markdown."""
    return src.text(**{'markdown': True} if with_link else {})


def _add_filters(env):
    def paragraphs(s):
        return '\n\n'.join(s.split('\n'))

    env.filters['paragraphs'] = paragraphs


def get_env(template_dir=None, fallback_template_dir=None):
    """Get Jinja2 environment."""
    loader = jinja2.FileSystemLoader(
        searchpath=[str(d) for d in nfilter([template_dir, fallback_template_dir, TEMPLATE_DIR])])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    _add_filters(env)
    return env


def iter_templates() -> Generator[tuple[pathlib.Path, str, list[str]], None, None]:
    """Yield available templates."""
    env = get_env()
    for p in sorted(TEMPLATE_DIR.iterdir(), key=lambda pp: pp.name):
        m = re.match(r"{#(.+?)#}", p.read_text(encoding='utf8'), flags=re.MULTILINE | re.DOTALL)
        doc = m.group(1) if m else None
        vars_ = jinja2.meta.find_undeclared_variables(env.parse(env.loader.get_source(env, p.name)))
        yield p, doc, [v for v in vars_ if v != 'ctx']


def pad_ex(obj: Iterable[str],
           gloss: Iterable[str],
           escape: Optional[bool] = True):
    """
    :param escape: Flag signaling whether to html.escape words and glosses.
    """
    out_obj = []
    out_gloss = []
    for o, g in zip(obj, gloss):
        g = g or ""
        diff = len(o) - len(g)
        if diff < 0:
            o += " "*-diff  # noqa E225
        else:
            g += " " * diff
        out_obj.append(html.escape(o, quote=False) if escape else o)
        out_gloss.append(html.escape(g, quote=False) if escape else g)
    return "  ".join(out_obj).strip(), "  ".join(out_gloss).strip()


def render(  # pylint: disable=R0913,R0917
        doc: PathType,
        cldf_dict: Union[Dataset, dict[Union[str, None], Dataset]],
        template_dir: Optional[PathType] = None,
        loader: Optional[jinja2.BaseLoader] = None,
        func_dict: Optional[dict[str, Callable]] = None,
        escape: Optional[bool] = True,
) -> str:
    """
    Render CLDF Markdown using customizable jinja2 templates.

    Features:

    - Reference list: Include a list of cited references using the link \
      `[](Source?cited_only#cldf:__all__)`

    :param doc: A CLDF Markdown document specified as string or filepath.
    :param cldf_dict: A CLDF dataset or a mapping of prefixes to CLDF datasets.
    :param template_dir: Path to custom template directory.
    :param loader: As alternative to a custom template directory, a custom jinja2 loader can be \
    specified.
    :param func_dict: Mapping of names to callables passed to templates as renderer globals, see \
    https://jinja.palletsprojects.com/en/3.1.x/api/#jinja2.Environment.globals.
    :return: Rendered document as string.
    """
    func_dict = func_dict or {}
    func_dict.update({
        "pad_ex": functools.partial(pad_ex, escape=escape),
        "source_markdown": source_markdown})

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


def iter_cldfviz_links(md: str) -> Generator[MarkdownImageLink, None, None]:
    """Support for finding links to images to be created via cldfviz."""
    for match in MarkdownImageLink.pattern.finditer(md):
        ml = MarkdownImageLink.from_match(match)
        if re.match(r'cldfviz\.(map|tree)', ml.parsed_url.fragment):
            yield ml


class TemplateRenderer(CLDFMarkdownText):
    """
    Implements templated rendering of CLDF Markdown.
    """
    def __init__(self, env: jinja2.Environment, func_dict: dict[str, Callable], *args, **kw):
        super().__init__(*args, **kw)
        self.env = env
        self.func_dict = func_dict
        self.with_partial_local_reflist = False
        self.cited = None

    def render_template(
            self,
            fname_or_component: Optional[str],
            ctx: dict[str, Any],
            index: bool = False,
            fmt: str = 'md',
    ) -> str:
        """Helper method, implementing templated rendering."""
        # Determine the template to use ...
        tmpl_fname = ctx.pop(
            '__template__',  # ... by looking for an explicit name ...
            # ... and falling back to the "most suitable" one.
            f"{fname_or_component}_{'index' if index else 'detail'}.{fmt}",
        )
        jinja_template = self.env.get_template(tmpl_fname)
        jinja_template.globals.update(self.func_dict)
        jinja_template.globals.update({"component": fname_or_component})
        return jinja_template.render(**ctx)

    def get_tmpl_context(self, ml: CLDFMarkdownLink) -> dict[str, Any]:
        """Create the context for a template."""
        tmpl_context: dict[str, Any] = {
            k: True if v[0] == '' else v[0] for k, v in ml.parsed_url_query.items()}
        for k in tmpl_context:
            # "with_" parameters get boolean values.
            if k.startswith('with_') and (tmpl_context[k] in ['0', 'false', 'False']):
                tmpl_context[k] = False
        tmpl_context['ctx'] = self.get_object(ml)
        tmpl_context['cldf'] = self.dataset_mapping[ml.prefix]
        tmpl_context['ml_label'] = ml.label
        return tmpl_context

    def render_link(self, cldf_link: CLDFMarkdownLink) -> Union[str, CLDFMarkdownLink]:
        """Render a link according using templates."""
        ref_link = all((
            cldf_link.all,
            'cited_only' in cldf_link.parsed_url_query,
            cldf_link.component(self.dataset_mapping[cldf_link.prefix]) == 'Source'))

        if self.cited:
            # We're in the second pass!
            if ref_link:
                ctx = self.get_tmpl_context(cldf_link)
                ctx['ctx'] = [s for s in self.get_object(cldf_link) if s.id in self.cited]
                ctx["with_anchor"] = True
                return self.render_template('Source', ctx, index=True)
            return cldf_link  # pragma: no cover

        if ref_link:  # So we need a second pass.
            self.with_partial_local_reflist = True
            return cldf_link

        return self.render_template(
            cldf_link.component(self.dataset_mapping[cldf_link.prefix]) or cldf_link.table_or_fname,
            self.get_tmpl_context(cldf_link),
            index=cldf_link.all)

    def render(
            self,
            simple_link_detection: bool = True,
            markdown_kw: Optional[dict[str, Any]] = None,
    ) -> str:
        md = super().render(simple_link_detection=simple_link_detection, markdown_kw=markdown_kw)
        if self.with_partial_local_reflist:
            # Second pass!
            # 1. Determine which sources have been referenced:
            self.cited = {
                ml.url.split('-', maxsplit=1)[-1]
                for ml in _markdownlink_finditer(md)
                if ml.url.startswith('#source-')}

            # 2. Insert the pruned list of sources:
            self.text = md
            md = super().render(
                simple_link_detection=simple_link_detection, markdown_kw=markdown_kw)
        return md


def _markdownlink_finditer(md):
    for ml in MarkdownLink.pattern.finditer(md):
        try:
            yield MarkdownLink.from_match(ml)
        except AttributeError:
            continue
