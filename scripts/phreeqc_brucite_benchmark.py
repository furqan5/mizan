"""Supplementary benchmark: brucite saturation pH against PHREEQC (wateq4f.dat).

Pre-registered in docs/staged/phreeqc_brucite_supplement_preregistration.md,
committed before PHREEQC was run on brucite. phreeqc.dat has no Brucite
phase, so the reference databases are wateq4f.dat (gated, run B1) and
llnl.dat (constants only, run B2) from the same PHREEQC installer.

    python scripts/phreeqc_brucite_benchmark.py build
    python scripts/phreeqc_brucite_benchmark.py run --phreeqc-exe EXE --db-dir DIR
    python scripts/phreeqc_brucite_benchmark.py score
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import phreeqc_grid_benchmark as g  # noqa: E402

ch = g.ch
OUT = g.OUT / "brucite"
WATEQ4F_SHA256 = "8bec1e1ed3fc686444bd00ba386883b1ff6d4349f9346049a6bd359c981e9945"
LLNL_SHA256 = "b6e397c0294866dddc6aa0afb710a272051b5969716dffed5cbcc1aa6e03b744"
TOL_PH = 0.05
COLS_B1 = "id T_C pH mu si_brucite lk_brucite lk_oh Mg_total Mg_free lg_mg".split()
COLS_B2 = "id T_C lk_brucite lk_oh".split()


def deck_b1(pts):
    head = ("TITLE Mizan brucite supplement, run B1, wateq4f.dat\nPRINT\n -reset false\n"
            "SELECTED_OUTPUT 1\n -file selected_b1.tsv\n -reset false\n -high_precision true\n"
            "USER_PUNCH 1\n -headings " + " ".join(COLS_B1) + "\n -start\n"
            ' 10 PUNCH CELL_NO, TC, -LA("H+"), MU, SI("Brucite")\n'
            ' 20 PUNCH LK_PHASE("Brucite"), LK_SPECIES("OH-"), TOT("Mg"), MOL("Mg+2"), LG("Mg+2")\n'
            " -end\n")
    body = []
    for p in pts:
        L = [f"SOLUTION {p['point'] + 1}", f" temp {p['T_C']:.17g}",
             " pH 9.0 Brucite 0.0", " units mol/kgw", " -water 1"]
        for k, el in g.ELEMENT.items():
            v = p["molality"][k]
            if v > 0:
                L.append(f" {el} {v:.17g}")
        L.append(f" C(4) {p['molality']['HCO3']:.17g}")
        body.append("\n".join(L) + "\nEND\n")
    return head + "".join(body)


def deck_b2():
    head = ("TITLE Mizan brucite supplement, run B2, llnl.dat constants\nPRINT\n -reset false\n"
            "SELECTED_OUTPUT 1\n -file selected_b2.tsv\n -reset false\n -high_precision true\n"
            "USER_PUNCH 1\n -headings " + " ".join(COLS_B2) + "\n -start\n"
            ' 10 PUNCH CELL_NO, TC, LK_PHASE("Brucite"), LK_SPECIES("OH-")\n -end\n')
    body = [f"SOLUTION {i + 1}\n temp {T:.17g}\n pH 7.0\n units mol/kgw\n Mg 0.001\n Cl 0.002\nEND\n"
            for i, T in enumerate(g.TEMPS_C)]
    return head + "".join(body)


def cmd_build(_a):
    OUT.mkdir(parents=True, exist_ok=True)
    pts = json.loads((g.OUT / "grid.json").read_text(encoding="utf-8"))
    (OUT / "deck_b1.pqi").write_text(deck_b1(pts), encoding="utf-8")
    (OUT / "deck_b2.pqi").write_text(deck_b2(), encoding="utf-8")
    print(f"B1 {len(pts)} solutions, B2 {len(g.TEMPS_C)} solutions -> {OUT}")


def cmd_run(a):
    exe, d = pathlib.Path(a.phreeqc_exe), pathlib.Path(a.db_dir)
    if g.sha256(exe) != g.EXE_SHA256:
        raise SystemExit("not the registered phreeqc.exe")
    if g.sha256(d / "wateq4f.dat") != WATEQ4F_SHA256 or g.sha256(d / "llnl.dat") != LLNL_SHA256:
        raise SystemExit("database hash mismatch")
    if (OUT / "selected_b1.tsv").exists():
        raise SystemExit("a stored run exists; each run is made once")
    prov = {"phreeqc_exe_sha256": g.EXE_SHA256, "wateq4f_dat_sha256": WATEQ4F_SHA256,
            "llnl_dat_sha256": LLNL_SHA256,
            "database_source": "phreeqcx64.cab of phreeqc-3.9.0-17591-x64.msi (its "
                               "phreeqc.dat matches the registered hash)",
            "preregistration": "docs/staged/phreeqc_brucite_supplement_preregistration.md",
            "runs": {}}
    for tag, db in (("b1", "wateq4f.dat"), ("b2", "llnl.dat")):
        r = subprocess.run([str(exe), f"deck_{tag}.pqi", f"deck_{tag}.out", str(d / db)],
                           cwd=OUT, capture_output=True, text=True, timeout=1800)
        (OUT / f"console_{tag}.txt").write_text(
            (r.stdout + r.stderr).replace(str(d), "<db_dir>"), encoding="utf-8")
        prov["runs"][tag] = {"command": f"phreeqc.exe deck_{tag}.pqi deck_{tag}.out <db_dir>/{db}",
                             "returncode": r.returncode,
                             "deck_sha256": g.sha256(OUT / f"deck_{tag}.pqi")}
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(json.dumps(prov["runs"], indent=2))


def compare(pts=None, rows=None):
    pts = json.loads((g.OUT / "grid.json").read_text(encoding="utf-8")) if pts is None else pts
    rows = g.read_selected(OUT / "selected_b1.tsv") if rows is None else rows
    if len(rows) != len(pts):
        raise ValueError(f"{len(rows)} B1 rows for {len(pts)} points")
    recs = {}
    for p, r in zip(pts, rows):
        if int(r["id"]) != p["point"] + 1 or abs(r["si_brucite"]) > 1e-6:
            raise ValueError(f"B1 row for point {p['point']} is not at brucite saturation")
        if not g._close(r["Mg_total"], p["molality"]["Mg"]):
            raise ValueError(f"Mg did not round-trip at point {p['point']}")
        w = getattr(ch, p["composition"]).concentrate(float(p["cycles"]))
        recs[(p["composition"], p["cycles"], p["T_C"])] = {
            "engine": ch.ph_saturation_brucite(p["T_C"], w), "phreeqc": r["pH"],
            "lk_hydroxide_phreeqc": r["lk_brucite"] + 2 * r["lk_oh"], "I": r["mu"]}
    out = []
    for (comp, c, T), v in recs.items():
        base = recs[(comp, c, 25.0)]
        row = {"composition": comp, "cycles": c, "T_C": T, **v,
               "offset": v["engine"] - v["phreeqc"]}
        if T != 25.0:
            row["D"] = (v["engine"] - base["engine"]) - (v["phreeqc"] - base["phreeqc"])
            row["within"] = abs(row["D"]) <= TOL_PH
        out.append(row)
    return out


def verdict(rows):
    gated = [r for r in rows if "D" in r]
    share = sum(r["within"] for r in gated) / len(gated)
    med45 = statistics.median(r["D"] for r in gated if r["T_C"] == 45.0)
    return {"n_gated": len(gated), "share_within": share,
            "verdict": "PASS" if share >= 0.95 else "FAIL",
            "median_D_by_T": {str(T): statistics.median(r["D"] for r in gated if r["T_C"] == T)
                              for T in (35.0, 45.0, 55.0)},
            "confirms_suspected_defect": share < 0.95 and med45 < -0.30}


def cmd_score(a):
    rows = compare()
    v = verdict(rows)
    b2 = g.read_selected(OUT / "selected_b2.tsv")
    v["logK_hydroxide_form"] = {
        str(r["T_C"]): {"engine": ch._vant_hoff(-11.18, -27.1, r["T_C"]) if a.pre_fix
                        else None,
                        "llnl": r["lk_brucite"] + 2 * r["lk_oh"]} for r in b2}
    v["offset_range_pH"] = [min(r["offset"] for r in rows), max(r["offset"] for r in rows)]
    v["worst"] = sorted((r for r in rows if "D" in r), key=lambda r: r["D"])[:3]
    name = "score_prefix.json" if a.pre_fix else "score_postfix.json"
    (OUT / name).write_text(json.dumps(v, indent=2), encoding="utf-8")
    print(json.dumps({k: v[k] for k in v if k != "worst"}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run")
    r.add_argument("--phreeqc-exe", required=True)
    r.add_argument("--db-dir", required=True)
    s = sub.add_parser("score")
    s.add_argument("--pre-fix", action="store_true")
    a = ap.parse_args()
    {"build": cmd_build, "run": cmd_run, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    main()
