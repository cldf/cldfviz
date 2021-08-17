import webbrowser

PACIFIC_CENTERED = 154


class Map:
    __formats__ = []

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

    def add_language(self, language, values, colormaps):  # pragma: no cover
        raise NotImplementedError()

    def add_legend(self, parameters, colormaps):  # pragma: no cover
        raise NotImplementedError()

    def open(self):  # pragma: no cover
        if self.args.format == 'html':
            webbrowser.open(self.args.output.resolve().as_uri())
