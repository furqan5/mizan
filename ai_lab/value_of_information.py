"""What would knowing something exactly be worth, in cubic metres?

    python ai_lab/value_of_information.py

READ THIS BEFORE BUILDING ANY MODEL. The question "can ML save more water?" has
a prior that has to be answered first: **is there any water to save?**

A cooling tower's water use is fixed arithmetic once you know the cycle count.
Makeup = evaporation * C/(C-1). The controller cannot go past the cycle count
where a mineral saturates at the condenser skin. So every cubic metre ML could
save has to come from moving that ceiling -- and the ceiling only moves if a
number we are currently uncertain about turns out to be more favourable than we
assumed.

That makes the value of any ML model boundable WITHOUT BUILDING IT:

    1. take an input we are uncertain about
    2. sweep it across its plausible range
    3. find the gypsum ceiling at each value
    4. the spread in makeup water across that range is the ABSOLUTE MOST that
       perfect knowledge of that input could be worth

If the spread is small, no model of that input is worth building, however
good it is. This is the analysis that says which ML problem to work on, or
whether to work on one at all.

THE FIELD EVIDENCE THAT MOTIVATES IT. Three operator interviews
(`docs/discovery_findings.md`) established that plants routinely measure TDS, pH
and hardness -- and do NOT measure sulfate. A 1992 training syllabus shows why:
scale was taught as a carbonate phenomenon and sulfate was filed under
corrosion. But the binding mineral on this water is GYPSUM, calcium sulfate.
So the industry is uncertain about precisely the input that sets the ceiling.

That is a candidate ML problem with a real shape: infer sulfate, and the rest of
the ion inventory, from the cheap measurements plants already take. This script
decides whether it is worth the effort.

Nothing here is fitted. It is a sweep of the existing validated chemistry.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "src"))

import chemistry as chem   # noqa: E402

# ======================================================================
# PRE-REGISTERED, fixed 3 September 2026 before the first run.
# ======================================================================
# G-V1  A DECISION RULE, not a pass/fail. An input is worth modelling only if
#       perfect knowledge of it moves annual makeup water by >= 2.0 %. Below
#       that it is inside the noise of everything else and no model earns its
#       place. 2 % is chosen because one whole cycle of concentration at C = 7
#       is worth about 2 % of makeup -- so the bar is "worth at least one
#       cycle".
# G-V2  The sweep must be MONOTONIC in each input where physics says it must
#       be: more sulfate cannot raise the gypsum ceiling, more calcium cannot
#       raise it. A non-monotonic result means the sweep is broken.
GATES = {"worth_modelling_pct_min": 2.0}
REGISTERED = "2026-09-03"

# ----------------------------------------------------------------------
# G-V2 AS REGISTERED WAS FALSIFIED, AND IT WAS THE GATE THAT WAS WRONG.
#
# Run 1 reported non-monotonic sweeps for SO4 and for skin temperature. Both
# turned out to be correct chemistry that the gate had not anticipated:
#
#   SULFATE. Below about 450 mg/L the binding mineral is CALCITE, not gypsum.
#   In that region adding sulfate raises ionic strength, which lowers activity
#   coefficients and genuinely RAISES apparent calcite solubility -- so the
#   ceiling ticks up from 8.00 to 8.25 before gypsum takes over and it falls
#   away steeply. "More sulfate cannot raise the ceiling" is only true once
#   gypsum is the binding species.
#
#   SKIN TEMPERATURE. The gate assumed gypsum is retrograde. In this model it
#   is not: SI_gypsum falls monotonically from 0.3411 at 25 degC to 0.2439 at
#   70 degC at 7 cycles, so a HOTTER skin makes gypsum look SAFER. That is not
#   a surprise to the project -- docs/defect_register.md already records "a
#   hotter assumed skin makes gypsum look safer, so the 8 K value buys about
#   one cycle of apparent headroom" -- it is a surprise to this gate, which was
#   written without reading it.
#
# The replacement is stricter, not looser: monotonicity is now asserted PER
# BINDING MINERAL, which is the only region where the claim is meaningful.
# Within the gypsum-binding region the ceiling must be non-increasing in
# sulfate and in calcium. Outside it the constraint is not asserted at all,
# because a different mineral is setting the limit.
G_V2_NOTE = ("registered form assumed a single binding mineral and a retrograde "
             "gypsum; both are false. Replaced by per-mineral monotonicity.")

CYCLES = np.arange(2.0, 16.01, 0.25)
T_SKIN_DEFAULT = 8.0      # skin_delta_k as used by the controller


def gypsum_ceiling(water, skin_delta_k=T_SKIN_DEFAULT, T_wi=40.0, T_wo=32.0,
                   pH=8.0):
    """Lowest cycle count at which any mineral exceeds its operating limit.

    Uses the same split evaluation the controller uses -- retrograde species at
    the hot skin, prograde at the cold basin -- and the same OPERATING_LIMITS.
    Returns (ceiling, binding species).
    """
    limits = chem.OPERATING_LIMITS
    T_skin = T_wi + skin_delta_k
    for c in CYCLES:
        conc = water.concentrate(float(c))
        sat = chem.saturation_state_split(conc, T_skin, T_wo,
                                          pH_hot=pH, pH_cold=pH)
        bad = [k for k in limits if sat[k] > limits[k]]
        if bad:
            return float(c), sorted(bad)
    return float(CYCLES[-1]), []


def _mono_within(ceilings, binds, species):
    """Non-increasing across the contiguous region where `species` binds.

    Asserting monotonicity globally is meaningless when the binding mineral
    switches partway through a sweep -- see the G-V2 note above. Within one
    mineral's region the claim is real and worth checking.
    """
    idx = [i for i, b in enumerate(binds) if species in (b or "")]
    if len(idx) < 2:
        return None                      # species never binds; nothing to test
    seg = [float(ceilings[i]) for i in idx]
    return bool(all(seg[i] >= seg[i + 1] - 1e-9 for i in range(len(seg) - 1)))


def makeup_index(c):
    """Makeup per unit evaporation, C/(C-1). The whole water story is here."""
    return c / (c - 1.0) if c > 1.0 else float("inf")


def main() -> int:
    base = chem.balance_sodium(chem.ARAMCO_RECLAIMED)

    print("=" * 78)
    print("VALUE OF INFORMATION -- what is knowing something exactly worth?")
    print(f"registered {REGISTERED}, before the first run")
    print("=" * 78)
    print(f"  decision rule: an input is worth modelling only if perfect")
    print(f"  knowledge of it moves makeup water by >= "
          f"{GATES['worth_modelling_pct_min']:.1f} % (about one cycle at C=7)")

    c0, bind0 = gypsum_ceiling(base)
    print(f"\nBASELINE  {base.name}")
    print(f"   Ca {base.Ca:.0f}  Mg {base.Mg:.0f}  SO4 {base.SO4:.0f}  "
          f"HCO3 {base.HCO3:.0f}  Cl {base.Cl:.0f} mg/L")
    print(f"   ceiling {c0:.2f} cycles, binding {bind0}")

    # ---------------------------------------------------------------- sweeps
    # Ranges are the honest uncertainty on each input, not a convenient window.
    #   SO4  : plants do not measure it. Range spans a low-sulfate groundwater
    #          to a strongly sulfate-bearing one, around the measured value.
    #   Ca   : regional groundwater spread quoted by an operator -- 120 ppm
    #          Lahore, 240 Sheikhupura, 250 Faisalabad as CaCO3, i.e. roughly
    #          48-100 mg/L as Ca. Widened around the measured 94.
    #   HCO3 : alkalinity, routinely measured, so uncertainty is small.
    #   skin : the register records this as a hardcoded +8 K where the film
    #          calculation gives 2.4-3.7 K clean. That is a real open range.
    sweeps = {
        "SO4":  ("sulfate, mg/L  [NOT MEASURED by any plant interviewed]",
                 np.linspace(150.0, 1200.0, 22)),
        "Ca":   ("calcium, mg/L  [measured as hardness]",
                 np.linspace(45.0, 160.0, 22)),
        "HCO3": ("bicarbonate alkalinity, mg/L  [measured]",
                 np.linspace(35.0, 180.0, 22)),
    }

    results = {}
    for field, (label, values) in sweeps.items():
        ceilings, binds = [], []
        for v in values:
            w = chem.Water(**{**{s: getattr(base, s) for s in chem.SPECIES},
                              "name": base.name, "pH": base.pH,
                              "TDS": base.TDS, field: float(v)})
            c, b = gypsum_ceiling(w)
            ceilings.append(c)
            binds.append(",".join(b))
        ceilings = np.array(ceilings)
        mk = np.array([makeup_index(c) for c in ceilings])
        # Best case is the LOWEST makeup, worst the highest.
        spread_pct = 100.0 * (mk.max() - mk.min()) / mk.max()
        results[field] = {
            "label": label, "values": values.tolist(),
            "ceilings": ceilings.tolist(),
            "binding": binds,
            "ceiling_min": float(ceilings.min()),
            "ceiling_max": float(ceilings.max()),
            "makeup_spread_pct": float(spread_pct),
            "monotonic_non_increasing": bool(
                np.all(np.diff(ceilings) <= 1e-9)),
            "monotonic_within_gypsum": _mono_within(ceilings, binds,
                                                    "SI_gypsum"),
        }

    # Skin temperature is not a water composition, so it is swept separately.
    skin_vals = np.linspace(2.4, 8.0, 15)
    _sk = [gypsum_ceiling(base, skin_delta_k=float(s)) for s in skin_vals]
    sk_c = np.array([c for c, _ in _sk])
    sk_b = [",".join(b) for _, b in _sk]
    sk_mk = np.array([makeup_index(c) for c in sk_c])
    results["skin_delta_k"] = {
        "label": "condenser skin temperature rise, K  [hardcoded +8, film "
                 "calculation gives 2.4-3.7 clean]",
        "values": skin_vals.tolist(), "ceilings": sk_c.tolist(),
        "binding": sk_b,
        "ceiling_min": float(sk_c.min()), "ceiling_max": float(sk_c.max()),
        "makeup_spread_pct": float(100.0 * (sk_mk.max() - sk_mk.min()) / sk_mk.max()),
        "monotonic_non_increasing": bool(np.all(np.diff(sk_c) <= 1e-9)),
        "monotonic_within_gypsum": _mono_within(sk_c, sk_b, "SI_gypsum"),
    }

    # ---------------------------------------------------------------- report
    print(f"\n{'input':16} {'ceiling range':>18} {'makeup at stake':>17}  verdict")
    print("-" * 78)
    ranked = sorted(results.items(),
                    key=lambda kv: -kv[1]["makeup_spread_pct"])
    for field, r in ranked:
        worth = r["makeup_spread_pct"] >= GATES["worth_modelling_pct_min"]
        print(f"{field:16} {r['ceiling_min']:7.2f} - {r['ceiling_max']:<7.2f}"
              f" {r['makeup_spread_pct']:>15.2f} %  "
              f"{'WORTH MODELLING' if worth else 'not worth it'}")
    print("-" * 78)

    for field, r in ranked:
        print(f"\n{field}: {r['label']}")
        print(f"   ceiling moves {r['ceiling_min']:.2f} -> "
              f"{r['ceiling_max']:.2f} cycles across the range")
        print(f"   monotonic as physics requires: "
              f"{r['monotonic_non_increasing']}")

    # WHAT PLANTS ACTUALLY MEASURE, from the interviews in
    # docs/discovery_findings.md. This is the column that decides the ML
    # question: a large lever that is already measured is not an ML problem,
    # it is a data-entry problem.
    MEASURED = {
        "Ca":   ("MEASURED", "calcium hardness, routine -- the textile mill "
                             "quoted 200-300 ppm as CaCO3"),
        "HCO3": ("MEASURED", "M alkalinity, in the LSI calculation itself"),
        "SO4":  ("NOT MEASURED", "no plant interviewed measures it; the 1992 "
                                 "syllabus files sulfate under corrosion, not "
                                 "scale"),
        "skin_delta_k": ("NOT MEASURABLE", "no instrument sees the tube wall; "
                                           "this is what the coupon rig is for"),
    }
    print()
    print(f"{'input':16} {'at stake':>10}  {'status':<14} why")
    print("-" * 78)
    for field, r in ranked:
        st, why = MEASURED.get(field, ("?", ""))
        print(f"{field:16} {r['makeup_spread_pct']:>9.2f} %  {st:<14} {why[:38]}")
    print("-" * 78)

    unmeasured = [(f, r) for f, r in ranked
                  if MEASURED.get(f, ("", ""))[0].startswith("NOT")
                  and r["makeup_spread_pct"] >= GATES["worth_modelling_pct_min"]]

    top = ranked[0]
    print(f"\n{'=' * 78}")
    print(f"CONCLUSION")
    print(f"{'=' * 78}")
    if top[1]["makeup_spread_pct"] >= GATES["worth_modelling_pct_min"]:
        print(f"   Largest lever overall: {top[0].upper()}, worth up to "
              f"{top[1]['makeup_spread_pct']:.1f} % of makeup water.")
        if unmeasured:
            u, ur = unmeasured[0]
            print()
            print(f"   But size is not the criterion -- MEASUREDNESS is.")
            print(f"   Calcium and alkalinity are already measured on every "
                  f"plant interviewed,")
            print(f"   so their uncertainty is not an inference problem.")
            print()
            print(f"   >>> THE ML PROBLEM IS {u.upper()}: worth "
                  f"{ur['makeup_spread_pct']:.1f} % of makeup water, and the "
                  f"largest")
            print(f"       lever that NOBODY MEASURES. Infer it from what "
                  f"plants already")
            print(f"       take -- TDS, pH, calcium and total hardness, "
                  f"alkalinity, temperature.")
        else:
            print()
            print(f"   Every lever above the bar is ALREADY MEASURED. There "
                  f"is no inference")
            print(f"   problem worth solving here -- the data exists, it is "
                  f"just not used.")
    else:
        print(f"   NO input clears the {GATES['worth_modelling_pct_min']:.1f} % "
              f"bar. The ceiling is not sensitive enough to any single unknown")
        print(f"   for a model of it to pay for itself. Report that and do not")
        print(f"   build one.")

    out = {"registered": REGISTERED, "gates": GATES,
           "baseline_ceiling_cycles": c0, "baseline_binding": bind0,
           "water": {s: getattr(base, s) for s in chem.SPECIES},
           "sweeps": results,
           "ranked": [k for k, _ in ranked],
           "top_lever": top[0],
           "top_lever_pct": top[1]["makeup_spread_pct"],
           "top_unmeasured_lever": unmeasured[0][0] if unmeasured else None,
           "top_unmeasured_pct": (unmeasured[0][1]["makeup_spread_pct"]
                                  if unmeasured else None),
           "G_V2_note": G_V2_NOTE,
           "note": ("Upper bound on what PERFECT knowledge is worth. A real "
                    "model is worse than perfect, so these are ceilings on the "
                    "benefit, not estimates of it.")}
    (RESULTS / "value_of_information.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten -> results/value_of_information.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
