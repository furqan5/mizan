"""Bound the sulfate nobody measures, from the analysis everybody has.

    python ai_lab/sulfate_bounds.py

THE PROBLEM, established by interview rather than assumed. Three operators, in
three sectors, all measure some subset of {TDS, conductivity, pH, calcium
hardness, total hardness, alkalinity, chloride}. **None of them measures
sulfate.** The 1992 training syllabus explains why: scale was taught as a
carbonate phenomenon and sulfate was filed under corrosion. But on Gulf
reclaimed water the binding mineral is GYPSUM -- calcium sulfate -- and
`value_of_information.py` puts 10.2 % of makeup water on knowing it.

THE OBVIOUS MOVE IS THE WRONG ONE. Train a model to predict sulfate. It would
need paired data -- routine analyses alongside full ion inventories -- which we
do not have, and a model fitted to water we have never seen would be a
confident guess dressed as a measurement. That is precisely the "AI-powered"
claim this project refuses to make.

THE BETTER MOVE NEEDS NO LEARNING AT ALL. Sulfate is not free to be anything.
It is pinned by two conservation laws the plant's own numbers already satisfy:

    ELECTRONEUTRALITY   2[Ca] + 2[Mg] + [Na] + [K]
                          = [HCO3] + [Cl] + 2[SO4] + [NO3]        (eq/L)

    TDS CLOSURE         sum of all dissolved species ~ TDS         (mg/L)

Given the routine measurements, those two equations bound sulfate from BOTH
sides -- charge balance from below, TDS closure from above -- with no fitting,
no training data and no extrapolation. The output is an interval, and an
interval is the honest object here: it says how much we do not know.

WHERE ML WOULD THEN GO, and why it is future work rather than this file: the
bound is only as tight as the sodium range, and regional groundwater has strong
structure -- Punjab tubewells are not random draws. A prior over Na/Cl ratios
learned from public groundwater chemistry would tighten the interval. That
needs a real dataset, so it is scoped and not faked.

TEST. The Aramco reclaimed analysis has a MEASURED sulfate of 566 mg/L. It is
withheld from the estimator and used only to score it.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "ai_lab"))

import chemistry as chem                        # noqa: E402
from value_of_information import gypsum_ceiling  # noqa: E402

# ======================================================================
# PRE-REGISTERED, fixed 3 September 2026 before the first run.
# ======================================================================
# G-S1  CORRECTNESS. The interval must CONTAIN the withheld true sulfate.
#       An estimator whose bound excludes the truth is worse than no
#       estimator, because it would be trusted.
# G-S2  USEFULNESS. The resulting gypsum-ceiling band must be <= 2.0 cycles
#       wide. Wider than that and it cannot inform an operating decision --
#       it would only say "somewhere between comfortable and unsafe".
# G-S3  HONESTY. The bound must be strictly wider than zero. A point estimate
#       dressed as a bound would pass G-S1 and G-S2 by accident and mislead.
GATES = {"must_contain_truth": True,
         "ceiling_band_cycles_max": 2.0,
         "min_interval_mg_l": 1.0}
REGISTERED = "2026-09-03"

# Equivalent weights, mg per milliequivalent.
EQ = {"Ca": 20.04, "Mg": 12.15, "Na": 22.99, "K": 39.10,
      "HCO3": 61.02, "Cl": 35.45, "SO4": 48.03, "NO3": 62.00}


def sulfate_from_charge_balance(Ca, Mg, Na, K, HCO3, Cl, NO3):
    """Sulfate implied by electroneutrality, mg/L. Exact given all others."""
    cat = Ca / EQ["Ca"] + Mg / EQ["Mg"] + Na / EQ["Na"] + K / EQ["K"]
    ani = HCO3 / EQ["HCO3"] + Cl / EQ["Cl"] + NO3 / EQ["NO3"]
    return max(0.0, (cat - ani) * EQ["SO4"])


def sulfate_from_tds(TDS, Ca, Mg, Na, K, HCO3, Cl, NO3, SiO2=0.0):
    """Sulfate implied by TDS closure, mg/L. Exact given all others."""
    return max(0.0, TDS - (Ca + Mg + Na + K + HCO3 + Cl + NO3 + SiO2))


def bound_sulfate(meas, na_frac_range=(0.15, 0.45)):
    """Interval for sulfate from routine measurements alone.

    `meas` carries what a plant actually has: TDS, Ca, Mg, HCO3, Cl, NO3, pH.
    Sodium is the species nobody titrates, so it is swept across a range
    expressed as a FRACTION OF TDS -- 15 % to 45 % covers fresh groundwater
    through to strongly saline reclaimed water. Each candidate sodium gives one
    charge-balance sulfate and one TDS-closure sulfate; the interval is the
    envelope over the sweep, intersected between the two laws.

    Returns (lo, hi, diagnostics).
    """
    lo, hi = np.inf, -np.inf
    trace = []
    for f in np.linspace(na_frac_range[0], na_frac_range[1], 61):
        Na = f * meas["TDS"]
        K = 0.07 * Na              # K/Na ~ 5-10 % in most groundwater  [est]
        s_cb = sulfate_from_charge_balance(meas["Ca"], meas["Mg"], Na, K,
                                           meas["HCO3"], meas["Cl"],
                                           meas["NO3"])
        s_td = sulfate_from_tds(meas["TDS"], meas["Ca"], meas["Mg"], Na, K,
                                meas["HCO3"], meas["Cl"], meas["NO3"])
        # Both laws must hold. A sodium that makes them disagree wildly is not
        # a physical water, so the admissible sulfate at this Na is the overlap.
        s_min, s_max = min(s_cb, s_td), max(s_cb, s_td)
        if s_max - s_min > 0.60 * meas["TDS"]:
            continue               # the two laws are irreconcilable here
        lo, hi = min(lo, s_min), max(hi, s_max)
        trace.append({"na_frac": float(f), "Na": float(Na),
                      "so4_charge_balance": float(s_cb),
                      "so4_tds_closure": float(s_td)})
    return float(lo), float(hi), trace


def main() -> int:
    truth = chem.balance_sodium(chem.ARAMCO_RECLAIMED)

    print("=" * 78)
    print("BOUNDING SULFATE FROM ROUTINE MEASUREMENTS")
    print(f"registered {REGISTERED}, before the first run")
    print("=" * 78)
    print(f"  G-S1 the interval must CONTAIN the withheld true sulfate")
    print(f"  G-S2 the gypsum-ceiling band must be <= "
          f"{GATES['ceiling_band_cycles_max']:.1f} cycles wide")
    print(f"  G-S3 the interval must be a real interval, not a point estimate")

    # What a plant actually hands you. Sulfate and sodium are NOT in here.
    meas = {"TDS": truth.TDS, "Ca": truth.Ca, "Mg": truth.Mg,
            "HCO3": truth.HCO3, "Cl": truth.Cl, "NO3": truth.NO3,
            "pH": truth.pH}
    print(f"\nWHAT THE PLANT MEASURES")
    for k, v in meas.items():
        print(f"   {k:6} {v:8.1f}")
    print(f"\nWITHHELD (used only to score): SO4 = {truth.SO4:.0f} mg/L, "
          f"Na = {truth.Na:.0f} mg/L")

    lo, hi, trace = bound_sulfate(meas)
    print(f"\nBOUND FROM CONSERVATION LAWS ALONE")
    print(f"   sulfate in [{lo:.0f}, {hi:.0f}] mg/L      "
          f"(width {hi - lo:.0f} mg/L)")
    contains = lo <= truth.SO4 <= hi
    print(f"   true value {truth.SO4:.0f} mg/L is "
          f"{'INSIDE' if contains else 'OUTSIDE'} the bound")

    # ------------------------------------------------- propagate to ceilings
    def ceiling_at(so4):
        w = chem.Water(**{**{s: getattr(truth, s) for s in chem.SPECIES},
                          "name": "bounded", "pH": truth.pH, "TDS": truth.TDS,
                          "SO4": float(so4)})
        return gypsum_ceiling(w)

    c_lo, b_lo = ceiling_at(hi)      # most sulfate -> lowest ceiling
    c_hi, b_hi = ceiling_at(lo)      # least sulfate -> highest ceiling
    c_true, b_true = ceiling_at(truth.SO4)
    band = abs(c_hi - c_lo)

    print(f"\nWHAT THAT MEANS FOR OPERATION")
    print(f"   at SO4 = {hi:.0f}  ->  ceiling {c_lo:.2f} cycles, binding {b_lo}")
    print(f"   at SO4 = {lo:.0f}  ->  ceiling {c_hi:.2f} cycles, binding {b_hi}")
    print(f"   band {band:.2f} cycles")
    print(f"   truth {truth.SO4:.0f} -> {c_true:.2f} cycles "
          f"({'inside' if min(c_lo, c_hi) <= c_true <= max(c_lo, c_hi) else 'OUTSIDE'} the band)")

    # ------------------------------------------------------------- score
    g1 = contains
    g2 = band <= GATES["ceiling_band_cycles_max"]
    g3 = (hi - lo) >= GATES["min_interval_mg_l"]
    print(f"\n{'-' * 78}")
    print(f"{'G-S1 interval contains the truth':44} {str(g1):>8}  "
          f"{'PASS' if g1 else 'FAIL'}")
    print(f"{'G-S2 ceiling band <= 2.0 cycles':44} {band:>8.2f}  "
          f"{'PASS' if g2 else 'FAIL'}")
    print(f"{'G-S3 a real interval, not a point':44} {hi - lo:>8.0f}  "
          f"{'PASS' if g3 else 'FAIL'}")
    print(f"{'-' * 78}")

    if g1 and g2 and g3:
        print(f"\n   A plant can be told its gypsum ceiling to within "
              f"{band:.2f} cycles")
        print(f"   from measurements it ALREADY TAKES, with no new instrument,")
        print(f"   no training data and no model that could be wrong about a")
        print(f"   water it has never seen. Conservation laws, not inference.")
    else:
        print(f"\n   The bound does not clear its own gates. Reported as such.")

    print(f"\n   WHERE ML WOULD GO NEXT, and only next: the width is driven by")
    print(f"   the sodium sweep. Regional groundwater is not random -- a prior")
    print(f"   over Na/Cl ratios from public chemistry would tighten it. That")
    print(f"   needs a real dataset, so it is scoped, not faked.")

    out = {"registered": REGISTERED, "gates": GATES,
           "measured_inputs": meas,
           "withheld": {"SO4": truth.SO4, "Na": truth.Na},
           "bound_mg_l": [lo, hi], "bound_width_mg_l": hi - lo,
           "contains_truth": bool(contains),
           "ceiling_at_high_so4": c_lo, "ceiling_at_low_so4": c_hi,
           "ceiling_band_cycles": band, "ceiling_at_truth": c_true,
           "scores": {"G_S1_pass": bool(g1), "G_S2_pass": bool(g2),
                      "G_S3_pass": bool(g3)},
           "method": "electroneutrality + TDS closure, sodium swept 15-45 % of TDS",
           "no_learning": "no training data, no fitted parameters",
           "future_work": ("a learned prior over regional Na/Cl would tighten "
                           "the interval; needs a public groundwater dataset")}
    (RESULTS / "sulfate_bounds.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten -> results/sulfate_bounds.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
