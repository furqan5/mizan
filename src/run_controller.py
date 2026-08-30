"""
MIZAN :: gate V3 (skin-temperature chemistry) and V5 (closed-loop economics)
============================================================================
Runs the supervisory optimiser against incumbent fixed-setpoint practice on
a Gulf district-cooling condenser loop, across a spread of ambient
conditions, using the fill law identified and validated in calibrate.py.

Every economic input is tagged. Tariffs are [A] pending founder
verification against SEC / Saudi Water Authority / Kahramaa published
schedules -- they are the one class of input in this package that is
assumed rather than measured, and the sensitivity of the result to them is
reported rather than hidden.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem
import controller as ctl
import psychro as ps

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
RESULTS.mkdir(exist_ok=True)

# ---- pre-registered acceptance criteria for V5 --------------------------
#
# THESE ARE THE ORIGINAL THRESHOLDS, FIXED AND PRINTED BEFORE ANY FITTING.
# They are not to be edited. If one of them turns out to have been badly
# chosen -- and the water threshold was, it required 8.5 cycles of
# concentration when gypsum saturates at 8 -- the honest response is to
# RECORD A REVISION below, not to change the number here.
V5_PRE_REGISTERED = {
    "makeup_water_reduction_pct_min": 15.0,
    "total_cost_reduction_pct_min": 3.0,
    "skin_SI_violations_allowed": 0,
}

# ---- declared revisions -------------------------------------------------
#
# A revision is legitimate. A SILENT revision is not. Anything added here
# must carry the original value, the new value, the date and the reason, and
# `src/audit.py` refuses to package a build where a revision exists without
# a matching entry in docs/threshold_revision_memo.md.
#
# To take option B from that memo, append:
#
#     {"criterion": "makeup_water_reduction_pct_min",
#      "was": 15.0, "now": 12.4, "date": "2026-08-30",
#      "reason": "The original threshold required 8.5 cycles of "
#                "concentration. Gypsum saturates at 8 on this makeup "
#                "water and is not pH-sensitive, so no control strategy "
#                "reaches it. Re-anchored to the saving available at the "
#                "last feasible cycle count, 7 cycles = 12.50 %."},
#
# and re-run. The report will print the revision alongside the result, and
# the deck will show the gate as revised rather than as originally passed.
V5_REVISIONS: list[dict] = []

V5_CRITERIA = dict(V5_PRE_REGISTERED)
for _rev in V5_REVISIONS:
    V5_CRITERIA[_rev["criterion"]] = _rev["now"]

# ---- plant archetype ----------------------------------------------------
# One condenser-water module of a Gulf district-cooling plant.
PLANT = {
    "Q_evap_kw": 10_000.0,        # 10 MW cooling, ~2 840 RT  [A archetype]
    "m_w": 478.0,                 # kg/s, sized for ~5 K condenser range [A]
    "m_a_rated": 400.0,           # kg/s at full fan  [A]
    "p_fan_rated_kw": 110.0,      # induced-draught cell bank  [A]
}

# ---- tariffs -- now from published schedules, not assumption ------------
# Electricity: Saudi business all-in retail, Dec 2025, SAR 0.277/kWh. The
#   published SEC schedule band is 22-32 halalas; the all-in figure includes
#   surcharge and 15% VAT. NO time-of-use tariff is published for Saudi
#   commercial/industrial customers, so the fan leg is valued at a FLAT
#   energy price -- claiming peak-shifting arbitrage would not survive
#   review.
# Water: Marafiq / Royal Commission for Jubail and Yanbu approved schedule,
#   effective 7 Dec 2025. The value of a cubic metre of blowdown avoided is
#   the makeup NOT bought plus the industrial wastewater NOT discharged:
#       SAR 8.04 (process water) + SAR 3.64 (industrial wastewater)
#     = SAR 11.68/m3 = USD 3.11/m3
#   This is the number that carries the business case, and both line items
#   come from the same approved schedule.
# Acid: bulk 98% H2SO4, Saudi. Quarterly assessments ran USD 148-380/tonne
#   over the last four quarters, the Q2-2026 spike attributed to Strait of
#   Hormuz disruption. Base case is set mid-range, deliberately not at
#   either extreme. Delivered small-lot pricing to a plant would be a
#   multiple of bulk and was not found [UNVERIFIED].
TARIFFS = {
    "elec_per_kwh": 0.074,        # USD/kWh, Saudi business all-in Dec 2025 [C]
    "water_per_m3": 3.11,         # USD/m3 avoided (makeup + discharge)     [C-derived]
    "acid_per_kg": 0.19,          # USD/kg bulk 98%, mid-range base case    [C]
    "antiscalant_per_m3": 0.05,   # USD per m3 makeup treated               [A]
}

# ---- makeup water: MEASURED Saudi analysis, not a third-party estimate ---
#
# Badruzzaman et al. (2022), Water Resources and Industry 28:100188 --
# Saudi Aramco, Dhahran. Treated municipal wastewater effluent used as
# makeup on an operating 4.2 MW cooling tower in Saudi Arabia.
#
# The published average column carries a ~14 % anion excess because the
# paper reports Min/Ave/Max independently per ion across a sampling
# campaign; averaging each ion separately does not preserve
# electroneutrality. Closed on sodium, the conventional balancing cation.
#
# Silica is not reported in the source and is NOT invented, so the silica
# constraint is inactive on this water. The true ceiling could therefore be
# lower than computed here if silica is present -- stated rather than
# assumed away.
TSE = chem.balance_sodium(chem.ARAMCO_RECLAIMED)

# ---- ambient conditions: Gulf operating spread [A] ----------------------
AMBIENTS = [
    ("Dhahran summer peak",   45.0, 20.0),
    ("Dhahran summer humid",  38.0, 55.0),
    ("Dhahran shoulder",      33.0, 40.0),
    ("Doha summer humid",     40.0, 50.0),
    ("Gulf winter",           22.0, 45.0),
]


def gate_v3():
    """V3: does evaluating saturation at the condenser skin, rather than in
    the bulk, change the operating limit by an amount that matters?"""
    print("=" * 78)
    print("GATE V3 -- saturation limit, bulk vs condenser skin temperature")
    print("=" * 78)
    print(f"makeup: published Saudi TSE, charge-balanced (Cl = {TSE.Cl:.0f} mg/L,"
          f" imbalance {TSE.charge_balance_pct():+.2f} %)")
    print()
    rows = []
    for T_bulk in [30.0, 33.0, 36.0]:
        for dT in [0.0, 3.8, 8.0]:   # 3.8 K typical, 8 K conservative/fouled
            T = T_bulk + dT
            mc = chem.max_cycles_split(TSE, T, T_bulk - 3.0)
            bm = chem.binding_mineral_split(TSE, mc, T, T_bulk - 3.0)
            rows.append({"T_bulk_C": T_bulk, "skin_delta_K": dT, "T_eval_C": T,
                         "max_cycles": mc, "binding_mineral": bm})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
    print()
    for T_bulk in [30.0, 33.0, 36.0]:
        sub = df[df.T_bulk_C == T_bulk]
        b = float(sub[sub.skin_delta_K == 0.0]["max_cycles"].iloc[0])
        typ = float(sub[sub.skin_delta_K == 3.8]["max_cycles"].iloc[0])
        s = float(sub[sub.skin_delta_K == 8.0]["max_cycles"].iloc[0])
        print(f"  bulk {T_bulk:.0f} C: limit {b:.2f} cycles; at +3.8 K (typical) "
              f"{typ:.2f} ({100*(b-typ)/typ:4.1f} % overstated); at +8 K (fouled) "
              f"{s:.2f} ({100*(b-s)/s:4.1f} % overstated)")
    df.to_csv(RESULTS / "v3_skin_vs_bulk.csv", index=False)
    return df


def gate_v5(fill_c, fill_n):
    """V5: optimised operation vs incumbent fixed-setpoint operation."""
    print()
    print("=" * 78)
    print("GATE V5 -- optimised vs incumbent fixed-setpoint operation")
    print("=" * 78)
    if V5_REVISIONS:
        print("pre-registered criteria:", json.dumps(V5_PRE_REGISTERED))
        print("DECLARED REVISIONS:")
        for r in V5_REVISIONS:
            print(f"   {r['criterion']}: {r['was']} -> {r['now']} "
                  f"({r['date']}) {r['reason']}")
        print("criteria as scored:", json.dumps(V5_CRITERIA))
    else:
        print("pre-registered criteria:", json.dumps(V5_CRITERIA),
              " (no revisions)")
    print(f"plant: {PLANT['Q_evap_kw']/1000:.0f} MW condenser module; "
          f"tariffs elec ${TARIFFS['elec_per_kwh']}/kWh, water "
          f"${TARIFFS['water_per_m3']}/m3 avoided  [published schedules]")
    print()

    ctl.reset_thermal_log()
    ctl.reset_chiller_range_log()

    rows = []
    for name, T_db, rh_pct in AMBIENTS:
        rh = rh_pct / 100.0
        T_wb = float(ps.wetbulb_from_rh(T_db, rh))
        cond = dict(PLANT)
        cond.update({"T_db": T_db, "rh": rh, "T_wi": T_wb + 12.0})

        # One solve first, to seed the duty fixed point for every later
        # point at this ambient. Without it each grid point re-converges
        # from a cold guess and the search costs several times more.
        seed = ctl._thermal_solve(70.0, 4.0, cond, TSE, fill_c, fill_n)
        if seed is not None:
            cond["T_wo_guess"] = seed[2]

        base = ctl.baseline(cond, TSE, TARIFFS, fill_c, fill_n,
                            fixed_cycles=4.0, fixed_ph=7.8, cw_setpoint_c=32.0,
                            fan_grid=np.arange(30, 101, 10.0))
        best, n_eval = ctl.optimise(
            cond, TSE, TARIFFS, fill_c, fill_n,
            fan_grid=np.arange(30, 101, 10.0),
            cycles_grid=np.arange(2.0, 10.01, 1.0),
            ph_grid=np.arange(7.0, 9.01, 0.25))
        if base is None or best is None:
            print(f"  {name:22s}  no feasible solution")
            continue

        rows.append({
            "condition": name, "T_db": T_db, "RH_pct": rh_pct, "T_wb": T_wb,
            "base_cycles": base["cycles"], "opt_cycles": best["cycles"],
            "base_fan_pct": base["fan_pct"], "opt_fan_pct": best["fan_pct"],
            "base_pH": base["target_ph"], "opt_pH": best["target_ph"],
            "base_makeup_m3_h": base["makeup_m3_h"],
            "opt_makeup_m3_h": best["makeup_m3_h"],
            "base_kW": base["P_total_kW"], "opt_kW": best["P_total_kW"],
            "base_fan_kW": base["P_fan_kW"], "opt_fan_kW": best["P_fan_kW"],
            "base_chiller_kW": base["P_chiller_kW"],
            "opt_chiller_kW": best["P_chiller_kW"],
            "base_cost_h": base["cost_per_h"], "opt_cost_h": best["cost_per_h"],
            "base_feasible_at_skin": base["feasible_at_skin"],
            "opt_feasible_at_skin": best["feasible_at_skin"],
            "base_T_cws_C": base["T_wo"], "opt_T_cws_C": best["T_wo"],
            "base_in_chiller_envelope": base["chiller_envelope_ok"],
            "opt_in_chiller_envelope": best["chiller_envelope_ok"],
            "water_saving_pct": 100 * (base["makeup_m3_h"] - best["makeup_m3_h"])
                                / base["makeup_m3_h"],
            "cost_saving_pct": 100 * (base["cost_per_h"] - best["cost_per_h"])
                               / base["cost_per_h"],
            # Electrical power is the first term of the objective and the
            # only reason fan speed is an actuator at all. It was being
            # monetised into cost_saving_pct and never reported on its own,
            # which made an energy product look like a water product.
            "energy_saving_pct": 100 * (base["P_total_kW"] - best["P_total_kW"])
                                 / base["P_total_kW"],
        })

    df = pd.DataFrame(rows)
    show = df[["condition", "T_wb", "base_cycles", "opt_cycles", "base_fan_pct",
               "opt_fan_pct", "base_makeup_m3_h", "opt_makeup_m3_h",
               "base_kW", "opt_kW", "energy_saving_pct",
               "water_saving_pct", "cost_saving_pct", "base_feasible_at_skin"]]
    print(show.to_string(index=False, float_format=lambda x: f"{x:8.2f}"))
    df.to_csv(RESULTS / "v5_controller.csv", index=False)

    w = float(df["water_saving_pct"].mean())
    c = float(df["cost_saving_pct"].mean())
    e = float(df["energy_saving_pct"].mean())
    viol = int((~df["opt_feasible_at_skin"]).sum())
    base_unsafe = int((~df["base_feasible_at_skin"]).sum())

    print()
    print(f"mean makeup-water reduction : {w:6.2f} %   "
          f"(criterion >= {V5_CRITERIA['makeup_water_reduction_pct_min']} %)  "
          f"{'PASS' if w >= V5_CRITERIA['makeup_water_reduction_pct_min'] else 'FAIL'}")
    print(f"mean total-cost reduction   : {c:6.2f} %   "
          f"(criterion >= {V5_CRITERIA['total_cost_reduction_pct_min']} %)  "
          f"{'PASS' if c >= V5_CRITERIA['total_cost_reduction_pct_min'] else 'FAIL'}")
    print(f"mean total-power reduction  : {e:6.2f} %   "
          f"(REPORTED, not a pre-registered gate -- see note below)")
    print(f"skin-SI violations by optimiser: {viol}   "
          f"(criterion 0)  {'PASS' if viol == 0 else 'FAIL'}")
    print()
    L, C = ctl.THERMAL_NONCONVERGED, ctl.CHILLER_RANGE_LOG
    print(f"numerics: {L['calls']} duty fixed points solved, "
          f"{L['failed']} did not converge to {1e-5:g} K")
    print(f"          chiller curve evaluated over "
          f"{C['T_cws_min']:.1f}-{C['T_cws_max']:.1f} degC entering condenser "
          f"water; {C['T_cws_out']} of {C['calls']} calls outside the fitted "
          f"range {ctl.CHILLER_TCWS_RANGE} (rejected, not extrapolated)")
    print()
    if base_unsafe:
        print(f"NOTE: the incumbent fixed 4-cycle baseline itself violates a "
              f"skin-temperature limit in {base_unsafe} of {len(df)} "
              f"conditions -- scaling while its bulk instrumentation reads "
              f"normal.")
    else:
        print(f"NOTE: the incumbent 4-cycle baseline is safe at skin "
              f"temperature in all {len(df)} conditions. It is conservative, "
              f"not unsafe: it leaves margin on the table rather than "
              f"crossing the limit.")
    up = int((df["opt_fan_pct"] > df["base_fan_pct"]).sum())
    down = int((df["opt_fan_pct"] < df["base_fan_pct"]).sum())
    print(f"      Optimiser raises cycles 4 -> {df['opt_cycles'].mean():.1f} "
          f"in every condition (the chemistry constraint boundary), and moves "
          f"the fan DOWN in {down} of {len(df)} conditions and UP in {up}.")
    print(f"      Fan speed is not a free lever: lowering it saves fan power "
          f"and evaporation but raises entering condenser water, and in the "
          f"four Gulf summer cases the optimum sits at")
    print(f"      {df['opt_T_cws_C'].max():.1f} degC -- hard against the "
          f"chiller's {ctl.CHILLER_TCWS_RANGE[1]:.0f} degC maximum entering "
          f"condenser water. In Gulf summer the binding limit on the fan is "
          f"the CHILLER envelope,")
    print(f"      not tower physics and not chemistry. That is the coupling "
          f"this product exists to price.")
    return df, {"revisions": V5_REVISIONS,
                "pre_registered": V5_PRE_REGISTERED,
                "water_pct": w, "cost_pct": c, "violations": viol,
                "energy_pct": e,
                "energy_pct_status": (
                    "REPORTED DIAGNOSTIC, NOT A PRE-REGISTERED GATE. "
                    "Electrical power reduction was always inside the "
                    "objective function -- cost = elec x P_total + water + "
                    "acid + antiscalant -- but was never reported on its "
                    "own. It is surfaced here because it is computed after "
                    "the fact; registering a threshold for it now would be "
                    "scoring a criterion chosen once the answer was known. "
                    "Same status as the hours-weighted annual figures in "
                    "results/annual_dhahran.json."),
                "baseline_unsafe_conditions": base_unsafe}


def gate_v5b(fill_c, fill_n, name="Dhahran summer humid", T_db=38.0,
             rh=0.55, fan=90.0):
    """The two ceilings.

    Sweeping cycles at fixed fan, with pH free to take its least-cost
    feasible value, separates two limits that incumbent practice conflates
    into one conductivity setpoint:

      * an ECONOMIC ceiling, where the acid needed to hold calcite in check
        starts costing more than the water it saves;
      * a PHYSICAL ceiling, where a mineral crosses saturation at the
        condenser skin.

    They are not the same number, and neither is visible to a fixed
    conductivity setpoint: the first needs a coupled cost model, the second
    needs ion-specific speciation. A Langelier index cannot see the binding
    mineral here at all.
    """
    print()
    print("=" * 78)
    print("GATE V5b -- the two ceilings: economic optimum vs physical limit")
    print("=" * 78)
    cond = dict(PLANT)
    cond.update({"T_db": T_db, "rh": rh})
    seed = ctl._thermal_solve(fan, 4.0, cond, TSE, fill_c, fill_n)
    if seed is not None:
        cond["T_wo_guess"] = seed[2]

    rows = []
    for cy in range(3, 13):
        th = ctl._thermal_solve(fan, float(cy), cond, TSE, fill_c, fill_n)
        if th is None:
            continue
        best, blocking = None, None
        for ph in np.arange(7.0, 9.01, 0.25):
            r = ctl._cost_at_ph(th, fan, float(cy), float(ph), cond, TSE,
                                TARIFFS, 8.0)
            if r["feasible"]:
                if best is None or r["cost_per_h"] < best["cost_per_h"]:
                    best = r
            elif blocking is None:
                blocking = sorted(r["violations"])
        rows.append({
            "cycles": cy,
            "feasible": best is not None,
            "best_pH": best["target_ph"] if best else np.nan,
            "makeup_m3_h": best["makeup_m3_h"] if best else np.nan,
            "acid_kg_h": best["acid_kg_h"] if best else np.nan,
            "water_cost_h": TARIFFS["water_per_m3"] * best["makeup_m3_h"] if best else np.nan,
            "acid_cost_h": TARIFFS["acid_per_kg"] * best["acid_kg_h"] if best else np.nan,
            "total_cost_h": best["cost_per_h"] if best else np.nan,
            "blocking_mineral": "" if best else ",".join(blocking or []),
        })
    df = pd.DataFrame(rows)
    print(f"condition: {name}, fan {fan:.0f} %, pH free to take its "
          f"least-cost feasible value")
    print(df.to_string(index=False, float_format=lambda x: f"{x:9.2f}"))

    feas = df[df.feasible]
    econ = int(feas.loc[feas.total_cost_h.idxmin(), "cycles"])
    infeas = df[~df.feasible]
    phys = int(infeas.cycles.min()) if len(infeas) else None
    mineral = infeas.blocking_mineral.iloc[0] if len(infeas) else "none in range"

    # Does the cost curve actually turn over inside the feasible region, or
    # does it fall monotonically until the chemistry stops it? These are
    # different situations and must not be described with the same words.
    turns_over = econ < int(feas.cycles.max())

    print()
    if turns_over:
        print(f"  ECONOMIC ceiling : {econ} cycles -- cost turns back up here, "
              f"because the acid needed to hold calcite starts costing more "
              f"than the water saved.")
        print(f"  PHYSICAL ceiling : {phys} cycles -- first saturation "
              f"violation at the evaluation point, binding mineral {mineral}.")
        print(f"  The two are {phys - econ} cycles apart. A plant operating "
              f"between them is paying for cycles that do not pay back.")
    else:
        print(f"  The cost curve does NOT turn over. Operating cost falls "
              f"monotonically to {econ} cycles, the last feasible point.")
        print(f"  PHYSICAL ceiling : {phys} cycles -- binding mineral "
              f"{mineral}. Acid cannot move it: sulfate saturation is not "
              f"pH-sensitive,")
        print(f"  so the lever that buys cycles against calcite stops working "
              f"entirely at this wall.")
        print()
        print(f"  This is the more dangerous case. The economics point "
              f"straight at a hard limit, and the Langelier index the "
              f"industry controls on")
        print(f"  describes calcite only -- it cannot represent "
              f"{mineral.replace('SI_','')} at all. An operator following the "
              f"money with LSI-based control walks into the wall blind.")
    df.to_csv(RESULTS / "v5b_two_ceilings.csv", index=False)
    return df, {"economic_ceiling_cycles": econ,
                "physical_ceiling_cycles": phys,
                "binding_mineral": mineral}


if __name__ == "__main__":
    cal = json.loads((RESULTS / "calibration.json").read_text())
    fill_c, fill_n = cal["fill_c"], cal["fill_n"]
    print(f"using validated fill law Me = {fill_c:.4f} (m_w/m_a)^({fill_n:.4f})")
    print(f"holdout accuracy: Tout MAE {cal['HOLDOUT']['Tout_MAE_K']:.3f} K, "
          f"evap MAPE {cal['HOLDOUT']['evap_MAPE_pct']:.2f} %\n")
    v3 = gate_v3()
    v5, summary = gate_v5(fill_c, fill_n)
    _v5b, ceilings = gate_v5b(fill_c, fill_n)
    summary.update(ceilings)
    (RESULTS / "controller_summary.json").write_text(
        json.dumps({"criteria": V5_CRITERIA, "plant": PLANT,
                    "tariffs": TARIFFS, "summary": summary}, indent=2),
        encoding="utf8")
    print(f"\nwritten -> {RESULTS/'v3_skin_vs_bulk.csv'}, "
          f"{RESULTS/'v5_controller.csv'}, {RESULTS/'controller_summary.json'}")
