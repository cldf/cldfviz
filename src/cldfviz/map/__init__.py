from . import leaflet  # noqa: F401
try:
    from . import mpl  # noqa: F401
    WITH_CARTOPY = True
except ImportError:  # pragma: no cover
    WITH_CARTOPY = False
from .base import Map  # noqa: F401
