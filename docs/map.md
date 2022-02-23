# `cdfviz.map`

The `cldfviz.map` subcommand for `cldfbench` allows you to create geographic maps displaying data from CLDF
`StructureDataset`s - i.e. maps as used in typological Atlases such as [WALS](https://wals.info).

Consulting the help for the `cldfbench cldfviz.map` command displays a somewhat lengthy message. So for better
readability, we'll explain some options here in more detail.

Note that some options are only valid for some output formats.


## Output

With `cldfviz.map` you can create
- interactive HTML maps, using the [Leaflet](https://leafletjs.com/) library
- printable maps in one of the image formats [PNG](https://en.wikipedia.org/wiki/Portable_Network_Graphics), 
  [JPG](https://en.wikipedia.org/wiki/JPEG) or [PDF](https://en.wikipedia.org/wiki/PDF), using the
  [cartopy](https://pypi.org/project/Cartopy/) library.

Since installation of cartopy is somewhat complex, it isn't installed with `cldfviz` by default, but has to
be explicitly specified as extra, running
```shell
pip install cldfviz[cartopy]
```

Choosing between output formats is done with the `--format` option, which accepts the string `html`, `png`, `jpg`
and `pdf`.

`cldfviz` tries to create similar looking maps for both output types so that you can explore your dataset using
HTML maps, and then create corresponding maps for a publication by just swapping the `--format` option.
In reality, though, you'll have to do some fiddling with the `--markersize`, `--width`, `--height`, `--dpi` and
`--padding-*` options to create satisfactory results for printable maps.

You can specify a filename for the map created by `cldfviz.map` via the `--output` option. By default, the
resulting map will be written to `map.<format>`. For all formats the resulting map will be contained in a single
file. In the case of HTML maps, the map will need to be rendered in a browser with access to the internet, to
load Javascript libraries and map tiles.


## Geo data from Glottolog

Since CLDF datasets can reference languoids in the [Glottolog catalog](https://glottolog.org) transparently,
it is possible to supplement a dataset with geo data from Glottolog to locate its languages on a map.

To do so,
- the dataset must have a column specified as [glottocode](https://cldf.clld.org/v1.0/terms.rdf#glottocode) in
  its `LanguageTable` (or Glottocodes as values of the `Language_ID` column for [metadata-free datasets](https://github.com/cldf/cldf#metadata-free-conformance))
- the path to a clone or export of the [glottolog/glottolog](https://github.com/glottolog/glottolog) repository
  must be specified for the `--glottolog` option
- optionally - if the repository has been cloned - a particular version of Glottolog can be specified using the
  `--glottolog-version` option. (See the [`cldfbench` docs](https://github.com/cldf/cldfbench/#catalogs) for details 
  on reference catalog maintenance.)


## What to map

By default - i.e. without specifying anything - `cldfviz.map` will plot all languages in a dataset (for which
geo coordinates can be determined) as dots on a map.

But you can also plot values of these languages for a selection of parameters in the dataset. To do so, specify
a comma-separated list of parameter IDs for the `--parameters` option.

In addition, you can map other language properties give in the dataset's `LanguageTable` by specifying a comma-separated
list of column names from the `LanguageTable` for the `--language-properties` option.


## Configuring marker appearance

### `--*-colormaps`

The default visual style for `cldfviz.map` maps is "dots", i.e. colored circle markers plotted at the
language's location on the map. Thus, the primary mechanism to influence the appearance is by specifying
colormaps to control the colors used for corresponding parameter values.

You don't have to specify any colormaps, but if you do, the number of colormaps specified for
`--colormaps` (and `--language-properties-colormaps` respectively) must match the number of parameters 
(and language properties respectively) to be plotted.

For details about how to specify colormaps, see [colormaps.md](colormaps.md).


### `--markersize`

The size of the mao markers is controled via the `--markersize` option. You might need to experiment a bit
to figure out a perfect size, since "size in pixels" may translate to quite different optics depending on
screen size, `--dpi` settings, projections, etc.


### Other general options

  --title TITLE         Title for the map plot (default: None)
  --pacific-centered    Center maps of the whole world at the pacific, thus
                        not cutting large language families in half. (default:
                        False)
  --language-labels     Display language names on the map (default: False)
  --missing-value MISSING_VALUE
                        A color used to indicate missing values. If not
                        specified missing values will be omitted. (default:
                        None)
  --no-legend           Don't add a legend to the map (e.g. because it would
                        be too big). (default: False)


### Options for HTML maps

  --base-layer {OpenStreetMap,OpenTopoMap,Esri_WorldImagery,Esri_WorldPhysical,Esri_NatGeoWorldMap}
                        Tile layer for Leaflet maps. (Only for FORMATs "html")
                        (default: OpenStreetMap)
  --with-layers         Create clickable Leaflet layers for each parameter
                        value (default: False)
  --with-layers-for-combinations
                        Create clickable Leaflet layers for each combination
                        of parameter values (default: False)


### Options for printable maps

  --padding-left PADDING_LEFT
                        Left padding of the map in degrees. (Only for FORMATs
                        "jpg", "png", "pdf") (default: 1)
  --padding-right PADDING_RIGHT
                        Right padding of the map in degrees. (Only for FORMATs
                        "jpg", "png", "pdf") (default: 1)
  --padding-top PADDING_TOP
                        Top padding of the map in degrees. (Only for FORMATs
                        "jpg", "png", "pdf") (default: 1)
  --padding-bottom PADDING_BOTTOM
                        Bottom padding of the map in degrees. (Only for
                        FORMATs "jpg", "png", "pdf") (default: 1)
  --extent EXTENT       Set extent of the figure in terms of coordinates
                        (left, right, top, bottom) (default: None)
  --width WIDTH         Width of the figure in inches. (Only for FORMATs
                        "jpg", "png", "pdf") (default: 6.4)
  --height HEIGHT       Height of the figure in inches. (Only for FORMATs
                        "jpg", "png", "pdf") (default: 4.8)
  --dpi DPI             Pixel density of the figure. (Only for FORMATs "jpg",
                        "png", "pdf") (default: 100.0)
  --projection {PlateCarree,RotatedPole,LambertCylindrical,Miller,TransverseMercator,OSGB,OSNI,UTM,EuroPP,Mercator,LambertConformal,LambertAzimuthalEqualArea,Gnomonic,Stereographic,NorthPolarStereo,SouthPolarStereo,Orthographic,EckertI,EckertII,EckertIII,EckertIV,EckertV,EckertVI,EqualEarth,Mollweide,Robinson,InterruptedGoodeHomolosine,Geostationary,NearsidePerspective,AlbersEqualArea,AzimuthalEquidistant,Sinusoidal,EquidistantConic}
                        Map projection. For details, see https://scitools.org.
                        uk/cartopy/docs/latest/crs/projections.html (Only for
                        FORMATs "jpg", "png", "pdf") (default: PlateCarree)
  --with-stock-img      Add a map underlay (using cartopy's `stock_img`
                        method). (Only for FORMATs "jpg", "png", "pdf")
                        (default: False)
  --zorder ZORDER       Determine zorder of individual markers by color.
                        (default: {})
