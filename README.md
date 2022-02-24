# cldfviz

[![Build Status](https://github.com/cldf/cldfviz/workflows/tests/badge.svg)](https://github.com/cldf/cldfviz/actions?query=workflow%3Atests)
[![PyPI](https://img.shields.io/pypi/v/cldfviz.svg)](https://pypi.org/project/cldfviz)

Python library providing tools to visualize [CLDF](https://cldf.clld.org) datasets.


## Install

Run
```shell
pip install cldfviz
```
If you want create maps in image formats (PNG, JPG, PDF), the `cartopy` package is needed,
which will be installed with
```shell
pip install cldfviz[cartopy]
```
Note: Since `cartopy` has quite a few system-level requirements, installation may be somewhat tricky. Should
problems arise, https://scitools.org.uk/cartopy/docs/v0.15/installing.html may help.


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
The `cldfviz.text` subcommand allows you "render" documents written in "CLDF markdown", i.e. converting
such documents to plain markdown by inserting suitable representations of the referenced data.
For details see [docs/text.md](docs/text.md).
