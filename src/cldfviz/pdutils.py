"""
Utilities to bridge CLDF and pandas objects.
"""
import types
import typing
import collections

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = types.SimpleNamespace(DataFrame=object)

__all__ = ['df_from_dicts']


class DF:
    def __init__(self):
        self.df = None
        self.acc = collections.defaultdict(list)

    def __enter__(self):
        return self

    def add(self, item):
        if self.df is None:
            self.df = pd.DataFrame(columns=list(item))
        for k, v in item.items():
            self.acc[k].append(v)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for k, v in self.acc.items():
            self.df[k] = v


def df_from_dicts(dicts: typing.Iterable[dict]) -> pd.DataFrame:
    """
    Combines "rows" given as `dict`s into a pandas DataFrame.
    """
    with DF() as df:
        for d in dicts:
            df.add(d)
    return df.df
