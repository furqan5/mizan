"""How much of gate V7's verdict is the baseline, and how much is the product?

V7 returned 15.01 % against a 15.00 % threshold. A margin of 0.01 points is
not a result -- it is a coin toss wearing a verdict. This sweeps the one
input that was changed and reports the whole curve, so the reader can see
exactly where the answer flips instead of taking a single point on trust.

The sourced band, from primary documents:

    2.0   Aramco pilot, groundwater. "The COC with groundwater was limited
          to 2, due to higher concentration of scale forming ions."
    3.0   pre-registered V7 baseline; Qatar Cool's stated maximum on TSE
    3.5   Aramco pilot, ACHIEVED on reclaimed water. "the COC ... could be
          almost doubled (from 2 to 3.5) with municipal reclaimed water"

    -- Badruzzaman et al. (2022), Water Resources and Industry 28:100188

Writes results/v7_baseline_sensitivity.json
"""
from __future__ import annotations
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import run_controller as rc   # noqa: E402

RESULTS = ROOT / "results"
BASELINES = [2.0, 2.5, 3.0, 3.5, 4.0]


def main() -> int:
    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]
    thr = rc.V5_CRITERIA["makeup_water_reduction_pct_min"]
    rows = []
    for b in BASELINES:
        _df, sm = rc.gate_v5(fc, fn, baseline_cycles=b, label=f"sens-{b:g}")
        rows.append({"baseline_cycles": b, "water_pct": sm["water_pct"],
                     "cost_pct": sm["cost_pct"], "energy_pct": sm["energy_pct"],
                     "violations": sm["violations"],
                     "arithmetic_headroom_to_5cy_pct":
                         100.0 * (1 - (5/4) / (b / (b - 1))),
                     "verdict": "PASS" if sm["water_pct"] >= thr else "FAIL"})

    print("\n" + "=" * 78)
    print("V7 BASELINE SENSITIVITY -- where the verdict actually flips")
    print("=" * 78)
    print(f"{'baseline':>9}{'arith 5cy':>11}{'water %':>10}{'verdict':>9}"
          f"{'cost %':>9}{'viol':>6}")
    for r in rows:
        print(f"{r['baseline_cycles']:>8.1f}c"
              f"{r['arithmetic_headroom_to_5cy_pct']:>11.2f}"
              f"{r['water_pct']:>10.2f}{r['verdict']:>9}"
              f"{r['cost_pct']:>9.2f}{r['violations']:>6.0f}")
    print(f"\n  Threshold {thr:g} % throughout. The product did not change "
          f"between these rows; only the incumbent did.")
    (RESULTS / "v7_baseline_sensitivity.json").write_text(
        json.dumps({"threshold_pct": thr, "rows": rows}, indent=2))
    print(f"\nwritten -> {RESULTS/'v7_baseline_sensitivity.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
