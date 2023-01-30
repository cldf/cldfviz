# cldfviz

[![Build Status](https://github.com/cldf/cldfviz/workflows/tests/badge.svg)](https://github.com/cldf/cldfviz/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/cldfviz.svg)](https://pypi.org/project/cldfviz)

Python library providing tools to visualize [CLDF](https://cldf.clld.org) datasets.


## Install

Run
```shell
pip install cldfviz
```
If you want to create maps in image formats (PNG, JPG, PDF), the `cartopy` package is needed,
which will be installed with
```shell
pip install cldfviz[cartopy]
```
Note: Since `cartopy` has quite a few system-level requirements, installation may be somewhat tricky. Should
problems arise, https://scitools.org.uk/cartopy/docs/v0.15/installing.html may help.

If you want to create "treemaps" (i.e. use the [lingreemaps](https://lingtreemaps.readthedocs.io/en/latest/?badge=latest)
package for CLDF data), you need to install via
```shell
pip install cldfviz[lingtreemaps]
```


## CLI

`cldfviz` is implemented as [`cldfbench`](https://github.com/cldf/cldfbench)
plugin, i.e. it provides subcommands for the `cldfbench` command.

After installation you should see subcommands with a `cldfviz.` prefix
listed when running
```shell
cldfbench -h
```


### `cldfviz.map`

A common way to visualize data from a CLDF StructureDataset is as "dots on a map",
i.e. as [WALS](https://wals.info)-like geographic maps, displaying typological variation.
The `cldfviz.map` subcommand allows you to create such maps. For details see [docs/map.md](docs/map.md).


### `cldfviz.text`

A rather traditional visualization of linguistic data is the practice of interspersing bits of data
in descriptive texts, most obviously perhaps as examples formatted as **I**nterlinear **G**lossed **T**ext.
The `cldfviz.text` subcommand allows you "render" documents written in [CLDF markdown](https://github.com/cldf/cldf/blob/master/extensions/markdown.md), i.e. converting
such documents to plain markdown by inserting suitable representations of the referenced data.
For details see [docs/text.md](docs/text.md).


### `cldfviz.examples`

While it is possible to (selectively) include IGT formatted examples in [CLDF Markdwown](https://github.com/cldf/cldf/blob/master/extensions/markdown.md) via `cldfviz.text`,
often it is useful to just look at an HTML formatted list of all examples from a dataset. This can
be done via `cldfviz.examples`. For details see [docs/text.md](docs/examples.md).


### `cldfviz.tree`

Phylogenetic (or classification) trees of languages are a "proper" [CLDF component](https://github.com/cldf/cldf/tree/master/components/trees)
since CLDF 1.2 - and an obvious candidate for visualization (because noone likes to look at [Newick](https://en.wikipedia.org/wiki/Newick_format)).

To provide a configurable visualization of trees in [SVG format](https://en.wikipedia.org/wiki/SVG), the
`cldfviz.tree` command renders CLDF trees using the powerful [toytree](https://toytree.readthedocs.io/en/latest/)
package. For details see [docs/text.md](docs/tree.md).


### `cldfviz.treemap`


### `cldfviz.audiowordlist`


### `cldfviz.erd`

CLDF datasets typically contain multiple, related tables. The most common visualization of such a data model
are "entity-relationship diagrams", i.e. diagramy of the [entitty-relationship model](https://en.wikipedia.org/wiki/Entity%E2%80%93relationship_model)
of the dataset. Such a diagram can be created via `cldfviz.erd` (if a Java runtime is installed).
For details see [docs/text.md](docs/erd.md).
