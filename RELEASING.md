
Releasing cldfviz
=================

- Do platform test via tox:
```
tox -r
```

- Make sure flake8 passes:
```
flake8 src
```

- Update the version number, by removing the trailing `.dev0` in:
  - `setup.cfg`
  - `src/cldfviz/__init__.py`

- Create the release commit:
```shell
git commit -a -m "release <VERSION>"
```

- Create a release tag:
```
git tag -a v<VERSION> -m"<VERSION> release"
```

- Release to PyPI: 
```shell
rm dist/*
python -m build -n
twine upload dist/*
```

- Push to github:
```
git push origin
git push --tags
```

- Change version for the next release cycle, i.e. incrementing and adding .dev0
  - `setup.cfg`
  - `src/cldfviz/__init__.py`

- Commit/push the version change:
```shell
git commit -a -m "bump version for development"
git push origin
```
