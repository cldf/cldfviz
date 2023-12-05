# `cldfviz.text`

A rather traditional visualization of linguistic data is the practice of interspersing bits of data
in descriptive texts, most obviously perhaps as examples formatted as **I**nterlinear **G**lossed **T**ext.
Other examples of data in text include forms, either in running text or in a table, or just references.

To support this use case, the `cldfviz.text` command can fill data from a CLDF dataset into a markdown
document, where references to CLDF data objects (rows of tables or complete tables) are marked using
markdown links.

While this process may seem overly complex - after all, you could just type an IGT example into your document - there
are advantages:
1. Valuable structured data can be made available as CLDF data, thus opening it up for re-use (and various
   attempts to extract IGT from text documents are proof that this content is considered valuable).
2. Rendering of structured data can be made more uniform and automatic - thereby simplifying authoring of such
   documents.

Basically, we want to have data in two places, and the better authoritative place for it seems to be the CLDF dataset.
With `cldfviz.text` we want to make it easier to "pull data back into text".


## Syntax

[CLDF Markdown](https://github.com/cldf/cldf/blob/master/extensions/markdown.md) is specified as CLDF extension
since CLDF 1.2. `cldfviz.text` provides a customizable CLDF Markdown renderer, which converts CLDF Markdown
to regular markdown, with CLDF Markdown links replaced by rendering Jinja templates.


## Rendering

Rendering of data objects is controlled with [templates](../src/cldfviz/templates/text) using the
[Jinja](https://jinja.palletsprojects.com/) template language. Sometimes, templates can be parametrized,
e.g. to choose only cognates belonging to the same cognate set from a `CognateTable`. These parameters can
be specified as [query string](https://en.wikipedia.org/wiki/Query_string) of the reference URL, e.g.
```
[cognateset X](some/path/CognateTable?cognatesetReference=X#cldf:__all__)
```

In addition to data objects you can also specify
- maps to be created with `cldfviz.map` and 
- trees to be created with `cldfviz.tree`

for inclusion in the resulting markdown document; e.g.:
```
![](map.jpg?parameters=1A#cldfviz.map)
```

An example of a document rendered with `cldfviz.text` is [text_example/README.md](text_example/README.md),
several paragraphs of [WALS' chapter 21](https://wals.info/chapter/21), rewritten in
["CLDF markdown"](text_example/README_tmpl.md) and rendered by "filling in" data from
[WALS as CLDF dataset](https://github.com/cldf-datasets/wals/).


### References

Any object in a CLDF dataset may reference sources. These references are typically rendered by the templates
associated with the object type. Thus, when a complete CLDF markdown document is rendered, it may be desireable
to include a list of all **cited** sources. This is supported as follows:

1. To insert a list of cited references in the document, add the link
   ```
   [References](Source?cited_only#cldf:__all__)
   ```
   at the location where the list should appear.
2. Discovery of cited sources relies on the references being rendered as links. Thus, it is necessary that all
   CLDF markdown links in the document are specified adding the `with_internal_ref_link` URL parameter.
3. If `Source` instances are referenced directly, the `ref` URL parameter needs to be supplied,
   e.g. `see [Meier 2012](Source?ref&with_internal_ref_links#cldf:Meier2012)`.


### Render an object using a selected properties

Sometimes it is desirable to render an object by just displaying a particular property, e.g. to
display the `name` or `description` of a Parameter as document title. This can be done using the
`property.md` template:
```
# [](ParameterTable?__template__=property.md&name=name#cldf:param1)
```


## CLI

```shell
$ cldfbench cldfviz.text -h
usage: cldfbench cldfviz.text [-h] [-l] [--text-string TEXT_STRING]
                              [--text-file TEXT_FILE] [--templates TEMPLATES]
                              [--output OUTPUT]
                              DATASET

positional arguments:
  DATASET               Dataset specification (i.e. path to a CLDF metadata
                        file or to the data file)

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            list templates (default: False)
  --text-string TEXT_STRING
  --text-file TEXT_FILE
  --templates TEMPLATES
  --output OUTPUT
```


## Examples

- Rendering a parameter description from a CLDF StructureDataset:
  ```shell
  $ cldfbench cldfviz.text --text-string "[](ParameterTable#cldf:D)" tests/StructureDataset/StructureDataset-metadata.json
  **Oblique Nouns**
  
  Description:
  Oblique stems of common nouns
  
  Codes:
  - 0: 0
  - 1: 1
  - 2: 2
  ```

- LGR
  ```shell
  $ cldfbench cldfviz.text https://raw.githubusercontent.com/cldf-datasets/lgr/main/cldf/Generic-metadata.json --text-string "[](ExampleTable#cldf:1)"
  
  > (1) Indonesian (Sneddon 1996: 237)
  <pre>
  Mereka  di  Jakarta  sekarang.  
  They    in  Jakarta  now  
  ‘They are in Jakarta now.’</pre>
  ```

- Maps and trees: Including maps and trees in CLDF Markdown can be very powerful.
  But as soon as it comes to customization, the nested formatting - e.g. passing
  a `toytree` styles dictionary as URL parameter - makes the process fragile.
  But as a proof-of-concept example you may look at the markdown source of
  [`wals_algic_tmpl.md`](output/wals_algic_tmpl.md) and the [markdown file](output/wals_algic.md)
  created from it running
  ```shell
  cldfbench cldfviz.text wals-2020.3/ --text-file wals_algic.md
  ```


## Referencing data from multiple CLDF datasets

While CLDF is designed to make merging data from multiple datasets easy, one may still want to reference data
from multiple datasets in the same CLDF markdown document. This is supported as follows.

The `cldfbench cldfviz.text` command accepts multiple datasets (specified by metadata file). To disambiguate
references, the URL fragment in reference links must also specify the dataset
- either by position in the argument list (starting from "1")
- or using an identifier assigned to the dataset (by appending it separated by `#` to the metadata file).

So for example, you can print sources from two CLDF datasets via
```shell
$ cldfbench cldfviz.text \
  peterson:tests/StructureDataset/StructureDataset-metadata.json list:tests/Wordlist/Wordlist-metadata.json \
  --text-string "[](Source#cldf-peterson:Peterson2017) [](Source#cldf-list:List2014e)"
Peterson, John. 2017. Fitting the pieces together - Towards a linguistic prehistory of eastern-central South Asia (and beyond). Journal of South Asian Languages and Linguistics 4. Walter de Gruyter {GmbH}.
List, J.-M. and Prokić, J. 2014. A benchmark database of phonetic alignments in historical linguistics and dialectology. In Calzolari, Nicoletta and Choukri, Khalid and Declerck, Thierry and Loftsson, Hrafn and Maegaard, Bente and Mariani, Joseph and Moreno, Asuncion and Odijk, Jan and Piperidis, Stelios (eds.), Proceedings of the Ninth International Conference on Language Resources and Evaluation, 288-294. Reykjavik, Iceland: European Language Resources Association (ELRA).
```

Similarly, for `cldfviz.map` references, use `cldfviz.map-<id>` as URL fragment in the relevant links.


## Related

There are several other efforts towards making Markdown a viable authoring platform for linguistic texts:
- Florian Matter's [pylingdocs](https://github.com/fmatter/pylingdocs) provides an authoring platform on top of CLDF Markdown
- Taras Zakahrko's [pandoc-glossify](https://github.com/tzakharko/pandoc-glossify) provides a [Pandoc](https://pandoc.org/) extension to render interlinear glossed text
- Michael Cysouw's [pandoc-ling](https://github.com/cysouw/pandoc-ling) also provides a [Pandoc](https://pandoc.org/) extension to render interlinear glossed text (testifying to the usefulness of Pandoc as cross-format authoring platform).
