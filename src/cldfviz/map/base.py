import webbrowser

from cldfviz.colormap import SHAPES

# For pacific-centered maps we chose 154°E as central longitude. This is particularly suitable,
# because the cut at 26°W does not cut through any macroareas.
# see https://en.wikipedia.org/wiki/154th_meridian_east and
# https://en.wikipedia.org/wiki/26th_meridian_west
PACIFIC_CENTERED = 154


class Map:
    __formats__ = []
    __marker_class__ = None

    def __init__(self, languages, args):
        self.languages = languages
        self.args = args

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # pragma: no cover
        """write files"""
        raise NotImplementedError()

    @staticmethod
    def get_shape_and_color(colors_or_shapes):
        if len(colors_or_shapes) == 2:
            shapes, colors = [], []
            for c in colors_or_shapes:
                (shapes if c in SHAPES else colors).append(c)
            if shapes:
                if len(shapes) > 1:
                    raise ValueError('Only one shape can be specified for a marker')
                return shapes[0], colors[0]

    @staticmethod
    def add_options(parser, help_suffix):  # pragma: no cover
        pass

    def api_add_language(self, language, values, colormaps):  # pragma: no cover
        marker_spec = None
        if self.args.marker_factory:
            marker_spec = self.args.marker_factory(self, language, values, colormaps)
            if marker_spec is True:
                # All done!
                return
            assert isinstance(marker_spec, self.__marker_class__)
        self.add_language(language, values, colormaps, spec=marker_spec)

    def add_language(self, language, values, colormaps, spec=None):  # pragma: no cover
        raise NotImplementedError()

    def api_add_legend(self, parameters, colormaps):
        if self.args.marker_factory:
            return self.args.marker_factory.legend(self, parameters, colormaps)
        self.add_legend(parameters, colormaps)

    def add_legend(self, parameters, colormaps):  # pragma: no cover
        raise NotImplementedError()

    def open(self):  # pragma: no cover
        if self.args.format == 'html':
            webbrowser.open(self.args.output.resolve().as_uri(), new=1)
