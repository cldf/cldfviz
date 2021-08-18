from . import leaflet  # noqa: F401
try:
    from . import mpl  # noqa: F401
    WITH_CARTOPY = True
except ImportError:  # pragma: no cover
    WITH_CARTOPY = False
    mpl = None
from .base import Map  # noqa: F401


class MarkerFactory:
    def __init__(self, dataset, args, *cfg):
        self.dataset = dataset
        self.args = args
        self.cfg = cfg

    def __call__(self, map, language, values, colormaps):
        if self.args.format == 'html':
            return leaflet.LeafletMarkerSpec()
        return mpl.MPLMarkerSpec()


class _TestFactory(MarkerFactory):  # Only used for testing import from module.
    pass
