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