"""

"""
from pycldf.cli_util import add_dataset, get_dataset
from pycldf import orm
from clldutils.misc import nfilter

from cldfviz.cli_util import (
    add_open, write_output, add_jinja_template, add_language_filter, get_filtered_languages,
)
from cldfviz.media import get_objects_and_media, get_media_url
from cldfviz.template import render_jinja_template, TEMPLATE_DIR


def register(parser):
    add_dataset(parser)
    parser.add_argument('text')
    add_open(parser)


def run(args):
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
