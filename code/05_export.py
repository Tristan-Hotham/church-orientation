"""Step 5: reusable data files and the compact page data.

data/churches.csv          every measured church: OSM id, name, position, axis, size, saint, date, period, listing, denomination
data/churches.json         the same, compact, for the map page (arrays; see KEYS)
data/saints_historic.csv   saint by saint: mean axis of the historic parish churches against the feast-day sunrise
data/groups.csv            the summary for each period, listing grade, denomination and nation
data/places.json           towns and villages for the page search (Wikidata, CC0)
"""
import csv, re
import numpy as np, pandas as pd
from common import *

R = jload(os.path.join(DATA, "results.json"))
K = pd.read_pickle(os.path.join(WORK, "measured.pkl"))
Fz = pd.read_pickle(os.path.join(WORK, "feast.pkl"))
K = K.merge(Fz.drop(columns="foffset"), on=["osm", "saint"], how="left")
F = pd.read_csv(os.path.join(ROOT, "code", "feasts.csv"))
FEAST = {r.saint: "%d %s" % (r.day, ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                                     "November", "December"][r.month]) for r in F.itertuples()}
K["feast"] = K.saint.map(FEAST)
GR = {"I": "Grade I", "II*": "Grade II*", "II": "Grade II", "A": "Category A", "B": "Category B", "C": "Category C",
      "NI A": "Grade A (NI)", "NI B+": "Grade B+ (NI)", "NI B": "Grade B (NI)", "SM": "Scheduled monument", "": ""}
out = K[["osm", "display_name", "lon", "lat", "bearing", "dev", "edge_bearing", "length", "width", "ratio", "area", "building", "denom", "dgroup",
         "saint", "saint_src", "feast", "pred", "foffset", "year", "period", "grade", "old", "qid", "wd_join", "nation"]].copy()
out = out.rename(columns={"display_name": "name", "pred": "feast_sunrise_az", "foffset": "julian_days_added", "dgroup": "denom_group"})
out["bearing"] = out.bearing.round(1)
out["dev"] = out.dev.round(1)
out["feast_sunrise_az"] = out.feast_sunrise_az.round(1)
out["osm_url"] = "https://www.openstreetmap.org/" + out.osm.str[0].map({"w": "way", "r": "relation"}) + "/" + out.osm.str[1:]
out.to_csv(os.path.join(DATA, "churches.csv"), index=False, quoting=csv.QUOTE_MINIMAL)

# compact page data
PER = ["medieval", "early", "victorian", "modern", "unknown"]
DEN = list(DNAME)
GRL = ["I", "II*", "II", "A", "B", "C", "NI A", "NI B+", "NI B", "SM", ""]
top = K.saint.value_counts()
SAINTS = sorted(top[top >= 1].index.tolist(), key=lambda s: -top[s])
si = {s: i for i, s in enumerate(SAINTS)}
rows = []
for r in K.itertuples():
    rows.append([round(r.lon, 5), round(r.lat, 5), round(r.bearing, 2), round(r.length), round(r.width), PER.index(r.period), DEN.index(r.dgroup),
                 si.get(r.saint, -1) if isinstance(r.saint, str) else -1, GRL.index(r.grade) if r.grade in GRL else 10, r.display_name or "",
                 r.osm, r.qid or "", int(r.year) if not np.isnan(r.year) else 0, round(r.pred, 1) if not np.isnan(r.pred) else -1, int(r.old)])
KEYS = ["lon", "lat", "bearing", "length", "width", "period", "denom", "saint", "grade", "name", "osm", "qid", "year", "feast_sunrise_az", "old"]
feasts = {s: FEAST.get(s, "") for s in SAINTS}
jsave({"keys": KEYS, "periods": [PNAME[p] for p in PER], "denoms": [DNAME[d] for d in DEN], "grades": [GR[g] for g in GRL],
       "saints": SAINTS, "feasts": [feasts[s] for s in SAINTS], "rows": rows}, os.path.join(DATA, "churches.json"))

pd.DataFrame(R["saints_old"]).rename(columns={"pred": "feast_sunrise_az_julian_adjusted", "pred_gregorian": "feast_sunrise_az_as_written",
                                               "se": "se_mean_bearing"}).to_csv(os.path.join(DATA, "saints_historic.csv"), index=False)
g = []
for key, lab in [("by_period", "period"), ("by_grade", "listing"), ("by_denom", "denomination"), ("by_nation", "nation")]:
    for k, v in R[key].items():
        if v.get("n"):
            g.append({"grouping": lab, "group": k, **v})
pd.DataFrame(g).to_csv(os.path.join(DATA, "groups.csv"), index=False)

# places for search: Wikidata UK settlements with a population of 1,000 or more, plus every settlement name once
P = []
with open(os.path.join(RAW, "uk_settlements.tsv"), encoding="utf-8") as f:
    rd = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    next(rd)
    for x in rd:
        m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", x[2])
        if not m:
            continue
        nm = x[1].split('"@')[0].strip('"')
        try:
            pop = float(x[3].split("^^")[0].strip('"')) if x[3] else 0
        except ValueError:
            pop = 0
        P.append((nm, round(float(m.group(1)), 4), round(float(m.group(2)), 4), pop))
Pd = pd.DataFrame(P, columns=["n", "lon", "lat", "pop"]).sort_values("pop", ascending=False).drop_duplicates(["n", "lon", "lat"])
Pd = Pd[(Pd.lon > -9) & (Pd.lon < 2) & (Pd.lat > 49.8) & (Pd.lat < 61)]
Pd = Pd.drop_duplicates("n").head(12000)
jsave([[r.n, r.lon, r.lat] for r in Pd.itertuples()], os.path.join(DATA, "places.json"))
print("churches", len(rows), "saints", len(SAINTS), "places", len(Pd))
