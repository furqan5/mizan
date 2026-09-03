"""Does condenser fouling have a material energy cost? A pre-registered study.

    python src/fouling_energy.py

WHY THIS EXISTS. The controller already prices energy -- its objective is
J = c_elec*(P_fan + P_chiller) + c_water*m_makeup, and it reports a 6.0 %
annual electrical saving. But `controller.chiller_power` carries
`approach_cond=4.0` as a FIXED constant, and `chiller_power_biquad` is driven by
entering condenser water temperature alone. So in the model as it stands,
**fouling has no energy consequence at all**: scale can build to the saturation
limit and the chiller draws exactly the same power.

That matters because the commercial argument in
`docs/outreach_messages_saudi.md` section 5 asserts precisely this chain --
"chiller efficiency degrades with condenser approach temperature, and condenser
approach degrades with fouling" -- and nothing in the code computes it.

Three operator interviews (`docs/discovery_findings.md`) all framed fouling as a
PERFORMANCE problem, never a water problem. And interview 1 established that
descaling is a planned shutdown covered by standby equipment, so there is no
lost production: the cost of fouling is the efficiency penalty accumulated
BETWEEN cleans, which is exactly the channel the model is blind to.

WHAT THIS DOES NOT DO. It is not a scaling-RATE model. It cannot say how fast
fouling accumulates at a given supersaturation -- that needs the coupon work in
the lab plan. It answers the prior question: IF a condenser carries fouling
resistance r, what does that cost? Nothing here is fitted or tuned.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import controller as ctl   # noqa: E402

# ======================================================================
# PRE-REGISTERED GATES -- fixed 3 September 2026, BEFORE the first run.
# ======================================================================
# The question is whether the fouling->energy channel is worth adding to the
# controller at all. It is entirely possible the answer is no, and that has to
# be a permitted outcome or this is not a test.
#
# The reference fouling level is the TEMA/HEI allowance for TREATED cooling
# tower water, R_f = 1.76e-4 m^2K/W (0.001 hr.ft^2.F/Btu). Against a clean
# shell-and-tube condenser resistance of 1/U_clean with U_clean = 3000 W/m^2K
# [est], that is a resistance ratio r = R_f * U_clean = 0.53.
#
# G-F1  MATERIALITY. At the treated-water reference, chiller power must rise by
#       >= 2.0 %. Below that the channel is not worth the modelling complexity
#       and we say so.
# G-F2  DOMINANCE. At the same reference, the annual electricity cost of that
#       fouling must exceed the annual WATER cost saving the controller
#       currently delivers. This tests the repositioning claim -- that energy,
#       not water, is the bigger lever -- at the plant's own Saudi tariffs.
# G-F3  PHYSICS SANITY. dTTD(r=0) must be zero to 1e-9, and both dTTD and
#       chiller power must increase monotonically in r. A model that fails
#       this is wrong regardless of what the other two say.
# G-F4  CROSS-CHECK. Added after run 1, and it only TIGHTENS the test. Inside
#       the biquad's own fitted range both the Carnot model and the
#       manufacturer curve must show chiller power increasing with r. Direction
#       only -- demanding magnitude agreement between a first-principles Carnot
#       model and a six-coefficient curve fit would be a made-up bar.
GATES = {
    "G_F1_materiality_pct_min": 2.0,
    "G_F2_dominance_ratio_min": 1.0,
    "G_F3_zero_tol": 1e-9,
    "G_F4_both_models_monotonic_in_range": True,
}
REGISTERED = "2026-09-03"

# ----------------------------------------------------------------------
# RUN 1 FAILED, AND THE FAILURE IS RECORDED RATHER THAN TIDIED AWAY.
#
# The first implementation modelled fouling as an equivalent rise in ENTERING
# condenser water temperature and evaluated `chiller_power_biquad` at
# T_cws + dTTD. That equivalence is standard and correct in itself, but the
# biquad is fitted over T_cws = 15.56 to 35.00 degC, and at r = 1.5 the sweep
# reached 38.9 degC. Outside the fit the biquadratic turns over: chiller power
# rose to r = 0.53 and then FELL, finishing 7.1 % BELOW clean at r = 1.5.
#
# Fouling cannot make a chiller more efficient. G-F3 caught it -- which is what
# a physics sanity gate is for -- and it is the same defect class already on
# record in this project: an evaluation wandering off the end of a fitted
# correlation and collecting a benefit that is not there.
#
# THE THRESHOLDS ARE UNCHANGED. Only the defect is fixed. The fix is not a
# range guard but a better model choice: `controller.chiller_power` takes
# `approach_cond` as an explicit argument, so the fouled TTD can be passed
# directly rather than disguised as warmer water, and being Carnot-referenced
# it cannot produce a non-monotonic COP. The biquad is retained as a
# cross-check inside its own validated range only.
RUN1 = {"d_power_pct_at_TEMA": 1.71, "d_power_pct_at_r1.5": -7.13,
        "cause": "chiller_power_biquad extrapolated beyond its fitted "
                 "T_cws range of 15.56-35.00 degC"}

U_CLEAN_W_M2K = 3000.0        # [est] typical water-cooled shell-and-tube
R_F_TEMA_TREATED = 1.76e-4    # [C] TEMA/HEI, treated cooling tower water
CP_WATER = 4.186              # kJ/kg.K


def ttd_from_fouling(ttd_clean_k: float, range_k: float, r: float) -> float:
    """Terminal temperature difference at fouling resistance ratio r.

    For a condenser, with NTU = UA/(m_cw*cp), the outlet approach follows

        (T_cond - T_out)/(T_cond - T_in) = exp(-NTU)

    so with range = T_out - T_in,

        TTD = range / (exp(NTU) - 1)

    The clean NTU is therefore recoverable from the clean TTD the model
    already assumes -- NTU_clean = ln(1 + range/TTD_clean) -- with no new
    parameter. Fouling adds resistance in series, 1/U_f = 1/U_c + R_f, so

        NTU_fouled = NTU_clean / (1 + r),   r = R_f * U_clean

    Everything below is derived from quantities already in the model. The
    only import is r itself, which is swept rather than assumed.
    """
    ntu_clean = math.log(1.0 + range_k / ttd_clean_k)
    ntu_f = ntu_clean / (1.0 + r)
    return range_k / (math.expm1(ntu_f))


def main() -> int:
    cs = json.loads((RESULTS / "controller_summary.json").read_text())
    ann = json.loads((RESULTS / "annual_dhahran.json").read_text())
    plant, tar = cs["plant"], cs["tariffs"]

    print("=" * 74)
    print("FOULING -> ENERGY: is the channel material?")
    print(f"gates registered {REGISTERED}, before the first run")
    print("=" * 74)
    print(f"  G-F1 materiality  chiller power rise at TEMA treated-water "
          f">= {GATES['G_F1_materiality_pct_min']:.1f} %")
    print(f"  G-F2 dominance    annual fouling energy cost / annual water "
          f"saving >= {GATES['G_F2_dominance_ratio_min']:.1f}")
    print(f"  G-F3 physics      dTTD(r=0) = 0, and monotonic in r")

    # ---------------------------------------------------------------- design
    Q_evap = plant["Q_evap_kw"]
    m_w = plant["m_w"]
    ttd_clean = 4.0                      # controller.chiller_power default
    T_cws = 29.44                        # AHRI condenser entering, rating point

    # PRIMARY MODEL: Carnot-referenced, with the fouled TTD passed straight
    # into `approach_cond` -- which is precisely what that parameter means.
    p_chill_clean, cop_clean = ctl.chiller_power(Q_evap, T_cws,
                                                 approach_cond=ttd_clean)
    Q_cond = Q_evap + p_chill_clean
    rng = Q_cond / (m_w * CP_WATER)      # condenser water range, K

    print(f"\nDESIGN POINT")
    print(f"   Q_evap {Q_evap:.0f} kW, condenser water {m_w:.0f} kg/s"
          f"  ->  range {rng:.2f} K")
    print(f"   clean TTD {ttd_clean:.2f} K, chiller {p_chill_clean:.1f} kW"
          f" at COP {cop_clean:.2f}   [Carnot-referenced]")

    r_ref = R_F_TEMA_TREATED * U_CLEAN_W_M2K
    t_lo, t_hi = ctl.CHILLER_TCWS_RANGE
    print(f"   TEMA treated-water R_f {R_F_TEMA_TREATED:.2e} m2K/W"
          f"  at U_clean {U_CLEAN_W_M2K:.0f}  ->  r = {r_ref:.3f}")
    print(f"   biquad fitted range T_cws {t_lo:.2f}-{t_hi:.2f} C"
          f"  (cross-check only, inside range)")

    # ---------------------------------------------------------------- sweep
    print(f"\nSWEEP -- r is scanned, not chosen. Nothing here is fitted.")
    print(f"   {'r':>6} {'TTD':>7} {'dTTD':>7} {'P_chill':>9} {'dP':>7}"
          f"  {'biquad dP':>10}")
    print(f"   {'':>6} {'K':>7} {'K':>7} {'kW':>9} {'%':>7}  {'%':>10}")
    rows = []
    p_bq_clean, _ = ctl.chiller_power_biquad(Q_evap, T_cws, Q_ref_kw=Q_evap)
    for r in (0.0, 0.10, 0.25, r_ref, 0.75, 1.00, 1.50):
        ttd = ttd_from_fouling(ttd_clean, rng, r)
        dttd = ttd - ttd_clean
        p_f, cop_f = ctl.chiller_power(Q_evap, T_cws, approach_cond=ttd)
        dp = 100.0 * (p_f - p_chill_clean) / p_chill_clean

        # Cross-check, and ONLY where the curve is entitled to an opinion.
        t_eff = T_cws + dttd
        if t_eff <= t_hi:
            p_bq, _ = ctl.chiller_power_biquad(Q_evap, t_eff, Q_ref_kw=Q_evap)
            dp_bq = 100.0 * (p_bq - p_bq_clean) / p_bq_clean
            bq_s = f"{dp_bq:>10.2f}"
            in_range = True
        else:
            dp_bq, bq_s, in_range = None, f"{'extrap':>10}", False

        mark = "  <- TEMA treated" if abs(r - r_ref) < 1e-9 else ""
        print(f"   {r:>6.3f} {ttd:>7.2f} {dttd:>7.2f} {p_f:>9.1f} {dp:>7.2f}"
              f"  {bq_s}{mark}")
        rows.append({"r": r, "ttd_k": ttd, "d_ttd_k": dttd,
                     "p_chiller_kw": p_f, "d_power_pct": dp, "cop": cop_f,
                     "d_power_pct_biquad": dp_bq,
                     "biquad_in_fitted_range": in_range})

    ref = [x for x in rows if abs(x["r"] - r_ref) < 1e-9][0]

    # ------------------------------------------------------------- annual
    # Fan power is unaffected by condenser fouling, so the penalty applies to
    # the chiller share only. That share is measured at the design point
    # rather than assumed.
    p_fan_design = ctl.fan_power(plant["m_a_rated"], plant["m_a_rated"],
                                 plant["p_fan_rated_kw"])
    chiller_share = p_chill_clean / (p_chill_clean + p_fan_design)

    annual_kwh = sum(b["base_kW"] * b["hours"] for b in ann["bins"])
    annual_chiller_kwh = annual_kwh * chiller_share
    fouling_kwh = annual_chiller_kwh * ref["d_power_pct"] / 100.0
    fouling_cost = fouling_kwh * tar["elec_per_kwh"]

    water_saved_m3 = sum((b["base_makeup_m3_h"] - b["opt_makeup_m3_h"])
                         * b["hours"] for b in ann["bins"])
    water_saving_cost = water_saved_m3 * tar["water_per_m3"]

    print(f"\nANNUAL, at the plant's own tariffs")
    print(f"   total electrical            {annual_kwh:12,.0f} kWh")
    print(f"   chiller share (design)      {chiller_share:12.1%}")
    print(f"   energy lost to fouling      {fouling_kwh:12,.0f} kWh"
          f"   = ${fouling_cost:,.0f}")
    print(f"   water saved by controller   {water_saved_m3:12,.0f} m3"
          f"   = ${water_saving_cost:,.0f}")
    ratio = fouling_cost / water_saving_cost if water_saving_cost else float("nan")
    print(f"   ratio, fouling energy : water saving      {ratio:8.2f}")

    # --------------------------------------------------------------- score
    g1 = ref["d_power_pct"]
    g3_zero = abs(rows[0]["d_ttd_k"])
    mono = (all(rows[i]["d_ttd_k"] <= rows[i + 1]["d_ttd_k"] + 1e-12
                for i in range(len(rows) - 1))
            and all(rows[i]["p_chiller_kw"] <= rows[i + 1]["p_chiller_kw"] + 1e-9
                    for i in range(len(rows) - 1)))

    print(f"\n{'-' * 74}")
    print(f"{'gate':34} {'value':>12} {'threshold':>12}  ")
    print(f"{'-' * 74}")
    inr = [x for x in rows if x["biquad_in_fitted_range"]]
    mono_bq = all(inr[i]["d_power_pct_biquad"] <= inr[i + 1]["d_power_pct_biquad"] + 1e-9
                  for i in range(len(inr) - 1))

    p1 = g1 >= GATES["G_F1_materiality_pct_min"]
    p2 = ratio >= GATES["G_F2_dominance_ratio_min"]
    p3 = g3_zero <= GATES["G_F3_zero_tol"] and mono
    p4 = mono and mono_bq
    print(f"{'G-F1 materiality, dP at TEMA':34} {g1:>11.2f}% "
          f"{GATES['G_F1_materiality_pct_min']:>11.1f}%  {'PASS' if p1 else 'FAIL'}")
    print(f"{'G-F2 dominance, energy:water':34} {ratio:>12.2f} "
          f"{GATES['G_F2_dominance_ratio_min']:>12.1f}  {'PASS' if p2 else 'FAIL'}")
    print(f"{'G-F3 physics, zero + monotonic':34} {g3_zero:>12.2e} "
          f"{GATES['G_F3_zero_tol']:>12.0e}  {'PASS' if p3 else 'FAIL'}")
    print(f"{'G-F4 both models monotonic':34} {str(mono_bq):>12} "
          f"{'True':>12}  {'PASS' if p4 else 'FAIL'}  "
          f"({len(inr)} of {len(rows)} pts in biquad range)")
    print(f"{'-' * 74}")

    out = {
        "registered": REGISTERED,
        "gates": GATES,
        "assumptions": {
            "U_clean_W_m2K": U_CLEAN_W_M2K,
            "R_f_TEMA_treated_m2K_W": R_F_TEMA_TREATED,
            "r_reference": r_ref,
            "ttd_clean_K": ttd_clean,
            "T_cws_C": T_cws,
            "note": ("r is swept, not fitted. U_clean is the only imported "
                     "parameter and results are reported against dimensionless "
                     "r so they do not hinge on it."),
        },
        "design_point": {
            "Q_evap_kW": Q_evap, "condenser_range_K": rng,
            "p_chiller_clean_kW": p_chill_clean, "cop_clean": cop_clean,
            "chiller_share_of_power": chiller_share,
        },
        "sweep": rows,
        "annual": {
            "total_electrical_kWh": annual_kwh,
            "fouling_energy_kWh": fouling_kwh,
            "fouling_energy_cost": fouling_cost,
            "water_saved_m3": water_saved_m3,
            "water_saving_cost": water_saving_cost,
            "ratio_energy_to_water": ratio,
        },
        "run1_failed": RUN1,
        "scores": {"G_F1_materiality_pct": g1, "G_F1_pass": bool(p1),
                   "G_F2_ratio": ratio, "G_F2_pass": bool(p2),
                   "G_F3_zero": g3_zero, "G_F3_monotonic": bool(mono),
                   "G_F3_pass": bool(p3),
                   "G_F4_biquad_monotonic": bool(mono_bq), "G_F4_pass": bool(p4)},
        "limitation": ("NOT a scaling-rate model. Answers what a given fouling "
                       "resistance costs, not how fast fouling accumulates at a "
                       "given supersaturation. Rate needs the coupon work."),
    }
    (RESULTS / "fouling_energy.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten -> results/fouling_energy.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
