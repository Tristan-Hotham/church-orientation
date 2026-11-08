"""Step 4: the analysis. Every number quoted anywhere comes from data/results.json, written here.

Definitions
  bearing   axis of the long side of the footprint, degrees from true north, folded to 0..180 (the east end).
  dev       bearing - 90: 0 is due east, negative turns the east end north (towards midsummer sunrise), positive south.
  old       the historic parish churches: dated before 1540, or (undated) listed Grade I or II* in England and Wales or
            category A in Scotland, of the Church of England, in Wales, of Scotland, Episcopal or with no denomination tagged.
Feast-day test
  For each church with a saint in code/feasts.csv, the predicted azimuth is sunrise over a flat horizon (altitude 0,
  no refraction) at the church's latitude on the feast day. Medieval feasts were kept in the Julian calendar: for churches
  dated before 1753 the Julian date is moved to the Gregorian date of that year (7 days in 1100 to 1299, 8 in 1300 to
  1399, 9 in 1400 to 1499, 10 in 1500 to 1699, 11 in 1700 to 1752); undated old churches are taken as founded c. 1200
  (7 days). Later churches use the date as written. The statistic is the mean absolute difference between axis and
  predicted sunrise; its null distribution comes from 10,000 random shuffles of the saints among the same churches.
"""
import sys, math
import numpy as np, pandas as pd
from common import *

rng = np.random.default_rng(2026)
A = pd.read_pickle(os.path.join(WORK, "churches.pkl"))
R = {"meta": {"slug": SLUG}}
R["n"] = {"polygons": len(A), "polygons_church_tag": int((A.src == "church").sum()), "polygons_pow": int((A.src == "pow").sum()),
          "nested": int(A.nested.sum()), "not_church_building": int((~A.is_church_bldg).sum())}
K = A[A.is_church_bldg & ~A.nested].copy()
R["n"]["candidates"] = len(K)
R["n"]["too_square"] = int((K.ratio <= MIN_RATIO).sum())
R["n"]["too_small"] = int(((K.ratio > MIN_RATIO) & (K.area < MIN_AREA)).sum())
R["n"]["too_big"] = int(((K.ratio > MIN_RATIO) & (K.area > MAX_AREA)).sum())
K = K[(K.ratio > MIN_RATIO) & (K.area >= MIN_AREA) & (K.area <= MAX_AREA)].copy()
R["n"]["measured"] = len(K)
R["n"]["wikidata_joined"] = int((K.qid != "").sum())
R["n"]["with_saint"] = int(K.saint.notna().sum())
R["n"]["dated"] = int((K.period != "unknown").sum())
R["n"]["rect_edge_agree_2deg"] = round(100 * float(((K.bearing - K.edge_bearing + 90) % 180 - 90).abs().lt(2).mean()), 1)
K["dev"] = K.bearing - 90
K["adev"] = K.dev.abs()
K["nation"] = np.where(K.grade.isin(["A", "B", "C"]), "Scotland", "")  # refined below by position
# nations by rough position for reporting (Wales and Scotland by Natural Earth admin-1)
import geopandas as gpd
adm = gpd.read_file(os.path.join(GEO, "ne_10m_admin_1_states_provinces.geojson")) if os.path.exists(os.path.join(GEO, "ne_10m_admin_1_states_provinces.geojson")) else None
if adm is not None:
    adm = adm[adm.adm0_a3 == "GBR"][["geonunit", "geometry"]]
    pts = gpd.GeoDataFrame(K[["osm"]], geometry=gpd.points_from_xy(K.lon, K.lat), crs=4326)
    j = gpd.sjoin(pts, adm, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    K["nation"] = j.geonunit.reindex(K.index).fillna("")
    # coastal points outside the generalised polygons: nearest
    miss = K.nation == ""
    if miss.any():
        jn = gpd.sjoin_nearest(pts[miss.values].to_crs(27700), adm.to_crs(27700), how="left")
        jn = jn[~jn.index.duplicated()]
        K.loc[miss, "nation"] = jn.geonunit.values
R["n"]["by_nation"] = K.nation.value_counts().to_dict()


def summ(d):
    if len(d) == 0:
        return {"n": 0}
    e = d[d.adev <= 45]
    return {"n": int(len(d)), "within5": round(100 * float((d.adev <= 5).mean()), 1), "within10": round(100 * float((d.adev <= 10).mean()), 1),
            "within20": round(100 * float((d.adev <= 20).mean()), 1), "beyond45": round(100 * float((d.adev > 45).mean()), 1),
            "median_adev": round(float(d.adev.median()), 1), "mean_dev_eastish": round(float(e.dev.mean()), 1),
            "sd_dev_eastish": round(float(e.dev.std()), 1), "north_of_east": round(100 * float((e.dev < 0).mean()), 1)}


R["all"] = summ(K)
hist = np.histogram(K.bearing, bins=36, range=(0, 180))[0]
R["hist_all"] = hist.tolist()

# ---- groups
OLDDEN = K.dgroup.isin(["anglican", "scotland", "unknown"])
OLDGR = K.grade.isin(["I", "II*", "A"])
K["old"] = OLDDEN & ((K.period == "medieval") | ((K.period == "unknown") & OLDGR))
R["old"] = summ(K[K.old])
R["by_period"] = {p: summ(K[K.period == p]) for p in list(PNAME)}
R["by_grade"] = {g: summ(K[K.grade == g]) for g in ["I", "II*", "II", "A", "B", "C"]}
R["by_grade"]["none"] = summ(K[K.grade == ""])
R["by_denom"] = {d: summ(K[K.dgroup == d]) for d in DNAME}
R["by_denom_victorian_modern"] = {d: summ(K[(K.dgroup == d) & K.period.isin(["victorian", "modern"])]) for d in DNAME}
R["by_nation"] = {n: summ(K[K.nation == n]) for n in ["England", "Wales", "Scotland", "Northern Ireland"]}
R["by_src"] = {s: summ(K[K.src == s]) for s in ["church", "pow"]}
R["hist_old"] = np.histogram(K[K.old].bearing, bins=36, range=(0, 180))[0].tolist()
R["hist_modern"] = np.histogram(K[K.period.isin(["victorian", "modern"])].bearing, bins=36, range=(0, 180))[0].tolist()
R["hist_nonconf"] = np.histogram(K[K.dgroup.isin(["nonconformist", "catholic"])].bearing, bins=36, range=(0, 180))[0].tolist()

# ---- west to east across England and Wales (Hinton 2006 reports a difference of about 10 degrees)
O = K[K.old & (K.adev <= 45) & K.nation.isin(["England", "Wales"])]
bands = np.arange(-6, 2.5, 1.0)
lon_t = []
for a in bands:
    s = O[(O.lon >= a) & (O.lon < a + 1)]
    if len(s) >= 30:
        lon_t.append({"lon": float(a + 0.5), "n": int(len(s)), "mean_dev": round(float(s.dev.mean()), 1), "median_dev": round(float(s.dev.median()), 1)})
R["by_longitude_old"] = lon_t
c = np.polyfit(O.lon, O.dev, 1)
R["lon_slope_old"] = {"deg_per_deg_lon": round(float(c[0]), 2), "n": int(len(O)), "r": round(float(np.corrcoef(O.lon, O.dev)[0, 1]), 3),
                      "west_mean": round(float(O[O.lon < -3].dev.mean()), 1), "east_mean": round(float(O[O.lon >= 0].dev.mean()), 1),
                      "n_west": int((O.lon < -3).sum()), "n_east": int((O.lon >= 0).sum())}

# ---- feast-day test
F = pd.read_csv(os.path.join(ROOT, "code", "feasts.csv"))
FD = {r.saint: (int(r.month), int(r.day)) for r in F.itertuples()}


def doy(m, d):
    return (pd.Timestamp(2001, m, d).dayofyear)


def found_year(r):
    if r.old and np.isnan(r.year):
        return 1200
    return None if np.isnan(r.year) else int(r.year)


def offset(r):
    y = found_year(r)
    if y is None or y >= 1753:
        return 0
    return julian_offset(y)


K["foffset"] = [offset(r) for r in K.itertuples()]


def pred_az(lat, m, d, off):
    return sunrise_az(lat, declination(((doy(m, d) + off - 1) % 365) + 1))


S = K[K.saint.isin(FD)].copy()
S["pred"] = [pred_az(la, *FD[s], o) for la, s, o in zip(S.lat, S.saint, S.foffset)]
S["err"] = S.bearing - S.pred


def feast_test(d, nperm=10000, label=""):
    d = d.reset_index(drop=True)
    obs = float(np.abs(d.bearing - d.pred).mean())
    w3 = float((np.abs(d.bearing - d.pred) <= 3).mean())
    b = d.bearing.values
    # shuffle saints: permute feast (month, day) among churches, recompute prediction with each church's own latitude and offset
    md = np.array([FD[s] for s in d.saint])
    lat, off = d.lat.values, d.foffset.values
    # precompute declination by day of year
    decl = np.array([declination(i) for i in range(1, 367)])
    dd = np.array([doy(m, dy) for m, dy in md])
    perm = np.empty(nperm)
    w3p = np.empty(nperm)
    phi = np.radians(lat)
    for k in range(nperm):
        p = rng.permutation(len(d))
        dy = (dd[p] + off - 1) % 365
        de = np.radians(decl[dy])
        az = np.degrees(np.arccos(np.clip(np.sin(de) / np.cos(phi), -1, 1)))
        e = np.abs(b - az)
        perm[k] = e.mean()
        w3p[k] = (e <= 3).mean()
    return {"label": label, "n": int(len(d)), "n_saints": int(d.saint.nunique()), "mean_abs_err": round(obs, 2),
            "perm_mean": round(float(perm.mean()), 2), "perm_p05": round(float(np.percentile(perm, 5)), 2),
            "p_value": round(float((1 + (perm <= obs).sum()) / (1 + nperm)), 4),
            "within3": round(100 * w3, 1), "within3_perm": round(100 * float(w3p.mean()), 1),
            "within3_perm_p95": round(100 * float(np.percentile(w3p, 95)), 1),
            "east_mean_abs_err": round(float(np.abs(d.bearing - 90).mean()), 2)}


R["feast"] = {"all": feast_test(S, label="all churches with a fixed-feast saint"),
              "old": feast_test(S[S.old], label="historic parish churches"),
              "medieval_dated": feast_test(S[S.period == "medieval"], label="dated before 1540"),
              "victorian_modern": feast_test(S[S.period.isin(["victorian", "modern"])], label="dated 1800 onwards")}

# saint by saint (historic parish churches): mean axis vs predicted sunrise
rows = []
for s, g in S[S.old].groupby("saint"):
    if len(g) < 25:
        continue
    e = g[(g.bearing > 45) & (g.bearing < 135)]
    rows.append({"saint": s, "feast": "%02d-%02d" % FD[s], "n": int(len(g)), "mean_bearing": round(float(e.bearing.mean()), 1),
                 "se": round(float(e.bearing.std() / math.sqrt(len(e))), 2), "pred": round(float(g.pred.mean()), 1),
                 "pred_gregorian": round(float(np.mean([pred_az(la, *FD[s], 0) for la in g.lat])), 1)})
SS = pd.DataFrame(rows).sort_values("pred")
R["saints_old"] = SS.to_dict("records")
cc = np.polyfit(SS.pred, SS.mean_bearing, 1, w=1 / SS.se)
R["saint_regression"] = {"n_saints": int(len(SS)), "n_churches": int(SS.n.sum()), "slope": round(float(cc[0]), 3),
                         "r": round(float(np.corrcoef(SS.pred, SS.mean_bearing)[0, 1]), 3),
                         "pred_range": [round(float(SS.pred.min()), 1), round(float(SS.pred.max()), 1)],
                         "obs_range": [round(float(SS.mean_bearing.min()), 1), round(float(SS.mean_bearing.max()), 1)]}
# summer vs winter saints among historic churches
sm = S[S.old & S.saint.isin(["John the Baptist", "Peter", "Peter and Paul", "Botolph", "Alban", "Etheldreda", "Barnabas"])]
wn = S[S.old & S.saint.isin(["Thomas", "Nicholas", "John the Evangelist", "Stephen", "Thomas Becket", "Andrew", "Edmund", "Catherine", "Clement"])]
smE, wnE = sm[sm.adev <= 45], wn[wn.adev <= 45]
R["summer_winter"] = {"summer_n": int(len(smE)), "summer_mean_bearing": round(float(smE.bearing.mean()), 1), "summer_pred": round(float(sm.pred.mean()), 1),
                      "winter_n": int(len(wnE)), "winter_mean_bearing": round(float(wnE.bearing.mean()), 1), "winter_pred": round(float(wn.pred.mean()), 1)}
R["summer_winter"]["summer_n_all"], R["summer_winter"]["winter_n_all"] = int(len(sm)), int(len(wn))   # all bearings, as in the collage roses
R["summer_winter"]["obs_gap"] = round(R["summer_winter"]["winter_mean_bearing"] - R["summer_winter"]["summer_mean_bearing"], 1)
R["summer_winter"]["pred_gap"] = round(R["summer_winter"]["winter_pred"] - R["summer_winter"]["summer_pred"], 1)
# Welch t test of the gap
from scipy import stats
t = stats.ttest_ind(wnE.bearing, smE.bearing, equal_var=False)
R["summer_winter"]["p"] = float("%.3g" % t.pvalue)

# Mary: which of her feasts fits best, if any
mary = K[K.old & (K.saint == "Mary") & (K.adev <= 45)]
mf = {}
for nm, (m, d) in {"Purification (2 Feb)": (2, 2), "Annunciation (25 Mar)": (3, 25), "Assumption (15 Aug)": (8, 15), "Nativity of Mary (8 Sep)": (9, 8)}.items():
    p = np.array([pred_az(la, m, d, o) for la, o in zip(mary.lat, mary.foffset)])
    mf[nm] = {"pred": round(float(p.mean()), 1)}
R["mary"] = {"n": int(len(mary)), "mean_bearing": round(float(mary.bearing.mean()), 1), "feasts": mf}

# Equinox and Easter: where does the average old church actually point?
R["old_mean_bearing"] = round(float(K[K.old & (K.adev <= 45)].bearing.mean()), 1)
R["old_median_bearing"] = round(float(K[K.old & (K.adev <= 45)].bearing.median()), 1)

# ---- street grid (sample)
sp = os.path.join(WORK, "streets.pkl")
if os.path.exists(sp):
    T = pd.read_pickle(sp).merge(K[["osm", "bearing", "dev", "adev", "period", "dgroup", "old"]], on="osm")
    T = T[T.grid.notna()]
    fold = lambda x: np.abs((x + 45) % 90 - 45)        # angular difference folded to 0..45 (parallel or square to)
    T["d_grid"] = fold(T.bearing - T.grid)
    T["d_east"] = fold(T.bearing - 90)
    T["d_near"] = np.where(T.near_dist <= 40, fold(T.bearing - T.near_brg), np.nan)
    T["grid_vs_east"] = fold(T.grid - 90)
    T["urban"] = T.road_len >= 2000
    R["streets_sample"] = {"n": int(len(T)), "urban_threshold_m": 2000, "radius_m": 150}

    def st(d):
        dist = d[d.grid_vs_east >= 15]            # street grid clearly not east-west
        return {"n": int(len(d)), "median_d_grid": round(float(d.d_grid.median()), 1), "median_d_east": round(float(d.d_east.median()), 1),
                "grid_within5": round(100 * float((d.d_grid <= 5).mean()), 1), "east_within5": round(100 * float((d.d_east <= 5).mean()), 1),
                "n_distinct": int(len(dist)), "closer_to_grid": round(100 * float((dist.d_grid < dist.d_east).mean()), 2) if len(dist) else None,
                "near_within5": round(100 * float((d.d_near.dropna() <= 5).mean()), 1)}
    R["streets"] = {"urban": st(T[T.urban]), "rural": st(T[~T.urban]),
                    "urban_old": st(T[T.urban & T.old]), "urban_victorian_modern": st(T[T.urban & T.period.isin(["victorian", "modern"])]),
                    "urban_nonconf_catholic": st(T[T.urban & T.dgroup.isin(["nonconformist", "catholic"])]),
                    "urban_anglican": st(T[T.urban & (T.dgroup == "anglican")]),
                    "all": st(T)}
    R["streets"]["urban_east_vs_rural"] = {"urban": summ(K[K.osm.isin(T[T.urban].osm)]), "rural": summ(K[K.osm.isin(T[~T.urban].osm)])}
    T[["osm", "road_len", "grid", "grid_str", "near_dist", "near_brg", "d_grid", "d_east", "d_near", "urban"]].to_csv(
        os.path.join(DATA, "street_grid_sample.csv"), index=False)

# ---- examples
G1 = K[K.grade.isin(["I", "A"]) & (K.display_name != "")]
ex = G1.sort_values("adev", ascending=False).head(40)
R["examples_far_old"] = [{"name": r.display_name, "bearing": round(r.bearing, 1), "dev": round(r.dev, 1), "lon": r.lon, "lat": r.lat,
                          "osm": r.osm, "qid": r.qid} for r in ex.itertuples()]
R["n"]["exactly_east_1deg"] = int((K.adev <= 1).sum())
# ---- derived values quoted in words
R["chance10"] = round(100 * 20 / 180, 1)              # a random axis lies within 10 degrees of east
R["min_ratio"], R["min_area"], R["max_area"] = MIN_RATIO, int(MIN_AREA), int(MAX_AREA)
R["old"]["mean_dev_eastish_abs"] = abs(R["old"]["mean_dev_eastish"])
R["summer_winter"]["obs_gap_abs"] = abs(R["summer_winter"]["obs_gap"])
R["saint_regression"]["pred_span"] = round(R["saint_regression"]["pred_range"][1] - R["saint_regression"]["pred_range"][0], 1)
R["saint_regression"]["obs_span"] = round(R["saint_regression"]["obs_range"][1] - R["saint_regression"]["obs_range"][0], 1)
R["lon_slope_old"]["west_mean_abs"] = abs(R["lon_slope_old"]["west_mean"])
R["lon_east_band"] = R["by_longitude_old"][-1]
R["mary"]["closest_feast"] = min(R["mary"]["feasts"], key=lambda k: abs(R["mary"]["feasts"][k]["pred"] - R["mary"]["mean_bearing"]))
K.to_pickle(os.path.join(WORK, "measured.pkl"))
S[["osm", "saint", "pred", "err", "foffset"]].to_pickle(os.path.join(WORK, "feast.pkl"))
jsave(R, os.path.join(DATA, "results.json"), indent=1)
print(json.dumps({k: R[k] for k in ["n", "all", "old", "feast", "saint_regression", "summer_winter", "lon_slope_old", "mary", "old_mean_bearing"]}, indent=1))
print(json.dumps(R["by_period"], indent=0)); print(json.dumps(R["by_denom"], indent=0)); print(json.dumps(R.get("streets"), indent=0))
