"""Step 1: measure the long axis of every church footprint in OpenStreetMap.

For each polygon: project to a local true-north metric frame (equirectangular about the polygon's centroid, which keeps
north up and is exact enough over 100 m), take the minimum-area rotated rectangle, and record the bearing of its long
side folded into 0 to 180 degrees (the end between north through east to south is taken as the east end), its length,
width, ratio and area. A second, independent estimate weights every polygon edge by its length and takes the
dominant direction (folded to 90 degrees) nearest the rectangle's axis; the two agree for clean footprints and the
difference is kept as a quality flag.
Output: WORK/axes.pkl
"""
import csv, sys, math
import numpy as np, pandas as pd
from shapely import wkt as W
from shapely.geometry import Polygon, MultiPolygon
from common import *

csv.field_size_limit(10**9)
R = 6371008.8


def read(path, src):
    rows = []
    with open(path, encoding="utf-8") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(r)
        for x in r:
            x = [v.strip('"') if v.startswith('"') else v for v in x]
            url = x[0].strip("<>")
            typ, oid = url.split("/")[-2:]
            g = x[8]
            if g.startswith("POINT"):
                continue
            g = g.split('"^^')[0].strip('"')
            rows.append(dict(osm=typ[0] + oid, src=src, building=x[1], name=x[2], dedication=x[3], denom=x[4],
                             heritage=x[5], start=x[6], wikidata=x[7], wkt=g))
    return rows


def unq(v):
    return v[:v.rfind('"')] if v.endswith('"') else v


rows = read(OSM_CH, "church") + read(OSM_POW, "pow")
print("polygons read", len(rows), file=sys.stderr)


def largest(g):
    if isinstance(g, Polygon):
        return g
    polys = []
    if hasattr(g, "geoms"):
        for p in g.geoms:
            if isinstance(p, Polygon):
                polys.append(p)
            elif isinstance(p, MultiPolygon):
                polys += list(p.geoms)
            elif p.geom_type == "LineString" and p.is_ring:
                polys.append(Polygon(p.coords))
    return max(polys, key=lambda p: p.area) if polys else None


def axis_of(poly):
    lon0, lat0 = poly.centroid.x, poly.centroid.y
    k = math.cos(math.radians(lat0))
    xy = np.array(poly.exterior.coords)
    X = (xy[:, 0] - lon0) * math.radians(1) * R * k
    Y = (xy[:, 1] - lat0) * math.radians(1) * R
    P = Polygon(np.c_[X, Y])
    if not P.is_valid:
        P = P.buffer(0)
        if P.geom_type != "Polygon":
            P = largest(P)
    area = P.area
    rect = P.minimum_rotated_rectangle
    c = np.array(rect.exterior.coords)[:4]
    e1, e2 = c[1] - c[0], c[2] - c[1]
    l1, l2 = np.hypot(*e1), np.hypot(*e2)
    e, L, Wd = (e1, l1, l2) if l1 >= l2 else (e2, l2, l1)
    brg = math.degrees(math.atan2(e[0], e[1])) % 180          # bearing from north, folded to 0..180
    # edge-weighted dominant direction, folded mod 90 so that both walls of a rectangle agree
    dx, dy = np.diff(X), np.diff(Y)
    ln = np.hypot(dx, dy)
    a4 = np.radians((np.degrees(np.arctan2(dx, dy)) % 90) * 4)   # x4 maps mod-90 to a full circle
    m = math.degrees(math.atan2((ln * np.sin(a4)).sum(), (ln * np.cos(a4)).sum())) / 4 % 90
    # unfold to the candidate nearest the rectangle bearing
    cands = [m + 90 * j for j in range(-2, 3)]
    eb = min(cands, key=lambda v: abs(v - brg))
    return dict(lon=round(lon0, 6), lat=round(lat0, 6), length=round(L, 1), width=round(Wd, 1), ratio=round(L / max(Wd, 0.1), 3),
                area=round(area, 1), rect_fill=round(area / max(rect.area, 1e-6), 3), bearing=round(brg, 2), edge_bearing=round(eb % 180, 2),
                verts=len(xy) - 1)


out = []
bad = 0
for r in rows:
    try:
        g = W.loads(r.pop("wkt"))
        p = largest(g)
        if p is None or p.is_empty:
            bad += 1
            continue
        r.update(axis_of(p))
        r["geom"] = p.wkb
        out.append(r)
    except Exception as ex:
        bad += 1
print("measured", len(out), "failed", bad, file=sys.stderr)
df = pd.DataFrame(out)

# Deduplicate: drop polygons whose centroid lies inside another, larger polygon (a chapel mapped inside a cathedral,
# a relation and its outer way), keeping the largest.
import shapely
from shapely.strtree import STRtree
geoms = [shapely.from_wkb(b) for b in df.geom]
tree = STRtree(geoms)
cent = shapely.points(df.lon.values, df.lat.values)
order = np.argsort(-df.area.values)
drop = np.zeros(len(df), bool)
pairs = tree.query(cent, predicate="within")   # [point index, polygon index]
for i, j in zip(*pairs):
    if i != j and df.area.values[j] > df.area.values[i] * 0.999 and not (df.area.values[j] == df.area.values[i] and j > i):
        drop[i] = True
df["nested"] = drop
print("nested or duplicate", int(drop.sum()), file=sys.stderr)
df.drop(columns="geom").to_pickle(os.path.join(WORK, "axes.pkl"))
# keep simplified outlines of the measured buildings for the zoomed-in map
df[["osm", "geom"]].to_pickle(os.path.join(WORK, "geoms.pkl"))
