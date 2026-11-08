"""Step 8: the paper, release/paper/Hotham_Church_Orientation.tex and .pdf (xelatex), filled from data/results.json.
10.5281/zenodo.24052501 and https://doi.org/10.5281/zenodo.24052501 stay as placeholders for the publisher (they are typeset as-is until filled)."""
import re, subprocess, shutil
from common import *

R = jload(f"{DATA}/results.json")
P = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Church_Orientation"
KEEP = {"DOI", "DOI_URL"}
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()


def tex(s):
    return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")


rows = []
for key, lab, items in [("by_period", "Date", [("medieval", "Before 1540"), ("early", "1540 to 1799"), ("victorian", "1800 to 1913"), ("modern", "1914 onwards"), ("unknown", "Not known")]),
                        ("by_grade", "Listing", [("I", "Grade I"), ("II*", "Grade II*"), ("II", "Grade II"), ("A", "Category A"), ("B", "Category B"), ("C", "Category C"), ("none", "None found")]),
                        ("by_denom", "Denomination", [(k, DNAME[k]) for k in ["anglican", "catholic", "scotland", "nonconformist", "orthodox", "other", "unknown"]]),
                        ("by_nation", "Nation", [(k, k) for k in ["England", "Wales", "Scotland", "Northern Ireland"]])]:
    rows.append("\\midrule\\multicolumn{7}{l}{\\textit{%s}}\\\\" % lab)
    for k, nm in items:
        v = R[key][k]
        rows.append(f"{tex(nm)} & {v['n']:,} & {v['within5']:.1f} & {v['within10']:.1f} & {v['within20']:.1f} & {v['beyond45']:.1f} & {v['median_adev']:.1f}\\\\")
o = R["old"]; a = R["all"]
rows.insert(0, f"All measured & {a['n']:,} & {a['within5']:.1f} & {a['within10']:.1f} & {a['within20']:.1f} & {a['beyond45']:.1f} & {a['median_adev']:.1f}\\\\\nHistoric parish churches & {o['n']:,} & {o['within5']:.1f} & {o['within10']:.1f} & {o['within20']:.1f} & {o['beyond45']:.1f} & {o['median_adev']:.1f}\\\\")
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Share of churches (\\%) within 5°, 10° and 20° of due east and beyond 45°, and the median absolute deviation (degrees), by group.}\\label{tab:groups}\n"
      "\\begin{tabular}{lrrrrrr}\\toprule Group & n & $\\le$5° & $\\le$10° & $\\le$20° & $>$45° & Median\\\\\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}")
fr = []
for k, lab in [("old", "Historic parish churches"), ("medieval_dated", "Dated before 1540"), ("victorian_modern", "Dated 1800 onwards"), ("all", "All churches")]:
    v = R["feast"][k]
    fr.append(f"{lab} & {v['n']:,} & {v['n_saints']} & {v['mean_abs_err']:.2f} & {v['perm_mean']:.2f} & {v['p_value']:.2f} & {v['within3']:.1f} & {v['within3_perm']:.1f}\\\\")
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{The feast-day test: mean absolute difference (degrees) between axis and feast-day sunrise for the real saints and, on average, for 10,000 random shuffles of the saints; one-sided p-value; and the share of churches (\\%) within 3° of the predicted sunrise.}\\label{tab:feast}\n"
      "\\begin{tabular}{lrrrrrrr}\\toprule Churches & n & Saints & Real & Shuffled & p & $\\le$3° real & $\\le$3° shuffled\\\\\\midrule\n" + "\n".join(fr) + "\n\\bottomrule\\end{tabular}\\end{table}")
import pandas as pd
fe = pd.read_csv(os.path.join(ROOT, "code", "feasts.csv"))
MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fd = {r.saint: f"{r.day} {MON[r.month]}" for r in fe.itertuples()}
sr = [f"{tex(r['saint'])} & {fd[r['saint']]} & {r['n']} & {r['pred_gregorian']:.1f} & {r['pred']:.1f} & {r['mean_bearing']:.1f} & {r['se']:.2f}\\\\" for r in R["saints_old"]]
TS = ("\\begin{longtable}{lrrrrrr}\\caption{Saints with 25 or more historic parish churches: predicted feast-day sunrise (degrees from north) with the date as written and moved to the solar year of foundation, and the mean axis of their churches with its standard error.}\\label{tab:saints}\\\\\n"
      "\\toprule Saint & Feast & n & Sunrise (as written) & Sunrise (Julian) & Mean axis & s.e.\\\\\\midrule\\endhead\n" + "\n".join(sr) + "\n\\bottomrule\\end{longtable}")
t = t.replace("{{TABLE_GROUPS}}", TG).replace("{{TABLE_FEAST}}", TF).replace("{{TABLE_SAINTS}}", TS)
t = t.replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO).replace("{{AI}}", AI)
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
left = set(re.findall(r"\{\{([^{}]+)\}\}", t))
assert left <= KEEP, left
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in t, bad
os.makedirs(P, exist_ok=True)
open(os.path.join(P, NAME + ".tex"), "w", encoding="utf-8").write(t)
# compile a copy with readable placeholders (the publisher recompiles with the DOI filled)
tc = t.replace("\\href{https://doi.org/10.5281/zenodo.24052501}{10.5281/zenodo.24052501}", "\\texttt{\\{\\{DOI\\}\\}}").replace("\\url{https://doi.org/10.5281/zenodo.24052501}", "\\texttt{\\{\\{DOI\\_URL\\}\\}}")
assert "{{" not in tc.replace("\\{\\{", ""), "placeholder left in compile copy"
open(os.path.join(P, "_build.tex"), "w", encoding="utf-8").write(tc)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "_build.tex"], cwd=P, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-3000:]); raise SystemExit("xelatex failed")
shutil.move(os.path.join(P, "_build.pdf"), os.path.join(P, NAME + ".pdf"))
for ext in ("aux", "log", "out", "tex"):
    f = os.path.join(P, "_build." + ext)
    if os.path.exists(f):
        os.remove(f)
pages = subprocess.run(["pdfinfo", os.path.join(P, NAME + ".pdf")], capture_output=True, text=True).stdout
print([l for l in pages.splitlines() if l.startswith("Pages")])
