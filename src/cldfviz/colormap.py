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

    def __init__(self, domain, name=None, novalue=None):
        self.novalue = novalue
        self._cm = getattr(cm, name or 'yyy', cm.jet)

        if isinstance(domain, tuple):
            # Initialize matplotlib colormap and normalizer:
            norm = Normalize(domain[0], domain[1])
            self.cm = lambda v: to_hex(self._cm(norm(float(v))))
        else:
            if name == 'seq':
                colors = sequential_colors(len(domain))
            elif name == "lb1":
                colors = ["crimson", "white", "lightgray"]
            elif name == "lb2":
                colors = ["cornflowerblue", "white", "lightgray"]
            else:
                colors = qualitative_colors(len(domain), set=name)
            self.cm = lambda v: dict(zip(domain, colors))[v]

    def scalar_mappable(self):
        return cm.ScalarMappable(norm=None, cmap=self._cm)

    def __call__(self, value):
        if value is None:
            return self.novalue
        return self.cm(value)
