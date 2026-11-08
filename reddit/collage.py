"""Reddit collage (reddit/church_orientation_collage.png, 3000 x 1900) and the social card (header.png, 1200 x 630).
Run from anywhere: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
import pandas as pd
from figstyle import *

R = jload(os.path.join(DATA, "results.json"))
K = pd.read_pickle(os.path.join(WORK, "measured.pkl"))
F = pd.read_pickle(os.path.join(WORK, "feast.pkl"))
sw = R["summer_winter"]
SUMMER = ["John the Baptist", "Peter", "Peter and Paul", "Botolph", "Alban", "Etheldreda", "Barnabas"]
WINTER = ["Thomas", "Nicholas", "John the Evangelist", "Stephen", "Thomas Becket", "Andrew", "Edmund", "Catherine", "Clement"]
SRC = "Data: OpenStreetMap contributors (ODbL), Wikidata (CC0)  ·  Analysis and map: Dr Tristan Hotham  ·  maps.tristanhotham.com/church-orientation"


def gbmap(ax, ext, lw=0.55, L=0.042, tick_lw=0.55):
    basemap(ax, ext=ext, lw=0.6)
    d = K.sample(frac=1, random_state=1)
    ticks(ax, d.lon.values, d.lat.values, d.bearing.values, d.dev.values, L=L, lw=tick_lw, alpha=0.88)


def colourbar(fig, rect, fs=13):
    ax = fig.add_axes(rect)
    g = (np.linspace(0, 1, 361) ** 2 * 90)[None, :]
    ax.imshow(g, aspect="auto", cmap=DEV_CMAP, norm=DEV_NORM, extent=(0, 1, 0, 1))
    tk = [0, 5, 10, 20, 45, 90]
    ax.set_yticks([]); ax.set_xticks([math.sqrt(a / 90) for a in tk]); ax.set_xticklabels([f"{a}°" for a in tk], fontsize=fs)
    for s in ax.spines.values():
        s.set_color(INK); s.set_linewidth(1)
    return ax


def rose(ax, b, colour, pred, title):
    h, e = np.histogram(b, bins=72, range=(0, 180))
    h = h / h.max()
    th = np.radians((e[:-1] + e[1:]) / 2)
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.bar(th, h, width=np.radians(2.5), color=colour, edgecolor="none")
    ax.bar(th + math.pi, h, width=np.radians(2.5), color=colour, edgecolor="none", alpha=0.22)
    ax.plot([np.radians(pred)] * 2, [0, 1.12], color="#C7861C", lw=3.2, ls=(0, (4, 2.5)), solid_capstyle="round")
    ax.plot([np.radians(90)] * 2, [0, 1.12], color=MUT, lw=1.0, ls=(0, (1, 2)))
    ax.set_ylim(0, 1.15); ax.set_yticks([])
    ax.set_xticks(np.radians([0, 90, 180, 270])); ax.set_xticklabels(["N", "E", "S", "W"], fontsize=15)
    ax.set_facecolor("#FBF5E4"); ax.spines["polar"].set_color(MUT); ax.grid(color=RULE, lw=0.8)
    ax.set_title(title, fontsize=15.5, pad=16, linespacing=1.35)


def collage():
    fig = plt.figure(figsize=(20, 12.6667)); paper(fig)
    fig.text(0.025, 0.968, "Do churches face sunrise on their saint's day?", fontproperties=DISP, fontsize=46, va="top")
    fig.text(0.025, 0.893, f"The long axis of {R['n']['measured']:,} church footprints in OpenStreetMap, measured against true east, with patron saints from Wikidata.",
             fontproperties=SERP, fontsize=21, color=MUT, va="top")
    # map
    ax = fig.add_axes([0.0, 0.045, 0.46, 0.8])
    ext = (-10.5, 4.6, 49.85, 59.5)
    gbmap(ax, ext)
    # legend and notes on open sea only: the North Sea (east of Scotland) and the Atlantic south-west of Ireland
    def at(lon, lat):
        return proj(lon, lat)
    x0, y0 = at(0.9, 58.75)
    x1, _ = at(4.4, 58.75)
    cb = ax.inset_axes([x0, y0, x1 - x0, 0.17], transform=ax.transData)
    g = (np.linspace(0, 1, 361) ** 2 * 90)[None, :]
    cb.imshow(g, aspect="auto", cmap=DEV_CMAP, norm=DEV_NORM, extent=(0, 1, 0, 1))
    tk = [0, 10, 45, 90]
    cb.set_yticks([]); cb.set_xticks([math.sqrt(v / 90) for v in tk]); cb.set_xticklabels([f"{v}°" for v in tk], fontsize=12)
    for sp in cb.spines.values():
        sp.set_color(INK)
    ax.text(*at(0.9, 59.1), "Turn from due east,\neither way", fontsize=13.5, color=INK, va="bottom", zorder=9)
    ax.text(*at(0.9, 58.2), "Each stroke is one church,\ndrawn along its axis; the\ntilt shows the turn north\nor south of east.", fontsize=13, color=INK, va="top", linespacing=1.35, zorder=9)
    ax.text(*at(0.9, 56.55), f"Within 10° of east:\nhistoric parish\nchurches {R['old']['within10']:.0f}%\nFree Church chapels {R['by_denom']['nonconformist']['within10']:.0f}%\nat random {R['chance10']:.0f}%", fontsize=13, color=INK, va="top", linespacing=1.35, zorder=9)
    ax.text(*at(-10.35, 51.05), "Red: close to east,\nmostly old parish\nchurches. Grey: chapels\nand town churches.", fontsize=12.5, color=INK, va="top", linespacing=1.35, zorder=9)
    # saints scatter
    S = pd.DataFrame(R["saints_old"])
    a2 = fig.add_axes([0.54, 0.53, 0.43, 0.275]); a2.set_facecolor("#FBF5E4")
    x = np.array([40, 140])
    a2.plot(x, x, color="#C7861C", lw=2.4, ls=(0, (5, 4)))
    a2.text(118, 132, "if churches faced the\nsunrise on their saint's day", color="#8A5A10", fontsize=14, ha="right", va="top")
    a2.axhline(90, color=MUT, lw=1); a2.text(141, 91.5, "due east", color=MUT, fontsize=13, ha="right")
    a2.scatter(S.pred, S.mean_bearing, s=np.sqrt(S.n) * 7, color="#8E2F1F", edgecolor=INK, lw=0.8, zorder=4)
    for nm, dx, dy in (("John the Baptist", 0, -40), ("Nicholas", 0, -40), ("All Saints", 0, -40), ("Michael", 0, -40), ("Peter", 18, 30), ("Andrew", -10, 30)):
        r = S[S.saint == nm].iloc[0]
        a2.annotate(nm, (r.pred, r.mean_bearing), xytext=(dx, dy), textcoords="offset points", ha="center", fontsize=13, color=INK,
                    arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8, shrinkA=0, shrinkB=6))
    a2.set_xlim(40, 140); a2.set_ylim(40, 140)
    a2.set_xlabel("Sunrise on the saint's feast day (degrees from north)", fontsize=13.5, labelpad=4)
    a2.set_ylabel("Average axis of\ntheir old churches", fontsize=14)
    a2.tick_params(labelsize=12)
    for s in ("top", "right"):
        a2.spines[s].set_visible(False)
    fig.text(0.54, 0.826, f"Each dot is a saint with 25+ historic churches.\nThe feast-day sunrise moves {R['saint_regression']['pred_span']:.0f}°; the churches move {R['saint_regression']['obs_span']:.0f}°.",
             fontsize=14, color=INK)
    # summer vs winter roses
    sm = K[K.old & K.saint.isin(SUMMER)]
    wn = K[K.old & K.saint.isin(WINTER)]
    r1 = fig.add_axes([0.555, 0.055, 0.17, 0.235], projection="polar")
    assert len(sm) == sw["summer_n_all"] and len(wn) == sw["winter_n_all"]
    rose(r1, sm.bearing, "#C4471F", sw["summer_pred"], f"Midsummer saints, {sw["summer_n_all"]:,} churches")
    r2 = fig.add_axes([0.785, 0.055, 0.17, 0.235], projection="polar")
    rose(r2, wn.bearing, "#2F5D8C", sw["winter_pred"], f"Midwinter saints, {sw["winter_n_all"]:,} churches")
    fig.text(0.755, 0.44, f"Gold dashes: feast-day sunrise ({sw['summer_pred']:.0f}° and {sw['winter_pred']:.0f}°). Their churches: {sw['summer_mean_bearing']:.1f}° and {sw['winter_mean_bearing']:.1f}°.\nMidsummer: John the Baptist, Peter, Botolph...  Midwinter: Nicholas, Thomas, Andrew...",
             fontsize=13, color=INK, ha="center", va="top", linespacing=1.4)
    fig.text(0.025, 0.014, SRC, fontsize=12.5, color=MUT)
    fig.savefig(os.path.join(ROOT, "reddit", "church_orientation_collage.png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def header():
    fig = plt.figure(figsize=(8, 4.2)); paper(fig)
    ax = fig.add_axes([0.52, 0.0, 0.48, 1.0])
    gbmap(ax, (-6.2, 2.0, 50.0, 55.9), L=0.05, tick_lw=0.75)
    fig.text(0.045, 0.88, "Which way do\nthe UK's churches\nface?", fontproperties=DISP, fontsize=27, va="top", linespacing=1.0)
    fig.text(0.045, 0.40, f"{R['n']['measured']:,} churches measured", fontsize=11, color=INK)
    fig.text(0.045, 0.33, f"{R['old']['within10']:.0f}% of old churches within 10° of east", fontsize=11, color=INK)
    fig.text(0.045, 0.26, f"Midsummer and midwinter saints: {abs(sw['obs_gap']):.1f}° apart", fontsize=11, color=INK)
    fig.text(0.045, 0.08, "Dr Tristan Hotham · maps.tristanhotham.com", fontsize=9, color=MUT)
    fig.savefig(os.path.join(ROOT, "header.png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


collage(); header()
from PIL import Image
print(Image.open(os.path.join(ROOT, "reddit", "church_orientation_collage.png")).size, Image.open(os.path.join(ROOT, "header.png")).size)
