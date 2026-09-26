"""
MIZAN :: two numbers the JWPE manuscript quotes, computed on the current engine
===============================================================================
1. Skin-rise sensitivity of the registered ceiling (manuscript Section 2.3).
   The ceiling is recomputed for both panel waters at the five reference
   ambients stored in results/incumbent_gap.json, with the bulk-to-skin rise
   stepped through every fouling allowance in chemistry.FOULING_ALLOWANCES
   (clean tube to the TEMA treated-cooling-tower value). The earlier figure,
   "4.92 to 4.56 cycles, 0.055 cycles per kelvin", came from the 12 September
   configuration, before the Riyadh silica correction (defect 67); it does not
   describe the panel the manuscript reports.

2. The DOE nanofiltered-effluent indices at heater temperatures (Section 3.2).
   tests/test_doe_benchmark.py pins the 40 C values inside windows; this prints
   the values themselves across 35-55 C.

No pandas, no weather data; the conditions come from the stored run.
Run:  python src/paper_jwpe_checks.py      Output: results/paper_jwpe_checks.json
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")

import chemistry as chem          # noqa: E402
import incumbent_gap as ig        # noqa: E402

WATERS = {"Dhahran (ARAMCO_FIELD_VALIDATED)": chem.ARAMCO_FIELD_VALIDATED,
          "Riyadh (ARAMCO_RIYADH_REFINERY_TSE)": chem.ARAMCO_RIYADH_REFINERY_TSE}
DOE_T = (35.0, 40.0, 45.0, 50.0, 55.0)


def skin_sweep():
    ladder = chem.skin_rise_ladder()
    deltas = sorted((round(v["delta_t_k"], 4), k) for k, v in ladder.items())
    conds = json.loads((RESULTS / "incumbent_gap.json").read_text(encoding="utf-8"))["conditions"]
    out = {"allowances_K": {k: d for d, k in deltas}, "waters": {}}
    print("skin-rise sensitivity of the ceiling, pH", ig.ACID_PH)
    for wname, w in WATERS.items():
        rows = []
        for c in conds:
            pts = []
            for d, k in deltas:
                r = ig.mizan_ceiling(w, c["T_return"] + d, c["T_basin"], pH=ig.ACID_PH, report=False)
                pts.append({"allowance": k, "skin_rise_K": d, "cycles": round(r["cycles"], 4),
                            "binding": r["binding"]})
            span_k = deltas[-1][0] - deltas[0][0]
            slope = (pts[-1]["cycles"] - pts[0]["cycles"]) / span_k
            rows.append({"condition": c["name"], "points": pts, "cycles_per_K": round(slope, 4)})
            print(f"  {wname[:8]:8s} {c['name']:22s} "
                  + "  ".join(f"{p['skin_rise_K']:.2f} K {p['cycles']:.2f}" for p in pts)
                  + f"   {slope:+.3f} cycles/K  ({pts[-1]['binding']})")
        out["waters"][wname] = rows
    return out


def doe_indices():
    w = chem.DOE_SYN_MWW_NF_COC4
    rows = []
    print("\nDOE nanofiltered effluent, four cycles (DOE_SYN_MWW_NF_COC4)")
    for T in DOE_T:
        s = chem.saturation_state(w, T)
        lsi = chem.langelier_index(w, T)
        rows.append({"T_C": T, "SI_calcite": round(s["SI_calcite"], 3), "SI_gypsum": round(s["SI_gypsum"], 3),
                     "SI_tcp": round(s["SI_tcp"], 3), "SI_hydroxyapatite": round(s["SI_hydroxyapatite"], 3),
                     "LSI": round(lsi, 3)})
        print(f"  {T:4.0f} C  calcite {s['SI_calcite']:+.3f}  gypsum {s['SI_gypsum']:+.3f}  "
              f"TCP {s['SI_tcp']:.3f}  HAP {s['SI_hydroxyapatite']:.3f}  LSI {lsi:+.3f}")
    return rows


if __name__ == "__main__":
    result = {"skin_sensitivity": skin_sweep(), "doe_indices": doe_indices()}
    (RESULTS / "paper_jwpe_checks.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print("\nwrote results/paper_jwpe_checks.json")
