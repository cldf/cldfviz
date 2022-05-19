"""
Build an HTML file to display a wordlist for a particular concept with associated audio.

Assumes that forms are linked to media files via a column with propertyUrl "mediaReference"
in FormTable.
"""
from clldutils.clilib import PathType
from pycldf.terms import term_uri
from pycldf.cli_util import get_dataset, add_dataset
from pycldf.media import Media
import jinja2

import cldfviz


def register(parser):
    add_dataset(parser)
    parser.add_argument(
        'concept',
        help='Specify a concept in the form COLNAME=VALUE or cldf:PROPNAME=VALUE, e.g. '
             '"Name=hand" or "cldf:id=10", using column names used in ParameterTable or '
             'CLDF properties available in ParameterTable.')
    #parser.add_argument('--mimetype', default=None)
    parser.add_argument(
        '--media-dir',
        help="If media files are available locally (downloaded via pycldf's `cldf downloadmedia` "
             "command), the media directory can be passed to access the audio files on disk.",
        type=PathType(type='dir'),
        default=None)
    parser.add_argument(
        '-o', '--output',
        type=PathType(type='file', must_exist=False),
        default=False)


def run(args):
    ds = get_dataset(args)

    # Determine the relevant concept (aka parameter):
    colspec, _, match = args.concept.partition('=')
    cldfprop = colspec.startswith('cldf:')
    colspec = colspec.replace('cldf:', '')
    colname = ds['ParameterTable', term_uri(colspec)].name if cldfprop else colspec

    for row in ds.iter_rows('ParameterTable', 'id', 'name'):
        if row[colname] == match:
            pid, concept = row['id'], row['name']
            break
    else:
        raise ValueError(args.concept)

    # Get relevant forms:
    forms, media = [], {}
    for form in ds.objects('FormTable'):
        if form.parameter.id == pid:
            if not isinstance(form.cldf.mediaReference, list):
                form.cldf.mediaReference = [form.cldf.mediaReference]
            for mid in form.cldf.mediaReference:
                media[mid] = form
            forms.append(form)

    # Retrieve relevant media - filtered by media type:
    for file in Media(ds):
        if file.id in media:  # Anything linked to one of our forms.
            if file.mimetype.type == 'audio':  # filter!
                if args.media_dir:
                    if file.local_path(args.media_dir).exists():
                        # Read audio from the file system:
                        media[file.id].audio = 'file://{}'.format(
                            file.local_path(args.media_dir).resolve())
                else:
                    # Read audio from the URL:
                    media[file.id].audio = file.url

    loader = jinja2.FileSystemLoader(
        searchpath=[str(cldfviz.PKG_DIR / 'templates' / 'audiowordlist')])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    res = env.get_template('audiowordlist.html').render(
        ds=ds,
        parameter=forms[0].parameter,
        forms=forms,
        local=bool(args.media_dir))
    if args.output:
        args.output.write_text(res, encoding='utf8')
        print('HTML written to {}'.format(args.output))
    else:
        print(res)
