"""Shared paths and helpers for the church-orientation study ("Which way do Britain's churches face?").

Raw inputs (read in place, never modified):
  OSM_CH   /home/claude/newdata/raw_new8/churches_gb.tsv
           OpenStreetMap via QLever (osm2rdf): every element in Great Britain with building=church, cathedral or chapel.
           Columns: OSM id URL, building, name, dedication, denomination, heritage, start_date, wikidata, WKT geometry.
  OSM_POW  /home/claude/newdata/raw_new8/churches_gb_pow.tsv
           amenity=place_of_worship + religion=christian with other building values (mostly building=yes). Same columns.
  WD       /home/claude/newdata/raw_new8/churches_wikidata_uk.tsv
           Wikidata church buildings in the UK: item, label, coordinates, dedication (P825), OSM way id (P10689),
           inception (P571), heritage designation (P1435).
  SG       saints-geography (Tristan Hotham 2026, https://github.com/Tristan-Hotham/saints-geography): its OSM extract
           data/raw/osm_pubs_churches.json.gz (rows: key, type, lat, lon, name, old_name, denomination, building, historic,
           heritage, start_date, dedication, addr) and its dedication parser saints.py (copied here).
  OFM      OpenFreeMap vector tiles (https://tiles.openfreemap.org), transportation layer, for the street-grid test.
"""
import json, gzip, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("CO_RAW", "/home/claude/newdata/raw_new8")
OSM_CH = os.path.join(RAW, "churches_gb.tsv")
OSM_POW = os.path.join(RAW, "churches_gb_pow.tsv")
WD = os.path.join(RAW, "churches_wikidata_uk.tsv")
SG_URL = "https://raw.githubusercontent.com/Tristan-Hotham/saints-geography/main/data/raw/osm_pubs_churches.json.gz"
GEO = "/home/claude/newdata/raw/geo"
FONTS = "/home/claude/ref/fonts"
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("CO_WORK", "/home/claude/work/new8/church-orientation/work")   # intermediates, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "church-orientation"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# Filters for a building whose long axis can be measured
MIN_RATIO = 1.3      # long side / short side of the minimum-area rectangle
MIN_AREA = 60.0      # m2, footprint
MAX_AREA = 8000.0    # m2, larger footprints are complexes (abbeys with cloisters, campuses)

# Periods (by year of building or foundation, where known)
PERIODS = [("medieval", "Medieval (before 1540)", -9999, 1539),
           ("early", "1540 to 1799", 1540, 1799),
           ("victorian", "1800 to 1913", 1800, 1913),
           ("modern", "1914 onwards", 1914, 9999)]
PNAME = {p[0]: p[1] for p in PERIODS}
PNAME["unknown"] = "Date not known"

DENOMS = {  # OSM denomination tag -> group
    "anglican": "anglican", "church_of_england": "anglican", "church_in_wales": "anglican", "episcopal": "anglican",
    "scottish_episcopal": "anglican",
    "catholic": "catholic", "roman_catholic": "catholic",
    "church_of_scotland": "scotland", "presbyterian": "scotland", "free_church_of_scotland": "scotland",
    "methodist": "nonconformist", "baptist": "nonconformist", "united_reformed": "nonconformist",
    "congregational": "nonconformist", "evangelical": "nonconformist", "pentecostal": "nonconformist",
    "salvation_army": "nonconformist", "quaker": "nonconformist", "wesleyan": "nonconformist",
    "independent": "nonconformist", "unitarian": "nonconformist", "plymouth_brethren": "nonconformist",
    "brethren": "nonconformist", "free_church": "nonconformist", "elim": "nonconformist",
    "orthodox": "orthodox", "greek_orthodox": "orthodox", "russian_orthodox": "orthodox",
}
DNAME = {"anglican": "Church of England, in Wales, Episcopal", "catholic": "Roman Catholic",
         "scotland": "Church of Scotland and Presbyterian", "nonconformist": "Methodist, Baptist and other Free Churches",
         "orthodox": "Orthodox", "other": "Other Christian", "unknown": "Not tagged"}

# Colour ramp for the size of the turn from due east (absolute degrees): true east is vermilion ink, large turns fade
# to slate blue. The sign (north or south of east) is shown by the tilt of each glyph.
ABS_STOPS = [(0, "#9E1F14"), (4, "#C4471F"), (9, "#DE8A2E"), (16, "#C9A35C"), (28, "#93A0A2"), (45, "#7F98B4"), (90, "#6F8AAE")]


def jsave(obj, path, indent=None):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "wt", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, dict):
        return {k: nonan(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "deg": return f"{float(v):.1f}°"
    if f == "deg0": return f"{round(float(v))}°"
    raise ValueError(f)


# ---------- the sun ----------
def declination(doy):
    """Solar declination (degrees) for day of year doy (1 = 1 January, Gregorian), Spencer (1971) series."""
    g = 2 * math.pi * (doy - 1) / 365.0
    d = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
         + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    return math.degrees(d)


def sunrise_az(lat, decl, h=0.0):
    """Azimuth of sunrise (degrees east of true north) over a flat horizon at altitude h."""
    p, d, hh = map(math.radians, (lat, decl, h))
    c = (math.sin(d) - math.sin(p) * math.sin(hh)) / (math.cos(p) * math.cos(hh))
    return math.degrees(math.acos(max(-1, min(1, c))))


def julian_offset(year):
    """Days to add to a Julian calendar date to get the Gregorian date in that year."""
    if year is None:
        return 0
    c = year // 100
    return c - c // 4 - 2
