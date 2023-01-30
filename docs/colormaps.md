# Colormaps for `cldfviz.map`

Colormaps are used to specify the appearance of map markers.

Colormaps can be specified in two ways:

1. You can specify a colormap by using its name as value for the option. `cldfviz.map` provides access to
   to the color schemes defined 
   - in [clldutils.color](https://clldutils.readthedocs.io/en/latest/color.html#clldutils.color.qualitative_colors)
     (i.e. `boynton` and `tol`) and
   - in [matplotlib](https://matplotlib.org/stable/tutorials/colors/colormaps.html) for continuous parameter values
2. You can specify a custom colormap for categorical variables by mapping each parameter value to a color.
   Such a mapping can then be passed as literal [JSON object](https://en.wikipedia.org/wiki/JSON#Data_types).
   E.g. to copy the colors of [WALS Online's feature 127A](https://wals.info/feature/127A), you could run
   ```shell
   $ cldfbench cldfviz.map https://raw.githubusercontent.com/cldf-datasets/wals/v2020.3/cldf/StructureDataset-metadata.json \
   --colormaps '{"Balanced":"#00D","Balanced/deranked": "#CCC", "Deranked": "#d00"}' --parameters 127A
   ```


## Shapes

The special use case of visualizing two categorical parameters on a map is often better
served by using color only for one dimension of the data and shapes for the other. (See
for example the approach to contrast descriptive status and endangerment status of languages
taken by [GlottoScope](https://glottolog.org/langdoc/status/browser?macroarea=Eurasia&focus=ed).)

`cldfviz.map` supports this in the following way: Re-using the syntax to specify custom
colormaps you can specify a "shapemap", i.e. rather than mapping parameter values to RGB colors,
you can map them to one of the shapes defined in the [`cldfviz.colormap` module](../src/cldfviz/colormap.py).

So, for example, to plot the languages spoken in Cameroun in Glottoscope-style - comparing descriptive
status with endangerment, we'd run
```shell
$ cldfbench cldfviz.map https://raw.githubusercontent.com/glottolog/glottolog-cldf/v4.7/cldf/cldf-metadata.json \
--language-filters '{"Countries": "CM"}' \
--parameters aes,med \
--colormaps '{"not endangered":"circle","threatened":"square","shifting":"diamond","moribund":"triangle_up","nearly extinct":"triangle_down","extinct":"triangle_down"},tol'
```
