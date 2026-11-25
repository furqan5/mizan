"""
MIZAN :: plant-scale results with the daily silica margin enforced
==================================================================
Registered in docs/staged/margin_sensitivity_preregistration.md, committed
before this script was first run. Read that first.

The registered plant-scale runs (V5, V7, the annual study and its W1 weather
scenario) hold the optimiser to chem.OPERATING_LIMITS, the steady-state
silica limit, on a 1-cycle grid. The ceiling the paper defines (Section 2.4,
incumbent_gap.mizan_ceiling) lowers the silica limit by the daily margin for
a +-5 K basin swing. This re-runs the same studies with that margin applied
at each candidate's own basin temperature, on a 0.1-cycle grid, and, as a
control, on the same fine grid without the margin. It is a sensitivity
analysis: V5 and V7 keep their registered verdicts.

Run (each part is independent, so they can run in parallel):
    python scripts/margin_sensitivity.py --variant margin   --part gates
    python scripts/margin_sensitivity.py --variant margin   --part annual
    python scripts/margin_sensitivity.py --variant margin   --part w1
    python scripts/margin_sensitivity.py --variant nomargin --part gates
    python scripts/margin_sensitivity.py --variant nomargin --part annual
    python scripts/margin_sensitivity.py --variant nomargin --part w1
Writes: results/margin_sensitivity/<variant>_<part>.json (+ CSVs for gates)
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = RESULTS / "margin_sensitivity"
PREREG = ROOT / "docs" / "staged" / "margin_sensitivity_preregistration.md"
sys.path.insert(0, str(ROOT / "src"))

import annual                                                   # noqa: E402
import chemistry as chem                                        # noqa: E402
import run_controller as rc                                     # noqa: E402

AMPLITUDE_K = 5.0                        # the same swing as Section 4.1
CYCLES_GRID = np.round(np.arange(2.0, 6.001, 0.1), 2)
GRID_TOP = float(CYCLES_GRID[-1])


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def margin_limits(T_basin_c: float) -> dict:
    return chem.limits_with_diurnal_margin(T_basin_c, AMPLITUDE_K)


def optimise_kwargs(variant: str) -> dict:
    kw = {"cycles_grid": CYCLES_GRID}
    if variant == "margin":
        kw["saturation_limits_fn"] = margin_limits
    return kw


def _interval(df, rng, gu):
    per = np.array([gu.sample_saving(r.base_makeup_m3_h, r.opt_makeup_m3_h,
                                     r.base_fan_pct, r.opt_fan_pct, rng)
                    for r in df.itertuples()])
    gate = per.mean(axis=0)
    lo, hi = np.percentile(gate, [2.5, 97.5])
    return {"mc_median_pct": float(np.median(gate)), "sd_pct": float(gate.std()),
            "ci95_low_pct": float(lo), "ci95_high_pct": float(hi),
            "p_exceeds_15": float((gate >= 15.0).mean())}


def part_gates(variant: str, fc: float, fn: float) -> dict:
    gu = _load_script("gate_uncertainty")
    rng = np.random.default_rng(gu.SEED)
    out = {}
    for gate, base in (("V5", 4.0), ("V7", 3.0)):
        label = f"msens-{variant}-{gate.lower()}"
        df, sm = rc.gate_v5(fc, fn, baseline_cycles=base, label=label,
                            optimise_kwargs=optimise_kwargs(variant))
        src = RESULTS / f"{label}_controller.csv"
        shutil.move(str(src), str(OUT / f"{variant}_{gate.lower()}_controller.csv"))
        out[gate] = {
            "baseline_cycles": base,
            "water_pct": sm["water_pct"], "cost_pct": sm["cost_pct"],
            "energy_pct": sm["energy_pct"], "violations": sm["violations"],
            "interval": _interval(df, rng, gu),
            "conditions": df[["condition", "opt_cycles", "opt_fan_pct", "opt_pH",
                              "opt_T_basin_C", "water_saving_pct",
                              "energy_saving_pct", "cost_saving_pct"]
                             ].to_dict(orient="records"),
            "grid_top_hit": bool((df["opt_cycles"] >= GRID_TOP - 1e-9).any()),
        }
    return out


def part_annual(variant: str, h: np.ndarray, title: str) -> dict:
    r = annual.run_annual(h, title=title, optimise_kwargs=optimise_kwargs(variant))
    keep = ("annual_water_pct_ratio_of_totals", "annual_energy_pct_ratio_of_totals",
            "annual_cost_pct_ratio_of_totals", "fraction_inside_validated_envelope",
            "unsolved_hours", "n_bins", "by_envelope", "bins")
    out = {k: r[k] for k in keep if k in r}
    out["input_hourly_sha256"] = annual.hourly_sha256(h)
    out["grid_top_hit"] = any(b.get("opt_cycles", 0) >= GRID_TOP - 1e-9 for b in r["bins"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("margin", "nomargin"), required=True)
    ap.add_argument("--part", choices=("gates", "annual", "w1"), required=True)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)

    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    fc, fn = cal["fill_c"], cal["fill_n"]
    print(f"variant {a.variant}, part {a.part}, fill law c {fc:.4f} n {fn:.4f}, "
          f"cycles grid {CYCLES_GRID[0]}-{GRID_TOP} step 0.1, "
          f"silica margin {'ON (+-%g K at the candidate basin)' % AMPLITUDE_K if a.variant == 'margin' else 'OFF'}")

    if a.part == "gates":
        res = part_gates(a.variant, fc, fn)
    elif a.part == "annual":
        h0 = np.load(RESULTS / "tmy_hourly.npy")
        res = part_annual(a.variant, h0, f"Dhahran TMYx, margin sensitivity ({a.variant})")
    else:
        w1 = _load_script("weather_w1_rescore")
        import weather_sensitivity as ws                         # noqa: E402
        h1, _info = ws.build_w1(np.load(RESULTS / "tmy_hourly.npy"), w1.load_climatology())
        res = part_annual(a.variant, h1, f"W1 station humidity, margin sensitivity ({a.variant})")

    meta = {"variant": a.variant, "part": a.part,
            "preregistration": str(PREREG.relative_to(ROOT)).replace("\\", "/"),
            "preregistration_sha256": (hashlib.sha256(PREREG.read_bytes()).hexdigest()
                                       if PREREG.exists() else None),
            "fill_c": fc, "fill_n": fn, "amplitude_k": AMPLITUDE_K,
            "cycles_grid": [float(CYCLES_GRID[0]), GRID_TOP, 0.1],
            "status": ("SENSITIVITY, registered after the registered results "
                       "were known. V5 and V7 keep their registered verdicts.")}
    path = OUT / f"{a.variant}_{a.part}.json"
    path.write_text(json.dumps({**meta, "results": res}, indent=1, default=float),
                    encoding="utf-8")
    print(f"\nwritten -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
