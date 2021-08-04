"""
Map plotting with matplotlib and cartopy
"""
import textwrap

import cartopy.feature
import cartopy.crs
from matplotlib import pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.legend_handler import HandlerPatch
from PIL import Image

from .base import Map, PACIFIC_CENTERED


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


class MapPlot(Map):
    """
    A geographic map, zoomed in to the extent defined by a list of languages.
    """
    __formats__ = ['jpg', 'png', 'pdf']

    def __init__(self, languages, args):
        Map.__init__(self, languages, args)
        lats, lons = [k.lat for k in languages], [k.lon for k in languages]
        self.central_longitude = PACIFIC_CENTERED if args.pacific_centered else 0
        self.extent = [
            round(min(lons) - args.padding_left, 1) + self.central_longitude,
            round(max(lons) + args.padding_right, 1) + self.central_longitude,
            round(min(lats) - args.padding_bottom, 1),
            round(max(lats) + args.padding_top, 1)
        ]
        self.ax = None
        self.scaling_factor = 1
        self.proj = cartopy.crs.PlateCarree(central_longitude=self.central_longitude)

    def __enter__(self):
        plt.clf()
        fig = plt.figure(figsize=(self.args.width, self.args.height), dpi=self.args.dpi)
        ax = fig.add_subplot(1, 1, 1, projection=self.proj)
        ax.set_extent(self.extent, crs=self.proj)
        if not self.args.test:  # pragma: no cover
            ax.coastlines(resolution='50m')
            ax.add_feature(cartopy.feature.LAND)
            ax.add_feature(cartopy.feature.OCEAN)
            ax.add_feature(cartopy.feature.COASTLINE)
            ax.add_feature(cartopy.feature.BORDERS, linestyle=':')
            ax.add_feature(cartopy.feature.LAKES, alpha=0.5)
            ax.add_feature(cartopy.feature.RIVERS)
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

    def _lonlat(self, language):
        lat, lon = language.lat, language.lon
        if self.central_longitude:
            lon = lon - self.central_longitude
            if lon < -180:
                lon += 360
        return lon, lat

    def plot_language_marker(self,
                             language,
                             text=None,
                             marker_kw=None,
                             text_kw=None,
                             text_offset=(-0.075, -0.075)):  # pragma: no cover
        lon, lat = self._lonlat(language)
        kw = dict(color='red', markersize=self.args.markersize, zorder=4, marker='o')
        if marker_kw:
            kw.update(marker_kw)
        self.ax.plot(lon, lat, **kw)

        if text:
            kw = dict(fontsize=10, zorder=5)
            if text_kw:
                kw.update(text_kw)
            self.ax.text(lon + text_offset[0], lat + text_offset[1], text, **kw)

    def add_language(self, language, values, colormaps):
        s, angle = 0, 360.0 / len(values)
        lon, lat = self._lonlat(language)
        for pid, vals in values.items():
            self.ax.add_patch(Wedge(
                [lon, lat],
                self.args.markersize * self.scaling_factor / 2.0,
                s,
                s + angle,
                facecolor=colormaps[pid](vals[0].v),
                edgecolor="black",
                label=language.name,
            ))
            s += angle
        if self.args.language_labels:
            self.ax.text(
                lon + self.args.markersize * self.scaling_factor + 3 * self.scaling_factor,
                lat, language.name, fontsize='small')

    def add_legend(self, parameters, colormaps):
        def wrapped_label(s):
            return '\n'.join(textwrap.wrap(s, width=20))

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
                    ))
            s += angle
        self.ax.legend(
            bbox_to_anchor=(1, 1),
            handles=handles,
            loc='upper left',
            handler_map={Wedge: HandleWedge()})
