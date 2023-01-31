# `cldfviz.treemap`

Plot values for a parameter of a CLDF dataset on a map linked to a tree.
The core functionality is implemented in Florian Matter's [lingtreemaps](https://pypi.org/project/lingtreemaps/)
package and all its [configuration options](https://lingtreemaps.readthedocs.io/en/latest/config.html) are
available from `cldfviz.treemap` as options prefixed with `--ltm-`.

`cldfviz.treemap` adds the ability to run `lingtreemaps` with data from CLDF datasets, exploiting
additional data from [LanguageTables](https://github.com/cldf/cldf/tree/master/components/languages) to
allow for configurable matching between data and tree.

As an example, we plot values of [WALS feature 88A](https://wals.info/feature/88A) for languages
in a couple of Indo-European genera against the Glottolog classification for [Indo-European](https://glottolog.org/resource/languoid/id/indo1319).

```shell
$ cldfbench cldfviz.treemap wals-2020.3/ 88A --tree indo1319 \
--output tm.svg --open --glottolog-cldf glottolog-cldf-4.7/ \
--language-filters '{"Genus":"Germanic|Romance|Celtic"}' --ltm-text-x-offset 0.5
```

> ![](output/treemap_wals88A.svg)


## Tree specification

The tree can be specified in various ways:

1. Using the `--tree` option which accepts
   - a Glottocode - in which case the Glottolog sub-classification tree for the languoid specified by
     `--tree` is used (see above),
   - a Newick-formatted string,
   - a path name to an existing file containing the Newick-formatted tree.
2. Using the `--tree-dataset` (and `--tree-id`) options to select a tree provided in the `TreeTable`
   of a CLDF dataset.

Since the WALS CLDF data contains the (shallow) trees of its [Genealogical Language List](https://wals.info/languoid/genealogy),
we can plot the same data again as follows:
```shell
$ cldfbench cldfviz.treemap wals-2020.3/ 88A --output tm.svg --open \
--language-filters '{"Genus":"Germanic|Romance|Celtic"}' --ltm-text-x-offset 0.5 \
--tree-dataset wals-2020.3/ --tree-id family-indoeuropean \
--tree-label-property ID
```

> ![](output/treemap_wals88A_2.svg)

Since WALS contains coordinates for all its languages, we do not have to access Glottolog data anymore.


## Matching languages in data and tree

Linking the languages in the parameter's dataset to languages in the tree can be configured via the
`--glottocodes-as-tree-labels` and `--tree-label-property` options. The former will re-name tree
labels to Glottocodes using the mapping given in the `--tree-dataset`'s `LanguageTable`. The latter
specifies a column in the parameter's `LanguageTable` values of which are used to match languages to
tree node labels.

In the second examples above, we used WALS family trees, which use the 'ID' values of the
`LanguageTable` as node labels. Thus, we had to specify `--tree-label-property ID` to make sure 
datapoints can be matched with nodes in the tree.
