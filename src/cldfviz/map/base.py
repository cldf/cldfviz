import webbrowser

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
            webbrowser.open(self.args.output.resolve().as_uri())
