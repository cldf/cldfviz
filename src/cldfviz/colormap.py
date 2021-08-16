import json
import collections

from matplotlib import cm
from matplotlib.colors import Normalize, to_hex
import matplotlib.pyplot as plt
from clldutils.color import qualitative_colors, sequential_colors

from cldfviz.multiparameter import CONTINUOUS, CATEGORICAL

COLORMAPS = {
    CATEGORICAL: ['boynton', 'tol', 'base', 'seq', "lb1", "lb2"],
    CONTINUOUS: [cm for cm in plt.colormaps() if not cm.endswith('_r')],
}


class Colormap:
    def __init__(self, parameter, name=None, novalue=None):
        domain = parameter.domain
        self.explicit_cm = None
        if name and name.startswith('{'):
            self.explicit_cm = collections.OrderedDict(
                (parameter.value_to_code[v], c)
                for v, c in json.loads(name, object_pairs_hook=collections.OrderedDict).items())
            if len(domain) > len(self.explicit_cm):  # pragma: no cover1G
                raise ValueError('Explicit Colormap {} does not cover all categories {}!'.format(
                    self.explicit_cm, list(domain.keys())
                ))
            name = None
            # reorder the domain of the parameter!
            parameter.domain = collections.OrderedDict(
                (v, l) for v, l in sorted(
                    parameter.domain.items(),
                    key=lambda i: list(self.explicit_cm.keys()).index(i[0]))
            )
        self.novalue = novalue
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

    def scalar_mappable(self):
        return cm.ScalarMappable(norm=None, cmap=self._cm)

    def __call__(self, value):
        if value is None:
            return self.novalue
        return self.cm(value)
