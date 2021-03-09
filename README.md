# cldfviz

Python library providing tools to visualize [CLDF](https://cldf.clld.org) datasets.

## Install

Run
```shell
pip install cldfviz
```

## CLI

`cldfviz` is implemented as [`cldfbench`](https://github.com/cldf/cldfbench)
plugin, i.e. it provides subcommands for the `cldfbench` command.

After installation you should see subcommands with a `cldfviz.` prefix
listed when running
```shell
cldfbench -h
```


### `cldfviz.htmlmap`

A common way to visualize data from a CLDF StructureDataset is as "dots on a map",
i.e. as [WALS](https://wals.info)-like geographic maps.

This can be done using the `cldfviz.htmlmap` command. Since geo-coordinates
for languages are looked up in Glottolog, this command needs 
- access to a local clone of the [glottolog/glottolog](https://github.com/glottolog/glottolog)
repository,
- Glottocodes for all languages in the set, either given as [`languageReference`](https://cldf.clld.org/v1.0/terms.rdf#languageReference)
  in the `ValueTable` or as [`glottocode`](https://cldf.clld.org/v1.0/terms.rdf#glottocode) in `LanguageTable`.
  
Then, running
```shell
cldfbench cldfviz.htmlmap --glottolog PATH/TO/glottolog
```
will create an HTML page `index.html`, and appropriate Javascript data,
and open it in the browser, thus rendering an interactive [leaflet](https://leafletjs.com/)
map of the data.

#### Example

`cldfviz.htmlmap` can be used in combination with tools from [`csvkit`](https://csvkit.readthedocs.io/en/latest/index.html)
to map customized selections of data from an existing CLDF dataset. E.g. we
can map single WALS features based on the CLDF data at https://github.com/cldf-datasets/wals
as follows.

1. Extract a [metadata-free CLDF StructureDataset](https://github.com/cldf/cldf#metadata-free-conformance)
   from the full WALS dataset via csvkit tools, using Glottocodes as `Language_ID`:
   ```shell
   # First, we filter values for just the feature 24A:
   csvgrep -c Parameter_ID -r "^24A" ../wals/wals/cldf/values.csv | \
   # Replace the numeric values with code names, ...
   csvjoin -c Code_ID,ID - ../wals/wals/cldf/codes.csv | \
   # ... narrow down to only the required columns ...
   csvcut -c ID,Language_ID,Parameter_ID,Name | \
   # ... and make sure the columns have the correct names.
   sed 's/ID,Language_ID,Parameter_ID,Name/ID,Language_ID,Parameter_ID,Value/g' | \
   # Then, replace language IDs with Glottocodes, ...
   csvjoin -q'"' -c Language_ID,ID - ../wals/wals/cldf/languages.csv | \
   # ... narrow down to only the required columns, ...
   csvcut -c ID,Glottocode,Parameter_ID,Value | \
   # ... skip rows with no Glottocode ...
   csvgrep -c Glottocode -r ".+" | \
   # ... and make sure the columns have the correct names.
   sed 's/ID,Glottocode,Parameter_ID,Value/ID,Language_ID,Parameter_ID,Value/g'
   ```
2. Run
   ```shell
   cldfbench cldfviz.htmlmap --glottolog PATH/TO/glottolog values.csv
   ```
