"""
Map plotting with matplotlib and cartopy
"""
import json
import textwrap

import attr
import numpy as np
import cartopy.feature
import cartopy.crs
from matplotlib import pyplot as plt
from matplotlib.patches import Wedge, Rectangle
from matplotlib.legend_handler import HandlerPatch
from PIL import Image

from .base import Map, PACIFIC_CENTERED

SHAPE_MAP = {
    'triangle_down': '^',
    'triangle_up': 'v',
    'square': 's',
    'diamond': 'D',
    'circle': 'o',
}


def iter_subclasses(cls):
    for cls_ in cls.__subclasses__():
        yield cls_
        yield from iter_subclasses(cls_)


class HandleWedge(HandlerPatch):
    def create_artists(
            self,
            legend,
            orig_handle,
            xdescent,
            ydescent,
            width,
            height,
            fontsize,
            trans):
        center = 0.5 * width - 0.5 * xdescent, 0.5 * height - 0.5 * ydescent
        p = Wedge(
            center, height / 1.5, orig_handle.theta1, orig_handle.theta2, width=orig_handle.width)
        self.update_prop(p, orig_handle, legend)
        p.set_transform(trans)
        return [p]


@attr.s
class MPLMarkerSpec:
    marker_kw = attr.ib(default=attr.Factory(dict))
    text = attr.ib(default=None)
    text_offset_x = attr.ib(default=None)
    text_offset_y = attr.ib(default=None)
    text_kw = attr.ib(default=attr.Factory(dict))


class MapPlot(Map):
    """
    A geographic map, zoomed in to the extent defined by a list of languages.
    """
    __formats__ = ['jpg', 'png', 'pdf']
    __marker_class__ = MPLMarkerSpec

    def __init__(self, languages, args):
        Map.__init__(self, languages, args)
        lats = [k.lat for k in languages if k.lat is not None]
        lons = [k.lon for k in languages if k.lon is not None]
        self.central_longitude = PACIFIC_CENTERED if args.pacific_centered else 0

        if args.extent:
            left, right, top, bottom = [float(x) for x in args.extent.replace('"', '').split(',')]
            self.extent = [left, right, bottom, top]
        else:
            self.extent = [
                round(min(lons) - args.padding_left, 1) + self.central_longitude,
                round(max(lons) + args.padding_right, 1) + self.central_longitude,
                round(min(lats) - args.padding_bottom, 1),
                round(max(lats) + args.padding_top, 1)
            ]
        self.ax = None
        self.scaling_factor = 1
        self.proj = getattr(cartopy.crs, args.projection)(central_longitude=self.central_longitude)

    def __enter__(self):
        plt.clf()
        fig = plt.figure(figsize=(self.args.width, self.args.height), dpi=self.args.dpi)
        ax = fig.add_subplot(1, 1, 1, projection=self.proj)
        if self.args.projection == 'PlateCarree':
            ax.set_extent(self.extent, crs=self.proj)
        else:
            pass
        if self.args.with_stock_img:
            ax.stock_img()
        if (not self.args.test) and (not self.args.with_stock_img):  # pragma: no cover
            ax.coastlines(resolution='50m', color='darkgrey')
            ax.add_feature(cartopy.feature.LAND, color='beige', zorder=1)
            ax.add_feature(cartopy.feature.OCEAN, color='#97B5E1', zorder=2)
            if not self.args.no_borders:
                ax.add_feature(cartopy.feature.BORDERS, linestyle=':', zorder=4)
            ax.add_feature(cartopy.feature.LAKES, color="#97B5E1", alpha=0.5, zorder=3)
            ax.add_feature(cartopy.feature.RIVERS, color="#97B5E1", zorder=3)
        self.ax = ax
        # Figure out the scaling factor between degrees and pixels. Many config values are given
        # in pixels but need to be converted to degrees for plotting.
        m = self.proj._as_mpl_transform(axes=self.ax)
        y0 = m.transform_point((self.extent[0], self.extent[2])).tolist()[1]
        y1 = m.transform_point((self.extent[0], self.extent[2] + 1)).tolist()[1]
        self.scaling_factor = 1.0 / (y1 - y0)
        # So 1 px = self.scaling_factor * 1°
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.args.title:
            plt.title(self.args.title)
        format = self.args.output.suffix.replace('.', '').lower()
        if format == 'jpg':
            mplfname = self.args.output.parent / '{}.png'.format(self.args.output.stem)
            plt.savefig(str(mplfname), bbox_inches="tight")
            img = Image.open(str(mplfname)).convert('RGB')
            img.save(str(self.args.output), optimize=True, quality=95)
            mplfname.unlink()
        else:
            plt.savefig(str(self.args.output), bbox_inches="tight")

        plt.close()

    @staticmethod
    def add_options(parser, help_suffix):
        for direction in ['left', 'right', 'top', 'bottom']:
            parser.add_argument(
                '--padding-{}'.format(direction),
                help="{} padding of the map in degrees. {}".format(
                    direction.capitalize(), help_suffix),
                type=int,
                default=1,
            )
        parser.add_argument(
            '--extent',
            help="Set extent of the figure in terms of coordinates (left, right, top, bottom)",
            default=None
        )
        parser.add_argument(
            '--width',
            help="Width of the figure in inches. {}".format(help_suffix),
            type=float,
            default=6.4,
        )
        parser.add_argument(
            '--height',
            help="Height of the figure in inches. {}".format(help_suffix),
            type=float,
            default=4.8,
        )
        parser.add_argument(
            '--dpi',
            help="Pixel density of the figure. {}".format(help_suffix),
            type=float,
            default=100.0,
        )
        parser.add_argument(
            '--projection',
            help="Map projection. For details, see "
                 "https://scitools.org.uk/cartopy/docs/latest/crs/projections.html "
                 "{}".format(help_suffix),
            choices=[
                c.__name__ for c in iter_subclasses(cartopy.crs.Projection)
                if c.__module__ == 'cartopy.crs' and not c.__name__.startswith('_')],
            default='PlateCarree',
        )
        parser.add_argument(
            '--with-stock-img',
            help="Add a map underlay (using cartopy's `stock_img` method). {}".format(help_suffix),
            action="store_true",
            default=False,
        )
        parser.add_argument(
            '--no-borders',
            help="Do not add country borders to the map. {}".format(help_suffix),
            action="store_true",
            default=False,
        )
        parser.add_argument(
            '--zorder',
            help="Determine zorder of individual markers by color.",
            type=lambda s: json.loads(s),
            action="store",
            default={},
        )

    def _lonlat(self, language):
        lat, lon = language.lat, language.lon
        if self.central_longitude:
            lon = lon - self.central_longitude
            if lon < -180:
                lon += 360
        return lon, lat

    def pie_markers(self, colors):
        start = 0.
        for color in colors:
            ratio = 1 / len(colors)
            x = [0] + \
                np.cos(np.linspace(2 * np.pi * start, 2 * np.pi * (start + ratio), 30)).tolist() + \
                [0]
            y = [0] + \
                np.sin(np.linspace(2 * np.pi * start, 2 * np.pi * (start + ratio), 30)).tolist() + \
                [0]
            yield color, np.column_stack([x, y])
            start += ratio

    def add_language(self, language, values, colormaps, spec=None):
        # add zorder by using a point-system that penalizes missing data
        # according to user-defined weights
        if self.args.zorder:
            zorders = []
            for val in values.values():
                zorders += [self.args.zorder.get(val[0].v.split('-')[-1], 5)]
            zorder = sum(zorders)
        else:
            zorder = 5 * len(values)

        if spec:
            marker_kw = dict(
                color='white',
                markersize=self.args.markersize,
                zorder=20,
                marker='o',
                markeredgecolor='black',
                linewidth=1,
                transform=cartopy.crs.Geodetic(),
            )
            marker_kw.update(spec.marker_kw)
            self.ax.plot(language.lon, language.lat, **marker_kw)
            if spec.text:
                text_kw = dict(zorder=20, fontsize='small')
                text_kw.update(spec.text_kw)
                self.ax.text(
                    language.lon + (spec.text_offset_x or 0),
                    language.lat + (spec.text_offset_y or 0),
                    spec.text,
                    **text_kw)
            return
        lon, lat = self._lonlat(language)
        if self.args.projection != 'PlateCarree':
            colors = [colormaps[pid](vals[0].v) for pid, vals in values.items()]
            res = self.get_shape_and_color(colors)
            if res:
                self.ax.plot(
                    language.lon, language.lat,
                    color=res[1],
                    markersize=self.args.markersize,
                    zorder=zorder,
                    marker=SHAPE_MAP[res[0]],
                    markeredgecolor='black',
                    linewidth=1,
                    transform=cartopy.crs.Geodetic(),
                )
                return

            if len(values) > 1:
                for color, marker in self.pie_markers(
                        [colormaps[pid](vals[0].v) for pid, vals in values.items()]):
                    self.ax.scatter(
                        [language.lon], [language.lat],
                        marker=marker,
                        s=[self.args.markersize * 10],
                        transform=cartopy.crs.Geodetic(),
                        zorder=zorder,
                        edgecolors=["black"],
                        facecolor=color,
                    )
                return
            pid, vals = list(values.items())[0]
            self.ax.plot(
                language.lon, language.lat,
                color=colormaps[pid](vals[0].v),
                markersize=self.args.markersize,
                zorder=zorder,
                marker='o',
                markeredgecolor='black',
                linewidth=1,
                transform=cartopy.crs.Geodetic(),
            )
            return

        colors = [colormaps[pid](vals[0].v) for pid, vals in values.items()]
        res = self.get_shape_and_color(colors)
        if res:
            self.ax.plot(
                lon, lat,
                color=res[1],
                markersize=self.args.markersize,
                zorder=zorder,
                marker=SHAPE_MAP[res[0]],
                markeredgecolor='black',
                linewidth=1,
            )
        else:
            s, angle = 0, 360.0 / len(values)
            for pid, vals in values.items():
                self.ax.add_patch(Wedge(
                    [lon, lat],
                    self.args.markersize * self.scaling_factor / 2.0,
                    s,
                    s + angle,
                    facecolor=colormaps[pid](vals[0].v),
                    edgecolor="black",
                    linewidth=1,
                    label=language.name,
                    zorder=zorder
                ))
                s += angle
        if self.args.language_labels:
            self.ax.text(
                lon + self.args.markersize * self.scaling_factor + 3 * self.scaling_factor,
                lat, language.name,
                zorder=zorder + 10,
                fontsize='small')

    def add_legend(self, parameters, colormaps):
        def wrapped_label(s):
            return '\n'.join(textwrap.wrap(s, width=20))

        with_shapes = False
        if len(parameters) == 2:
            for pid, parameter in parameters.items():
                if not isinstance(parameter.domain, tuple):
                    for v, label in parameter.domain.items():
                        if colormaps[pid](v) in SHAPE_MAP:
                            with_shapes = True
                            break

        if with_shapes:
            handles = []
            for pid, parameter in parameters.items():
                handles.append(
                    Rectangle(
                        (0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0,
                        label=wrapped_label(parameter.name)))
                for v, label in parameter.domain.items():
                    color = colormaps[pid](v)
                    handles.append(
                        plt.Line2D(
                            [], [],
                            marker=SHAPE_MAP[color] if color in SHAPE_MAP else 'o',
                            color='#000000' if color in SHAPE_MAP else color,
                            linewidth=1,
                            linestyle='',
                            label=wrapped_label(label))
                    )
            self.ax.legend(
                bbox_to_anchor=(1, 1),
                handles=handles,
                loc='upper left',
            )
            return

        handles = []
        s, angle = 0, 360.0 / len(parameters)
        for pid, parameter in parameters.items():
            handles.append(Wedge(
                [-100, -100],
                self.args.markersize,
                s,
                s + angle,
                facecolor="None",
                edgecolor="black",
                label=wrapped_label(parameter.name),
                zorder=20
            ))
            if isinstance(parameter.domain, tuple):
                cbar = plt.colorbar(
                    colormaps[pid].scalar_mappable(),
                    ax=self.ax,
                    aspect=80,
                    label=parameter.name,
                    shrink=0.5,
                    pad=0.05,
                    location="bottom",
                )
                cbar.set_ticks([0.0, 1.0])
                cbar.set_ticklabels([
                    str(round(parameter.domain[0], 2)),
                    str(round(parameter.domain[1], 2))])
            else:
                for v, label in parameter.domain.items():
                    handles.append(Wedge(
                        [-100, -100],
                        self.args.markersize,
                        s,
                        s + angle,
                        facecolor=colormaps[pid](v),
                        edgecolor="black",
                        label=wrapped_label(label),
                        zorder=20
                    ))
            s += angle
        self.ax.legend(
            bbox_to_anchor=(1, 1),
            handles=handles,
            loc='upper left',
            handler_map={Wedge: HandleWedge()})
