# `cdfviz.map`

A common way to visualize data from a CLDF StructureDataset is as "dots on a map",
i.e. as [WALS](https://wals.info)-like geographic maps.

This can be done using the `cldfviz.map` command.
Consulting the help for the `cldfbench cldfviz.map` command displays a somewhat lengthy message. So for better
readability, we'll explain some options here in more detail.

Note that some options are only valid for some output formats.

For example usage of `cldfviz.map`, see the [Examples](#examples) section below.


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
- the path to a clone or download of the [glottolog/glottolog](https://github.com/glottolog/glottolog) repository
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

- `--*-colormaps`
  The default visual style for `cldfviz.map` maps is "dots", i.e. colored circle markers plotted at the
  language's location on the map. Thus, the primary mechanism to influence the appearance is by specifying
  colormaps to control the colors used for corresponding parameter values.

  You don't have to specify any colormaps, but if you do, the number of colormaps specified for
  `--colormaps` (and `--language-properties-colormaps` respectively) must match the number of parameters 
  (and language properties respectively) to be plotted.

  For details about how to specify colormaps, see [colormaps.md](colormaps.md).

- `--markersize`
  The size of the map markers is controled via the `--markersize` option. You might need to experiment a bit
  to figure out a perfect size, since "size in pixels" may translate to quite different optics depending on
  screen size, `--dpi` settings, projections, etc.


### Other general options

There's a handfull of options to control the overall appearance of maps:

- `--title`:  Specify a title for the map plot.
- `--pacific-centered`: Flag to center maps of the whole world at the pacific, thus not cutting large language families 
  in half.
- `--language-labels`: Flag to display language names on the map. Note: This quickly gets crowded.
- `--missing-value`: Specify a color used to indicate missing values. If not specified missing values will be omitted.
- `--no-legend`: Flag to not add a legend to the map. This is mainly of interest for printable maps, e.g. when a
  legend is provided elsewhere in a paper.


### Options for HTML maps

The following options are only relevant for HTML maps:

- `--base-layer`: Specify a [tile layer](https://leafletjs.com/reference.html#tilelayer) to use for the Leaflet maps.
  See [cldfviz.map.leaflet](../src/cldfviz/map/leaflet.py) for available layers.
- `--with-layers`: Add a [Leaflet layer control](https://leafletjs.com/examples/layers-control/) to toggle between
  displaying and hiding markers for individual values of a parameter.
- `--with-layers-for-combinations`: Add a [Leaflet layer control](https://leafletjs.com/examples/layers-control/) to 
  toggle between displaying and hiding markers for individual combinations of values for the plotted parameters. Note:
  While this option allows more fine-grained control over the displayed markers (in comparison with `--with-layers`),
  it may lead to unwieldy legends in case several parameters with multiple values are chosen.


### Options for printable maps

The following options are only relevant for image (aka printable) maps:

- `--padding-left|right|top|bottom`: Specify the padding to be added to maps (around the bounding box of the
  displayed markers) in degrees. 
- `--extent`: Specify the explicit geographic extent of the map as comma-separated list of degrees for 
  (left, right, top, bottom) edge of the map.
- `--width`: Width of the figure in inches.
- `--height`: Height of the figure in inches.
- `--dpi`: Pixel density of the figure. The default of `100` makes for rather small file size and is mostly suitable
  for experimentation. For printable quality you should set it to `300`.
- `--projection`: Map projection. For available projections, see 
  https://scitools.org.uk/cartopy/docs/latest/crs/projections.html
- `--with-stock-img`: Add a map underlay (using cartopy's 
  [`stock_img`](https://scitools.org.uk/cartopy/docs/v0.15/matplotlib/intro.html) method).
- `--zorder`: Specify explit drawing order (i.e. specify what's plotted on top) by giving a JSON dictionary mapping
  parameter values to integers (the higher, the more on top).


## Examples

We'll explain the usage of the command by using it with the [WALS CLDF data](https://github.com/cldf-datasets/wals/releases/tag/v2020.1).
You can download the WALS data - for example - using another `cldfbench` plugin: [cldfzenodo](https://github.com/cldf/cldfzenodo/#cli):
```shell
cldfbench zenodo.download 10.5281/zenodo.4683137 --directory wals-2020.1/
```

### HTML maps

With the [leaflet](https://leafletjs.com) library, we can create interactive maps which can be explored in a browser.

Running
```shell
cldfbench cldfviz.map wals-2020.1/StructureDataset-metadata.json --base-layer Esri_WorldPhysical --pacific-centered
```
will create an HTML page `map.html` and open it in the browser, thus rendering an interactive
map of the languages in the dataset.

![WALS languages](wals_languages.jpg)

For smaller language samples, it may be suitable to display the language names on the map, too.
Here's [WALS' feature 10B](https://wals.info/feature/10B):
```shell
cldfbench cldfviz.map wals-2020.1/StructureDataset-metadata.json --parameters 10B --colormaps tol --markersize 20 --language-labels
```
![WALS 10B](wals_10B.jpg)

`cldfviz.map` can detect and display continuous variables, too. There are no continuous features in WALS, but since
`cldfviz.map` also works with
[metadata-free CLDF datasets](https://github.com/cldf/cldf/blob/master/README.md#metadata-free-conformance), let's
quickly create one. Using the [UNIX shell](https://swcarpentry.github.io/shell-novice/) tools `sed` and `awk` and the
tools of the[csvkit](https://csvkit.readthedocs.io/en/latest/) toolbox, we
can run
```shell
csvgrep -c Latitude,Glottocode -r".+" wals-2020.1/languages.csv | \
csvcut -c ID,Glottocode,Latitude | \
awk '{if(NR==1){print $0",Parameter_ID"}else{print $0",latitude"}}' | \
sed 's/ID,Glottocode,Latitude,Parameter_ID/ID,Language_ID,Value,Parameter_ID/g' > values.csv
```
Let's break this down: The first line selects all WALS languages for which latitude and Glottocode is given.
The next line narrows the resulting CSV to just three columns - the future `ID`, `Language_ID` and `Value`
columns of our metadata-free StructureDataset. The `awk` command adds a constant column `Parameter_ID`,
and the `sed` command renames the columns appropriately.

The resulting CSV looks as follows:
```shell
$ head -n 4 values.csv 
ID,Language_ID,Value,Parameter_ID
aar,aari1239,6,latitude
aba,abau1245,-4,latitude
abb,chad1249,13.8333333333,latitude
```

Mapping metadata-free CLDF data **always** relies on Glottolog data for the geo-coordinates. Thus,
we must clone or download a release of [glottolog/glottolog](https://github.com/glottolog/glottolog).
The latter can be done via
```shell
curl -OL https://github.com/glottolog/glottolog/archive/refs/tags/v4.6.zip
unzip v4.6.zip
```

Now we can run
```shell
cldfbench cldfviz.map values.csv --parameters latitude --glottolog glottolog-4.6/
```
![WALS latitudes](wals_latitude.jpg)

Note that since we looked up coordinates in Glottolog, languages
may be displayed at slightly different locations than above (when the coordinates in WALS differ).

Now we could have done this in a simpler way, too, because `cldfviz.map` has a special option to display language
properties encoded as columns in the `LanguageTable` as if they were parameters of the dataset. We can use this
option to visualize a claim from [WALS' chapter 129](https://wals.info/chapter/129) that there is a

> strong correlation between values [for feature 129] and latitudinal location

```shell
cldfbench cldfviz.map wals-2020.1/cldf/StructureDataset-metadata.json --parameters 129A --colormaps tol \
--markersize 20 --language-properties Latitude --pacific-centered
```
![WALS 129A and latitude](wals_latitude_handandarm.jpg)

As seen above, `cldfviz.map` can visualize multiple parameters at once. E.g. we can explore the related WALS
features 129A, 130A and 130B, selecting suitable colormaps for the two boolean parameters:
```shell
cldfbench cldfviz.map wals-2020.1/cldf/StructureDataset-metadata.json --parameters 129A,130A,130B \
--colormaps base,base,tol --pacific-centered --markersize 30 
```

![WALS 129A, 130A and 130B](wals_129A_130A_130B.jpg)


#### Printable maps via cartopy

If `cldfviz` is installed with `cartopy` similar maps to the ones shown above can also be created
in various image formats:
```shell
cldfbench cldfviz.map wals-2020.1/StructureDataset-metadata.json --parameters 129A --colormaps tol \
--language-properties Latitude --pacific-centered \
--format jpg --width 20 --height 10 --dpi 300 --markersize 40
```
![WALS 129A and latitude](wals_latitude_handandarm_2.jpg)

While these maps lack the interactivity of the HTML maps, they may be better suited for inclusion in print
formats than screen shots of maps in the browser. They also provide some additional options like a choice
between various map projections.


#### Advanced dataset pre-processing

Going one step further, we might visualize data that has been synthesized on the fly. E.g. we
can visualize the AES endangerment information given in the [Glottolog CLDF data](https://github.com/glottolog/glottolog-cldf/releases/tag/v4.4)
for the WALS languages:

Since we will alter the WALS CLDF data, we make a copy of it first:
```shell
cp -r wals-2020.1 wals-copy
```

Now we extract the AES data from Glottolog ...
```shell
csvgrep -c Parameter_ID -m"aes" glottolog-cldf-4.4/cldf/values.csv |\
csvgrep -c Value -m"NA" -i |\
csvcut -c Language_ID,Parameter_ID,Code_ID  > aes1.csv
```

... and massage it into a form that can be appended to the WALS `ValueTable`:
```shell
csvjoin -y 0 -c Glottocode,Language_ID wals-2020.1/cldf/languages.csv aes1.csv |\
csvcut -c Parameter_ID,Code_ID,ID |\
awk '{if(NR==1){print $0",ID"}else{print $0",aes-"NR}}' |\
sed 's/Parameter_ID,Code_ID,ID,ID/Parameter_ID,Value,Language_ID,ID/g' |\
csvcut -c ID,Language_ID,Parameter_ID,Value |\
awk '{if(NR==1){print $0",Code_ID,Comment,Source,Example_ID"}else{print $0",,,,"}}' > aes2.csv
```
Notes:
- The first `awk` call adds a unique value `ID`. We cannot re-use the value `ID` from Glottolog,
  because the mapping between WALS and Glottolog languages is many-to-one.
- Using `awk` to manipulate CSV data is somewhat fragile, since it will break if the data contains
  multi-line cell content. To guard against that, you may compare the row count reported by
  `csvstat` with the line count from `wc -l` before using `awk`.

Now we append the values and a row for the `ParameterTable` ...
```shell
csvstack aes2.csv wals-copy/cldf/values.csv > values.csv
cp values.csv wals-copy/cldf
echo "ID,Name,Description,Chapter_ID" > aes_param.csv
echo "aes,AES,," >> aes_param.csv
csvstack aes_param.csv wals-copy/cldf/parameters.csv > parameters.csv
cp parameters.csv wals-copy/cldf
```

... and make sure the resulting dataset is valid:
```shell
cldf validate wals-copy/cldf/StructureDataset-metadata.json
```

Finally, we can plot the map:
```shell
cldfbench cldfviz.map wals-copy/cldf/StructureDataset-metadata.json --pacific-centered --colormaps seq --parameters aes
```
![WALS AES](wals_aes.jpg)
