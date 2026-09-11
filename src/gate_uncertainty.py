"""
FURQAN / MIZAN :: error bars on the water gates.

WHY THIS EXISTS, AND WHAT IT WOULD HAVE PREVENTED.

Gate V7 returned 15.01 % against a 15.00 % threshold and was recorded as a
PASS. The margin was 0.01 percentage points. Nothing in the package could say
whether that was a result or a rounding artefact, because no gate carried an
interval -- `uncertainty.py` existed, was used by the audit, the drift study
and the report, and by NO GATE.

This module closes that. It does not invent an uncertainty model: it
propagates the one the calibration data already measured.

WHAT THE CALIBRATION ACTUALLY SHOWS

Scoring the evaporation model against 165 points across three campaigns and
regressing the relative error on fan speed, campaign by campaign:

    campaign   n     offset a      slope k        residual sd
    Exp1      33     -0.52 %      -0.2002 %/fan%     6.27 pp
    Exp2     115     +9.06 %      -0.3660 %/fan%    11.63 pp
    Exp3      17    -14.59 %      +0.1873 %/fan%     3.18 pp

Two components, and they behave completely differently in a gate:

  OFFSET a -- spread -14.6 to +9.1 pp, sd 9.71. A constant multiplicative
      error on evaporation. A water SAVING is a RATIO of two makeup figures
      computed by the same model at the same site, so a constant offset
      CANCELS. This is the large component and it is harmless.

  SLOPE k -- spread -0.366 to +0.187 %/fan%, sd 0.232, AND THE SIGN IS NOT
      CONSISTENT between campaigns. The baseline and the optimised case run
      at DIFFERENT FAN SPEEDS, and fan speed sets the latent-to-sensible
      split, which is exactly where this error lives. So it does NOT cancel.
      This is the small component and it is the one that matters.

THE CONSEQUENCE, in one line: a gate in which the optimiser moves the fan by
D percentage points carries roughly 0.232 * D percentage points of
irreducible uncertainty on its water saving. V5 moves the fan by about 24
points on average, so its water figures carry about +/- 5.6 pp at one
standard deviation.

    V5 water  4.38 %  ->  4 +/- 6
    V7 water 15.01 %  -> 15 +/- 6

Which means V7's 0.01-point margin is not a pass, and the 20 % that keeps
being asked for is INSIDE the error bar of numbers already computed. You
cannot distinguish 15 % from 20 % with this instrument. Improving the water
result past this point is a calibration problem, not a control problem.

HOW TO NARROW IT, since that is the actionable half:

  * one tower, metered, across a fan range -- a single site's offset cancels
    and its slope can be measured directly, collapsing sd 0.232 to that
    site's own value
  * or hold the fan fixed between baseline and optimised and take the water
    saving from cycles alone, where no fan-dependent term enters at all
"""

from __future__ import annotations

import json
import math
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Measured on the calibration data, campaign by campaign. Recorded as data
# rather than recomputed at import so the gate does not depend on the dataset
# being present, and so the numbers are auditable against the docstring.
CAMPAIGN_FITS = {
    "Exp1": {"n": 33, "offset_pct": -0.52, "slope_pct_per_fanpct": -0.2002,
             "residual_sd_pp": 6.27},
    "Exp2": {"n": 115, "offset_pct": 9.06, "slope_pct_per_fanpct": -0.3660,
             "residual_sd_pp": 11.63},
    "Exp3": {"n": 17, "offset_pct": -14.59, "slope_pct_per_fanpct": 0.1873,
             "residual_sd_pp": 3.18},
}


def slope_spread():
    """Standard deviation of the fan-dependent error across campaigns."""
    ks = np.array([c["slope_pct_per_fanpct"] for c in CAMPAIGN_FITS.values()])
    return float(ks.std(ddof=0)), float(ks.min()), float(ks.max())


def offset_spread():
    a = np.array([c["offset_pct"] for c in CAMPAIGN_FITS.values()])
    return float(a.std(ddof=0)), float(a.min()), float(a.max())


def water_saving_interval(saving_pct, mean_abs_fan_change_pp, k_sigma=1.0):
    """Interval on a water-saving figure, from the fan-dependent term only.

    `mean_abs_fan_change_pp` is how far the optimiser moves the fan, averaged
    over the conditions the gate scores. That is the whole driver: a gate in
    which the fan does not move carries none of this uncertainty.

    The offset term is deliberately NOT included, because it cancels in a
    ratio taken at one site. Saying so is the point -- the large error is the
    harmless one.
    """
    sd, lo_k, hi_k = slope_spread()
    half = k_sigma * sd * float(mean_abs_fan_change_pp)
    return {
        "saving_pct": float(saving_pct),
        "half_width_pp": half,
        "low": float(saving_pct) - half,
        "high": float(saving_pct) + half,
        "k_sigma": k_sigma,
        "fan_change_pp": float(mean_abs_fan_change_pp),
        "slope_sd_pct_per_fanpct": sd,
        "worst_case_low": float(saving_pct) + lo_k * float(mean_abs_fan_change_pp),
        "worst_case_high": float(saving_pct) + hi_k * float(mean_abs_fan_change_pp),
    }


def verdict_is_decidable(saving_pct, threshold_pct, mean_abs_fan_change_pp,
                         k_sigma=1.0):
    """Can this gate's verdict be told apart from its opposite?

    A gate whose interval straddles its own threshold has not been decided,
    whichever side the point estimate fell. Returns the verdict AND whether
    it means anything, because reporting the first without the second is what
    produced the 15.01 problem.
    """
    iv = water_saving_interval(saving_pct, mean_abs_fan_change_pp, k_sigma)
    passes = saving_pct >= threshold_pct
    straddles = iv["low"] <= threshold_pct <= iv["high"]
    return {
        **iv,
        "threshold_pct": float(threshold_pct),
        "point_verdict": "PASS" if passes else "FAIL",
        "decidable": not straddles,
        "margin_pp": float(saving_pct) - float(threshold_pct),
        "margin_in_sigma": ((float(saving_pct) - float(threshold_pct))
                            / iv["half_width_pp"]) if iv["half_width_pp"] else float("inf"),
    }


def fan_movement_from_gate(csv_path=None):
    """Mean absolute fan movement in the V5 gate, read from its own artefact."""
    import csv
    p = pathlib.Path(csv_path or (RESULTS / "v5_controller.csv"))
    if not p.exists():
        return None
    deltas = []
    with p.open() as f:
        for r in csv.DictReader(f):
            try:
                deltas.append(abs(float(r["opt_fan_pct"]) - float(r["base_fan_pct"])))
            except (KeyError, ValueError):
                continue
    return float(np.mean(deltas)) if deltas else None


def report(saving_pct, threshold_pct, label="gate"):
    """One-line human summary, with the caveat attached to the number."""
    d = fan_movement_from_gate()
    if d is None:
        return f"{label}: {saving_pct:.2f} % (fan movement unknown, no interval)"
    v = verdict_is_decidable(saving_pct, threshold_pct, d)
    tail = ("DECIDED" if v["decidable"]
            else "NOT DECIDABLE -- the interval straddles the threshold")
    return (f"{label}: {saving_pct:.2f} % +/- {v['half_width_pp']:.1f} pp "
            f"(1 sd, from a mean fan movement of {d:.0f} points) against "
            f"{threshold_pct:.0f} % -- point verdict {v['point_verdict']}, "
            f"{tail}")


def main() -> int:
    sd, klo, khi = slope_spread()
    asd, alo, ahi = offset_spread()
    print("=" * 74)
    print("GATE UNCERTAINTY -- propagated from the calibration, not invented")
    print("=" * 74)
    print(f"  offset spread {alo:+.2f} to {ahi:+.2f} pp (sd {asd:.2f})  "
          f"-> CANCELS in a ratio")
    print(f"  slope  spread {klo:+.4f} to {khi:+.4f} %/fan% (sd {sd:.4f})  "
          f"-> does NOT cancel, and the sign is inconsistent")
    d = fan_movement_from_gate()
    print(f"\n  mean absolute fan movement in the V5 gate: "
          f"{d:.1f} points" if d else "\n  v5_controller.csv not found")
    if d:
        print()
        for label, saving, thr in (("V5 water", 4.38, 15.0),
                                   ("V7 water", 15.01, 15.0)):
            print("  " + report(saving, thr, label))
        print()
        iv = water_saving_interval(15.01, d)
        print(f"  and the question that keeps being asked: 20 % sits "
              f"{'INSIDE' if iv['low'] <= 20.0 <= iv['high'] else 'outside'} "
              f"the interval on V7 ({iv['low']:.1f} to {iv['high']:.1f} %).")
        print("  You cannot distinguish 15 % from 20 % with this instrument.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
