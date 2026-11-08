"""House style for the static figures: parchment paper, iron-gall ink, vermilion lettering; Britain and Ireland from
Natural Earth 1:10m in a simple plate carree stretched for latitude 54.5."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
INKFONTS = os.path.join(ROOT, "fonts", "ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
HAND = fm.FontProperties(fname=f"{INKFONTS}/MedievalSharp.ttf")
FELL = fm.FontProperties(fname=f"{INKFONTS}/IMFeENrm28P.ttf")
FELLI = fm.FontProperties(fname=f"{INKFONTS}/IMFeGPit28P.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6E604E", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E604E", "ytick.color": "#6E604E", "text.color": "#2B2119"})
PAPER, PAPER2, INK, MUT, RED, RULE, BLUE = "#F6EED8", "#F3E5BF", "#2B2119", "#6E604E", "#A3261B", "#E2D3AE", "#2F5D8C"
LANDC, SEAC = "#ECD9AC", "#DFE6E1"
from matplotlib.colors import PowerNorm
DEV_CMAP = LinearSegmentedColormap.from_list("adev", [(math.sqrt(a / 90), c) for a, c in ABS_STOPS])
DEV_NORM = PowerNorm(0.5, 0, 90)
LAT0 = 54.5


def proj(lon, lat):
    return np.asarray(lon, float) * math.cos(math.radians(LAT0)), np.asarray(lat, float)


NE10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


def basemap(ax, ext=(-8.8, 2.0, 49.8, 60.95), lw=0.6, ripple=True, ireland=True):
    ax.set_facecolor(SEAC)
    polys = []
    for f in NE10["features"]:
        if f["properties"]["ADMIN"] not in ("United Kingdom", "Ireland", "Isle of Man", "France", "Belgium", "Netherlands"):
            continue
        for r in rings(f["geometry"]):
            if r[:, 0].max() < ext[0] - 2 or r[:, 0].min() > ext[1] + 2 or r[:, 1].max() < ext[2] - 2 or r[:, 1].min() > ext[3] + 2:
                continue
            x, y = proj(r[:, 0], r[:, 1])
            polys.append(MPoly(np.c_[x, y], closed=True))
    if ripple:
        for w, a in ((6, 0.16), (3.4, 0.28)):
            ax.add_collection(PatchCollection(polys, facecolor="none", edgecolor="#6C9FD6", lw=w, alpha=a, zorder=1))
    ax.add_collection(PatchCollection(polys, facecolor=LANDC, edgecolor="none", zorder=2))
    ax.add_collection(PatchCollection(polys, facecolor="none", edgecolor=INK, lw=lw, zorder=5))
    xs, ys = proj(np.array(ext[:2]), np.array(ext[2:]))
    ax.set_xlim(*xs); ax.set_ylim(*ys)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def ticks(ax, lon, lat, bearing, dev, L=0.05, lw=0.5, alpha=0.9, z=6):
    """Each church as a short line along its axis, coloured by its deviation from east."""
    x, y = proj(lon, lat)
    b = np.radians(bearing)
    k = math.cos(math.radians(LAT0))
    dx, dy = np.sin(b) * L, np.cos(b) * L          # projected units: x already scaled by cos(LAT0), keep isotropic
    segs = np.stack([np.c_[x - dx, y - dy], np.c_[x + dx, y + dy]], axis=1)
    o = np.argsort(-np.abs(dev))                       # the truest to east drawn last, on top
    lc = LineCollection(segs[o], colors=DEV_CMAP(DEV_NORM(np.abs(dev)[o])), linewidths=lw, alpha=alpha, zorder=z, capstyle="round")
    ax.add_collection(lc)


def paper(fig):
    fig.patch.set_facecolor(PAPER)


def title(fig, t, sub=None, y=0.965, x=0.04, size=30, subsize=13.5):
    fig.text(x, y, t, fontproperties=DISP, fontsize=size, color=INK, va="top")
    if sub:
        fig.text(x, y - 0.052 * (size / 30) * (fig.get_figheight() and 8 / fig.get_figheight()), sub, fontproperties=SERP, fontsize=subsize, color=MUT, va="top")


def foot(fig, s, y=0.018, x=0.04):
    fig.text(x, y, s, fontsize=9.5, color=MUT, va="bottom")


def save(fig, path, dpi=150):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
