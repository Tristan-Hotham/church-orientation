# NOTES: church-orientation (study 7)

Working notes so work survives interruption. Intermediates in /home/claude/work/new8/church-orientation/work (not repo).

## Plan
1. 01_orient.py: OSM polygons (churches_gb.tsv + churches_gb_pow.tsv), drop points, MRR long axis in local true-north metric frame, filters (ratio>1.3, area>=60 m2), dedupe nested/overlapping.
2. 02_attrs.py: join saints-geography extract (dedication, heritage, start_date) by OSM id; Wikidata (P825 saint, inception, listing) via wikidata tag, P10689, or point-in-polygon; saint parsing via saints.py (copied from saints-geography, MIT).
3. 03_streets.py: OpenFreeMap z14 transportation layer around a sample of churches: local street-grid orientation.
4. 04_analysis.py: variation, periods, denomination, feast-day sunrise test (permutation), saint-level regression, street grid.
5. site, figures, paper, blog, release, collage, readme, QA.

## Log
- 01 done: 40,636 polygons measured (27,560 church/chapel/cathedral + 13,076 pow). 02 done: Wikidata joined 26,290 (tag/P10689/spatial); dated 7,745 (medieval 4,294).
- saints-geography extract has almost no dedication tags (6), so only its parser saints.py is used; saint from Wikidata P825 first.
- Verified citations (WebSearch/WebFetch on publisher pages):
  * Ali, J.R. and Cunich, P. (2001) The orientation of churches: some new evidence. Antiquaries Journal 81, 155-193. doi:10.1017/S0003581500072188 (143 sites; patron-saint sunrise could account for up to 43% if sunrise and sunset both allowed)
  * Hinton, I. (2006) Church alignment and patronal saint's days. Antiquaries Journal 86, 206-226. doi:10.1017/S0003581500000111 (~1,500 rural churches; no support; summer and winter saints face the same way; ~10 deg east-west difference across England)
  * Furuhashi, T. and Terado, H. (2026) Between sacred tradition and urban form: an OpenStreetMap-based analysis of church orientation patterns in Milan. ISPRS Archives L-4/W1-2026, 43-48 (FOSS4G 2026 academic track). doi:10.5194/isprs-archives-L-4-W1-2026-43-2026 (114 churches, entrance bearings, mean 245.4 deg)
  * Spencer (1971) declination series: standard, cited from memory as Spencer, J.W. (1971) Fourier series representation of the position of the sun. Search 2(5), 172.
- 03 streets: running on 6,000 random churches (OFM z14 tiles, UA header required; urllib default UA gets 403).
- 03 streets done: 5,967 of 6,000 sampled churches (7,243 tiles). Urban (>=2000 m road in 150 m): later churches closer to grid than east 84.5%, historic 58.9% (small n), rural 61.8% (association both ways: lanes follow churchyards).
- 04-07 built: results.json, data files, figures (b_map, b_roses, b_saints, b_groups, b_longitude, b_footprints, b_streets), index.html from code/page_template.html.
- Key results: old within10 53.5% vs nonconformist 14.2% (chance 11.1%); feast test p=0.63 (old); summer 85.5 vs winter 85.4 deg (pred gap 78); lean north of east 4.9 deg; east band +0.3 vs west -6.3.
- TODO: paper (08), blog (09), release zip (10), readme (11), collage, header.png, QA.
- Paper (11 pp), blog (7 figs, 1234 words), zenodo zip, README/LICENSE/post, collage (3000x1900) and header done. QA: only Google Fonts errors (blocked in container). Popups now pan below overlays; ink houses ('towns' group) off; OFM building outlines at z>=14.
- QA screenshots converted to jpg; study ~45M.
