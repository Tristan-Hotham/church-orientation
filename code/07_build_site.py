"""Step 7: index.html from code/page_template.html, filled from data/results.json, with the full-screen snippet;
page images in img/ (the blog figures at 1200 px). 10.5281/zenodo.24052501, https://doi.org/10.5281/zenodo.24052501 and https://blog.tristanhotham.com/2026/10/31/church-orientation/ stay as placeholders for the publisher."""
import re
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI_URL", "BLOG_URL", "DOI"}
# facts stated in words on the page
sw = R["summer_winter"]
assert sw["pred_gap"] > 70 and abs(sw["obs_gap"]) < 2 and sw["p"] > 0.05
assert R["feast"]["old"]["p_value"] > 0.05 and R["feast"]["old"]["mean_abs_err"] >= R["feast"]["old"]["perm_p05"]
assert R["old"]["within10"] > R["by_period"]["victorian"]["within10"] > R["by_period"]["modern"]["within10"]
assert R["by_denom"]["nonconformist"]["within10"] < 2 * R["chance10"]
assert R["old"]["mean_dev_eastish"] < 0 and R["old"]["north_of_east"] > 50
assert abs(R["lon_east_band"]["mean_dev"]) < 1 and R["lon_east_band"]["lon"] == 1.5 and R["lon_slope_old"]["west_mean"] < R["lon_slope_old"]["east_mean"]
assert R["mary"]["closest_feast"] in ("Annunciation (25 Mar)", "Nativity of Mary (8 Sep)")
assert abs(R["mary"]["mean_bearing"] - R["old_mean_bearing"]) < 1.5
st = R["streets"]
assert st["urban_victorian_modern"]["closer_to_grid"] > 75 > st["urban_old"]["closer_to_grid"] > 50 and st["rural"]["closer_to_grid"] > 50, st
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{ABS_STOPS}}", json.dumps(ABS_STOPS))
F = {r["saint"]: r for r in R["saints_old"]}
import pandas as pd
fe = pd.read_csv(os.path.join(ROOT, "code", "feasts.csv"))
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fd = {r.saint: f"{r.day} {MON[r.month]}" for r in fe.itertuples()}
rows = [[r["saint"], fd[r["saint"]], r["n"], r["pred"], r["mean_bearing"]] for r in sorted(R["saints_old"], key=lambda r: -r["n"])]
t = t.replace("{{SAINT_ROWS}}", json.dumps(rows, ensure_ascii=False))
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
left = set(re.findall(r"\{\{([^}]+)\}\}", t))
assert left <= KEEP, left
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in vis, bad
os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
for nm in ("roses", "groups", "saints", "longitude", "streets", "footprints"):
    im = Image.open(os.path.join(ROOT, "release", "blog", f"b_{nm}.png")).convert("RGB")
    im.thumbnail((1200, 1200), Image.LANCZOS)
    im.save(os.path.join(ROOT, "img", f"{nm}.png"), optimize=True)
    t = re.sub(r'(src="img/%s\.png"[^>]*?)width="\d+" height="\d+"' % nm, r'\g<1>width="%d" height="%d"' % im.size, t)
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
