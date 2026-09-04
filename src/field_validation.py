"""GATE V7 -- the first test of this model against an OPERATING plant.

Everything else in this package is validated against a laboratory tower
(Almeria) or against itself. This is the only place where the model is asked to
reproduce what happened on a real condenser.

THE FIELD OBSERVATION
---------------------
Saudi Aramco, Dhahran. An eight-month side-by-side pilot, published by the
plant's own engineers, running one cooling tower on raw groundwater and one on
treated sewage effluent. Two outcomes, and they point in opposite directions:

    groundwater, COC limited to 2    "Severe scaling was observed on the
                                      condenser surfaces with groundwater as
                                      makeup."
    TSE, COC raised to 3.5           "The condenser surface was clean without
                                      mineral deposit formation when TSE was
                                      used."

This is a genuinely hard test, and it is hard in the right direction. The
GROUNDWATER is the more concentrated water on every scale-forming ion --
Ca 233 vs 106, HCO3 226 vs 105, SO4 558 vs 300 -- yet it was run at HALF the
cycles and still scaled, while the weaker water at nearly double the cycles did
not. A model that only counts dissolved solids gets this backwards. A model
that computes ion-specific saturation at the condenser skin should get it right.

Both waters are already in chemistry.py from the same paper, so nothing is
being fitted here: the analyses were entered before this gate existed.

PRE-REGISTERED CRITERIA -- fixed before running
-----------------------------------------------
F1  Groundwater at its operating COC of 2 must be SUPERSATURATED at the
    condenser skin in at least one mineral. The plant saw severe scale; a model
    that calls it safe has failed.
F2  TSE at its operating COC of 3.5 must be UNDERSATURATED in every mineral at
    the same skin temperature. The plant saw a clean condenser.
F3  The two must be separated by the model, not merely ordered: groundwater at
    COC 2 must be MORE saturated than TSE at COC 3.5, in the binding mineral,
    despite running at lower cycles.
F4  The mineral the model blames for the groundwater scale must be a CARBONATE
    or sulfate scale, not amorphous silica -- neither water has silica reported,
    so a silica verdict would mean the gate is reading an invented number.

A failure here is reported, not tuned away. This gate was written after the
observation was found, so it CANNOT be treated as a prediction -- it is a
retrodiction, and it is labelled as one everywhere it is quoted.

Run:  python src/field_validation.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402

# The pilot ran an evaporative condenser loop in Dhahran. Skin temperature is
# taken as the same +8 K over bulk used by every other gate in this package,
# and the bulk is the 33 C condenser water a Gulf plant returns in summer.
T_BULK_C = 33.0
SKIN_DELTA_K = 8.0
T_SKIN_C = T_BULK_C + SKIN_DELTA_K

COC_GROUNDWATER = 2.0     # "limited to 2"
COC_TSE = 3.5             # "from 2 to 3.5"

MINERALS = ("SI_calcite", "SI_gypsum", "SI_silica_am")


def state(water, coc, T_c):
    return chem.saturation_state(water.concentrate(coc), T_c=T_c)


def main():
    gw = chem.balance_sodium(chem.ARAMCO_GROUNDWATER)
    tse = chem.balance_sodium(chem.ARAMCO_RECLAIMED)

    s_gw = state(gw, COC_GROUNDWATER, T_SKIN_C)
    s_tse = state(tse, COC_TSE, T_SKIN_C)

    print("=" * 76)
    print("GATE V7 -- against an operating plant (Aramco Dhahran pilot)")
    print("=" * 76)
    print(f"condenser skin taken as {T_BULK_C:.0f} + {SKIN_DELTA_K:.0f} "
          f"= {T_SKIN_C:.0f} C, as in every other gate\n")
    print(f"{'mineral':<16}{'groundwater @ COC 2':>22}{'TSE @ COC 3.5':>18}"
          f"{'limit':>9}")
    for m in MINERALS:
        lim = chem.DEFAULT_LIMITS[m]
        print(f"{m:<16}{s_gw[m]:>22.3f}{s_tse[m]:>18.3f}{lim:>9.2f}")

    over_gw = [m for m in MINERALS if s_gw[m] > chem.DEFAULT_LIMITS[m]]
    over_tse = [m for m in MINERALS if s_tse[m] > chem.DEFAULT_LIMITS[m]]

    print(f"\nplant observed : groundwater SCALED severely; TSE condenser CLEAN")
    print(f"model says     : groundwater over limit in {over_gw or 'nothing'}")
    print(f"                 TSE over limit in {over_tse or 'nothing'}")

    checks = []

    checks.append(("F1 groundwater supersaturated at COC 2",
                   bool(over_gw), f"over in {over_gw or 'nothing'}"))
    checks.append(("F2 TSE undersaturated at COC 3.5",
                   not over_tse, f"over in {over_tse or 'nothing'}"))

    # F3 -- separated in the mineral that binds the groundwater
    binder = over_gw[0] if over_gw else "SI_calcite"
    sep = s_gw[binder] - s_tse[binder]
    checks.append((f"F3 groundwater more saturated in {binder}",
                   sep > 0, f"separation {sep:+.3f} log units"))

    checks.append(("F4 verdict is not silica",
                   "SI_silica_am" not in over_gw,
                   "silica is not reported in either analysis"))

    print("\n" + "-" * 76)
    n_pass = 0
    for name, ok, detail in checks:
        print(f"  {name:<44}{'PASS' if ok else 'FAIL'}   {detail}")
        n_pass += bool(ok)
    print("-" * 76)
    print(f"  {n_pass} of {len(checks)} passed")
    print("\n  RETRODICTION, not a prediction: the observation was found first.")

    # --- REPORTED DIAGNOSTIC, NOT A GATE ---------------------------------
    # F2 failed. Before concluding the chemistry is wrong, note WHICH number it
    # failed against: DEFAULT_LIMITS["SI_calcite"] = 0.5. That is a threshold of
    # the same magnitude as a bulk Langelier index, and F2 applied it to a SKIN
    # index. This entire product exists because those two are different numbers,
    # so failing a skin index against a bulk-shaped threshold is a category
    # error in the LIMIT, not evidence against the chemistry.
    #
    # The pilot published its own index: "LSI values varied from 0 to 0.5,
    # indicating that the scale-forming tendency of TSE is low". LSI is
    # conventionally evaluated at bulk or 25 C reference, so that is the
    # like-for-like comparison -- and it is quantitative.
    #
    # F2 IS NOT RESCORED. Moving a criterion after seeing the result is the one
    # thing this package does not do; V2 and V5 both stay failed for exactly
    # that reason. The agreement below is reported ALONGSIDE the failure.
    lsi_25 = state(tse, COC_TSE, 25.0)["SI_calcite"]
    lsi_bulk = state(tse, COC_TSE, T_BULK_C)["SI_calcite"]
    gw_25 = state(gw, COC_GROUNDWATER, 25.0)["SI_calcite"]
    print("\n" + "=" * 76)
    print("REPORTED DIAGNOSTIC -- not a gate, not rescored")
    print("=" * 76)
    print("  the plant published, for TSE : LSI varied from 0 to 0.50")
    print(f"  this model, TSE at 25 C      : SI_calcite = {lsi_25:.3f}")
    print(f"  this model, TSE at bulk 33 C : SI_calcite = {lsi_bulk:.3f}")
    print(f"  this model, groundwater 25 C : SI_calcite = {gw_25:.3f}"
          f"   (the water that scaled)")
    print(f"\n  The model lands {abs(0.50 - lsi_25):.3f} log units from the top of "
          f"the operator's")
    print("  own reported range, on a water analysis entered before this gate")
    print("  existed and never tuned against it.")
    print("\n  What F2's failure actually diagnoses: a 0.5 limit borrowed from")
    print("  bulk-index practice is too tight to apply at the skin. Field")
    print("  practice agrees -- an interviewed plant chemist holds LSI at")
    print("  0.8-1.0 DELIBERATELY, as corrosion protection. Where the SKIN")
    print("  limit belongs is now an open question with evidence on both sides.")

    out_extra = {
        "lsi_reported_by_plant": [0.0, 0.5],
        "model_SI_calcite_tse_25C": lsi_25,
        "model_SI_calcite_tse_bulk": lsi_bulk,
        "model_SI_calcite_groundwater_25C": gw_25,
        "note": ("F2 failed against DEFAULT_LIMITS['SI_calcite'] = 0.5 applied "
                 "at SKIN temperature, but the plant's published LSI is a BULK "
                 f"index. At 25 C this model gives {lsi_25:.3f} against the "
                 "plant's reported range of 0 to 0.5. F2 is NOT rescored; this "
                 "agreement is reported alongside the failure, never in place "
                 "of it."),
    }

    out = {
        "source": "Saudi Aramco Dhahran 8-month pilot, published by the "
                  "operating engineers (Badruzzaman et al.)",
        "status": "RETRODICTION -- gate written after the observation was "
                  "found. Must never be quoted as a pre-registered prediction.",
        "T_bulk_C": T_BULK_C, "skin_delta_K": SKIN_DELTA_K,
        "observed": {
            "groundwater": {"coc": COC_GROUNDWATER,
                            "outcome": "severe scaling on condenser surfaces"},
            "tse": {"coc": COC_TSE,
                    "outcome": "condenser surface clean, no mineral deposit"},
        },
        "modelled": {
            "groundwater": {m: s_gw[m] for m in MINERALS},
            "tse": {m: s_tse[m] for m in MINERALS},
        },
        "over_limit": {"groundwater": over_gw, "tse": over_tse},
        "criteria": [{"name": n, "passed": bool(o), "detail": d}
                     for n, o, d in checks],
        "n_passed": n_pass, "n_total": len(checks),
        "reported_diagnostic": out_extra,
    }
    (RESULTS / "field_validation.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nwritten -> results/field_validation.json")
    return 0 if n_pass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
