"""
FURQAN / MIZAN :: what the water gates are actually worth, with an interval.

WHY THIS EXISTS.

Gate V7 returned 15.01 % against a 15.00 % threshold and was reported as a
pass. A 0.01-point margin is only meaningful if the number carries an error
smaller than 0.01 points, and nobody had ever computed the error.

This does. The answer is that the interval is several percentage points wide,
so the V7 margin is meaningless -- and so is any attempt to distinguish a
15 % result from a 20 % one with this instrument.

WHERE THE ERROR COMES FROM, MEASURED RATHER THAN ASSUMED.

Gate V2 scores the evaporation model against the pilot-plant dataset and
FAILS at 9.90 % MAPE against an 8 % threshold, with a -9.44 % bias. Makeup
water is computed from evaporation, so every water number in this package
inherits that error.

Decomposing the residual per campaign as  rel_error[%] = a + k * fan[%]:

    campaign   n     a         k (%/fan%)   residual sd
    Exp1      33   -0.52      -0.2002        6.27 pp
    Exp2     115   +9.06      -0.3660       11.63 pp
    Exp3      17  -14.59      +0.1873        3.18 pp

The OFFSET a varies hugely between campaigns (-14.6 to +9.1) and CANCELS in
a ratio: a water saving is (M_base - M_opt)/M_base, and a common
multiplicative error on both terms divides out. One tower is one campaign, so
within a deployment the offset is common.

The SLOPE k does NOT cancel, because the baseline and the optimised case run
at DIFFERENT FAN SPEEDS. Its sign is not even consistent between campaigns
(-0.366 to +0.187), so it cannot be corrected -- only propagated.

That is the whole error model, and it is deliberately the smallest one that
is defensible: no assumed distributions beyond resampling the three measured
slopes, no claim that the offset cancels perfectly, no claim that three
campaigns characterise a population.

Run:  python scripts/gate_uncertainty.py
Writes: results/gate_uncertainty.json
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
RESULTS = ROOT / "results"

# Measured per-campaign slopes of relative evaporation error against fan
# speed, in percentage points of error per percentage point of fan. From
# src/dataset.py + src/calibrate.py on the pilot dataset; reproduced by
# tests/test_gate_uncertainty.py so they cannot drift silently.
CAMPAIGN_SLOPES = {"Exp1": -0.2002, "Exp2": -0.3660, "Exp3": +0.1873}

# Residual scatter about each campaign's own fit, in percentage points.
CAMPAIGN_RESID_SD = {"Exp1": 6.27, "Exp2": 11.63, "Exp3": 3.18}

N_SAMPLES = 20_000
SEED = 20260911


def sample_saving(base_mk, opt_mk, base_fan, opt_fan, rng, n=N_SAMPLES):
    """Monte Carlo the water saving under the measured error model.

    For each draw: pick a campaign's slope (the tower we happen to be on),
    apply the differential bias implied by the fan change, and add the
    campaign's own residual scatter independently to each case.

    The predicted evaporation relates to truth as
        pred = true * (1 + e/100)
    so  true = pred / (1 + e/100),  and makeup is proportional to evaporation.
    """
    keys = list(CAMPAIGN_SLOPES)
    pick = rng.integers(0, len(keys), size=n)
    k = np.array([CAMPAIGN_SLOPES[keys[i]] for i in pick])
    sd = np.array([CAMPAIGN_RESID_SD[keys[i]] for i in pick])

    out = np.empty(n)
    for j in range(n):
        # common offset cancels, so only the fan-dependent part is applied,
        # referenced to the baseline fan
        e_base = rng.normal(0.0, sd[j])
        e_opt = k[j] * (opt_fan - base_fan) + rng.normal(0.0, sd[j])
        b = base_mk / (1.0 + e_base / 100.0)
        o = opt_mk / (1.0 + e_opt / 100.0)
        out[j] = 100.0 * (b - o) / b
    return out


def run(csv_name, label, rng):
    df = pd.read_csv(RESULTS / csv_name)
    per = []
    for r in df.itertuples():
        s = sample_saving(r.base_makeup_m3_h, r.opt_makeup_m3_h,
                          r.base_fan_pct, r.opt_fan_pct, rng)
        per.append(s)
    per = np.array(per)                 # conditions x samples
    gate = per.mean(axis=0)             # V5/V7 score the unweighted mean
    point = float(df["water_saving_pct"].mean())
    lo, hi = np.percentile(gate, [2.5, 97.5])
    return {
        "gate": label,
        "point_estimate_pct": point,
        "mc_median_pct": float(np.median(gate)),
        "sd_pct": float(gate.std()),
        "ci95_low_pct": float(lo), "ci95_high_pct": float(hi),
        "mean_abs_fan_change_pp": float(
            np.abs(df["opt_fan_pct"] - df["base_fan_pct"]).mean()),
        "p_exceeds_15": float((gate >= 15.0).mean()),
        "p_exceeds_20": float((gate >= 20.0).mean()),
    }


def main() -> int:
    rng = np.random.default_rng(SEED)
    print("=" * 78)
    print("WATER GATES WITH AN INTERVAL")
    print("=" * 78)
    print("error model: measured per-campaign fan-slope of the evaporation")
    print("residual. The common offset cancels in a ratio; the fan-dependent")
    print("part does not, and its sign is not consistent across campaigns.")
    print()

    rows = []
    for csv_name, label in (("v5_controller.csv", "V5 (4.0 cycle baseline)"),
                            ("v7_controller.csv", "V7 (3.0 cycle baseline)")):
        if not (RESULTS / csv_name).exists():
            print(f"  {csv_name} missing, skipped")
            continue
        rows.append(run(csv_name, label, rng))

    hdr = (f"{'gate':<26}{'point':>8}{'sd':>7}{'95% interval':>18}"
           f"{'P(>=15%)':>10}{'P(>=20%)':>10}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['gate']:<26}{r['point_estimate_pct']:>7.2f}%"
              f"{r['sd_pct']:>7.2f}"
              f"{r['ci95_low_pct']:>9.1f} to {r['ci95_high_pct']:<6.1f}"
              f"{r['p_exceeds_15']:>10.2f}{r['p_exceeds_20']:>10.2f}")
    print()
    for r in rows:
        print(f"  {r['gate']}: mean |fan change| "
              f"{r['mean_abs_fan_change_pp']:.0f} pp")
    print()
    print("  READ THIS BEFORE QUOTING EITHER NUMBER.")
    print("  The interval is wide because the instrument is wide: gate V2")
    print("  fails at 9.90 % evaporation MAPE against an 8 % threshold, and")
    print("  the best achievable IN-SAMPLE on this dataset is 7.57 %, so V2")
    print("  is not passable under an honest train/test protocol. Until a")
    print("  better evaporation dataset exists this interval cannot narrow,")
    print("  and no water result from this package can be quoted to better")
    print("  than a few percentage points.")

    (RESULTS / "gate_uncertainty.json").write_text(json.dumps(
        {"error_model": {"campaign_slopes_pct_per_fanpct": CAMPAIGN_SLOPES,
                         "campaign_residual_sd_pp": CAMPAIGN_RESID_SD,
                         "n_samples": N_SAMPLES, "seed": SEED},
         "gates": rows}, indent=2))
    print(f"\nwritten -> {RESULTS / 'gate_uncertainty.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
