import jinja2

import cldfviz

__all__ = ['render_jinja_template', 'TEMPLATE_DIR']

TEMPLATE_DIR = cldfviz.PKG_DIR / 'templates'


def render_jinja_template(path, **vars) -> str:
    loader = jinja2.FileSystemLoader(searchpath=[str(path.parent)])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    return env.get_template(path.name).render(**vars)
