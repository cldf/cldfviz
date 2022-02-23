import pytest

from cldfviz.map import Map


def test_Map():
    with pytest.raises(ValueError):
        Map.get_shape_and_color(['circle', 'diamond'])
    assert Map.get_shape_and_color(['#aaaaaa', 'circle']) == ('circle', '#aaaaaa')