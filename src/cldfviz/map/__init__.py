import argparse

import pycldf

from . import leaflet  # noqa: F401
try:
    from . import mpl  # noqa: F401
    WITH_CARTOPY = True
except ImportError:  # pragma: no cover
    WITH_CARTOPY = False
    mpl = None
from .base import Map  # noqa: F401


class MarkerFactory:
    """
    If the capabilities of standard `Map` implementations are not sufficient, custom plotting
    code can be provided as subclass of `MarkerFactory`.

    Note:
    It's the responsibility of the `MarkerFactory` to figure out what map format is requested.
    This can be done by inspecting `self.args.format`, or checking the type of `map` using
    `isinstance` in the drawing methods.
    """
    def __init__(self, dataset: pycldf.Dataset, args: argparse.Namespace, *cfg):
        """
        Called when the CLDF data is available.

        :param dataset: The CLDF data.
        :param args: The cli arguments.
        :param cfg: Whatever has been passed to `--marker-factory` in addition to the module \
        providing the `MarkerFactory` (split by comma).
        """
        self.dataset = dataset
        self.args = args
        self.cfg = cfg

    def __call__(self, map: Map, language, values, colormaps):
        """
        Called for each language on the map. An implementation must return either
        - `True`: to signal that all plotting has been done (e.g. by plotting directly to `map.ax` \
          in the case of matplotlib) or
        - an instance of `map.__marker_class__`, providing a marker specification to `map`.

        :param map:
        :param language:
        :param values:
        :param colormaps:
        :return:
        """
        if self.args.format == 'html':
            return leaflet.LeafletMarkerSpec()
        return mpl.MPLMarkerSpec()

    def legend(self, map, parameters, colormaps):
        """
        :param map:
        :param parameters:
        :param colormaps:
        :return:
        """
        return


class _TestFactory(MarkerFactory):  # Only used for testing import from module.
    pass
