"""
FURQAN / MIZAN :: four-region 24-hour benchmark, for the pitch pack.

WHAT THIS PRODUCES AND WHAT IT IS WORTH.

Four regional archetypes, each run for 24 hours through the coupled
tower + CDU + chemistry supervisor, comparing two policies:

    blind_free_cooling    the thermal-only economizer. Takes the coldest
                          facility water the tower can make, because colder
                          water is compressor work avoided. This is what
                          every optimiser in the surveyed literature does.
    chemically_bounded    refuses to cool below the silica floor, and pays
                          for the warmer supply on the CDU side instead.

EVERY PARAMETER CARRIES AN EVIDENCE TAG, and the script prints them:

    [C]  confirmed against a published schedule, standard or dataset
    [A]  an archetype -- a plausible design figure, not a measurement
    [U]  unverified: a working number that a reviewer should replace

The Dhahran profile is REAL HOURLY WEATHER from the station TMYx file. The
other three are sinusoidal profiles anchored on published design conditions,
which is weaker and is tagged accordingly. A sine is not a climate, and a
number derived from one should not be quoted as an annual saving.

RUNTIME, resolved 11 Sep 2026. This script previously completed only the
Gulf region and the banner here said so. The cause was never the physics:
`hybrid_supervisor.solve_free_cooling` was a damped fixed-point substitution
taking 17.7 s per call, and `fan_for_target_fws` bisected over it. Replacing
the substitution with a secant iteration cut it to 2.82 s -- 6.3x, to the
same answer -- and all four regions now run.

WHAT IS STILL WEAK, and must not be quoted as if it were not:

  * silica in the makeup is ASSUMED at 26.8 mg/L, imported from Riyadh
    brackish groundwater. We now hold a MEASURED Gulf TSE silica -- 18.0
    mg/L, NACE Paper 577 Table 1 -- and the Cycle Ceiling Report runs on it.
    This script does not, because switching the package default would move
    every pinned gate figure at once. Until that is done deliberately, the
    silica-driven results here are a SENSITIVITY, not a site prediction.
  * three of the four weather profiles are sinusoids anchored on design
    conditions, not real weather. Only Dhahran is a TMYx file.

Run:  python scripts/generate_pitch_artifacts.py
Writes: results/pitch_artifacts.json
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chemistry as chem                    # noqa: E402
import hybrid_supervisor as hs              # noqa: E402
import psychro as ps                        # noqa: E402
from models import cdu_model as cdu         # noqa: E402

RESULTS = ROOT / "results"

USD_PER_PKR = 1.0 / 278.0      # [C] Pakistan Observer, 8 Sep 2026
USD_PER_EUR = 1.08             # [U] working rate
USD_PER_SAR = 1.0 / 3.75       # [C] peg


# ---------------------------------------------------------------------------
# Regional archetypes
# ---------------------------------------------------------------------------
REGIONS = {
    "Gulf_Dhahran": {
        "label": "Gulf — Dhahran, Saudi Arabia",
        "weather": "tmy",                      # [C] station TMYx 2011-2025
        "q_it_kw": 9_000.0,                    # [A] a 9 MW IT hall
        "cycles": 5.0,
        "tariffs": {
            "elec_per_kwh": 0.074,             # [C] SEC business all-in, Dec 2025
            "water_per_m3": 3.115,             # [C] Marafiq, 7 Dec 2025
            "water_makeup_per_m3": 2.144,      # [C] SAR 8.04 / 3.75
            "water_discharge_per_m3": 0.971,   # [C] SAR 3.64 / 3.75
            "acid_per_kg": 0.19,               # [C] bulk 98 % H2SO4
            "antiscalant_per_m3": 0.05,        # [A]
        },
        "driver": "Ministerial Directive 20/2013 — desalinated water "
                  "forbidden for cooling; TSE mandated",   # [C]
        "currency": ("USD", 1.0),
    },
    "USA_NorthernVirginia": {
        "label": "USA — Loudoun County, Virginia",
        "weather": ("sine", 24.0, 34.0, 0.55),   # [A] profile shape
        "q_it_kw": 20_000.0,                     # [A]
        "cycles": 5.0,
        "tariffs": {
            "elec_per_kwh": 0.0853,            # [C] Dominion GS-4, 15 MW at
                                               #     73 % LF, June 2026
            "water_per_m3": 3.05,              # [U] derived, see below
            "water_makeup_per_m3": 1.31,       # [U] supply rate NOT FOUND
            "water_discharge_per_m3": 1.74,    # [C-derived] Loudoun Water
                                               #     $5.76/kgal 2024 + 7 % + 7 %
            "acid_per_kg": 0.19,               # [A]
            "antiscalant_per_m3": 0.05,        # [A]
        },
        "driver": "No federal reuse law; state-level water reporting "
                  "mandates advancing. SC and KS considering closed-loop "
                  "mandates",                  # [C]
        "currency": ("USD", 1.0),
    },
    "Europe_Frankfurt": {
        "label": "Europe — Frankfurt, Germany",
        "weather": ("sine", 14.0, 22.0, 0.62),   # [A] profile shape
        "q_it_kw": 20_000.0,                     # [A]
        "cycles": 5.0,
        "tariffs": {
            "elec_per_kwh": 0.216,             # [U] ~EUR 0.20 industrial
            "water_per_m3": 4.60,              # [U]
            "water_makeup_per_m3": 2.30,       # [U]
            "water_discharge_per_m3": 2.30,    # [U]
            "acid_per_kg": 0.25,               # [A]
            "antiscalant_per_m3": 0.06,        # [A]
        },
        "driver": "EnEfG: PUE <= 1.2 for data centres commissioned from "
                  "1 Jul 2026 (within two years); existing <= 1.5 by "
                  "1 Jul 2027 and <= 1.3 by 1 Jul 2030. ERF >= 10 % from "
                  "1 Jul 2026, 15 % 2027, 20 % 2028. Applies above 300 kW; "
                  "fines to EUR 100,000",      # [C]
        "currency": ("EUR", 1.0 / USD_PER_EUR),
    },
    "Pakistan_Balloki": {
        "label": "Pakistan — Balloki / Punjab industrial",
        "weather": ("sine", 27.0, 40.0, 0.45),   # [A] profile shape
        "q_it_kw": 8_000.0,                      # [C-derived] see note
        "cycles": 5.0,
        "tariffs": {
            "elec_per_kwh": 27.00 * USD_PER_PKR,   # [C] NEPRA B3 peak
            "elec_offpeak_per_kwh": 23.67 * USD_PER_PKR,  # [C] NEPRA B3
            "water_per_m3": 5.0 * USD_PER_PKR,     # [U] WWF/ILO implied
            "water_makeup_per_m3": 5.0 * USD_PER_PKR,
            "water_discharge_per_m3": 0.0,         # [U] not separately billed
            "acid_per_kg": 0.19,                   # [A]
            "antiscalant_per_m3": 0.05,            # [A]
        },
        "driver": "NEQS effluent limits; Punjab Water Act 2019 abstraction "
                  "licensing. Water is largely area-billed, so its marginal "
                  "cost is near zero — the lever here is kWh and the 56 % "
                  "peak/off-peak spread",       # [C]
        "currency": ("PKR", 1.0 / USD_PER_PKR),
    },
}

# The Pakistan IT load is not an invention. A Pakistani cooling-tower EPC
# published a live project on 10 Sep 2026: induced-draught CLOSED-LOOP towers,
# 328 m3/hr per tower, three towers, nine cells, 38/31 C inlet/outlet. That is
#     Q = 984 m3/h * 1000 kg/m3 * 4.186 kJ/kgK * 7 K / 3600 s = 8.0 MW
# so the archetype is sized to a real, currently-commissioning Pakistani
# plant rather than to a round number. Closed-loop isolates the PROCESS
# fluid; the spray water still evaporates and concentrates, so the chemistry
# problem is entirely present. [C -- vendor project announcement]
PAKISTAN_REFERENCE_PLANT = {
    "source": "Fibre Craft Industries project announcement, 10 Sep 2026",
    "flow_m3_h_per_tower": 328.0, "towers": 3, "cells_per_tower": 3,
    "T_in_c": 38.0, "T_out_c": 31.0,
    "duty_kw": 328.0 * 3 * 1000.0 * 4.186 * (38.0 - 31.0) / 3600.0,
}


def diurnal_profile(spec):
    """24 hourly (T_db, rh) pairs."""
    if spec == "tmy":
        import diurnal as dn
        h = np.load(RESULTS / "tmy_hourly.npy")
        idx, _ = dn.pick_summer_day(h)
        return [(float(h[i, 3]), float(h[i, 4])) for i in idx], "real TMYx day"
    _, t_min, t_max, rh = spec
    mean, amp = 0.5 * (t_min + t_max), 0.5 * (t_max - t_min)
    out = []
    for t in range(24):
        # minimum near 05:00, maximum near 15:00
        T = mean - amp * math.cos(2 * math.pi * (t - 5) / 24.0)
        out.append((T, rh))
    return out, "sinusoidal, anchored on design conditions [A]"


def run_region(key, cfg, makeup, fill_c, fill_n):
    hours, weather_note = diurnal_profile(cfg["weather"])
    q_it = cfg["q_it_kw"]
    unit = cdu.sized_for(q_it, delta_t_k=10.0)
    cycles = cfg["cycles"]
    floor = chem.temperature_floor_for_silica(makeup, cycles)

    rows = []
    for t, (T_db, rh) in enumerate(hours):
        cmp_ = hs.compare_blind_vs_bounded(
            T_db=T_db, rh=rh, q_it_kw=q_it, makeup=makeup, cycles=cycles,
            tariffs=cfg["tariffs"], unit=unit,
            m_w_pri=q_it / 20.0,          # [A] ~5 K primary range
            m_a_rated=q_it / 22.5,        # [A] scaled from the 10 MW archetype
            fill_c=fill_c, fill_n=fill_n)
        rows.append({"hour": t, "T_db": T_db, "rh": rh, **cmp_})

    def agg(policy, field):
        vals = [r[policy][field] for r in rows if r[policy] is not None]
        return vals

    solved = [r for r in rows if r["blind"] and r["bounded"]]
    if not solved:
        return {"label": cfg["label"], "solved_hours": 0}

    b_water = sum(r["blind"]["makeup_m3_h"] for r in solved)
    c_water = sum(r["bounded"]["makeup_m3_h"] for r in solved)
    b_pow = sum(r["blind"]["P_facility_kW"] for r in solved)
    c_pow = sum(r["bounded"]["P_facility_kW"] for r in solved)
    b_cost = sum(r["blind"]["cost_per_h"] for r in solved)
    c_cost = sum(r["bounded"]["cost_per_h"] for r in solved)
    n = len(solved)
    hours_per_year = 8760.0 * n / 24.0

    # DEFECT 40. Counting a violation with a strict > against a root-found
    # boundary counts the solver's own tolerance as scaling.
    #
    # The bounded controller drives the silica index TO its limit, so it
    # lands on whichever side the root-finder stops at -- here about 1e-5 to
    # 1e-4 log units above zero. Counted strictly, that reads as 24 violating
    # hours out of 24, identical to the blind case, when the blind case is
    # exceeding by 1e-2 to 1e-1. The table said the controller was no better
    # than no controller.
    #
    # SI is a LOG scale, and that is the whole point: SI = 1e-4 is a
    # saturation ratio of 1.0002, and SI = 0.119 is 1.32, i.e. 32 % super-
    # saturated. One of those deposits solid and the other is not
    # measurable. So both counts are reported -- every hour strictly over
    # the line, AND every hour over it by more than the solver can resolve --
    # together with the saturation ratio, which is the number an operator
    # can actually check against a coupon.
    SI_SOLVER_TOL = 1e-3       # 0.23 % supersaturation; below any measurement

    def _over(r, case, tol=0.0):
        v = r[case]["violations"].get("SI_silica_am")
        return v is not None and v > tol

    blind_violating = [r for r in solved if _over(r, "blind")]
    bounded_violating = [r for r in solved if _over(r, "bounded")]
    blind_material = [r for r in solved if _over(r, "blind", SI_SOLVER_TOL)]
    bounded_material = [r for r in solved if _over(r, "bounded", SI_SOLVER_TOL)]

    cur_name, cur_rate = cfg["currency"]
    return {
        "label": cfg["label"],
        "driver": cfg["driver"],
        "weather": weather_note,
        "solved_hours": n,
        "q_it_kw": q_it,
        "cycles": cycles,
        "chemical_floor_c": floor,
        "PUE_blind": float(np.mean([r["blind"]["PUE"] for r in solved])),
        "PUE_bounded": float(np.mean([r["bounded"]["PUE"] for r in solved])),
        "WUE_blind": float(np.mean([r["blind"]["WUE_L_per_kWh"] for r in solved])),
        "WUE_bounded": float(np.mean([r["bounded"]["WUE_L_per_kWh"] for r in solved])),
        "water_blind_m3_day": b_water * 24.0 / n,
        "water_bounded_m3_day": c_water * 24.0 / n,
        "water_saved_m3_day": (b_water - c_water) * 24.0 / n,
        "water_saved_pct": 100.0 * (b_water - c_water) / b_water,
        "facility_power_delta_kW": (c_pow - b_pow) / n,
        "cost_delta_per_h_usd": (c_cost - b_cost) / n,
        "cost_delta_per_year_usd": (c_cost - b_cost) / n * hours_per_year,
        "cost_delta_per_year_local": ((c_cost - b_cost) / n * hours_per_year
                                      * cur_rate),
        "currency": cur_name,
        "hours_blind_violating_silica": len(blind_violating),
        "hours_bounded_violating_silica": len(bounded_violating),
        "si_solver_tolerance": SI_SOLVER_TOL,
        "hours_blind_materially_violating": len(blind_material),
        "hours_bounded_materially_violating": len(bounded_material),
        "max_silica_SR_blind": 10.0 ** max(r["blind"]["SI"]["SI_silica_am"]
                                           for r in solved),
        "max_silica_SR_bounded": 10.0 ** max(r["bounded"]["SI"]["SI_silica_am"]
                                             for r in solved),
        "max_SI_silica_blind": max(r["blind"]["SI"]["SI_silica_am"]
                                   for r in solved),
        "max_SI_silica_bounded": max(r["bounded"]["SI"]["SI_silica_am"]
                                     for r in solved),
        "max_SI_calcite_bounded": max(r["bounded"]["SI"]["SI_calcite"]
                                      for r in solved),
        "max_secondary_flow_ratio": max(r["bounded"]["secondary_flow_ratio"]
                                        for r in solved),
        "rows": rows,
    }


def main() -> int:
    import run_controller as rc
    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]
    makeup = rc.TSE

    print("=" * 96)
    print("MIZAN :: four-region 24-hour benchmark  --  blind free cooling "
          "vs chemically-bounded")
    print("=" * 96)
    print(f"makeup water : {makeup.name}")
    print(f"               SiO2 {makeup.SiO2:.1f} mg/L (ASSUMED, imported "
          f"from Riyadh groundwater), PO4 {makeup.PO4:.1f} mg/L (MEASURED)")
    print(f"Pakistan archetype sized on a real plant: "
          f"{PAKISTAN_REFERENCE_PLANT['duty_kw']/1000:.1f} MW "
          f"({PAKISTAN_REFERENCE_PLANT['source']})")
    print()

    out = {"makeup": makeup.name,
           "pakistan_reference_plant": PAKISTAN_REFERENCE_PLANT,
           "regions": {}}
    for key, cfg in REGIONS.items():
        print(f"  running {cfg['label']} ...", flush=True)
        out["regions"][key] = run_region(key, cfg, makeup, fc, fn)

    print()
    hdr = (f"{'region':<34}{'floor':>7}{'PUE b/c':>16}{'WUE b/c':>16}"
           f"{'water m3/d':>13}{'saved %':>9}{'max SR silica b/c':>20}"
           f"{'scaling h':>11}")
    print(hdr)
    print("-" * len(hdr))
    for key, r in out["regions"].items():
        if not r.get("solved_hours"):
            print(f"{r['label']:<34}  no feasible hours")
            continue
        print(f"{r['label']:<34}"
              f"{r['chemical_floor_c']:>6.1f}C"
              f"{r['PUE_blind']:>8.3f}/{r['PUE_bounded']:<7.3f}"
              f"{r['WUE_blind']:>8.2f}/{r['WUE_bounded']:<7.2f}"
              f"{r['water_bounded_m3_day']:>13.1f}"
              f"{r['water_saved_pct']:>9.2f}"
              f"{r['max_silica_SR_blind']:>10.3f}/"
              f"{r['max_silica_SR_bounded']:<9.3f}"
              f"{r['hours_blind_materially_violating']:>5d}/"
              f"{r['hours_bounded_materially_violating']:<5d}")
    print()
    print("  floor      = minimum facility-water temperature at which "
          "amorphous silica stays at or below saturation, at the stated cycles")
    print("  b/c        = blind free cooling / chemically bounded")
    print("  max SR     = peak amorphous-silica saturation RATIO, the number an")
    print("               operator can check against a coupon. 1.00 is saturation.")
    print("  scaling h  = hours out of 24 supersaturated by more than the solver")
    print("               can resolve (SI > 1e-3, i.e. SR > 1.002). The bounded")
    print("               controller drives the index TO its limit, so counting a")
    print("               strict SI > 0 would count the root-finder's own tolerance")
    print("               as scaling -- see defect 40.")
    print("  strict h   = "
          + ", ".join(f"{r['label'].split()[0]} "
                      f"{r['hours_blind_violating_silica']}/"
                      f"{r['hours_bounded_violating_silica']}"
                      for r in out["regions"].values() if r.get("solved_hours"))
          + "  (any SI > 0 at all, both cases, for completeness)")
    print()
    print("  NOTE: the three non-Gulf profiles are sinusoids anchored on "
          "design conditions [A], not real weather. Annual figures derived "
          "from them are indicative only.")

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "pitch_artifacts.json").write_text(json.dumps(out, indent=2,
                                                             default=float))
    print(f"\nwritten -> {RESULTS / 'pitch_artifacts.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
