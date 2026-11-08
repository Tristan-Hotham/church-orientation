"""Step 10: README.md, LICENSE and the Reddit post text (reddit/post.md), filled from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
n, a, o, sw, fo = R["n"], R["all"], R["old"], R["summer_winter"], R["feast"]["old"]
P, D, st = R["by_period"], R["by_denom"], R["streets"]
readme = f"""# Which way do the UK's churches face?

The long axis of {n['measured']:,} church footprints in OpenStreetMap for the United Kingdom, measured against true east, with saints, dates and listing grades from Wikidata, and a test of the old idea that churches were aligned to sunrise on their patron saint's day. Mapped on a hand-inked map.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24052501}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/church-orientation/}}
Code and data: {REPO}

## Headline results

- {a['within10']:.1f}% of all measured churches lie within 10° of due east, but {o['within10']:.1f}% of the {o['n']:,} historic parish churches (dated before 1540, or undated and listed Grade I, II* or category A), against {P['victorian']['within10']:.1f}% of churches dated 1800 to 1913, {P['modern']['within10']:.1f}% from 1914 onwards and {D['nonconformist']['within10']:.1f}% of Methodist, Baptist and other Free Church buildings ({R['chance10']:.1f}% would be expected by chance).
- The patron saint's day makes no difference. Historic churches of midsummer saints point at {sw['summer_mean_bearing']:.1f}° on average and those of midwinter saints at {sw['winter_mean_bearing']:.1f}°, although their feast-day sunrises are {sw['pred_gap']:.1f}° apart. With the saints shuffled at random 10,000 times, the real saints fit no better (mean miss {fo['mean_abs_err']:.1f}° against {fo['perm_mean']:.1f}°, p = {fo['p_value']:.2f}).
- Historic churches lean north of east by {abs(o['mean_dev_eastish']):.1f}° on average ({o['north_of_east']:.0f}% turn north), more in the west (west of 3°W: {R['lon_slope_old']['west_mean']:.1f}°) than in the east (east of 1°E: {R['lon_east_band']['mean_dev']:.1f}°).
- In towns, {st['urban_victorian_modern']['closer_to_grid']:.0f}% of churches dated 1800 onwards are closer to their local street grid than to east, where the two differ by at least 15° (street sample of {R['streets_sample']['n']:,} churches).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`): the Inked World map style on MapLibre GL JS, every church as a small nave pointing along its axis, coloured by its turn from east; filters by date, denomination, listing and saint; axis, due east and feast-day sunrise lines when zoomed in; search and popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/churches.csv` | Every measured church ({n['measured']:,} rows): OpenStreetMap id and link, name, centroid, axis bearing, deviation, second (edge) estimate, length, width, ratio, area, denomination, saint and its source, feast and predicted sunrise azimuth, calendar shift, date, period, listing grade, Wikidata id and how it was joined. ODbL. |
| `data/saints_historic.csv` | Saint by saint, historic parish churches: mean axis against the feast-day sunrise. |
| `data/groups.csv` | Shares within 5°, 10°, 20° and beyond 45° of east by period, listing, denomination and nation. |
| `data/street_grid_sample.csv` | The street sample: road length within 150 m, grid direction and strength, nearest road, angles to grid and to east. |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/churches.json`, `data/places.json` | Page data: compact rows for the map; towns and villages for the search (Wikidata, CC0). |
| other `data/*` files, `js/`, `fonts/` | The Inked World map style (engine, lettering fonts and basemap data), copied from the ink-map study. |
| `img/` | Figures on the page. |
| `code/` | Numbered scripts, the feast-day table (`feasts.csv`), the dedication parser from saints-geography (`saints.py`), page, paper and blog templates, `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Footprints: OpenStreetMap elements tagged building=church, cathedral or chapel ({n['polygons_church_tag']:,} polygons), plus Christian places of worship drawn as other buildings ({n['polygons_pow']:,}), from QLever. Points dropped; houses, schools and the like dropped; footprints inside a larger church footprint dropped.
- Axis: each footprint in a local true-north equirectangular frame; the long side of the minimum-area enclosing rectangle, folded to 0° to 180° (the east end). Kept if longer than {MIN_RATIO} times its width and {int(MIN_AREA)} to {int(MAX_AREA):,} m²: {n['measured']:,} churches. An independent edge-direction estimate agrees within 2° for {n['rect_edge_agree_2deg']:.1f}%.
- Wikidata: joined through the wikidata tag, P10689 (OSM way id) or the item's coordinates in the footprint ({n['wikidata_joined']:,} joined). Saint from P825, else the name (saints-geography parser); Wikidata's Oswald of Worcester dedications are reassigned to Oswald of Northumbria, as almost all are northern St Oswald churches. Date: earliest of OSM start_date and Wikidata inception ({n['dated']:,} dated).
- Feast test: sunrise azimuth over a flat horizon, cos A = sin(declination) / cos(latitude), Spencer (1971) declination. Julian feast dates moved to the solar year for churches dated before 1753 (7 days in 1100 to 1299, rising to 11); undated historic churches taken as c. 1200. Statistic: mean absolute difference between axis and sunrise; null from 10,000 permutations of the saints. Mary, the Holy Trinity, Christ, the Holy Cross, Paul alone and John without a qualifier are left out (no single fixed feast).
- Street grid: OpenFreeMap vector tiles (zoom 14) around a random sample of {R['streets_sample']['n']:,} churches; roads within 150 m; length-weighted dominant direction folded to 90°; urban means at least 2,000 m of road within 150 m.
- Caveats: a footprint is not a nave (towers, aisles, transepts); Wikidata inception can be the foundation of an earlier church (Coventry Cathedral); dedications change; the horizon is taken as flat; the street test uses today's streets and the link runs both ways.

## How to rerun

Needs Python 3 with pandas, numpy, shapely, geopandas, scipy, matplotlib, Pillow, fontTools and mapbox-vector-tile; xelatex and pdfinfo; node with Playwright for `code/qa.js`. Raw inputs are listed in `code/common.py` (not redistributed except as the derived table); intermediates go to `CO_WORK`. Step 03 reads OpenFreeMap tiles over the network.

```
python3 code/01_orient.py      # axes of every footprint
python3 code/02_attrs.py       # Wikidata, saints, dates, denominations
python3 code/03_streets.py     # street grid sample (network)
python3 code/04_analysis.py    # results.json
python3 code/05_export.py      # data files and page data
python3 code/06_figures.py     # figures
python3 code/07_build_site.py  # index.html
python3 code/08_paper.py       # paper PDF
python3 reddit/collage.py      # collage and header
python3 code/10_readme.py      # README, LICENSE, Reddit post
python3 code/09_release.py     # blog post, Zenodo files
```

## Sources and licences

- OpenStreetMap (https://www.openstreetmap.org/), © OpenStreetMap contributors, Open Database Licence. Queried with QLever (University of Freiburg). `data/churches.csv` and `data/churches.json` are derived databases under the ODbL.
- Wikidata (https://www.wikidata.org/), CC0: saints, inception dates, listing grades (from Historic England, Cadw, Historic Environment Scotland, the Northern Ireland record), and the settlements used for search.
- saints-geography (https://github.com/Tristan-Hotham/saints-geography): dedication parser, MIT.
- OpenFreeMap vector tiles (OpenMapTiles schema, OpenStreetMap data) for the street grid and the map.
- Map style: the Inked World (ink-map study, MIT code), with Natural Earth, RESOLVE Ecoregions 2017 (CC BY 4.0), Wikidata (CC0) and AWS Terrain Tiles.
- Fonts: MedievalSharp and IM Fell (SIL Open Font License); Fraunces, Source Serif 4, IBM Plex Mono (SIL Open Font License).
- Earlier work: Ali and Cunich (2001), The Antiquaries Journal 81, 155 to 193; Hinton (2006), The Antiquaries Journal 86, 206 to 226; Furuhashi and Terado (2026), ISPRS Archives L-4/W1-2026, 43 to 48.

## Citation

Hotham, T. (2026) Which way do the UK's churches face? The axes of church footprints from OpenStreetMap and a test of the patron saint's sunrise. Zenodo. {{https://doi.org/10.5281/zenodo.24052501}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in "\n".join(l for l in readme.replace("```", "").splitlines() if not l.startswith("|---")), bad
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = """MIT License (code)

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Text and figures: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), Tristan Hotham, 2026.
Church data (data/churches.csv, data/churches.json, data/street_grid_sample.csv): derived from OpenStreetMap, © OpenStreetMap contributors, Open Database Licence 1.0 (https://opendatacommons.org/licenses/odbl/1-0/).
Saints, dates, listing and settlements: Wikidata, CC0.
code/saints.py: from saints-geography by Tristan Hotham, MIT.
Map style files in js/, fonts/ and the basemap data in data/ come from the ink-map study (code MIT; data credits in its README: OpenStreetMap ODbL, RESOLVE Ecoregions CC BY 4.0, Wikidata CC0, Natural Earth). Fonts under the SIL Open Font License (see fonts/ttf).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""**Title:** [OC] Do churches face sunrise on their saint's day? I measured {n['measured']:,} churches in the UK: midsummer and midwinter saints' churches point the same way, {abs(sw['obs_gap']):.1f}° apart, where the sun is {sw['pred_gap']:.0f}° apart

**Body:**

Old churches face east, but rarely exactly east, and a popular explanation is that the builders aimed the nave at sunrise on the patron saint's feast day. So a church of John the Baptist (midsummer) should point well north of east, and a church of St Nicholas (December) well south.

I measured the long axis of every church footprint in OpenStreetMap for the UK that is clearly longer than wide ({n['measured']:,}), and took saints and dates from Wikidata.

- Historic parish churches: {o['within10']:.0f}% within 10° of east. Churches from 1914 onwards: {P['modern']['within10']:.0f}%. Free Church chapels: {D['nonconformist']['within10']:.0f}% (random would be {R['chance10']:.0f}%).
- Midsummer saints' churches average {sw['summer_mean_bearing']:.1f}°, midwinter saints' {sw['winter_mean_bearing']:.1f}°. Shuffling the saints at random fits just as well (p = {fo['p_value']:.2f}).
- What they do share is a lean of about {abs(o['mean_dev_eastish']):.0f}° north of east, stronger in the west of England and Wales.

Interactive map (zoom in to see each church's axis and its saint's-day sunrise): {PAGE}

**Source comment:**

Data: OpenStreetMap contributors (ODbL), queried with QLever; Wikidata (CC0); OpenFreeMap tiles for the street test. Tools: Python (shapely, pandas, matplotlib), MapLibre. Axis = long side of the minimum-area rectangle around each footprint, in a local true-north frame. Feast-day sunrise over a flat horizon, with medieval dates moved from the Julian calendar. Earlier work found the same: Hinton (2006), Antiquaries Journal 86. Paper and code: {REPO}
"""
for bad in ("—", "–", "--"):
    assert bad not in post, bad
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README, LICENSE, post written")
