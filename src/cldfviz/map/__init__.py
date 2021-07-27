from . import leaflet
try:
    from . import mpl
    WITH_CARTOPY = True
except ImportError:
    WITH_CARTOPY = False
from .base import Map
