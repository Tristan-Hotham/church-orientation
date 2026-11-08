"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24052501, https://doi.org/10.5281/zenodo.24052501 and https://blog.tristanhotham.com/2026/10/31/church-orientation/ stay as placeholders for the publisher."""
import json as _json, re, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Church_Orientation"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}

# numbers and facts in words in the blog text and alt text
assert round(R["by_period"]["medieval"]["within10"]) == 55 and round(R["by_period"]["modern"]["within10"]) == 20
assert round(R["by_grade"]["I"]["within10"]) == 54 and round(R["by_grade"]["none"]["within10"]) == 20
assert round(R["by_denom"]["anglican"]["within10"]) == 45 and round(R["by_denom"]["nonconformist"]["within10"]) == 14
assert 81.5 < R["saint_regression"]["obs_range"][0] and R["saint_regression"]["obs_range"][1] < 90 and R["saint_regression"]["pred_range"][0] < 50 and R["saint_regression"]["pred_range"][1] > 129
assert -7.5 < min(b["mean_dev"] for b in R["by_longitude_old"]) < -6 and abs(R["lon_east_band"]["mean_dev"]) < 1
ex = {e["name"]: e for e in R["examples_footprints"]}
assert abs(ex["Bristol Cathedral"]["dev"]) < 1 and round(-ex["St Nicholas Cathedral"]["dev"]) == 16 and round(ex["Great Yarmouth Minster"]["dev"]) == 12
assert abs(ex["Coventry Cathedral Church of St Michael"]["dev"]) > 80 and round(abs(ex["Westminster Cathedral"]["dev"])) == 59
assert R["streets"]["urban_old"]["median_d_grid"] < 15 and R["streets"]["urban_old"]["median_d_east"] < 15

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, (img, Image.open(f"{REL}/blog/{img}").size)
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^{}|]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
sw = R["summer_winter"]
meta = {"title": "Which way do the UK's churches face? Not towards their saint's sunrise",
        "slug": "church-orientation",
        "excerpt": f"I measured the axes of {R['n']['measured']:,} churches from OpenStreetMap. Old churches face east, Victorian ones often face the street, and the old idea that churches point at sunrise on their patron saint's day fails: midsummer and midwinter saints' churches face the same way.",
        "seo_description": f"{R['n']['measured']:,} church axes measured: old churches face east, new ones the street, and the patron saint's sunrise makes no difference.",
        "tags": ["maps", "churches", "orientation", "archaeoastronomy", "OpenStreetMap", "Wikidata", "saints", "data visualisation", "history"],
        "header_alt": f"Title card reading 'Which way do the UK's churches face?' in black on parchment, beside a map of England and Wales covered in short red and grey strokes, one per church, with the lines '{R['n']['measured']:,} churches measured', '{R['old']['within10']:.0f}% of old churches within 10° of east' and 'Midsummer and midwinter saints: {abs(sw['obs_gap']):.1f}° apart'."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
OWN = ["churches.csv", "saints_historic.csv", "groups.csv", "street_grid_sample.csv", "results.json"]
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith(".pyc") or fn == "__pycache__" or fn.endswith(".png"):
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in OWN:
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "")
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab)
zmeta = {"title": "Which Way Do the UK's Churches Face? The Axes of Church Footprints from OpenStreetMap and a Test of the Patron Saint's Sunrise",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/church-orientation/}}.</p><p>Sources: OpenStreetMap contributors (ODbL), queried with QLever; Wikidata (CC0); OpenFreeMap vector tiles. The church table (churches.csv) is derived from OpenStreetMap and released under the Open Database Licence; other derived data and text CC BY 4.0; code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["church orientation", "archaeoastronomy", "patron saints", "OpenStreetMap", "Wikidata", "medieval churches", "historical geography", "urban form"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.openstreetmap.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "10.1017/S0003581500000111", "relation": "references", "resource_type": "publication-article"},
                                 {"identifier": "10.1017/S0003581500072188", "relation": "references", "resource_type": "publication-article"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
