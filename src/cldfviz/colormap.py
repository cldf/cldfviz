import json
import itertools
import collections
from typing import Union, Optional, Callable

from matplotlib import cm
from matplotlib.colors import Normalize, to_hex, CSS4_COLORS, BASE_COLORS
import matplotlib.pyplot as plt
from clldutils.color import qualitative_colors, sequential_colors, rgb_as_hex

from cldfviz.multiparameter import ParameterType, Parameter

__all__ = [
    'WeightedColorsType',
    'COLORMAPS', 'hextriplet', 'Colormap', 'get_shape_and_color', 'weighted_colors']

ValueType = Union[str, None]
ColorType = Union[tuple[str, str], str]
CategoricalColormapType = collections.OrderedDict[ValueType, ColorType]
ColormapType = Callable[[ValueType], ColorType]
WeightedColorsType = list[tuple[float, ColorType]]
COLORMAPS = {
    ParameterType.CATEGORICAL: ['boynton', 'tol', 'base', 'seq'],
    ParameterType.CONTINUOUS: [cm for cm in plt.colormaps() if not cm.endswith('_r')],
}
SHAPES = {
    'triangle_down',
    'triangle_up',
    'square',
    'diamond',
    'circle',
}
SVG_SHAPE_MAP = {
    'triangle_down': 'f',
    'triangle_up': 't',
    'square': 's',
    'diamond': 'd',
    'circle': 'c',
}


def hextriplet(s: Union[str, tuple[str, str], list[str]]) -> ColorType:
    """
    Wrap clldutils.color.rgb_as_hex to provide unified error handling.
    """
    if isinstance(s, (list, tuple)) and s[0] in SHAPES:
        return s[0], hextriplet(s[1])
    if s in SHAPES:
        # A bit of a hack: We allow a handful of shape names as "color" spec as well.
        return s
    if s in BASE_COLORS:
        return rgb_as_hex([float(d) for d in BASE_COLORS[s]])
    if s in CSS4_COLORS:
        return CSS4_COLORS[s]
    try:
        return rgb_as_hex(s)
    except (AssertionError, ValueError) as e:
        raise ValueError(f'Invalid color spec: "{s}" ({str(e)})')


def _get_explicit_cm(
        name: Optional[str],
        parameter: Parameter,
        novalue: Optional[str],
) -> Union[None, CategoricalColormapType]:
    if (not name) or (not name.startswith('{')):
        return None
    if isinstance(parameter.domain, tuple):
        raise ValueError('Explicit color maps are only supported for categorical parameters')
    res = collections.OrderedDict()
    raw = json.loads(name, object_pairs_hook=collections.OrderedDict)
    if novalue:
        raw.setdefault('None', novalue)
    label_to_code = {v: k for k, v in parameter.domain.items()}
    for v, c in raw.items():
        if v in parameter.value_to_code:
            v = parameter.value_to_code[v]
        elif v in parameter.value_to_code.values():
            pass  # pragma: no cover
        elif v in label_to_code:
            v = label_to_code[v]  # pragma: no cover
        else:
            raise ValueError(
                f'Colormap value "{v}" not in domain '
                f'{sorted(set(parameter.value_to_code.values()))}')
        res[v] = hextriplet(c)
    vals = set(parameter.value_to_code.values())
    if len(vals) > len(res):
        raise ValueError(f'Colormap {dict(raw)} does not cover all values {vals}!')

    # reorder the domain of the parameter (and prune it to valid values):
    parameter.domain = collections.OrderedDict(
        (c, l) for c, l in sorted(
            [i for i in parameter.domain.items() if i[0] in res],
            key=lambda i: list(res.keys()).index(i[0]))
    )
    return res


class Colormap:
    def __init__(self, parameter: Parameter, name: Optional[str] = None, novalue=None):
        domain = parameter.domain
        self.explicit_cm: Optional[CategoricalColormapType] = _get_explicit_cm(
            name, parameter, novalue)
        if self.explicit_cm:
            name = None

        self.novalue: Optional[ColorType] = hextriplet(novalue) if novalue else None
        self._cm = getattr(cm, name or 'yyy', cm.jet)

        if isinstance(domain, tuple):
            assert not self.explicit_cm
            # Initialize matplotlib colormap and normalizer:
            norm = Normalize(domain[0], domain[1])
            self.cm: ColormapType = lambda v: to_hex(self._cm(norm(float(v))))
        else:
            if self.explicit_cm:
                self.cm: ColormapType = lambda v: self.explicit_cm[v]
            else:
                if name == 'seq':
                    colors = sequential_colors(len(domain))
                else:
                    colors = qualitative_colors(len(domain), set=name)
                self.cm: ColormapType = lambda v: dict(zip(domain, colors))[v]

    @property
    def with_shapes(self) -> bool:
        return bool(self.explicit_cm) and any(
            c in SHAPES if isinstance(c, str) else c[0] in SHAPES for c in self.explicit_cm.values()
        )

    def scalar_mappable(self):
        return cm.ScalarMappable(norm=None, cmap=self._cm)

    def __call__(self, value: ValueType) -> ColorType:
        if value is None:
            return self.novalue
        return self.cm(value)


def get_shape_and_color(colors_or_shapes):
    if 1 <= len(colors_or_shapes) <= 2:
        shapes, colors = [], []
        for _, c in colors_or_shapes:
            if isinstance(c, (tuple, list)):
                shapes.append(c[0])
                colors.append(c[1])
            else:
                (shapes if c in SHAPES else colors).append(c)
        if shapes:
            if len(shapes) > 1:
                raise ValueError('Only one shape can be specified for a marker')
            return shapes[0], colors[0] if colors else '#000000'


def weighted_colors(values, colormaps) -> WeightedColorsType:
    colors = []
    for pid, vals in values.items():
        cm = colormaps[pid]
        total = sum(1 if vv.weight is None else vv.weight for vv in vals)
        for code, vvs in itertools.groupby(sorted(vals, key=lambda vv: vv.v), lambda vv: vv.v):
            colors.append((
                sum(1 if vv.weight is None else vv.weight for vv in vvs) / total / len(values),
                cm(code)))
    return colors
