import pytest

from cldfviz.colormap import Colormap


@pytest.mark.parametrize(
    'vals,kw,val,expected',
    [
        ((1, 5), {}, 2, '#0080ff'),
        ([1, '4', 5], {'name': 'tol'}, 5, '#CC6677'),
    ]
)
def test_Colormap(vals, kw, val, expected):
    cm = Colormap(vals, **kw)
    assert cm(val) == expected
    assert cm.scalar_mappable()


def test_Colormap2():
    cm = Colormap(dict(a=1, b=2, c=3), name='seq', novalue='x')
    assert cm('b') == '#FEC44F'
    assert cm(None) == 'x'
