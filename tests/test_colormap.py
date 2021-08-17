import pytest

from cldfviz.colormap import *
from cldfviz.multiparameter import Parameter


@pytest.mark.parametrize(
    's,res',
    [
        ('r', '#FF0000'),
        ('aqua', '#00FFFF'),
        ('a00', '#AA0000'),
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
