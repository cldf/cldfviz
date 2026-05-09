"""
FIXME: Work in progress
"""
import argparse

from pycldf.cli_util import add_dataset, get_dataset

from cldfviz.cli_util import add_open


def register(parser: argparse.ArgumentParser):  # pylint: disable=C0116
    add_dataset(parser)
    parser.add_argument('text')
    add_open(parser)


def run(args: argparse.Namespace):  # pylint: disable=C0116
    ds = get_dataset(args)

    for text in ds.objects('ContributionTable'):
        if text.id == args.text:
            break
    else:
        raise ValueError(args.text)

    for k, v in text.data.items():
        print(k, v)

    lines = [ex for ex in ds.objects('ExampleTable') if ex.cldf.contributionReference == text.id]
    print(len(lines))

    for line in lines:
        for media in line.all_related('mediaReference'):
            if media.cldf.mediaType == 'audio/mpeg':
                break
        else:
            media = None
        print(line.cldf.primaryText)
        print(line.cldf.translatedText)
        if media:
            print(media.cldf.downloadUrl.path, line.data['Audio_Start'], line.data['Audio_End'])
