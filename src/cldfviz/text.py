import re

import attr
from pycldf import orm, Dataset
from pycldf.util import pkg_path
from pycldf.dataset import MD_SUFFIX
import jinja2
import jinja2.meta
import jmespath
from clldutils.misc import nfilter
from clldutils.markup import MarkdownLink, MarkdownImageLink

import cldfviz

__all__ = ['iter_templates', 'render', 'iter_cldf_image_links', 'CLDFMarkdownLink']

TEMPLATE_DIR = cldfviz.PKG_DIR.joinpath('templates', 'text')


def get_env(template_dir=None, fallback_template_dir=None):
    loader = jinja2.FileSystemLoader(
        searchpath=[str(d) for d in nfilter([template_dir, fallback_template_dir, TEMPLATE_DIR])])
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


def render_template(env, fname_or_component, ctx, func_dict, index=False, fmt='md'):
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


def render(doc, cldf_dict, template_dir=None, loader=None, func_dict=None):
    func_dict = func_dict or {}
    func_dict.update({"pad_ex": pad_ex})
    if isinstance(cldf_dict, Dataset):
        cldf_dict = {None: cldf_dict}
    for prefix, cldf in cldf_dict.items():
        table_map = {}
        for table in cldf.tables:
            fname = str(table.url)
            if (fname, 'id') in cldf:
                try:
                    table_map[fname] = cldf.get_tabletype(table)
                except ValueError:
                    table_map[fname] = None
        table_map[cldf.bibname] = 'Source'
        table_map[cldf.tablegroup._fname.name] = 'Metadata'
        folder_env = get_env(template_dir=template_dir)
        if loader is None:
            env = folder_env
        else:
            env = jinja2.Environment(
                loader=jinja2.ChoiceLoader([loader, folder_env.loader]),
                trim_blocks=True,
                lstrip_blocks=True)
        doc = replace_links(env, doc, cldf, prefix, table_map, func_dict=func_dict)
    return doc


@attr.s
class CLDFMarkdownLink(MarkdownLink):
    """
    CLDF markdown links are specified using URLs of a particular format.
    """
    fragment_pattern = re.compile(r'cldf(-(?P<dsid>[a-zA-Z0-9_]+))?:')

    @classmethod
    def from_component(cls, comp, objid='__all__', label=None):
        return cls(
            label=label or '{}:{}'.format(comp, objid),
            url='{}#cldf:{}'.format(comp, objid))

    @property
    def is_cldf_link(self):
        return bool(self.fragment_pattern.match(self.parsed_url.fragment))

    @property
    def dsid(self):
        if self.is_cldf_link:
            return self.fragment_pattern.match(self.parsed_url.fragment).group('dsid')

    @property
    def table_or_fname(self):
        if self.is_cldf_link:
            return self.parsed_url.path.split('/')[-1]

    def component(self, cldf=None):
        """
        :param cldf: `pycldf.Dataset` instance to which the link refers.
        :return: Name of the CLDF component the link pertains to or `None`.
        """
        name = self.table_or_fname
        if cldf is None:
            # If no CLDF dataset is passed as context, we can only detect links using proper
            # component names as path:
            return name if name == 'Source' or pkg_path('components', name + MD_SUFFIX).exists() \
                else None

        if name == cldf.bibname or name == 'Source':
            return 'Source'
        try:
            return cldf.get_tabletype(cldf[name])
        except (KeyError, ValueError):
            return None

    @property
    def objid(self):
        if self.is_cldf_link:
            return self.parsed_url.fragment.split(':', maxsplit=1)[-1]

    @property
    def all(self):
        return self.objid == '__all__'


def iter_cldf_image_links(md):
    for match in MarkdownImageLink.pattern.finditer(md):
        ml = MarkdownImageLink.from_match(match)
        if ml.parsed_url.fragment.startswith('cldfviz.map'):
            yield ml


def replace_links(env, md, cldf, prefix, table_map, func_dict=None):
    func_dict = func_dict or {}
    func_dict.update({"pad_ex": pad_ex})
    datadict = {}
    datadict[cldf.bibname] = {src.id: src for src in cldf.sources}
    datadict[cldf.tablegroup._fname.name] = cldf.tablegroup.asdict(omit_defaults=True)
    reverse_table_map = {v: k for k, v in table_map.items()}
    with_partial_local_reflist = False  # Only cited references are to be included.

    def get_tmpl_context(ml, fname):
        if fname not in datadict:
            objs = cldf.objects(table_map[fname]) \
                if table_map[fname] else cldf.iter_rows(fname, 'id')
            datadict[fname] = {r.id if isinstance(r, orm.Object) else r['id']: r for r in objs}
        tmpl_context = {k: True if v[0] == '' else v[0] for k, v in ml.parsed_url_query.items()}
        for k in tmpl_context:
            if k.startswith('with_') and (tmpl_context[k] in ['0', 'false', 'False']):
                tmpl_context[k] = False
        if table_map[fname] == 'Metadata':
            tmpl_context['ctx'] = jmespath.search(ml.objid, datadict[fname])
        else:
            tmpl_context['ctx'] = list(datadict[fname].values()) \
                if ml.all else datadict[fname][ml.objid]
        tmpl_context['cldf'] = cldf
        return tmpl_context

    def repl(ml):
        if ml.is_cldf_link and (prefix is None or (ml.dsid == prefix)):
            if ml.component(cldf) == 'Source' and ml.all and 'cited_only' in ml.parsed_url_query:
                nonlocal with_partial_local_reflist
                with_partial_local_reflist = True
                return ml

            fname = reverse_table_map.get(ml.table_or_fname, ml.table_or_fname)
            type_ = table_map[fname]
            return render_template(
                env, type_ or fname, get_tmpl_context(ml, fname), index=ml.all, func_dict=func_dict)
        return ml

    md = CLDFMarkdownLink.replace(md, repl)

    if with_partial_local_reflist:
        # We need a second pass.
        # 1. Determine which sources have been referenced:
        cited = set(
            MarkdownLink.from_match(ml).url.split('-', maxsplit=1)[-1]
            for ml in MarkdownLink.pattern.finditer(md)
            if MarkdownLink.from_match(ml).url.startswith('#source-'))

        # 2. Insert the pruned list of sources:
        def insert_refs(ml):
            if ml.is_cldf_link:
                if ml.component(cldf) == 'Source' and \
                        ml.all and \
                        'cited_only' in ml.parsed_url_query:
                    ctx = get_tmpl_context(ml, cldf.bibname)
                    ctx['ctx'] = [v for k, v in datadict[cldf.bibname].items() if k in cited]
                    ctx["with_anchor"] = True
                    return render_template(env, 'Source', ctx, index=True, func_dict=func_dict)
            return ml

        md = CLDFMarkdownLink.replace(md, insert_refs)

    return md
