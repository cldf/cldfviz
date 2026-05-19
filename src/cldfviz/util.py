"""
Utilities with no dependencies on other cldfviz code.
"""
import argparse

from clldutils.clilib import PathType


def add_download_dir(parser: argparse.ArgumentParser):
    """Add an opttion to specify a download dir."""
    try:
        parser.add_argument(
            '--download-dir',
            type=PathType(type='dir'),
            help='An existing directory to use for downloading a dataset (if necessary).',
            default=None,
        )
    except argparse.ArgumentError:  # pragma: no cover
        pass  # output option already added.
