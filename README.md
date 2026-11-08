# Which way do the UK's churches face?

The long axis of 32,007 church footprints in OpenStreetMap for the United Kingdom, measured against true east, with saints, dates and listing grades from Wikidata, and a test of the old idea that churches were aligned to sunrise on their patron saint's day. Mapped on a hand-inked map.

Interactive page: https://maps.tristanhotham.com/church-orientation/
Paper: https://doi.org/10.5281/zenodo.24052501
Blog post: https://blog.tristanhotham.com/2026/10/31/church-orientation/
Code and data: https://github.com/Tristan-Hotham/church-orientation

## Headline results

- 30.4% of all measured churches lie within 10° of due east, but 53.5% of the 8,565 historic parish churches (dated before 1540, or undated and listed Grade I, II* or category A), against 24.9% of churches dated 1800 to 1913, 19.9% from 1914 onwards and 14.2% of Methodist, Baptist and other Free Church buildings (11.1% would be expected by chance).
- The patron saint's day makes no difference. Historic churches of midsummer saints point at 85.5° on average and those of midwinter saints at 85.4°, although their feast-day sunrises are 78.3° apart. With the saints shuffled at random 10,000 times, the real saints fit no better (mean miss 30.9° against 30.9°, p = 0.54).
- Historic churches lean north of east by 4.9° on average (65% turn north), more in the west (west of 3°W: -6.3°) than in the east (east of 1°E: 0.3°).
- In towns, 85% of churches dated 1800 onwards are closer to their local street grid than to east, where the two differ by at least 15° (street sample of 5,967 churches).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/07_build_site.py`): the Inked World map style on MapLibre GL JS, every church as a small nave pointing along its axis, coloured by its turn from east; filters by date, denomination, listing and saint; axis, due east and feast-day sunrise lines when zoomed in; search and popups. |
| `header.png` | Social card, 1200 x 630. |
| `data/churches.csv` | Every measured church (32,007 rows): OpenStreetMap id and link, name, centroid, axis bearing, deviation, second (edge) estimate, length, width, ratio, area, denomination, saint and its source, feast and predicted sunrise azimuth, calendar shift, date, period, listing grade, Wikidata id and how it was joined. ODbL. |
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

- Footprints: OpenStreetMap elements tagged building=church, cathedral or chapel (27,560 polygons), plus Christian places of worship drawn as other buildings (13,076), from QLever. Points dropped; houses, schools and the like dropped; footprints inside a larger church footprint dropped.
- Axis: each footprint in a local true-north equirectangular frame; the long side of the minimum-area enclosing rectangle, folded to 0° to 180° (the east end). Kept if longer than 1.3 times its width and 60 to 8,000 m²: 32,007 churches. An independent edge-direction estimate agrees within 2° for 90.9%.
- Wikidata: joined through the wikidata tag, P10689 (OSM way id) or the item's coordinates in the footprint (21,956 joined). Saint from P825, else the name (saints-geography parser); Wikidata's Oswald of Worcester dedications are reassigned to Oswald of Northumbria, as almost all are northern St Oswald churches. Date: earliest of OSM start_date and Wikidata inception (6,750 dated).
- Feast test: sunrise azimuth over a flat horizon, cos A = sin(declination) / cos(latitude), Spencer (1971) declination. Julian feast dates moved to the solar year for churches dated before 1753 (7 days in 1100 to 1299, rising to 11); undated historic churches taken as c. 1200. Statistic: mean absolute difference between axis and sunrise; null from 10,000 permutations of the saints. Mary, the Holy Trinity, Christ, the Holy Cross, Paul alone and John without a qualifier are left out (no single fixed feast).
- Street grid: OpenFreeMap vector tiles (zoom 14) around a random sample of 5,967 churches; roads within 150 m; length-weighted dominant direction folded to 90°; urban means at least 2,000 m of road within 150 m.
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

Hotham, T. (2026) Which way do the UK's churches face? The axes of church footprints from OpenStreetMap and a test of the patron saint's sunrise. Zenodo. https://doi.org/10.5281/zenodo.24052501

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
