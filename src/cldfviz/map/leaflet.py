import html
import json
import string

import attr
from clldutils import svg
from clldutils.html import HTML
from clldutils.clilib import PathType
from clldutils import jsonlib

from cldfviz.colormap import get_shape_and_color, weighted_colors, SVG_SHAPE_MAP as SHAPE_MAP
from .base import Map, PACIFIC_CENTERED
from cldfviz.template import TEMPLATE_DIR
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
    'USGS.USTopo': (
        'https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/tile/{z}/{y}/{x}',
        {
            'maxZoom': 20,
            'attribution':
                'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
        }
    ),
    'USGS.USImagery': (
        'https://basemap.nationalmap.gov/arcgis/rest/services/'
        'USGSImageryOnly/MapServer/tile/{z}/{y}/{x}',
        {
            'maxZoom': 20,
            'attribution':
                'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
        }
    ),
    'USGS.USImageryTopo': (
        'https://basemap.nationalmap.gov/arcgis/rest/services/'
        'USGSImageryTopo/MapServer/tile/{z}/{y}/{x}',
        {
            'maxZoom': 20,
            'attribution':
                'Tiles courtesy of the <a href="https://usgs.gov/">U.S. Geological Survey</a>'
        }
    ),
}
GEOJSON_LAYERS = {p.name.split('.')[0]: p for p in TEMPLATE_DIR.joinpath('map').glob('*.geojson*')}


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
        parser.add_argument(
            '--with-layers',
            default=False,
            action='store_true',
            help='Create clickable Leaflet layers for each parameter value. {}'.format(help_suffix),
        )
        parser.add_argument(
            '--with-layers-for-combinations',
            default=False,
            action='store_true',
            help='Create clickable Leaflet layers for each combination of parameter values. '
                 '{}'.format(help_suffix),
        )
        parser.add_argument(
            '--value-template',
            default='{parameter}: {code}',
            help='A format string specifying how to format values as text labels.',
        )
        parser.add_argument(
            '--overlay-geojson',
            type=PathType(type='file', must_exist=False),
            default=None,
            help='Path to the GeoJSON file containing a FeatureCollection to overlay on the map. '
                 'Note: You may also chose from {}.'.format(list(GEOJSON_LAYERS.keys()))
        )
        parser.add_argument(
            '--overlay-options',
            type=PathType(type='file'),
            default=None,
        )

    def _lonlat(self, language):
        lon, lat = language.lon, language.lat
        if self.args.pacific_centered and lon <= PACIFIC_CENTERED - 180:
            # Anything west of 26°W is moved by 360°.
            lon += 360  # make the map pacific-centered.
        return [lon, lat]

    def _icon(self, colors):
        scolors = []
        if isinstance(colors[0], list):
            ncolors = []
            for s, c in colors:
                ncolors.append(s)
                scolors.append(c)
            colors = ncolors
        colors = [(1 / len(colors), t) if isinstance(t, str) else t for t in colors]
        res = get_shape_and_color(colors)
        if res:
            if scolors:
                return svg.icon(SHAPE_MAP[res[0]] + scolors[0].replace('#', ''))
            return svg.icon(SHAPE_MAP[res[0]] + res[1].replace('#', ''))
        return svg.pie([c[0] for c in colors], [c[1] for c in colors], stroke_circle=True)

    def add_language(self, language, values, colormaps, spec=None):
        icon = self._icon(weighted_colors(values, colormaps))
        props = {
            "name": language.name,
            "tooltip": language.name,
            "values": ' / '.join(
                [self.args.value_template.format(
                    parameter=pid, code=vals[0].v) for pid, vals in values.items() if vals]),
            "icon": svg.data_url(icon),
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
        def marker(colors):
            return HTML.img(
                src=svg.data_url(self._icon(colors)),
                width="{}".format(min([20, self.args.markersize * 2])))

        trs = []
        for i, (pid, parameter) in enumerate(parameters.items()):
            if i != 0:
                trs.append(HTML.tr(HTML.th(HTML.hr(), colspan='2')))
            trs.append(HTML.tr(
                HTML.th(
                    marker(['#000000' if j == i else '#ffffff' for j in range(len(parameters))])),
                HTML.th(parameter.name, style="text-align: left;")
            ))
            if isinstance(parameter.domain, tuple):
                # Create an HTML color bar for a continuous variable, as table with two rows and
                # 11 columns.
                min_, max_ = parameter.domain
                tds_label = []
                tds_color = []
                for j in range(11):
                    if j == 0:
                        tds_label.append(HTML.td(str(round(min_, 2))))
                    elif j == 10:
                        tds_label.append(HTML.td(str(round(max_, 2)), style="text-align: right;"))
                    else:
                        tds_label.append(HTML.td(' '))
                    tds_color.append(HTML.td(
                        ' ',
                        style='height: 20px; width: 1em; background-color: {};'.format(
                            colormaps[pid](min_ + j * (max_ - min_) / 10))))
                trs.append(HTML.tr(HTML.td(HTML.table(
                    HTML.tr(*tds_label),
                    HTML.tr(*tds_color)
                ), colspan='2')))
            else:
                for v, label in parameter.domain.items():
                    trs.append(HTML.tr(
                        HTML.td(marker([
                            colormaps[pid](v) if j == i else '#ffffff'
                            for j in range(len(parameters))])),
                        HTML.td(str(label))
                    ))
        self.legend = HTML.table(*trs, **{'class': 'legend'})

    def __exit__(self, exc_type, exc_val, exc_tb):
        """write files"""
        import zipfile

        overlay_geojson, overlay_options = dict(features=[]), '{}'
        if self.args.overlay_geojson:
            if str(self.args.overlay_geojson) in GEOJSON_LAYERS:  # cast PathType() to str!
                self.args.overlay_options = \
                    TEMPLATE_DIR / 'map' / '{}.js'.format(self.args.overlay_geojson)
                self.args.overlay_geojson = GEOJSON_LAYERS[str(self.args.overlay_geojson)]
            if zipfile.is_zipfile(self.args.overlay_geojson):
                zip = zipfile.ZipFile(self.args.overlay_geojson)
                overlay_geojson = json.loads(zip.read(zip.namelist()[0]).decode('utf8'))
            else:
                overlay_geojson = jsonlib.load(self.args.overlay_geojson)  # pragma: no cover
            if self.args.overlay_options:
                overlay_options = self.args.overlay_options.read_text(encoding='utf8')

        html_ = string.Template(
            cldfviz.PKG_DIR.joinpath('templates', 'map', 'leaflet.html').read_text(encoding='utf8')
        ).substitute(
            title=self.args.title or '',
            css='\n'.join(sorted(self.css)),
            legend=self.legend,
            options=json.dumps({
                'language_labels': self.args.language_labels,
                'with_layers': self.args.with_layers,
                'with_layers_for_combinations': self.args.with_layers_for_combinations,
            }),
            tile_url=json.dumps(BASE_LAYERS[self.args.base_layer][0]),
            tile_options=json.dumps(BASE_LAYERS[self.args.base_layer][1]),
            geojson=json.dumps({"features": self.features, "type": "FeatureCollection"}),
            overlay_geojson=json.dumps(overlay_geojson['features']),
            overlay_options=html.escape(overlay_options, quote=False),
        )
        self.args.output.write_text(html_, encoding='utf8')
