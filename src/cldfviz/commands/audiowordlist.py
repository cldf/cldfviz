"""
Build an HTML file to display a wordlist for a particular concept with associated audio.

Assumes that
- the dataset is a CLDF Wordlist, coding concepts as parameters,
- forms are linked to media files
  - via a column with propertyUrl "mediaReference" in FormTable or
  - a column with propertyUrl "formReference" in MediaTable.
"""
from clldutils.clilib import PathType
from clldutils.misc import nfilter
from pycldf.terms import term_uri
from pycldf.cli_util import get_dataset, add_dataset

from cldfviz.cli_util import add_open, write_output, add_jinja_template
from cldfviz.media import get_objects_and_media, get_media_url
from cldfviz.template import render_jinja_template, TEMPLATE_DIR


def register(parser):
    add_dataset(parser)
    parser.add_argument(
        'concept',
        help='Specify a concept in the form COLNAME=VALUE or cldf:PROPNAME=VALUE, e.g. '
             '"Name=hand" or "cldf:id=10", using column names used in ParameterTable or '
             'CLDF properties available in ParameterTable.')
    # parser.add_argument('--mimetype', default=None)
    mod = __name__.split('.')[-1]
    add_jinja_template(parser, TEMPLATE_DIR / mod / '{}.html'.format(mod))
    parser.add_argument(
        '--media-dir',
        help="If media files are available locally (downloaded via pycldf's `cldf downloadmedia` "
             "command), the media directory can be passed to access the audio files on disk.",
        type=PathType(type='dir'),
        default=None)
    add_open(parser)


def run(args):
    ds = get_dataset(args)

    # Determine the relevant concept (aka parameter):
    colspec, sep, match = args.concept.partition('=')
    colname = None
    if not sep:
        match = colspec
    else:
        cldfprop = colspec.startswith('cldf:')
        colspec = colspec.replace('cldf:', '')
        colname = ds['ParameterTable', term_uri(colspec)].name if cldfprop else colspec

    if 'ParameterTable' in ds:
        for row in ds.iter_rows('ParameterTable', 'id', 'name'):
            if (colname and row[colname] == match) or row['id'] == match:
                pid = row['id']
                break
        else:
            raise ValueError(args.concept)  # pragma: no cover
    else:
        assert colname is None
        pid = match

    # Get relevant forms and linked media:
    forms = []
    for form, media in get_objects_and_media(
            ds, 'FormTable', 'formReference', filter=lambda f: f.cldf.parameterReference == pid):
        forms.append((
            form,
            nfilter(get_media_url(f, args.media_dir) for f in media if f.mimetype.type == 'audio')))

    res = render_jinja_template(
        args.template,
        ds=ds,
        pid=pid,
        parameter=forms[0][0].parameter,
        forms=forms,
        local=bool(args.media_dir))
    write_output(args, res)
