# Changes


## [Unreleased]

- Support for plotting data on trees.
- Support for multi-valued parameters.
- Support SVG output for `cldfviz.map`.
- 100% statement coverage in tests.

**Backward incompatibilities:**

- `cldfviz.tree` has **no** required dataset argument anymore. To plot a tree from the TreeTable
  of a CLDF dataset, pass the dataset locator as `--tree-dataset` option.


## [v0.11.0] - 2023-01-31

**Backward incompatibilities:**

- `cldfviz.tree` has **no** required output argument anymore. Instead, it writes the result to
  `stdout` by default, and to a file if one is specified as `--output` option.
