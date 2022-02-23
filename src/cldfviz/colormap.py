import json
import typing
import collections

from matplotlib import cm
from matplotlib.colors import Normalize, to_hex, CSS4_COLORS, BASE_COLORS
import matplotlib.pyplot as plt
from clldutils.color import qualitative_colors, sequential_colors, rgb_as_hex

from cldfviz.multiparameter import CONTINUOUS, CATEGORICAL, Parameter

__all__ = ['COLORMAPS', 'hextriplet', 'Colormap']
COLORMAPS = {
    CATEGORICAL: ['boynton', 'tol', 'base', 'seq'],
    CONTINUOUS: [cm for cm in plt.colormaps() if not cm.endswith('_r')],
}
SHAPES = {
    'triangle_down',
    'triangle_up',
    'square',
    'diamond',
    'circle',
}


def hextriplet(s):
    """
    Wrap clldutils.color.rgb_as_hex to provide unified error handling.
    """
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
        raise ValueError('Invalid color spec: "{}" ({})'.format(s, str(e)))


class Colormap:
    def __init__(self, parameter: Parameter, name: typing.Optional[str] = None, novalue=None):
        domain = parameter.domain
        self.explicit_cm = None
        if name and name.startswith('{'):
            if isinstance(parameter.domain, tuple):
                raise ValueError(
                    'Explicit color maps are only supported for categorical parameters')
            self.explicit_cm = collections.OrderedDict()
            raw = json.loads(name, object_pairs_hook=collections.OrderedDict)
            if novalue:
                raw.setdefault('None', novalue)
            label_to_code = {v: k for k, v in parameter.domain.items()}
            for v, c in raw.items():
                if (v not in parameter.value_to_code) and v not in label_to_code:
                    raise ValueError('Colormap value "{}" not in domain {}'.format(
                        v, list(parameter.value_to_code.keys())))
                v = parameter.value_to_code.get(v, label_to_code.get(v))
                self.explicit_cm[v] = hextriplet(c)
            vals = list(parameter.value_to_code)
            if len(vals) > len(self.explicit_cm):
                raise ValueError('Colormap {} does not cover all values {}!'.format(
                    dict(raw), vals))
            name = None
            # reorder the domain of the parameter (and prune it to valid values):
            parameter.domain = collections.OrderedDict(
                (c, l) for c, l in sorted(
                    [i for i in parameter.domain.items() if i[0] in self.explicit_cm],
                    key=lambda i: list(self.explicit_cm.keys()).index(i[0]))
            )
        self.novalue = hextriplet(novalue) if novalue else None
        self._cm = getattr(cm, name or 'yyy', cm.jet)

        if isinstance(domain, tuple):
            assert not self.explicit_cm
            # Initialize matplotlib colormap and normalizer:
            norm = Normalize(domain[0], domain[1])
            self.cm = lambda v: to_hex(self._cm(norm(float(v))))
        else:
            if self.explicit_cm:
                self.cm = lambda v: self.explicit_cm[v]
            else:
                if name == 'seq':
                    colors = sequential_colors(len(domain))
                else:
                    colors = qualitative_colors(len(domain), set=name)
                self.cm = lambda v: dict(zip(domain, colors))[v]

    @property
    def with_shapes(self):
        return self.explicit_cm and any(c in SHAPES for c in self.explicit_cm.values())

    def scalar_mappable(self):
        return cm.ScalarMappable(norm=None, cmap=self._cm)

    def __call__(self, value):
        if value is None:
            return self.novalue
        return self.cm(value)
