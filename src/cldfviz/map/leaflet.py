import json
import string

import attr
import yattag
from clldutils import svg

from .base import Map
import cldfviz


BASE_LAYERS = {
    'OpenStreetMap': (
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            'maxZoom': 18,
            'attribution':
                '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'}
    ),
    'OpenTopoMap': (
        'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        {
            'maxZoom': 17,
            'attribution':
                'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap'
                '</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | '
                'Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> '
                '(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'}
    ),
    'Esri_WorldImagery': (
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/'
        'tile/{z}/{y}/{x}',
        {
            'attribution':
                'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, '
                'Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'}
    ),
    'Esri_WorldPhysical': (
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/'
        'tile/{z}/{y}/{x}',
        {
            'attribution': 'Tiles &copy; Esri &mdash; Source: US National Park Service',
            'maxZoom': 8}
    ),
    'Esri_NatGeoWorldMap': (
        'https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/'
        'tile/{z}/{y}/{x}',
        {
            'attribution':
                'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, '
                'USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',
            'maxZoom': 16}
    ),
}


@attr.s
class LeafletMarkerSpec:
    icon = attr.ib(default=svg.data_url(svg.icon('c000')))
    name = attr.ib(default=None)
    values = attr.ib(default=None)
    tooltip = attr.ib(default=None)
    tooltip_class = attr.ib(default=None)
    markersize = attr.ib(default=None)
    css = attr.ib(default=None)


class MapLeaflet(Map):
    __formats__ = ['html']
    __marker_class__ = LeafletMarkerSpec

    def __init__(self, languages, args):
        Map.__init__(self, languages, args)
        self.features = []
        self.legend = ''
        self.css = set()

    @staticmethod
    def add_options(parser, help_suffix):
        parser.add_argument(
            '--base-layer',
            default='OpenStreetMap',
            help="Tile layer for Leaflet maps. {}".format(help_suffix),
            choices=list(BASE_LAYERS),
        )

    def _lonlat(self, language):
        lon, lat = language.lon, language.lat
        if self.args.pacific_centered and lon <= -26:
            lon += 360  # make the map pacific-centered.
        return [lon, lat]

    def add_language(self, language, values, colormaps, spec=None):
        props = {
            "name": language.name,
            "tooltip": language.name,
            "values": ' / '.join(['{}'.format(vals[0].v) for vals in values.values() if vals]),
            "icon": svg.data_url(svg.pie(
                [1] * len(values),
                [colormaps[pid](vals[0].v) for pid, vals in values.items()],
                stroke_circle=True)),
            "markersize": self.args.markersize,
            "tooltip_class": "tt",
        }
        if spec:
            if spec.css:
                self.css.add(spec.css)
            props.update(
                {k: v for k, v in attr.asdict(spec).items() if v is not None and k != 'css'})
        self.features.append({
            # A language as GeoJSON point with svg marker icon
            "geometry": {"coordinates": self._lonlat(language), "type": "Point"},
            "id": language.id,
            "properties": props,
            "type": "Feature"
        })

    def add_legend(self, parameters, colormaps):
        doc, tag, text = yattag.Doc().tagtext()

        def marker(colors):
            doc.stag('img', src=svg.data_url(svg.pie(
                [1] * len(parameters),
                colors,
                stroke_circle=True,
            )), width="{}".format(min([20, self.args.markersize * 2])))

        with tag('table', klass="legend"):
            for i, (pid, parameter) in enumerate(parameters.items()):
                if i != 0:
                    with tag('tr'):
                        with tag('th', colspan=2):
                            doc.stag('hr')
                with tag('tr'):
                    with tag('th'):
                        marker(['#000000' if j == i else '#ffffff' for j in range(len(parameters))])
                    with tag('th', style="text-align: left;"):
                        text(parameter.name)
                if isinstance(parameter.domain, tuple):
                    min_, max_ = parameter.domain
                    with tag('tr'):
                        with tag('td', colspan=2):
                            with tag('table'):
                                with tag('tr'):
                                    with tag('td'):
                                        text(str(round(min_, 2)))
                                    for _ in range(9):
                                        with tag('td'):
                                            text(' ')
                                    with tag('td', style="text-align: right;"):
                                        text(str(round(max_, 2)))
                                with tag('tr'):
                                    for j in range(11):
                                        with tag(
                                            'td',
                                            style='height: 20px; width: 1em; background-color: '
                                                  '{};'.format(
                                                colormaps[pid](min_ + j * (max_ - min_) / 10))
                                        ):
                                            text(' ')
                else:
                    for v, label in parameter.domain.items():
                        with tag('tr'):
                            with tag('td'):
                                marker([colormaps[pid](v) if j == i else '#ffffff'
                                        for j in range(len(parameters))])
                            with tag('td'):
                                text(str(label))
        self.legend = doc.getvalue()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """write files"""
        html = string.Template(
            cldfviz.PKG_DIR.joinpath('templates', 'map', 'leaflet.html').read_text(encoding='utf8')
        ).substitute(
            title=self.args.title or '',
            css='\n'.join(sorted(self.css)),
            legend=self.legend,
            options=json.dumps({'language_labels': self.args.language_labels}),
            tile_url=json.dumps(BASE_LAYERS[self.args.base_layer][0]),
            tile_options=json.dumps(BASE_LAYERS[self.args.base_layer][1]),
            geojson=json.dumps({"features": self.features, "type": "FeatureCollection"}))
        self.args.output.write_text(html, encoding='utf8')
