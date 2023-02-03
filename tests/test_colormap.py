import itertools

import pytest

from cldfviz.multiparameter import Parameter, Value
from cldfviz.colormap import *


@pytest.mark.parametrize(
    's,res',
    [
        ('r', '#FF0000'),
        ('aqua', '#00FFFF'),
        ('a00', '#AA0000'),
        ('diamond', 'diamond'),
    ]
)
def test_hextriplet(s, res):
    assert hextriplet(s) == res


@pytest.mark.parametrize(
    'vals,kw,val,expected',
    [
        ((1, 5), {}, 2, '#0080ff'),
        ([1, '4', 5], {'name': 'tol'}, 5, '#CC6677'),
    ]
)
def test_Colormap(vals, kw, val, expected):
    cm = Colormap(Parameter(id='x', name='y', domain=vals), **kw)
    assert cm(val) == expected
    assert cm.scalar_mappable()


def test_Colormap2():
    with pytest.raises(ValueError):
        _ = Colormap(Parameter(id='x', name='y', domain=dict(a=1)), name='seq', novalue='x')

    param = Parameter(
        id='x',
        name='y',
        domain=dict(a=1, b=2, c=3),
        value_to_code={'a': 'a', 'b': 'b', 'c': 'c', 'None': None},
    )
    with pytest.raises(ValueError):
        _ = Colormap(param, name='{"a":"0a0"}', novalue='a00')

    cm = Colormap(param, name='{"a":"0a0","b":"fec44f","c":"blue"}', novalue='a00')
    assert cm('b') == '#FEC44F'
    assert cm(None) == '#AA0000'
    cm = Colormap(param, name='seq')
    assert cm('b') == '#FEC44F'


def test_get_shape_and_color():
    with pytest.raises(ValueError):
        get_shape_and_color([(1, 'circle'), (1, 'diamond')])
    assert get_shape_and_color([(1, '#aaaaaa'), (1, 'circle')]) == ('circle', '#aaaaaa')


def _make_value(v, pid, weight=None):
    return Value(v=v, pid=pid, lid='l', code=v, weight=weight)


@pytest.mark.parametrize(
    'values,count',
    [
        ([_make_value('x', 'a')], 1),
        ([_make_value('x', 'a'), _make_value('x', 'a')], 1),
        ([_make_value('x', 'a'), _make_value('y', 'a')], 2),
        ([_make_value('x', 'a'), _make_value('y', 'b'), _make_value('x', 'b', 3)], 3),
        ([_make_value('x', 'a', 20), _make_value('y', 'a', 2)], 2),
        ([_make_value('x', 'a'), _make_value('x', 'b')], 2),
    ]
)
def test_weighted_colors(values, count):
    class Colormap(dict):
        def __call__(self, v):
            return self[v]

    values = {
        pid: list(vals) for pid, vals in
        itertools.groupby(sorted(values, key=lambda v: v.pid), lambda v: v.pid)}
    colormaps = dict(a=Colormap(x='x', y='y'), b=Colormap(x='x', y='y', z='z'))
    res = weighted_colors(values, colormaps)
    assert len(res) == count
    assert sum(c[0] for c in res) == pytest.approx(1.0)
