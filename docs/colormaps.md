# Colormaps for `cldfviz.map`

Colormaps are used to specify the appearance of map markers.

Colormaps can be specified in two ways:

1. You can specify a colormap by using its name as value for the option. `cldfviz.map` provides access to
   to the color schemes defined 
   - in [clldutils.color](https://clldutils.readthedocs.io/en/latest/color.html)
     for categorical (or sequential or diverging parameter values) and
   - in [matplotlib](https://matplotlib.org/stable/tutorials/colors/colormaps.html) for continuous parameter values
2. You can specify a custom colormap for categorical variables by mapping each parameter value to a color.
   Such a mapping can then be passed as literal [JSON object](https://en.wikipedia.org/wiki/JSON#Data_types).


## Shapes

The special use case of visualizing two categorical parameters on a map is often better
served by using color only for one dimension of the data and shapes for the other. (See
for example the approach to contrast descriptive status and endangerment status of languages
taken by [GlottoScope](https://glottolog.org/langdoc/status/browser?macroarea=Eurasia&focus=ed).)

`cldfviz.map` supports this in the following way: Re-using the syntax to specify custom
colormaps you can specify a "shapemap", i.e. rather than mapping parameter values to RGB colors,
you can map them to one of the shapes defined in the [`cldfviz.colormap` module](../src/cldfviz/colormap.py).
