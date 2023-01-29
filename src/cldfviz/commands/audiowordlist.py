"""
Build an HTML file to display a wordlist for a particular concept with associated audio.

Assumes that
- the dataset is a CLDF Wordlist, coding concepts as parameters,
- forms are linked to media files
  - via a column with propertyUrl "mediaReference" in FormTable or
  - a column with propertyUrl "formReference" in MediaTable.
"""
import collections

from clldutils.clilib import PathType
from pycldf.terms import term_uri
from pycldf.cli_util import get_dataset, add_dataset
from pycldf.media import MediaTable
import jinja2

import cldfviz


def as_list(obj):
    if isinstance(obj, list):
        return obj
    return [obj]


def register(parser):
    add_dataset(parser)
    parser.add_argument(
        'concept',
        help='Specify a concept in the form COLNAME=VALUE or cldf:PROPNAME=VALUE, e.g. '
             '"Name=hand" or "cldf:id=10", using column names used in ParameterTable or '
             'CLDF properties available in ParameterTable.')
    # parser.add_argument('--mimetype', default=None)
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
    forms, media = [], set()
    if ('FormTable', 'mediaReference') in ds:
        for form in ds.objects('FormTable'):
            if form.cldf.parameterReference == pid:
                mrefs = as_list(form.cldf.mediaReference)
                media |= set(mrefs)
                forms.append((form, mrefs))
    elif ('MediaTable', 'formReference') in ds:
        media_by_fid = collections.defaultdict(list)
        for row in ds.iter_rows('MediaTable', 'id', 'formReference'):
            for fid in as_list(row['formReference']):
                media_by_fid[fid].append(row['id'])
        for form in ds.objects('FormTable'):
            if form.cldf.parameterReference == pid:
                mrefs = media_by_fid.get(form.id, [])
                media |= set(mrefs)
                forms.append((form, mrefs))

    media = {mid: None for mid in media}

    # Retrieve relevant media - filtered by media type:
    for file in MediaTable(ds):
        if file.id in media and file.mimetype.type == 'audio':  # filter!
            if args.media_dir:
                if file.local_path(args.media_dir).exists():
                    # Read audio from the file system:
                    media[file.id] = 'file://{}'.format(
                        file.local_path(args.media_dir).resolve())
            else:
                # Read audio from the URL:
                media[file.id] = file.url

    loader = jinja2.FileSystemLoader(
        searchpath=[str(cldfviz.PKG_DIR / 'templates' / 'audiowordlist')])
    env = jinja2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    res = env.get_template('audiowordlist.html').render(
        ds=ds,
        pid=pid,
        parameter=forms[0][0].parameter,
        forms=[(form, [media[mid] for mid in mrefs if media[mid]]) for form, mrefs in forms],
        local=bool(args.media_dir))
    if args.output:
        args.output.write_text(res, encoding='utf8')
        print('HTML written to {}'.format(args.output))
    else:
        print(res)
