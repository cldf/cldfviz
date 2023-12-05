# Changes

## [Unreleased]

- Fixed bug whereby non-source CLDF Markdown links were not replaced when a
  link to insert a reference list of cited sources was present.


## [v1.0.1] - 2023-12-01

- Fixed bug whereby CLDF examples were not properly HTML escaped when rendered as Markdown.
- Fixed bug whereby the --language-filters option was ignored in `cldfviz.map` when no
  parameters were specified.
- Added Python 3.12 to supported version.


## [v1.0.0] - 2023-08-14

- Added `--db` option to `cldfviz.erd` command to allow bypassing SQLite creation.
- Dropped py3.7 compatibility.


## [v0.12.0] - 2023-02-06

- Support for plotting data on trees.
- Support for multi-valued parameters.
- Support SVG output for `cldfviz.map`.
- Support custom GeoJSON layer in HTML maps.
- 100% statement coverage in tests.

**Backward incompatibilities:**

- `cldfviz.tree` has **no** required dataset argument anymore. To plot a tree from the TreeTable
  of a CLDF dataset, pass the dataset locator as `--tree-dataset` option.


## [v0.11.0] - 2023-01-31

**Backward incompatibilities:**

- `cldfviz.tree` has **no** required output argument anymore. Instead, it writes the result to
  `stdout` by default, and to a file if one is specified as `--output` option.
