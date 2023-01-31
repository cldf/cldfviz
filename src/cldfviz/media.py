import typing
import collections

from csvw.datatypes import anyURI
from pycldf import Dataset
from pycldf.media import MediaTable, File


def as_list(obj):
    if isinstance(obj, list):
        return obj
    return [obj]


def get_objects_and_media(ds: Dataset, comp: str, refprop: str, filter=None) -> typing.List:
    """
    Objects can be related to media via a `mediaReference` on the object's table or via an object
    reference on `MediaTable`.
    """
    objs, media = [], set()
    if (comp, 'mediaReference') in ds:
        for obj in ds.objects(comp):
            if filter is None or filter(obj):
                mrefs = as_list(obj.cldf.mediaReference)
                media |= set(mrefs)
                objs.append((obj, mrefs))
    elif ('MediaTable', refprop) in ds:
        media_by_fid = collections.defaultdict(list)
        for row in ds.iter_rows('MediaTable', 'id', refprop):
            for fid in as_list(row[refprop]):
                media_by_fid[fid].append(row['id'])
        for obj in ds.objects(comp):
            if filter is None or filter(obj):
                mrefs = media_by_fid.get(obj.id, [])
                media |= set(mrefs)
                objs.append((obj, mrefs))
    else:
        objs = [(obj, []) for obj in ds.objects(comp) if filter is None or filter(obj)]

    media = {mid: None for mid in media}
    if 'MediaTable':
        for file in MediaTable(ds):
            if file.id in media:
                media[file.id] = file
    return [(obj, [media[mid] for mid in mrefs if media[mid]]) for obj, mrefs in objs]


def get_media_url(file: File, media_dir=None) -> typing.Union[None, str]:
    if media_dir:
        if file.local_path(media_dir).exists():
            # Read audio from the file system:
            return 'file://{}'.format(file.local_path(media_dir).resolve())
    else:
        # Read audio from the URL:
        return anyURI.to_string(file.url)
