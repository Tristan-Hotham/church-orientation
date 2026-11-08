**Title:** [OC] Do churches face sunrise on their saint's day? I measured 32,007 churches in the UK: midsummer and midwinter saints' churches point the same way, 0.1° apart, where the sun is 78° apart

**Body:**

Old churches face east, but rarely exactly east, and a popular explanation is that the builders aimed the nave at sunrise on the patron saint's feast day. So a church of John the Baptist (midsummer) should point well north of east, and a church of St Nicholas (December) well south.

I measured the long axis of every church footprint in OpenStreetMap for the UK that is clearly longer than wide (32,007), and took saints and dates from Wikidata.

- Historic parish churches: 54% within 10° of east. Churches from 1914 onwards: 20%. Free Church chapels: 14% (random would be 11%).
- Midsummer saints' churches average 85.5°, midwinter saints' 85.4°. Shuffling the saints at random fits just as well (p = 0.54).
- What they do share is a lean of about 5° north of east, stronger in the west of England and Wales.

Interactive map (zoom in to see each church's axis and its saint's-day sunrise): https://maps.tristanhotham.com/church-orientation/

**Source comment:**

Data: OpenStreetMap contributors (ODbL), queried with QLever; Wikidata (CC0); OpenFreeMap tiles for the street test. Tools: Python (shapely, pandas, matplotlib), MapLibre. Axis = long side of the minimum-area rectangle around each footprint, in a local true-north frame. Feast-day sunrise over a flat horizon, with medieval dates moved from the Julian calendar. Earlier work found the same: Hinton (2006), Antiquaries Journal 86. Paper and code: https://github.com/Tristan-Hotham/church-orientation
