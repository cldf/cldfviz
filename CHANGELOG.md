# Changes

## [Unreleased]

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
