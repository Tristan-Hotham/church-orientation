"""Step 2: attach names, saints, dates, listing and denomination to every measured footprint.

Wikidata items are joined to footprints in three ways, in order: the footprint's own wikidata tag; the item's OSM way id
(P10689); and, for items not yet joined, the item's coordinates falling inside a footprint (or within 15 m of exactly
one). The patron saint comes from Wikidata (P825), else the OSM dedication tag, else the name, parsed with the
saints-geography parser (saints.py). The date is the earliest of the OSM start_date and the Wikidata inception.
Output: WORK/churches.pkl
"""
import re, csv, sys
import numpy as np, pandas as pd, shapely
from shapely.strtree import STRtree
from common import *
from saints import saint as parse_saint

A = pd.read_pickle(os.path.join(WORK, "axes.pkl"))
G = pd.read_pickle(os.path.join(WORK, "geoms.pkl"))
assert (A.osm.values == G.osm.values).all()

# ---- footprints that are not church buildings (houses, schools, offices used for worship) are left out
KEEP_POW = {"yes", "place_of_worship", "religious", "kingdom_hall", "temple", "yes;church", "church;yes", "meeting_house",
            "gospel_hall", "cemetery_chapel", "abbey", "monastery", "convent", "ruins", "heritage", "yes;chapel"}
A["is_church_bldg"] = (A.src == "church") | A.building.isin(KEEP_POW)

# ---- Wikidata
rows = []
with open(WD, encoding="utf-8") as f:
    r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    next(r)
    for x in r:
        x += [""] * (8 - len(x))
        lab = lambda v: v.split('"@')[0].strip('"') if v else ""
        m = re.match(r"POINT\(([-\d.]+) ([-\d.]+)\)", x[2])
        if not m:
            continue
        rows.append(dict(qid=x[0].rsplit("/", 1)[-1].strip(">"), wlabel=lab(x[1]), wlon=float(m.group(1)), wlat=float(m.group(2)),
                         wsaint=lab(x[4]), osmw=x[5].strip('"'), inc=(re.match(r'"?\+?(-?\d{1,4})-', x[6]).group(1) if re.match(r'"?\+?(-?\d{1,4})-', x[6]) else ""), her=lab(x[7])))
W = pd.DataFrame(rows)
GRADE = [("Grade I listed building", "I"), ("Grade II* listed building", "II*"), ("Grade II listed building", "II"),
         ("category A listed building", "A"), ("category B listed building", "B"), ("category C listed building", "C"),
         ("Grade A listed building", "NI A"), ("Grade B+ listed building", "NI B+"), ("Grade B1 listed building", "NI B"),
         ("Grade B2 listed building", "NI B"), ("Grade B listed building", "NI B"), ("scheduled monument", "SM")]
GR = dict(GRADE)
GORDER = [g for _, g in GRADE]


def agg(g):
    yrs = [int(v) for v in g.inc if re.fullmatch(r"-?\d{1,4}", v or "")]
    grades = sorted({GR[h] for h in g.her if h in GR}, key=GORDER.index)
    saints = sorted({s for s in g.wsaint if s})
    return pd.Series(dict(wlabel=g.wlabel.iloc[0], wlon=g.wlon.iloc[0], wlat=g.wlat.iloc[0], osmw=next((v for v in g.osmw if v), ""),
                          inc=min(yrs) if yrs else np.nan, grade=grades[0] if grades else "", wsaint="; ".join(saints)))


W = W.groupby("qid", sort=False).apply(agg, include_groups=False).reset_index()
print("wikidata items", len(W), file=sys.stderr)

A["qid"] = A.wikidata.where(A.wikidata.str.match(r"^Q\d+$"), "")
by_way = {("w" + v): q for q, v in zip(W.qid, W.osmw) if v}
m2 = A.osm.map(by_way)
A.loc[(A.qid == "") & m2.notna(), "qid"] = m2
joined = set(A.qid[A.qid != ""])
rest = W[~W.qid.isin(joined)]
geoms = shapely.from_wkb(G.geom.values)
tree = STRtree(geoms)
pts = shapely.points(rest.wlon.values, rest.wlat.values)
pi, gi = tree.query(pts, predicate="within")
hit = pd.DataFrame(dict(q=rest.qid.values[pi], g=gi))
# within 15 m (about 0.00014 degrees lat) when the point is outside every footprint
inside = set(pi)
out = np.array([i for i in range(len(rest)) if i not in inside])
if len(out):
    pj, gj = tree.query(pts[out], predicate="dwithin", distance=0.00018)
    cnt = pd.Series(pj).value_counts()
    one = np.isin(pj, cnt[cnt == 1].index)
    hit = pd.concat([hit, pd.DataFrame(dict(q=rest.qid.values[out[pj[one]]], g=gj[one]))])
hit = hit.drop_duplicates("g", keep=False)               # a footprint claimed by two items stays unjoined
hit = hit[A.qid.values[hit.g.values] == ""]
A.loc[A.index[hit.g.values], "qid"] = hit.q.values
A["wd_join"] = np.where(A.wikidata.str.match(r"^Q\d+$"), "tag", np.where(m2.notna(), "P10689", np.where(A.qid != "", "spatial", "")))
A = A.merge(W[["qid", "wlabel", "inc", "grade", "wsaint"]], on="qid", how="left")
print("footprints joined to Wikidata", (A.qid != "").sum(), A.wd_join.value_counts().to_dict(), file=sys.stderr)


# ---- dates
def start_year(s):
    if not isinstance(s, str) or not s:
        return np.nan
    s = s.lower()
    m = re.search(r"(?<!\d)(\d{3,4})(?!\d)", s)
    c = re.search(r"c(\d{1,2})(?!\d)|(\d{1,2})(?:th|st|nd|rd) century", s)
    ys = []
    if m:
        ys.append(int(m.group(1)))
    if c:
        n = int(c.group(1) or c.group(2))
        ys.append((n - 1) * 100 + 50)
    return min(ys) if ys else np.nan


A["start_y"] = A.start.map(start_year)
A["year"] = A[["start_y", "inc"]].min(axis=1)
A.loc[(A.year < 400) | (A.year > 2026), "year"] = np.nan


def period(y):
    if np.isnan(y):
        return "unknown"
    for k, _, a, b in PERIODS:
        if a <= y <= b:
            return k
    return "unknown"


A["period"] = A.year.map(period)


# ---- denomination
def denom(d, name):
    d = (d or "").lower()
    if d in DENOMS:
        return DENOMS[d]
    if d:
        return "other"
    n = (name or "").lower()
    for k, g in [("methodist", "nonconformist"), ("baptist", "nonconformist"), ("united reformed", "nonconformist"),
                 ("congregational", "nonconformist"), ("salvation army", "nonconformist"), ("quaker", "nonconformist"),
                 ("friends meeting", "nonconformist"), ("chapel", None), ("catholic", "catholic"), ("parish church", None),
                 ("kingdom hall", "other"), ("orthodox", "orthodox")]:
        if k in n and g:
            return g
    return "unknown"


A["dgroup"] = [denom(d, n) for d, n in zip(A.denom, A.name)]

# ---- saint: Wikidata P825, else OSM dedication, else the name
WD_MAP = {"Mary": "Mary", "Virgin Mary": "Mary", "Blessed Virgin Mary": "Mary", "All Saints": "All Saints", "Saint Peter": "Peter",
          "Paul the Apostle": "Paul", "Michael": "Michael", "Saint Michael": "Michael", "Andrew the Apostle": "Andrew",
          "John the Baptist": "John the Baptist", "John the Evangelist": "John the Evangelist", "John the Apostle": "John the Evangelist",
          "Nicholas of Myra": "Nicholas", "Saint Nicholas": "Nicholas", "Margaret the Virgin": "Margaret", "Margaret of Antioch": "Margaret",
          "James the Great": "James", "James, son of Zebedee": "James", "Lawrence of Rome": "Lawrence", "Saint Lawrence": "Lawrence",
          "Leonard of Noblac": "Leonard", "Giles": "Giles", "Saint Giles": "Giles", "Helena": "Helen", "Helena of Constantinople": "Helen",
          "Holy Trinity": "Holy Trinity", "Trinity": "Holy Trinity", "Bartholomew the Apostle": "Bartholomew", "Botolph": "Botolph",
          "Saint George": "George", "Martin of Tours": "Martin", "Luke the Evangelist": "Luke", "Mark the Evangelist": "Mark",
          "Matthew the Apostle": "Matthew", "Saint Stephen": "Stephen", "Stephen": "Stephen", "Thomas the Apostle": "Thomas",
          "Thomas Becket": "Thomas Becket", "Edmund the Martyr": "Edmund", "Oswald of Northumbria": "Oswald", "Cuthbert": "Cuthbert",
          "Chad of Mercia": "Chad", "Wilfrid": "Wilfrid", "Aidan of Lindisfarne": "Aidan", "Hilda of Whitby": "Hilda", "Saint David": "David",
          "Swithun": "Swithun", "Dunstan": "Dunstan", "Saint Alban": "Alban", "Augustine of Canterbury": "Augustine",
          "Æthelthryth": "Etheldreda", "Mary Magdalene": "Mary Magdalene", "Catherine of Alexandria": "Catherine", "Saint Anne": "Anne",
          "Pope Clement I": "Clement", "Denis of Paris": "Denys", "Saint Denis": "Denys", "Faith": "Faith", "Saint Faith": "Faith",
          "Pope Gregory I": "Gregory", "Barnabas": "Barnabas", "Jude the Apostle": "Jude", "Simon the Zealot": "Simon",
          "Philip the Apostle": "Philip", "Kenelm": "Kenelm", "Guthlac": "Guthlac", "Petroc": "Petroc", "Piran": "Piran",
          "Columba": "Columba", "Ninian": "Ninian", "Saint Mungo": "Kentigern", "Brigid of Kildare": "Bride", "Saint Patrick": "Patrick",
          "Edward the Confessor": "Edward", "Edward the Martyr": "Edward the Martyr", "Werburgh": "Werburgh", "Mildrith": "Mildred",
          "Pancras of Rome": "Pancras", "Osgyth": "Osyth", "Cedd": "Cedd", "Felix of Burgundy": "Felix", "Matthias the Apostle": "Matthias",
          "Peter and Paul": "Peter and Paul", "Saints Peter and Paul": "Peter and Paul", "Jesus Christ": "Christ", "Holy Cross": "Holy Cross",
          "True Cross": "Holy Cross", "Benedict of Nursia": "Benedict", "Olaf II of Norway": "Olave", "Saint Teilo": "Teilo",
          "Beuno": "Beuno", "Tysilio": "Tysilio", "Illtud": "Illtud", "Deiniol": "Deiniol", "Cadoc": "Cadoc", "Dyfrig": "Dyfrig",
          "Winefride": "Winefride", "Saint Non": "Non", "Saint Peter": "Peter", "All Saints' Day": "All Saints",
          "Saint James the Elder": "James", "James the Elder": "James", "John of Patmos": "John the Evangelist", "Botwulf of Thorney": "Botolph",
          "Helena Augusta": "Helen", "Denis": "Denys", "Gregory I": "Gregory", "Hilda": "Hilda", "Winifred": "Winefride",
          "Massacre of the Innocents": "Holy Innocents", "Assumption of Mary": "Mary", "Æthelberht II": "Ethelbert",
          "Saint Christopher": "Christopher", "Saint Joseph": "Joseph", "Saint Petroc": "Petroc", "Saint Boniface": "Boniface",
          "James the Less": "James the Less", "God the Holy Spirit": "Holy Spirit", "Ascension of Jesus": "Ascension",
          "Gabriel": "Gabriel", "Clement": "Clement", "Oswald of Worcester": "Oswald",  # reviewed: these Wikidata dedications are almost all northern St Oswald churches (Oswald of Northumbria), so all are reassigned
          "Augustine of Hippo": "Augustine of Hippo", "Mary, mother of Jesus": "Mary", "Kentigern": "Kentigern"}
ws = A.wsaint.fillna("")
first = ws.str.split("; ").str[0]
from_wd = first.map(lambda v: WD_MAP.get(v) or (v.replace("Saint ", "") if v else None))
pairs = {frozenset(["Peter", "Paul"]): "Peter and Paul", frozenset(["Philip", "James"]): "Philip and James",
         frozenset(["Simon", "Jude"]): "Simon and Jude"}
for i, v in ws.items():
    if "; " in v:
        parts = frozenset(WD_MAP.get(p, p) for p in v.split("; "))
        from_wd[i] = pairs.get(parts, from_wd[i])
from_name = [parse_saint(n, d or None) for n, d in zip(A.name, A.dedication)]
A["saint"] = [w if isinstance(w, str) and w else n for w, n in zip(from_wd, from_name)]
A["saint_src"] = np.where(from_wd.notna() & (first != ""), "wikidata", np.where(pd.Series(from_name).notna(), "name", ""))
A["display_name"] = np.where(A.name != "", A.name, A.wlabel.fillna(""))
A.to_pickle(os.path.join(WORK, "churches.pkl"))
print(A.period.value_counts().to_dict(), file=sys.stderr)
print(A.dgroup.value_counts().to_dict(), file=sys.stderr)
print(A.grade.value_counts().to_dict(), file=sys.stderr)
print(A.saint.value_counts().head(40).to_dict(), file=sys.stderr)
print("with saint", A.saint.notna().sum(), A.saint_src.value_counts().to_dict(), file=sys.stderr)
