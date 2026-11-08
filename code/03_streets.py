"""Step 3: the street grid around a random sample of churches, as a rival explanation for orientation.

For a random sample of measured churches (seed 7), the OpenFreeMap vector tile at zoom 14 holding the church (and any
neighbour tile its 150 m circle reaches) is read, and the road centrelines (motorway to service roads; paths and
tracks left out) within 150 m are collected. For each church:
  road_len    metres of road within 150 m (an urban density measure)
  grid        the length-weighted dominant road direction, folded to 0..90 degrees
  grid_str    its strength (0 = roads in all directions, 1 = one direction only)
  near_brg    bearing (0..180) of the nearest road segment within 60 m, and its distance
Tiles are read into memory only. Output: WORK/streets.pkl
"""
import math, sys, random, io, time, urllib.request, json
import numpy as np, pandas as pd
import mapbox_vector_tile as mvt
from concurrent.futures import ThreadPoolExecutor
from common import *

N_SAMPLE = int(os.environ.get("CO_STREET_N", 6000))
Z = 14
ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary", "minor", "service", "busway", "raceway"}
UA = {"User-Agent": "church-orientation-study/1.0 (research; maps.tristanhotham.com)"}
tj = json.load(urllib.request.urlopen(urllib.request.Request("https://tiles.openfreemap.org/planet", headers=UA)))
URL = tj["tiles"][0]

A = pd.read_pickle(os.path.join(WORK, "churches.pkl"))
K = A[(A.ratio > MIN_RATIO) & (A.area >= MIN_AREA) & (A.area <= MAX_AREA) & ~A.nested & A.is_church_bldg]
S = K.sample(n=min(N_SAMPLE, len(K)), random_state=7)
n = 2 ** Z


def tile_xy(lon, lat):
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y


need = {}
for i, r in S.iterrows():
    dlat = 150 / 111195
    dlon = dlat / math.cos(math.radians(r.lat))
    ts = set()
    for lo in (r.lon - dlon, r.lon + dlon):
        for la in (r.lat - dlat, r.lat + dlat):
            x, y = tile_xy(lo, la)
            ts.add((int(x), int(y)))
    need[i] = ts
tiles = sorted(set().union(*need.values()))
print("sample", len(S), "tiles", len(tiles), file=sys.stderr)


def fetch(t):
    x, y = t
    for k in range(4):
        try:
            req = urllib.request.Request(URL.format(z=Z, x=x, y=y), headers=UA)
            b = urllib.request.urlopen(req, timeout=60).read()
            d = mvt.decode(b, default_options={"y_coord_down": True})
            segs = []
            lay = d.get("transportation")
            if lay:
                ext = lay["extent"]
                for f in lay["features"]:
                    if f["properties"].get("class") not in ROADS or f["geometry"]["type"] not in ("LineString", "MultiLineString"):
                        continue
                    cs = f["geometry"]["coordinates"]
                    lines = cs if f["geometry"]["type"] == "MultiLineString" else [cs]
                    for ln in lines:
                        a = np.array(ln, float)
                        lon = (x + a[:, 0] / ext) / n * 360 - 180
                        lat = np.degrees(np.arctan(np.sinh(math.pi * (1 - 2 * (y + a[:, 1] / ext) / n))))
                        segs.append(np.c_[lon, lat].astype(np.float64))
            return t, segs
        except Exception as ex:
            time.sleep(2 + 3 * k)
    print("failed", t, file=sys.stderr)
    return t, None


T = {}
t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    for j, (t, segs) in enumerate(ex.map(fetch, tiles)):
        T[t] = segs
        if j % 500 == 0:
            print(j, round(time.time() - t0), file=sys.stderr)

R = 6371008.8
out = []
for i, r in S.iterrows():
    segs = []
    ok = True
    for t in need[i]:
        if T.get(t) is None:
            ok = False
            break
        segs += T[t]
    if not ok:
        continue
    k = math.cos(math.radians(r.lat))
    L, ang, nearest = 0.0, [], (1e9, None)
    for s in segs:
        X = (s[:, 0] - r.lon) * math.radians(1) * R * k
        Y = (s[:, 1] - r.lat) * math.radians(1) * R
        for a0, b0, a1, b1 in zip(X[:-1], Y[:-1], X[1:], Y[1:]):
            dx, dy = a1 - a0, b1 - b0
            ln = math.hypot(dx, dy)
            if ln < 0.5:
                continue
            # distance from church centroid (origin) to the segment
            tpar = max(0, min(1, -(a0 * dx + b0 * dy) / (ln * ln)))
            dist = math.hypot(a0 + tpar * dx, b0 + tpar * dy)
            if dist > 150:
                continue
            brg = math.degrees(math.atan2(dx, dy)) % 180
            L += ln
            ang.append((brg, ln))
            if dist < nearest[0]:
                nearest = (dist, brg)
    if ang:
        b = np.array(ang)
        a4 = np.radians((b[:, 0] % 90) * 4)
        C, Sn = (b[:, 1] * np.cos(a4)).sum(), (b[:, 1] * np.sin(a4)).sum()
        grid = math.degrees(math.atan2(Sn, C)) / 4 % 90
        strength = math.hypot(C, Sn) / b[:, 1].sum()
    else:
        grid, strength = np.nan, np.nan
    out.append(dict(osm=r.osm, road_len=round(L, 1), grid=round(grid, 2) if ang else np.nan, grid_str=round(strength, 3) if ang else np.nan,
                    near_dist=round(nearest[0], 1) if nearest[1] is not None else np.nan,
                    near_brg=round(nearest[1], 2) if nearest[1] is not None else np.nan))
pd.DataFrame(out).to_pickle(os.path.join(WORK, "streets.pkl"))
print("done", len(out), file=sys.stderr)
