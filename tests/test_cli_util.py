import argparse

from cldfviz import cli_util


def test_tree(tmp_path):
    nwk = tmp_path / 'test.nwk'
    nwk.write_text('((a,b),c)d;')
    parser = argparse.ArgumentParser()
    cli_util.add_tree(parser)
    args = parser.parse_args(['--tree', str(nwk)])
    res = cli_util.get_tree(args)
    assert res[0].name == 'd'
