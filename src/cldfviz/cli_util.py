import argparse


def add_testable(parser):
    parser.add_argument('--test', action='store_true', default=False, help=argparse.SUPPRESS)
