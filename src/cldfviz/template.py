import jinja2

import cldfviz

__all__ = ['render_jinja_template', 'TEMPLATE_DIR']

TEMPLATE_DIR = cldfviz.PKG_DIR / 'templates'


def render_jinja_template(fname, pkg=None, **vars) -> str:
    pkg = pkg or fname.partition('.')[0]
    loader = jinja2.FileSystemLoader(searchpath=[str(TEMPLATE_DIR / pkg)])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    return env.get_template(fname).render(**vars)
