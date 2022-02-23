# Colormaps for `cldfviz.map`

Colormaps are use to specify the appearance of map markers.


## Shapes

The special use case of visualizing two categorical parameters on a map is often better
served by using color only for one dimension of the data and shapes for the other. (See
for example the approach to contrast descriptive status and endangerment status of languages
taken by [GlottoScope](https://glottolog.org/langdoc/status/browser?macroarea=Eurasia&focus=ed).)

`cldfviz.map` supports this in the following way: Re-using the syntax to specify custom
colormaps you can specify a "shapemap", i.e. rather than mapping parameter values to RGB colors,
you can map them to one of the shapes defined in the [`cldfviz.colormap` module](../src/cldfviz/colormap.py).
