"""
Base class for format-specific language map implementations.
"""
import argparse
import webbrowser
from collections.abc import Iterable

from cldfviz.multiparameter import Language, ValueDictType, ParameterDictType
from cldfviz.colormap import ColormapDictType

# For pacific-centered maps we chose 154°E as central longitude. This is particularly suitable,
# because the cut at 26°W does not cut through any macroareas.
# see https://en.wikipedia.org/wiki/154th_meridian_east and
# https://en.wikipedia.org/wiki/26th_meridian_west
PACIFIC_CENTERED = 154


class Map:
    """A map object allowing to add languages to it."""
    __formats__ = []
    __marker_class__ = None

    def __init__(self, languages: Iterable[Language], args: argparse.Namespace):
        self.languages: Iterable[Language] = languages
        self.args: argparse.Namespace = args

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        """write files"""
        raise NotImplementedError()

    @staticmethod
    def add_options(parser: argparse.ArgumentParser, help_suffix: str):  # pragma: no cover
        """Add subclass-specific rendering option."""

    def api_add_language(
            self,
            language: Language,
            values: ValueDictType,
            colormaps: ColormapDictType,
    ):  # pragma: no cover
        """API to add a language."""
        marker_spec = None
        if self.args.marker_factory:
            marker_spec = self.args.marker_factory(self, language, values, colormaps)
            if marker_spec is True:
                # All done!
                return
            if self.__marker_class__ is not None:
                assert isinstance(marker_spec, self.__marker_class__)
        self.add_language(language, values, colormaps, spec=marker_spec)

    def add_language(
            self,
            language: Language,
            values: ValueDictType,
            colormaps: ColormapDictType,
            spec=None):  # pragma: no cover
        """Implementation to add a language."""
        raise NotImplementedError()

    def api_add_legend(self, parameters: ParameterDictType, colormaps: ColormapDictType):
        """API to add a legend."""
        if self.args.marker_factory:
            return self.args.marker_factory.legend(self, parameters, colormaps)
        self.add_legend(parameters, colormaps)
        return None

    def add_legend(
            self, parameters: ParameterDictType, colormaps: ColormapDictType):  # pragma: no cover
        """Implementation of adding a legend."""
        raise NotImplementedError()

    def open(self):  # pragma: no cover
        """Maybe open the rendered map in the browser."""
        if self.args.format == 'html':
            webbrowser.open(self.args.output.resolve().as_uri(), new=1)
