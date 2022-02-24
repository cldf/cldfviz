# `cldfviz.text`

A rather traditional visualization of linguistic data is the practice of interspersing bits of data
in descriptive texts, most obviously perhaps as examples formatted as **I**nterlinear **G**lossed **T**ext.
Other examples of data in text include forms, either in running text or in a table, or just references.

To support this use case, the `cldfviz.text` command can fill data from a CLDF dataset into a markdown
document, where references to CLDF data objects (rows of tables or complete tables) are marked using the
markdown link format with a special URL syntax. To reference a single row:

```
[An arbitrary label](some/path/<component-name-or-csv-filename>#cldf:<obect-id>)
```

To reference a whole table:
```
[An arbitrary label](some/path/<component-name-or-csv-filename>#cldf:__all__)
```

Note: Only the last component of the URL path is used to determine a CLDF component or table of the dataset, while
the first part is ignored. This allows using URLs that are even somewhat functional in the unrendered
document. E.g.
```
[Meier 2020](cldf/sources.bib#cldf:Meier2020)
```
will render as `Meier 2020`, linking to the BibTeX file when the document is simply rendered as markdown by
a service like GitHub, while the enhanced document created from `cldfviz.text` will replace the link with
the reference data expanded to a full citation according to the Unified Stylesheet for Linguistics.

Rendering of data objects is controled with [templates](../src/cldfviz/templates/text) using the
[Jinja](https://jinja.palletsprojects.com/) template language. Sometimes, templates can be parametrized,
e.g. to choose only cognates belonging to the same cognate set from a `CognateTable`. These parameters can
be specified as [query string](https://en.wikipedia.org/wiki/Query_string) of the reference URL, e.g.
```
[cognateset X](some/path/CognateTable?cognatesetReference=X#cldf:__all__)
```

In addition to data objects you can also specify maps to be created with `cldfviz.map` and included in the
resulting markdown document; e.g.:
```
![](map.jpg?parameters=1A#cldfviz.map)
```

An example of a document rendered with `cldfviz.text` is [text_example/README.md](text_example/README.md),
several paragraphs of [WALS' chapter 21](https://wals.info/chapter/21), rewritten in
["CLDF markdown"](text_example/README_tmpl.md) and rendered by "filling in" data from
[WALS as CLDF dataset](https://github.com/cldf-datasets/wals/).
