"""
Create an HTML/Javascript map displaying the data of a CLDF StructureDataset.
"""
import copy
import json
import string
import pathlib
import argparse
import itertools
import webbrowser
import collections

from clldutils import color, svg
from pycldf import StructureDataset
from clldutils.clilib import ParserError, PathType
from cldfbench.cli_util import add_dataset_spec, get_dataset, add_catalog_spec

import cldfviz


def register(parser):
    parser.add_argument('--output', type=PathType('dir'), default=pathlib.Path('.'))
    add_dataset_spec(parser)
    add_catalog_spec(parser, 'glottolog')
    parser.add_argument('--test', action='store_true', default=False, help=argparse.SUPPRESS)


def run(args):
    try:
        ds = get_dataset(args).cldf_reader()
    except (ParserError, ModuleNotFoundError):
        # Try to load plain (i.e. non-cldfbench-enabled) CLDF dataset.
        try:
            ds = StructureDataset.from_metadata(args.dataset)
        except json.JSONDecodeError:
            ds = StructureDataset.from_data(args.dataset)

    languoids = {lang.id: lang for lang in args.glottolog.api.languoids()}
    values = collections.defaultdict(lambda: collections.defaultdict(list))
    #
    # FIXME: consult LanguageTable to look up coordinates and/or Glottocodes!
    #
    for value in ds.iter_rows('ValueTable', 'parameterReference', 'languageReference', 'value'):
        if value['value'] is None:
            continue  # pragma: no cover
        if (value['languageReference'] in languoids) and \
                languoids[value['languageReference']].latitude is not None:
            values[value['parameterReference']][value['value']].append(value['languageReference'])
        else:
            args.log.warning(
                'Language with unknow or non-geo-referenced Glottocode {}'.format(
                    value['languageReference']))

    domains = [
        (pid, sorted([cid for cid in vals if cid]))
        for pid, vals in sorted(values.items(), key=lambda i: i[0])
    ]

    values_by_lang = collections.defaultdict(dict)
    for pid, vals in values.items():
        for cid, langs in vals.items():
            for lang in langs:
                values_by_lang[lang][pid] = cid

    combinations = collections.Counter()
    for gc in list(values_by_lang.keys()):
        vals = values_by_lang[gc]
        spec = []
        for pid, domain in domains:
            spec.append((pid, vals.get(pid)))
        # Store normalized values tuple per language:
        values_by_lang[gc] = tuple(spec)
        combinations.update([tuple(spec)])

    colors = {}
    for pid, domain in domains:
        for d, c in zip(
            domain,
            color.qualitative_colors(len(domain), set='tol' if len(domain) <= 12 else None)
        ):
            colors[(pid, d)] = c
        colors[(pid, None)] = '#fff'
    icons = {
        t: svg.data_url(svg.pie(
            [1] * len(domains), [colors[pid, d] for pid, d in t], stroke_circle=True))
        for t in itertools.product(
            *[[(pid, d) for d in list(domain) + [None]] for pid, domain in domains])}
    legend = '<table>'
    empty_spec = [(p[0], None) for p in domains]
    for i, (pid, domain) in enumerate(domains):
        legend += '<tr><th colspan="2">{}</th></tr>'.format(pid)
        for cid in domain:
            icon_spec = copy.copy(empty_spec)
            icon_spec[i] = (pid, cid)
            legend += '<tr><td><img src="{}"></td><td>{}</td></tr>'.format(
                icons[tuple(icon_spec)], cid)
    legend += '</table>'

    def l2f(n, icon_spec):
        lon, lat = n.longitude, n.latitude
        if lon <= -26:
            lon += 360  # make the map pacific-centered.

        return {
            "geometry": {"coordinates": [lon, lat], "type": "Point"},
            "id": n.id,
            "properties": {
                "name": n.name,
                "values": ' / '.join(['{}'.format(v) for k, v in icon_spec]),
                "icon": icons[icon_spec],
            },
            "type": "Feature"
        }

    geojson = {
        "features": [l2f(languoids[gc], vals) for gc, vals in values_by_lang.items()],
        "type": "FeatureCollection"
    }

    def rendered_template(name, **kw):
        return string.Template(
            cldfviz.PKG_DIR.joinpath('templates', 'htmlmap', name).read_text(encoding='utf8')
        ).substitute(**kw)

    jsname = 'cldfviz_map.js'
    args.output.joinpath(jsname).write_text(
        rendered_template(
            'htmlmap.js',
            combinations=json.dumps([[' / '.join(['{}'.format(v) for k, v in c[0]]), c[1]]
                                     for c in combinations.most_common()]),
            geojson=json.dumps(geojson, indent=4)),
        encoding='utf8')
    html = args.output.joinpath('index.html')
    html.write_text(
        rendered_template(
            'htmlmap.html',
            title=ds.properties.get('dc:title') or args.dataset,
            jsname=jsname,
            legend=legend,
            nlangs=len(values_by_lang)),
        encoding='utf8')
    if not args.test:
        webbrowser.open(html.resolve().as_uri())  # pragma: no cover
