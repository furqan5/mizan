"""Multi-composition benchmark of src/chemistry.py against PHREEQC 3.9.0.

Pre-registered in docs/staged/phreeqc_benchmark_preregistration.md, which was
committed before PHREEQC was run on this grid. Read that file for the grid,
the input mapping, the tolerances and the pass criterion; this script only
implements them.

    python scripts/phreeqc_grid_benchmark.py build          # grid.json + deck.pqi
    python scripts/phreeqc_grid_benchmark.py run --phreeqc-dir DIR
                                                             # ONE PHREEQC run
    python scripts/phreeqc_grid_benchmark.py parse          # reference.csv
    python scripts/phreeqc_grid_benchmark.py score          # score.json

`run` needs a local PHREEQC install and refuses to overwrite a stored run.
`parse` and `score` need only the stored files, so the comparison is
reproducible without PHREEQC -- tests/test_phreeqc_grid.py uses them.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import chemistry as ch  # noqa: E402

OUT = ROOT / "data" / "reference" / "phreeqc_benchmark_20260917"

# --- registered grid (section 2) ------------------------------------------
DOE_RECIPES = ("DOE_SYN_MWW_NF_COC4", "DOE_SYN_MWW_NF_COC4_TABLE_2_3_2",
               "DOE_SYN_MWW_COC4")
CYCLES = (1, 2, 3, 4, 5, 6, 7, 8)
TEMPS_C = (25.0, 35.0, 45.0, 55.0)
# --- registered carbonate bracket (section 3) -----------------------------
C4_MULTIPLIERS = (1.00, 1.10, 1.25, 1.50, 2.00, 3.00)
# --- registered reference (section 1) -------------------------------------
PHREEQC_VERSION = "3.9.0-17591"
EXE_SHA256 = "5147679081f53abd4a40d1ba07b3cf7ee5078df9d3510c6378ff5d45db6437c8"
DAT_SHA256 = "5745f0be5f5f585e72c647895b9b182388ab1f018db3d654529ce2461de499f1"

ELEMENT = {"Ca": "Ca", "Mg": "Mg", "Na": "Na", "K": "K", "Cl": "Cl",
           "SO4": "S(6)", "NO3": "N(5)", "SiO2": "Si", "PO4": "P"}

MINERALS = {  # key: (PHREEQC column, engine key, engine log K, components)
    "calcite": ("si_calcite", "SI_calcite", ch.log_k_calcite, ("Ca", "HCO3")),
    "gypsum": ("si_gypsum", "SI_gypsum", ch.log_k_gypsum, ("Ca", "SO4")),
    "silica_am": ("si_silica", "SI_silica_am", ch.log_k_silica_am, ("SiO2",)),
    "hydroxyapatite": ("si_hap", "SI_hydroxyapatite", ch.log_k_hydroxyapatite,
                       ("Ca", "PO4")),
}
ION_COUNT_SCALE = {"calcite": 1.0, "gypsum": 1.0, "silica_am": 1.0,
                   "hydroxyapatite": 4.0}      # section 5: 8 ions / 2 ions

COLUMNS = ("id T_C pH mu pct_err Ca S6 C4 Si P alk hco3_sum "
           "si_calcite si_gypsum si_silica si_hap "
           "lk_calcite lk_gypsum lk_silica lk_hap "
           "lg_ca lg_so4 lg_hco3 lg_h4sio4 lg_hpo4").split()


def compositions():
    names = sorted(n for n in dir(ch) if isinstance(getattr(ch, n), ch.Water))
    valid = [n for n in names
             if all(ok for ok, _ in ch.validate_analysis(getattr(ch, n)).values())]
    return valid + [n for n in DOE_RECIPES if n not in valid]


def grid():
    pts = []
    for name in compositions():
        w = getattr(ch, name)
        for c in CYCLES:
            cw = w.concentrate(float(c))
            m = cw.molality()
            for T in TEMPS_C:
                pts.append({"point": len(pts), "composition": name,
                            "cycles": c, "T_C": T, "pH": cw.pH,
                            "molality": {k: m[k] for k in
                                         list(ELEMENT) + ["HCO3"]}})
    return pts


def tolerance(I):
    if I <= 0.1:
        return 0.05
    if I <= 0.5:
        return 0.10
    return None


def _solution(sid, p, *, c4=None, alk=None):
    L = [f"SOLUTION {sid}", f" temp {p['T_C']:.17g}", f" pH {p['pH']:.17g}",
         " units mol/kgw", " -water 1"]
    for k, el in ELEMENT.items():
        v = p["molality"][k]
        if v > 0:
            L.append(f" {el} {v:.17g}")
    if c4 is not None:
        L.append(f" C(4) {c4:.17g}")
    if alk is not None:
        L.append(f" Alkalinity {alk:.17g}")
    return "\n".join(L) + "\nEND\n"


def blocks(pts):
    """(solution id, point, C(4) multiplier).

    The registered deck also carried an `Alkalinity` block per point as a
    diagnostic. Run 1 stopped at solution 497 with "Is non-carbonate
    alkalinity greater than total alkalinity?" -- the DOE Table 2.3.2 recipe
    carries more phosphate (0.48 mM) than bicarbonate (0.40 mM), so an
    alkalinity input cannot be satisfied there. That is the pre-registered
    reason Alkalinity was not the primary mapping. The diagnostic is replaced
    by the f = 1.00 block already in the deck (C(4) = the engine's HCO3), and
    recorded in the pre-registration addendum and execution_error_run1/.
    """
    out, sid = [], 1
    for p in pts:
        for f in C4_MULTIPLIERS:
            out.append((sid, p["point"], f)); sid += 1
    return out


def deck(pts):
    head = ("TITLE Mizan chemistry engine benchmark, pre-registered in "
            "docs/staged/phreeqc_benchmark_preregistration.md\n"
            "PRINT\n -reset false\n"
            "SELECTED_OUTPUT 1\n -file selected.tsv\n -reset false\n"
            " -high_precision true\n"
            "USER_PUNCH 1\n -headings " + " ".join(COLUMNS) + "\n -start\n"
            ' 10 PUNCH CELL_NO, TC, -LA("H+"), MU, PERCENT_ERROR\n'
            ' 20 PUNCH TOT("Ca"), TOT("S(6)"), TOT("C(4)"), TOT("Si"), TOT("P"), ALK\n'
            ' 30 PUNCH MOL("HCO3-") + MOL("CaHCO3+") + MOL("MgHCO3+") + MOL("NaHCO3") + MOL("KHCO3")\n'
            ' 40 PUNCH SI("Calcite"), SI("Gypsum"), SI("SiO2(a)"), SI("Hydroxyapatite")\n'
            ' 50 PUNCH LK_PHASE("Calcite"), LK_PHASE("Gypsum"), LK_PHASE("SiO2(a)"), LK_PHASE("Hydroxyapatite")\n'
            ' 60 PUNCH LG("Ca+2"), LG("SO4-2"), LG("HCO3-"), LG("H4SiO4"), LG("HPO4-2")\n'
            " -end\n")
    byid = {p["point"]: p for p in pts}
    body = []
    for sid, pid, kind in blocks(pts):
        p = byid[pid]
        body.append(_solution(sid, p, c4=kind * p["molality"]["HCO3"]))
    return head + "".join(body)


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def cmd_build(_a):
    OUT.mkdir(parents=True, exist_ok=True)
    pts = grid()
    (OUT / "grid.json").write_text(json.dumps(pts, indent=1), encoding="utf-8")
    (OUT / "deck.pqi").write_text(deck(pts), encoding="utf-8")
    print(f"{len(pts)} points, {len(blocks(pts))} PHREEQC solutions -> {OUT}")


def cmd_run(a):
    d = pathlib.Path(a.phreeqc_dir)
    exe, dat = d / "phreeqc.exe", d / "phreeqc.dat"
    if sha256(exe) != EXE_SHA256 or sha256(dat) != DAT_SHA256:
        raise SystemExit("PHREEQC executable or database is not the registered one")
    if (OUT / "selected.tsv").exists():
        raise SystemExit("a stored run exists; the benchmark is run once")
    cmd = [str(exe), "deck.pqi", "deck.out", str(dat)]
    r = subprocess.run(cmd, cwd=OUT, capture_output=True, text=True, timeout=1800)
    (OUT / "console.txt").write_text(r.stdout + r.stderr, encoding="utf-8")
    prov = {"phreeqc_version": PHREEQC_VERSION,
            "phreeqc_banner": "the executable prints 'PHREEQC_3.8.9, October 13, "
                              "2025'; it is the binary installed by "
                              "phreeqc-3.9.0-17591-x64.msi, identified by hash",
            "phreeqc_exe_sha256": EXE_SHA256,
            "phreeqc_dat_sha256": DAT_SHA256,
            "command": "phreeqc.exe deck.pqi deck.out <path>/phreeqc.dat "
                       "(cwd = this directory)",
            "returncode": r.returncode, "deck_sha256": sha256(OUT / "deck.pqi"),
            "run": "2 (run 1 was an execution error, see execution_error_run1/)",
            "preregistration": "docs/staged/phreeqc_benchmark_preregistration.md"}
    (OUT / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(json.dumps(prov, indent=2))
    if r.returncode != 0:
        raise SystemExit("PHREEQC execution error; see console.txt")


def read_selected(path=None):
    path = OUT / "selected.tsv" if path is None else path
    rows = []
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().split()
        for line in fh:
            if line.strip():
                rows.append(dict(zip(head, map(float, line.split()))))
    return rows


def _close(a, b, rel=1e-7, ab=1e-10):
    return abs(a - b) <= ab + rel * abs(b)


def reference(pts, rows):
    """Interpolate every PHREEQC quantity to the engine's HCO3 definition."""
    bl = blocks(pts)
    if len(rows) != len(bl):
        raise ValueError(f"{len(rows)} PHREEQC rows for {len(bl)} solutions")
    per = {}
    for (sid, pid, kind), r in zip(bl, rows):
        if int(r["id"]) != sid:
            raise ValueError(f"solution id mismatch {r['id']} vs {sid}")
        p = pts[pid]
        m = p["molality"]
        for col, key in (("Ca", "Ca"), ("S6", "SO4"), ("Si", "SiO2"), ("P", "PO4")):
            if not _close(r[col], m[key]):
                raise ValueError(f"total {col} did not round-trip at solution {sid}")
        if not (_close(r["pH"], p["pH"], ab=1e-6) and _close(r["T_C"], p["T_C"], ab=1e-6)):
            raise ValueError(f"pH or temperature changed at solution {sid}")
        if not _close(r["C4"], kind * m["HCO3"]):
            raise ValueError(f"C(4) did not round-trip at solution {sid}")
        per.setdefault(pid, {})[kind] = r
    out = []
    for p in pts:
        blk, target = per[p["point"]], p["molality"]["HCO3"]
        rec = {"point": p["point"], "bracketed": False}
        for f0, f1 in zip(C4_MULTIPLIERS, C4_MULTIPLIERS[1:]):
            s0, s1 = blk[f0]["hco3_sum"], blk[f1]["hco3_sum"]
            if s0 <= target <= s1:
                w = (math.log10(target) - math.log10(s0)) / (math.log10(s1) - math.log10(s0))
                for col in COLUMNS[1:]:
                    rec[col] = blk[f0][col] + w * (blk[f1][col] - blk[f0][col])
                rec["bracketed"], rec["bracket"] = True, [f0, f1]
                break
        for col in ("si_calcite", "si_gypsum", "si_hap", "pct_err"):
            rec["c4eq_" + col] = blk[1.00][col]
        out.append(rec)
    return out


def cmd_parse(_a):
    pts = json.loads((OUT / "grid.json").read_text(encoding="utf-8"))
    ref = reference(pts, read_selected())
    cols = sorted({k for r in ref for k in r})
    with open(OUT / "reference.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=cols)
        wr.writeheader()
        for r in ref:
            wr.writerow({k: (json.dumps(v) if isinstance(v, list) else v)
                         for k, v in r.items()})
    print(f"{len(ref)} reference points, {sum(r['bracketed'] for r in ref)} bracketed")


def load_reference():
    with open(OUT / "reference.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ref = {}
    for r in rows:
        rec = {}
        for k, v in r.items():
            if k == "bracketed":
                rec[k] = v == "True"
            elif k == "bracket":
                rec[k] = json.loads(v) if v else None
            else:
                rec[k] = float(v) if v not in ("", None) else None
        ref[int(rec["point"])] = rec
    return ref


def compare(pts=None, ref=None):
    """Engine (live code) against stored PHREEQC values, per section 4-6."""
    pts = json.loads((OUT / "grid.json").read_text(encoding="utf-8")) if pts is None else pts
    ref = load_reference() if ref is None else ref
    rows = []
    for p in pts:
        w = getattr(ch, p["composition"]).concentrate(float(p["cycles"]))
        live = w.molality()
        for k, v in p["molality"].items():
            if not _close(live[k], v, rel=1e-12, ab=1e-15):
                raise ValueError(f"{p['composition']} {k} changed since the grid was built")
        st = ch.saturation_state(w, p["T_C"])
        I = ch.speciate(w, p["T_C"])["I"]
        r = ref[p["point"]]
        for mineral, (col, key, lk, comps) in MINERALS.items():
            if not all(p["molality"][c] > 0 for c in comps):
                continue
            tau = tolerance(I)
            row = {"point": p["point"], "composition": p["composition"],
                   "cycles": p["cycles"], "T_C": p["T_C"], "I": I,
                   "mineral": mineral, "engine_SI": st[key]}
            if r["bracketed"]:
                d = st[key] - r[col]
                row.update(ref_SI=r[col], dSI=d,
                           dSI_same_K=st[key] - (r[col] + r["lk_" + col[3:]] - lk(p["T_C"])),
                           ref_pct_charge_error=r["pct_err"])
                if mineral != "silica_am":
                    row["dSI_C4_equals_HCO3_mapping"] = st[key] - r["c4eq_" + col]
            else:
                d = None
                row.update(ref_SI=None, dSI=None)
            row["tolerance"] = None if tau is None else tau * ION_COUNT_SCALE[mineral]
            row["gated"] = tau is not None
            row["within"] = (d is not None and tau is not None
                             and abs(d) <= row["tolerance"])
            row["within_unscaled"] = (d is not None and tau is not None
                                      and abs(d) <= tau)
            rows.append(row)
    return rows


def verdict(rows):
    g = [r for r in rows if r["gated"]]
    share = sum(r["within"] for r in g) / len(g)
    per = {}
    for m in MINERALS:
        mg = [r for r in g if r["mineral"] == m]
        if mg:
            per[m] = sum(r["within"] for r in mg) / len(mg)
    ok = share >= 0.95 and all(v >= 0.90 for v in per.values())
    return {"n_gated": len(g), "share_within": share, "share_by_mineral": per,
            "criterion": ">= 95 % overall and >= 90 % for every mineral",
            "verdict": "PASS" if ok else "FAIL"}


def _shares(rows, key):
    out = {}
    for r in rows:
        if r["gated"]:
            out.setdefault(str(r[key]), []).append(r["within"])
    return {k: sum(v) / len(v) for k, v in out.items()}


def cmd_score(_a):
    rows = compare()
    v = verdict(rows)
    g = [r for r in rows if r["gated"]]
    band = lambda r: "I<=0.1" if r["I"] <= 0.1 else "0.1<I<=0.5"
    for r in g:
        r["band"] = band(r)
    worst = sorted((r for r in g if r["dSI"] is not None),
                   key=lambda r: -abs(r["dSI"]) / r["tolerance"])[:10]
    hap = [r for r in g if r["mineral"] == "hydroxyapatite"]
    summary = {
        **v,
        "share_by_temperature": _shares(g, "T_C"),
        "share_by_composition": _shares(g, "composition"),
        "share_by_I_band": _shares(g, "band"),
        "hydroxyapatite_share_within_UNSCALED_tolerance":
            sum(r["within_unscaled"] for r in hap) / len(hap) if hap else None,
        "max_abs_dSI_by_mineral": {m: max(abs(r["dSI"]) for r in g
                                          if r["mineral"] == m and r["dSI"] is not None)
                                   for m in MINERALS if any(r["mineral"] == m for r in g)},
        "max_abs_dSI_same_K_by_mineral": {m: max(abs(r["dSI_same_K"]) for r in g
                                                 if r["mineral"] == m and r["dSI"] is not None)
                                          for m in MINERALS if any(r["mineral"] == m for r in g)},
        "max_abs_dSI_C4_equals_HCO3_mapping_by_mineral": {
            m: max(abs(r["dSI_C4_equals_HCO3_mapping"]) for r in g
                   if r["mineral"] == m and r.get("dSI_C4_equals_HCO3_mapping") is not None)
            for m in ("calcite", "gypsum", "hydroxyapatite")},
        "reference_pct_charge_error_range": [min(r["ref_pct_charge_error"] for r in g),
                                             max(r["ref_pct_charge_error"] for r in g)],
        "worst_ten_by_dSI_over_tolerance": [
            {k: r[k] for k in ("composition", "cycles", "T_C", "I", "mineral",
                               "engine_SI", "ref_SI", "dSI", "dSI_same_K", "tolerance")}
            for r in worst],
        "preregistration": "docs/staged/phreeqc_benchmark_preregistration.md",
    }
    (OUT / "score.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    with open(OUT / "comparison.csv", "w", newline="", encoding="utf-8") as fh:
        keys = sorted({k for r in rows for k in r})
        wr = csv.DictWriter(fh, fieldnames=keys)
        wr.writeheader()
        wr.writerows(rows)
    print(json.dumps({k: summary[k] for k in list(summary)[:12]}, indent=2))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    r = sub.add_parser("run")
    r.add_argument("--phreeqc-dir", required=True)
    sub.add_parser("parse")
    sub.add_parser("score")
    a = ap.parse_args()
    {"build": cmd_build, "run": cmd_run, "parse": cmd_parse, "score": cmd_score}[a.cmd](a)


if __name__ == "__main__":
    main()
