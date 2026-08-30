"""
MIZAN :: is the residual model deficiency, or fill drift?
=========================================================
Uncertainty propagation put the holdout error at 2.5x the combined
measurement uncertainty, with a systematic +0.45 K bias. That is too large
and too structured to be experimental scatter, so something real is being
missed. This module separates the two candidate explanations.

  (a) MODEL-FORM deficiency. The Poppe formulation or the fill law is
      wrong, and the error would persist even within a single campaign.

  (b) FILL DRIFT. The fill characteristic is not constant. The campaigns
      span October 2019 to October 2023; fill fouls, scales and degrades
      over four years, so one Merkel coefficient fitted in 2021 cannot
      describe a tower measured in 2019 and 2023.

The test discriminates cleanly:

    if within-campaign error approaches the measurement uncertainty while
    across-campaign error does not, the model form is sound and the
    residual is drift.

The distinction matters commercially as well as scientifically. If the fill
characteristic drifts on a timescale of months to years, then a controller
that assumes a fixed characteristic degrades silently in service -- and
periodic recalibration against the plant's own telemetry stops being an
upsell and becomes a functional requirement.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import calibrate as cal
import dataset as ds

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
CAMPAIGNS = ["Exp1", "Exp2", "Exp3"]


def fit_and_score(train_df, test_df):
    """Fit the fill law on train_df, score forward prediction on test_df."""
    Me, LG, _, ok = cal.demanded_merkel(train_df)
    if ok.sum() < 5:
        return None
    c, n, r2 = cal.fit_fill_law(Me, LG, ok)
    T_out, evap, okp = cal.predict(test_df, c, n)
    m = cal.metrics(test_df, T_out, evap, okp)
    m.update({"fill_c": c, "fill_n": n, "fit_r2": r2})
    return m


def main():
    unc = json.loads((RESULTS / "uncertainty.json").read_text())
    u_c = unc["u_combined_K"]

    all_df = ds.derive(ds.load_all())
    by = {c: all_df[all_df.campaign == c].reset_index(drop=True) for c in CAMPAIGNS}

    print("Is the residual model deficiency, or fill drift?", flush=True)
    print(f"combined measurement uncertainty u_c = {u_c:.3f} K "
          f"(expanded U = {2*u_c:.3f} K)\n", flush=True)

    rows = []

    print("WITHIN campaign (fitted and scored on the same campaign):", flush=True)
    for c in CAMPAIGNS:
        m = fit_and_score(by[c], by[c])
        if m is None:
            continue
        rows.append({"mode": "within", "train": c, "test": c, **m})
        print(f"  {c:5s} n={m['n_points']:3d}  MAE={m['Tout_MAE_K']:.3f} K  "
              f"bias={m['Tout_bias_K']:+.3f}  MAE/u_c={m['Tout_MAE_K']/u_c:.2f}  "
              f"c={m['fill_c']:.3f} n={m['fill_n']:+.3f}", flush=True)

    print("\nACROSS campaigns (fitted on one, scored on another):", flush=True)
    for a, b in itertools.permutations(CAMPAIGNS, 2):
        m = fit_and_score(by[a], by[b])
        if m is None:
            continue
        rows.append({"mode": "across", "train": a, "test": b, **m})
        print(f"  {a} -> {b}  n={m['n_points']:3d}  MAE={m['Tout_MAE_K']:.3f} K  "
              f"bias={m['Tout_bias_K']:+.3f}  MAE/u_c={m['Tout_MAE_K']/u_c:.2f}",
              flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "drift.csv", index=False)

    within = df[df["mode"] == "within"]
    across = df[df["mode"] == "across"]
    w_mae = float(within.Tout_MAE_K.mean())
    a_mae = float(across.Tout_MAE_K.mean())

    print()
    print(f"  mean WITHIN-campaign MAE : {w_mae:.3f} K  "
          f"({w_mae/u_c:.2f} x u_c)")
    print(f"  mean ACROSS-campaign MAE : {a_mae:.3f} K  "
          f"({a_mae/u_c:.2f} x u_c)")
    print(f"  drift penalty            : {a_mae - w_mae:+.3f} K")
    print()

    # spread of the identified fill coefficient across campaigns
    cs = within.fill_c.values
    ns = within.fill_n.values
    print(f"  identified fill coefficient c across campaigns: "
          f"{cs.min():.3f} to {cs.max():.3f}  "
          f"(spread {100*(cs.max()-cs.min())/cs.mean():.1f} % of mean)")
    print(f"  identified exponent n across campaigns:         "
          f"{ns.min():+.3f} to {ns.max():+.3f}")
    print()

    if w_mae <= 1.5 * u_c and a_mae > 2.0 * u_c:
        verdict = ("FILL DRIFT. Within a campaign the model tracks the "
                   "experiment to near its measurement uncertainty; across "
                   "campaigns it does not. The functional form is sound and "
                   "the fill characteristic is not constant in time.")
    elif w_mae > 2.0 * u_c:
        verdict = ("MODEL-FORM DEFICIENCY. The error persists even within a "
                   "single campaign, so it cannot be explained by drift "
                   "between them.")
    else:
        verdict = ("MIXED. Within-campaign error is above the measurement "
                   "uncertainty but the across-campaign penalty is also "
                   "material; both effects are present.")
    print("  VERDICT:", verdict)

    out = {"u_combined_K": u_c, "within_MAE_K": w_mae, "across_MAE_K": a_mae,
           "drift_penalty_K": a_mae - w_mae,
           "within_over_uc": w_mae / u_c, "across_over_uc": a_mae / u_c,
           "fill_c_range": [float(cs.min()), float(cs.max())],
           "fill_c_spread_pct": float(100 * (cs.max() - cs.min()) / cs.mean()),
           "fill_n_range": [float(ns.min()), float(ns.max())],
           "verdict": verdict}
    (RESULTS / "drift.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    print(f"\nwritten -> {RESULTS/'drift.json'}")


if __name__ == "__main__":
    main()
