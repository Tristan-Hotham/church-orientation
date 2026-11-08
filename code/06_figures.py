"""Step 6: figures for the blog (release/blog/b_*.png), the paper (release/paper/f_*.png) and the page (img/)."""
import shapely
import pandas as pd
from figstyle import *

R = jload(os.path.join(DATA, "results.json"))
K = pd.read_pickle(os.path.join(WORK, "measured.pkl"))
G = pd.read_pickle(os.path.join(WORK, "geoms.pkl")).set_index("osm")
BLOG = os.path.join(ROOT, "release", "blog"); PAP = os.path.join(ROOT, "release", "paper"); IMG = os.path.join(ROOT, "img")
for d in (BLOG, PAP, IMG):
    os.makedirs(d, exist_ok=True)
SRC = "Data: OpenStreetMap contributors (ODbL), Wikidata (CC0). Analysis: Tristan Hotham, maps.tristanhotham.com/church-orientation"


def out(fig, name, paper=True):
    dpi = 1800 / fig.get_figwidth()          # every blog figure 1800 px wide
    fig.savefig(os.path.join(BLOG, f"b_{name}.png"), dpi=dpi, facecolor=fig.get_facecolor())
    if paper:
        fig.savefig(os.path.join(PAP, f"f_{name}.png"), dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def colourbar(fig, rect, label="Turn from due east, either way"):
    ax = fig.add_axes(rect)
    g = (np.linspace(0, 1, 361) ** 2 * 90)[None, :]
    ax.imshow(g, aspect="auto", cmap=DEV_CMAP, norm=DEV_NORM, extent=(0, 1, 0, 1))
    tk = [0, 5, 10, 20, 45, 90]
    ax.set_yticks([]); ax.set_xticks([math.sqrt(a / 90) for a in tk]); ax.set_xticklabels([f"{a}°" for a in tk], fontsize=10)
    for s in ax.spines.values():
        s.set_color(INK); s.set_linewidth(0.8)
    ax.set_title(label, fontsize=9.5, color=MUT, pad=4)
    return ax


# ---------- 1. the map of Britain
def fig_map():
    fig = plt.figure(figsize=(10, 13)); paper(fig)
    ax = fig.add_axes([0.0, 0.015, 1.0, 0.875])
    basemap(ax, ext=(-8.3, 2.6, 49.85, 59.4))
    d = K.sample(frac=1, random_state=1)
    ticks(ax, d.lon.values, d.lat.values, d.bearing.values, d.dev.values, L=0.042, lw=0.55, alpha=0.85)
    fig.text(0.05, 0.965, "Which way do the UK's churches face?", fontproperties=DISP, fontsize=31, va="top")
    fig.text(0.05, 0.925, f"{R['n']['measured']:,} church footprints from OpenStreetMap, each drawn along its long axis\nand tinted by how far it turns from due east",
             fontproperties=SERP, fontsize=14, color=MUT, va="top")
    colourbar(fig, [0.69, 0.62, 0.26, 0.014])
    fig.text(0.69, 0.585, "Each line runs along a church;\nits tilt shows the turn north\nor south of east.", fontsize=10.5, color=INK, va="top")
    fig.text(0.69, 0.515, f"Within 10° of east:\nall churches {R['all']['within10']:.0f}%\nhistoric parish churches {R['old']['within10']:.0f}%", fontsize=10.5, color=INK, va="top")
    fig.text(0.05, 0.012, SRC, fontsize=8.5, color=MUT)
    out(fig, "map")


# ---------- 2. roses
def rose(ax, bearings, colour, title, n):
    h, e = np.histogram(bearings, bins=72, range=(0, 180))
    h = h / h.max()
    th = np.radians((e[:-1] + e[1:]) / 2)
    w = np.radians(2.5)
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.bar(th, h, width=w, color=colour, edgecolor="none", alpha=0.9)
    ax.bar(th + math.pi, h, width=w, color=colour, edgecolor="none", alpha=0.25)
    ax.set_yticks([]); ax.set_xticks(np.radians([0, 90, 180, 270])); ax.set_xticklabels(["N", "E", "S", "W"], fontsize=11)
    ax.set_facecolor("#FBF5E4"); ax.spines["polar"].set_color(MUT)
    ax.grid(color=RULE, lw=0.7)
    ax.set_title(f"{title}\n{n:,} churches", fontsize=11.5, pad=12)


def fig_roses():
    fig = plt.figure(figsize=(13, 6.2)); paper(fig)
    fig.text(0.03, 0.96, "Old churches face east. New ones face the street.", fontproperties=DISP, fontsize=27, va="top")
    fig.text(0.03, 0.885, "Direction of the long axis of each footprint (the solid half; the pale half is the same axis read the other way)",
             fontproperties=SERP, fontsize=13, color=MUT, va="top")
    groups = [(K[K.old].bearing, "#8E2F1F", "Historic parish churches"),
              (K[K.period == "victorian"].bearing, "#C97A4A", "Dated 1800 to 1913"),
              (K[K.period == "modern"].bearing, "#6F9CC4", "Dated 1914 onwards"),
              (K[K.dgroup == "nonconformist"].bearing, "#2F5D8C", "Methodist, Baptist and\nother Free Churches")]
    for i, (b, c, t) in enumerate(groups):
        ax = fig.add_axes([0.03 + i * 0.245, 0.1, 0.2, 0.62], projection="polar")
        rose(ax, b, c, t, len(b))
    fig.text(0.03, 0.02, SRC, fontsize=8.5, color=MUT)
    out(fig, "roses")


# ---------- 3. saints
def fig_saints():
    S = pd.DataFrame(R["saints_old"])
    fig = plt.figure(figsize=(12, 8.4)); paper(fig)
    ax = fig.add_axes([0.09, 0.11, 0.6, 0.66])
    ax.set_facecolor("#FBF5E4")
    x = np.linspace(40, 140, 2)
    ax.plot(x, x, color=RED, lw=1.4, ls=(0, (5, 4)), zorder=2)
    ax.text(135, 128, "if churches faced\nsunrise on the\nsaint's day", color=RED, fontsize=10.5, ha="right", va="top")
    ax.axhline(90, color=MUT, lw=0.8, zorder=1); ax.text(76, 91.2, "due east", color=MUT, fontsize=10)
    ax.errorbar(S.pred, S.mean_bearing, yerr=1.96 * S.se, fmt="none", ecolor=INK, elinewidth=0.8, alpha=0.6, zorder=3)
    ax.scatter(S.pred, S.mean_bearing, s=np.sqrt(S.n) * 4, color="#8E2F1F", edgecolor=INK, lw=0.6, zorder=4)
    lab = {"John the Baptist": (10, -30), "Peter": (6, 22), "Michael": (0, 22), "All Saints": (-4, 22), "Andrew": (0, 26), "Nicholas": (6, -30),
           "Lawrence": (0, -32), "James": (4, -34)}
    for r in S.itertuples():
        if r.saint in lab:
            dx, dy = lab[r.saint]
            ax.annotate(r.saint, (r.pred, r.mean_bearing), xytext=(dx, dy), textcoords="offset points", ha="center", fontsize=9.5, color=INK,
                        arrowprops=dict(arrowstyle="-", color=MUT, lw=0.6, shrinkA=0, shrinkB=4))
    ax.set_xlim(40, 140); ax.set_ylim(40, 140)
    ax.set_xlabel("Sunrise on the saint's feast day (degrees from north)"); ax.set_ylabel("Average axis of their churches (degrees from north)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    rr = R["saint_regression"]; sw = R["summer_winter"]
    fig.text(0.05, 0.965, "The saint's day makes no difference", fontproperties=DISP, fontsize=28, va="top")
    fig.text(0.05, 0.905, f"{rr['n_saints']} saints with 25 or more historic parish churches ({rr['n_churches']:,} churches). Feast-day sunrise spans {rr['pred_range'][1] - rr['pred_range'][0]:.0f}°;\n"
             f"the churches' average axes span {rr['obs_range'][1] - rr['obs_range'][0]:.0f}°. Dot size: number of churches; bars: 95% intervals.", fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
    t = (f"Midsummer saints\n(John the Baptist, Peter,\nBotolph and others)\nsunrise at {sw['summer_pred']:.0f}°\nchurches at {sw['summer_mean_bearing']:.1f}°\n\n"
         f"Midwinter saints\n(Nicholas, Thomas,\nAndrew and others)\nsunrise at {sw['winter_pred']:.0f}°\nchurches at {sw['winter_mean_bearing']:.1f}°\n\n"
         f"Shuffling the saints at random\nfits the churches just as well\n(p = {R['feast']['old']['p_value']:.2f}).")
    fig.text(0.73, 0.74, t, fontsize=11.5, color=INK, va="top", linespacing=1.35)
    fig.text(0.05, 0.02, SRC, fontsize=8.5, color=MUT)
    out(fig, "saints")


# ---------- 4. groups
def fig_groups():
    rows = [("Medieval (before 1540)", R["by_period"]["medieval"]), ("1540 to 1799", R["by_period"]["early"]),
            ("1800 to 1913", R["by_period"]["victorian"]), ("1914 onwards", R["by_period"]["modern"]), None,
            ("Listed Grade I", R["by_grade"]["I"]), ("Grade II*", R["by_grade"]["II*"]), ("Grade II", R["by_grade"]["II"]),
            ("Not listed (or not linked)", R["by_grade"]["none"]), None,
            ("Church of England, in Wales", R["by_denom"]["anglican"]), ("Roman Catholic", R["by_denom"]["catholic"]),
            ("Church of Scotland", R["by_denom"]["scotland"]), ("Methodist, Baptist, Free", R["by_denom"]["nonconformist"])]
    fig = plt.figure(figsize=(12, 8.6)); paper(fig)
    ax = fig.add_axes([0.3, 0.12, 0.47, 0.68]); ax.set_facecolor(PAPER)
    y = 0; Y, L = [], []
    for r in rows:
        if r is None:
            y += 0.7; continue
        name, v = r
        a, b, c = v["within5"], v["within10"] - v["within5"], v["within20"] - v["within10"]
        ax.barh(y, a, color="#8E2F1F", height=0.7); ax.barh(y, b, left=a, color="#C97A4A", height=0.7); ax.barh(y, c, left=a + b, color="#E9C9A6", height=0.7)
        ax.text(v["within20"] + 1, y, f"{v['within10']:.0f}% within 10°   (n = {v['n']:,})", va="center", fontsize=10, color=INK)
        Y.append(y); L.append(name); y += 1
    ax.set_yticks(Y); ax.set_yticklabels(L, fontsize=11); ax.invert_yaxis()
    ax.set_xlim(0, 100); ax.set_xlabel("Share of churches whose axis lies within 5°, 10° and 20° of due east (%)")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(0.04, 0.965, "The older the church, the truer to east", fontproperties=DISP, fontsize=28, va="top")
    fig.text(0.04, 0.905, "Dark: within 5°; middle: 5° to 10°; pale: 10° to 20°. Dates from OpenStreetMap and Wikidata;\nlisting from Wikidata (Historic England, Cadw); denomination as tagged in OpenStreetMap.",
             fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
    fig.text(0.04, 0.015, SRC, fontsize=8.5, color=MUT)
    out(fig, "groups")


# ---------- 5. west to east
def fig_longitude():
    T = pd.DataFrame(R["by_longitude_old"])
    O = K[K.old & (K.adev <= 45) & K.nation.isin(["England", "Wales"])]
    fig = plt.figure(figsize=(12, 7.2)); paper(fig)
    ax = fig.add_axes([0.08, 0.12, 0.52, 0.66]); ax.set_facecolor("#FBF5E4")
    ax.axhline(0, color=MUT, lw=0.8)
    ax.plot(T.lon, T.mean_dev, color="#8E2F1F", lw=2.2, marker="o", ms=7, mec=INK, zorder=4)
    for r in T.itertuples():
        ax.text(r.lon, r.mean_dev - 0.75, f"{r.n:,}", ha="center", va="top", fontsize=8.5, color=MUT)
    ax.set_ylim(-9, 2.5); ax.set_xlim(-6.2, 2.2)
    ax.set_xlabel("Longitude (one-degree bands)"); ax.set_ylabel("Mean turn from east (°; minus = north)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax2 = fig.add_axes([0.63, 0.06, 0.36, 0.78])
    basemap(ax2, ext=(-5.9, 1.9, 49.9, 55.9), lw=0.5)
    for a in np.arange(-6, 2.5, 1.0):
        x, _ = proj(a, 0)
        ax2.axvline(x, color=MUT, lw=0.4, alpha=0.6, zorder=6)
    d = O.sample(frac=1, random_state=2)
    ticks(ax2, d.lon.values, d.lat.values, d.bearing.values, d.dev.values, L=0.05, lw=0.6)
    fig.text(0.05, 0.965, "Further east, truer to east", fontproperties=DISP, fontsize=28, va="top")
    ls = R["lon_slope_old"]
    fig.text(0.05, 0.905, f"Historic parish churches of England and Wales. West of 3°W they turn on average {abs(ls['west_mean']):.1f}° north of east;\n"
             f"east of the Greenwich meridian, {abs(ls['east_mean']):.1f}°. Numbers under the dots: churches in each band.", fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
    fig.text(0.05, 0.015, SRC, fontsize=8.5, color=MUT)
    out(fig, "longitude")


# ---------- 6. footprints
EXAMPLES = []


def pick_examples():
    want = []
    old = K[K.old & (K.display_name != "") & (K.length > 25) & (K.rect_fill > 0.6)]
    # a medieval church almost exactly east, one well north of east, one well south of east
    e = old[old.adev < 0.5].sort_values("length", ascending=False).head(1)
    n = old[(old.dev < -14) & (old.dev > -20)].sort_values("length", ascending=False).head(1)
    s = old[(old.dev > 12) & (old.dev < 18)].sort_values("length", ascending=False).head(1)
    cov = K[K.osm == "w25312607"]
    urb = K[(K.period == "victorian") & (K.adev > 35) & (K.adev < 60) & (K.display_name != "") & (K.length > 30)].sort_values("length", ascending=False).head(1)
    for d, cap in ((e, "on the button"), (n, "north of east"), (s, "south of east"), (cov, "north to south"), (urb, "Victorian, far off east")):
        if len(d):
            want.append((d.iloc[0], cap))
    return want


def fig_footprints():
    ex = pick_examples()
    fig = plt.figure(figsize=(13, 5.6)); paper(fig)
    fig.text(0.03, 0.96, "Five footprints and their axes", fontproperties=DISP, fontsize=26, va="top")
    fig.text(0.03, 0.885, "Outline from OpenStreetMap; red line: the long axis of the smallest rectangle around it; grey: due east. North is up.",
             fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
    for i, (r, cap) in enumerate(ex):
        ax = fig.add_axes([0.02 + i * 0.196, 0.12, 0.18, 0.62]); ax.set_facecolor("#FBF5E4")
        g = shapely.from_wkb(G.loc[r.osm, "geom"])
        k = math.cos(math.radians(r.lat))
        xy = np.array(g.exterior.coords)
        X = (xy[:, 0] - r.lon) * 111195 * k; Y = (xy[:, 1] - r.lat) * 111195
        ax.fill(X, Y, color=LANDC, ec=INK, lw=1.2)
        L = r.length * 0.62
        b = math.radians(r.bearing)
        ax.plot([-L * math.sin(b), L * math.sin(b)], [-L * math.cos(b), L * math.cos(b)], color=RED, lw=2)
        ax.plot([-L, L], [0, 0], color=MUT, lw=0.9, ls=(0, (4, 3)))
        m = max(np.abs(X).max(), np.abs(Y).max()) * 1.15
        ax.set_xlim(-m, m); ax.set_ylim(-m, m); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color(RULE)
        nm = r.display_name.replace(" Church of St Michael", "") if len(r.display_name) < 30 or "Coventry" in r.display_name else r.display_name[:28] + "…"
        dv = f"{abs(r.dev):.1f}° {'north' if r.dev < 0 else 'south'} of east" if r.adev >= 0.05 else "due east"
        yr = ""   # Wikidata inception can be the foundation, not the standing building (Coventry), so no years here
        ax.set_title(f"{cap}\n", fontproperties=HAND, fontsize=15, color=RED, pad=2)
        ax.text(0.5, -0.04, f"{nm}{yr}\naxis {r.bearing:.1f}°: {dv}", transform=ax.transAxes, ha="center", va="top", fontsize=9, color=INK)
        EXAMPLES.append({"osm": r.osm, "name": r.display_name, "bearing": round(r.bearing, 1), "dev": round(r.dev, 1), "caption": cap})
    fig.text(0.03, 0.01, SRC, fontsize=8.5, color=MUT)
    out(fig, "footprints")


# ---------- 7. streets
def fig_streets():
    sp = os.path.join(DATA, "street_grid_sample.csv")
    T = pd.read_csv(sp).merge(K[["osm", "period", "old", "dgroup"]], on="osm")
    fig = plt.figure(figsize=(12, 6.6)); paper(fig)
    bins = np.arange(0, 46, 3)
    for i, (d, t) in enumerate(((T[T.urban & T.old], "Historic parish churches in towns"),
                                (T[T.urban & ~T.old], "All other churches in towns"))):
        ax = fig.add_axes([0.07 + i * 0.47, 0.13, 0.4, 0.6]); ax.set_facecolor("#FBF5E4")
        ax.hist(d.d_east, bins=bins, color="#8E2F1F", alpha=0.75, label="turn from due east", density=True)
        ax.hist(d.d_grid, bins=bins, histtype="step", color=BLUE, lw=2.2, label="turn from the local streets", density=True)
        ax.axhline(1 / 45, color=MUT, lw=0.8, ls=(0, (4, 3)))
        ax.set_title(f"{t} (n = {len(d):,})", fontsize=12)
        ax.set_xlabel("Angle (degrees; 0 = parallel or square to it)"); ax.set_yticks([])
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        if i == 0:
            ax.legend(frameon=False, fontsize=10.5)
    fig.text(0.05, 0.965, "In towns, the street often wins", fontproperties=DISP, fontsize=28, va="top")
    fig.text(0.05, 0.885, "A random sample of churches with dense roads within 150 m (OpenFreeMap vector tiles). Dashed line: what a random\nangle would give.",
             fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
    fig.text(0.05, 0.015, SRC.replace("Wikidata (CC0)", "Wikidata (CC0), OpenFreeMap"), fontsize=8.5, color=MUT)
    out(fig, "streets")


fig_map(); fig_roses(); fig_saints(); fig_groups(); fig_longitude(); fig_footprints()
if os.path.exists(os.path.join(DATA, "street_grid_sample.csv")):
    fig_streets()
R["examples_footprints"] = EXAMPLES
jsave(R, os.path.join(DATA, "results.json"), indent=1)
print("figures done", [e["name"] for e in EXAMPLES])
