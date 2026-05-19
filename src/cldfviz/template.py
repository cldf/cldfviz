"""
Functionality to render jinja2 templates.
"""
import pathlib

import jinja2

import cldfviz

__all__ = ['render_jinja_template', 'TEMPLATE_DIR']

TEMPLATE_DIR: pathlib.Path = cldfviz.PKG_DIR / 'templates'


def render_jinja_template(path: pathlib.Path, **vars_) -> str:
    """Render a jinja2 template."""
    loader = jinja2.FileSystemLoader(searchpath=[str(path.parent)])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    return env.get_template(path.name).render(**vars_)
