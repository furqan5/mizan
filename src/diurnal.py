"""
FURQAN / MIZAN :: 24-hour diurnal supervisory run, on a real Gulf summer day.

WHY A DIURNAL RUN AT ALL, AND WHAT IT IS ALLOWED TO CLAIM.

The pre-registered V5 gate is an unweighted mean over five named design
conditions. It scored a 4.38 % makeup-water reduction against a 15 % threshold
and FAILED. Nothing in this file revises that. This is a different experiment:
one real day, hour by hour, with the cycle target free to move between hours
instead of being pinned for the whole day.

The idea under test is that a fixed conductivity setpoint -- which is what
every incumbent controller holds -- is leaving margin on the table at night,
because the saturation limit it is protecting against is a function of
temperature and temperature moves 15 K over a Gulf day.

THE THING THAT MAKES THIS NON-OBVIOUS, AND WHICH THE MODEL DECIDES RATHER
THAN THE AUTHOR.

Mineral solubilities do not share a sign.

    calcite, calcium phosphate   RETROGRADE -- least soluble HOT
                                 -> bind at the condenser tube skin
                                 -> margin LOOSENS as the day cools
    amorphous silica             PROGRADE  -- least soluble COLD
                                 -> binds at the tower basin
                                 -> margin TIGHTENS as the day cools

So the naive expectation -- "float cycles up at night" -- is only correct
while a retrograde mineral binds. On this water the binding mineral is
amorphous silica, which is prograde, so the night is the WORSE time and
floating up may buy nothing at all. That is not asserted here. Both boundaries
are tracked every hour and whichever binds, binds. The result is reported
whichever way it comes out.

Run:  python src/diurnal.py
Writes: results/diurnal_gulf.json
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import chemistry as chem            # noqa: E402
import controller as ctl            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# Load model, identical to src/annual.py so the two are comparable.
# [A -- a load model, not a measurement]
T_LO, T_HI = 18.0, 46.0

# Search grids. Coarser than the V5 gate's, because this runs 24 conditions
# rather than five and the thermal solve dominates. Declared here rather than
# buried, because a coarser grid can only ever make the optimiser look WORSE
# -- it cannot manufacture a saving.
FAN_GRID = np.arange(30.0, 100.1, 5.0)
CYCLES_GRID = np.arange(2.0, 8.01, 0.5)
PH_GRID = np.arange(7.0, 9.01, 0.25)

BASELINE_CYCLES = 4.0        # incumbent fixed conductivity setpoint
BASELINE_PH = 7.8
BASELINE_CW_SETPOINT = 29.0


def load_fraction(T_db):
    return float(np.clip(0.55 + 0.45 * (T_db - T_LO) / (T_HI - T_LO),
                         0.35, 1.0))


def pick_summer_day(h):
    """The 24 hours of the real day with the highest mean wet-bulb.

    Chosen on the daily MEAN rather than the peak hour, because a single
    extreme hour would give a day that is unrepresentative either side of it
    and the whole point here is the swing between night and afternoon.
    """
    month, day, T_db, T_wb = h[:, 0], h[:, 1], h[:, 3], h[:, 5]
    key = month * 100 + day
    best, best_mean = None, -1e9
    for k in np.unique(key):
        idx = np.flatnonzero(key == k)
        if idx.size != 24:
            continue
        m = float(T_wb[idx].mean())
        if m > best_mean:
            best, best_mean = idx, m
    return best, best_mean


def condition_for_hour(T_db, T_wb, rh, plant, makeup, fill_c, fill_n):
    """Same construction as gate V5, so the two are directly comparable.

    `T_wi` is the condenser-water return temperature the tower has to cool.
    V5 sets it 12 K above the wet bulb; the same convention is kept here so a
    diurnal number can be read against a gate number without an adjustment
    nobody would remember to apply.
    """
    cond = dict(plant)
    cond.update({"T_db": float(T_db), "rh": float(rh),
                 "T_wi": float(T_wb) + 12.0})
    cond["Q_evap_kw"] = plant["Q_evap_kw"] * load_fraction(T_db)
    seed = ctl._thermal_solve(70.0, 4.0, cond, makeup, fill_c, fill_n)
    if seed is not None:
        cond["T_wo_guess"] = seed[2]
    return cond


def run(makeup, tariffs, plant, fill_c, fill_n, hours, programme=None,
        lambda_water=ctl.LAMBDA_WATER_DEFAULT, skin_delta_k=8.0,
        max_energy_penalty_pct=0.05):
    """One 24-hour run of the baseline and all three objectives."""
    limits = chem.limits_for_programme(programme)
    rows = []
    for t, (T_db, T_wb, rh) in enumerate(hours):
        cond = condition_for_hour(T_db, T_wb, rh, plant,
                                  makeup, fill_c, fill_n)

        base = ctl.baseline(cond, makeup, tariffs, fill_c, fill_n,
                            fixed_cycles=BASELINE_CYCLES,
                            fixed_ph=BASELINE_PH,
                            cw_setpoint_c=BASELINE_CW_SETPOINT,
                            skin_delta_k=skin_delta_k,
                            saturation_limits=limits)
        if base is None:
            rows.append({"hour": t, "T_db": float(T_db), "T_wb": float(T_wb),
                         "solved": False})
            continue

        modes = {}
        for mode in ctl.OPTIMIZATION_MODES:
            kw = {}
            if mode == "CONSTRAINED_WATER":
                kw = {"max_energy_penalty_pct": max_energy_penalty_pct,
                      "p_baseline_kw": base["P_total_kW"]}
            best, _ = ctl.optimise(
                cond, makeup, tariffs, fill_c, fill_n,
                fan_grid=FAN_GRID, cycles_grid=CYCLES_GRID, ph_grid=PH_GRID,
                skin_delta_k=skin_delta_k, optimization_mode=mode,
                lambda_water=lambda_water, saturation_limits=limits, **kw)
            modes[mode] = best

        # The floating ceiling at this hour's OWN two boundaries, with pH
        # left to atmospheric CO2 equilibrium -- i.e. what the water would
        # tolerate with NO ACID DOSED. It is deliberately a different
        # quantity from the cycles the controller actually selects, which are
        # higher because the controller buys margin with acid. Reported
        # because the gap between them IS the acid lever, priced.
        wp = modes["WATER_PRESERVING"] or modes["COST_MINIMIZING"]
        ceiling, binding = float("nan"), None
        if wp is not None:
            ceiling = chem.max_cycles_split(
                makeup, wp["T_skin"], wp["T_basin"], limits=limits,
                lo=1.0, hi=12.0)
            binding = chem.binding_mineral_split(
                makeup, ceiling, wp["T_skin"], wp["T_basin"], limits=limits)

        row = {
            "hour": t, "solved": True,
            "T_db": float(T_db), "T_wb": float(T_wb), "rh": float(rh),
            "load": load_fraction(T_db),
            "Q_evap_kw": cond["Q_evap_kw"],
            "base_cycles": base["cycles"], "base_fan_pct": base["fan_pct"],
            "base_T_wo": base["T_wo"], "base_T_skin": base["T_skin"],
            "base_makeup_m3_h": base["makeup_m3_h"],
            "base_P_total_kW": base["P_total_kW"],
            "base_cost_per_h": base["cost_per_h"],
            "base_m_evap_kg_s": base["m_evap_kg_s"],
            "uncontrolled_ceiling_cycles": ceiling,
            "uncontrolled_ceiling_binding": binding,
        }
        for mode, r in modes.items():
            tag = {"COST_MINIMIZING": "cost", "WATER_PRESERVING": "water",
                   "CONSTRAINED_WATER": "cwater"}[mode]
            if r is None:
                row[f"{tag}_solved"] = False
                continue
            row.update({
                f"{tag}_solved": True,
                f"{tag}_cycles": r["cycles"], f"{tag}_fan_pct": r["fan_pct"],
                f"{tag}_ph": r["target_ph"],
                f"{tag}_T_wo": r["T_wo"], f"{tag}_T_skin": r["T_skin"],
                f"{tag}_T_basin": r["T_basin"],
                f"{tag}_makeup_m3_h": r["makeup_m3_h"],
                f"{tag}_blowdown_m3_h": r["blowdown_m3_h"],
                f"{tag}_P_total_kW": r["P_total_kW"],
                f"{tag}_P_fan_kW": r["P_fan_kW"],
                f"{tag}_cost_per_h": r["cost_per_h"],
                f"{tag}_m_evap_kg_s": r["m_evap_kg_s"],
                f"{tag}_SI_calcite": r["SI_calcite"],
                f"{tag}_SI_silica_am": r["SI_silica_am"],
                f"{tag}_SI_tcp": chem.saturation_state(
                    makeup.concentrate(r["cycles"]), r["T_skin"],
                    pH=r["target_ph"])["SI_tcp"],
            })
        rows.append(row)
    return rows


def totals(rows, tag):
    """Ratios of daily totals -- what a plant actually banks over the day."""
    ok = [r for r in rows if r.get("solved") and r.get(f"{tag}_solved")]
    if not ok:
        return None
    b_w = sum(r["base_makeup_m3_h"] for r in ok)
    o_w = sum(r[f"{tag}_makeup_m3_h"] for r in ok)
    b_p = sum(r["base_P_total_kW"] for r in ok)
    o_p = sum(r[f"{tag}_P_total_kW"] for r in ok)
    b_c = sum(r["base_cost_per_h"] for r in ok)
    o_c = sum(r[f"{tag}_cost_per_h"] for r in ok)
    return {
        "hours_solved": len(ok),
        "water_pct": 100.0 * (b_w - o_w) / b_w,
        "energy_pct": 100.0 * (b_p - o_p) / b_p,
        "cost_pct": 100.0 * (b_c - o_c) / b_c,
        "base_makeup_m3_day": b_w, "opt_makeup_m3_day": o_w,
        "makeup_saved_m3_day": b_w - o_w,
        "base_kWh_day": b_p, "opt_kWh_day": o_p,
        "base_cost_day": b_c, "opt_cost_day": o_c,
        "mean_cycles": float(np.mean([r[f"{tag}_cycles"] for r in ok])),
        "min_cycles": float(np.min([r[f"{tag}_cycles"] for r in ok])),
        "max_cycles": float(np.max([r[f"{tag}_cycles"] for r in ok])),
        "max_SI_calcite": float(np.max([r[f"{tag}_SI_calcite"] for r in ok])),
        "max_SI_silica_am": float(np.max([r[f"{tag}_SI_silica_am"] for r in ok])),
        "max_SI_tcp": float(np.max([r[f"{tag}_SI_tcp"] for r in ok])),
    }


def night_day_split(rows, tag):
    """Does the cycle target actually float UP at night? The question the
    whole diurnal idea rests on, answered rather than assumed."""
    ok = [r for r in rows if r.get("solved") and r.get(f"{tag}_solved")]
    night = [r for r in ok if r["hour"] < 6 or r["hour"] >= 21]
    day = [r for r in ok if 11 <= r["hour"] < 17]
    if not night or not day:
        return None
    return {
        "night_hours": len(night), "day_hours": len(day),
        "night_mean_cycles": float(np.mean([r[f"{tag}_cycles"] for r in night])),
        "day_mean_cycles": float(np.mean([r[f"{tag}_cycles"] for r in day])),
        "night_mean_T_skin": float(np.mean([r[f"{tag}_T_skin"] for r in night])),
        "day_mean_T_skin": float(np.mean([r[f"{tag}_T_skin"] for r in day])),
        "night_mean_T_basin": float(np.mean([r[f"{tag}_T_basin"] for r in night])),
        "day_mean_T_basin": float(np.mean([r[f"{tag}_T_basin"] for r in day])),
        "night_mean_ceiling": float(np.nanmean([r["uncontrolled_ceiling_cycles"] for r in night])),
        "day_mean_ceiling": float(np.nanmean([r["uncontrolled_ceiling_cycles"] for r in day])),
        "night_binding": sorted({r["uncontrolled_ceiling_binding"] for r in night
                                 if r["uncontrolled_ceiling_binding"]}),
        "day_binding": sorted({r["uncontrolled_ceiling_binding"] for r in day
                               if r["uncontrolled_ceiling_binding"]}),
    }


def main() -> int:
    import run_controller as rc

    hp = RESULTS / "tmy_hourly.npy"
    if not hp.exists():
        print("results/tmy_hourly.npy missing. Run src/tmy.py first.")
        return 1
    h = np.load(hp)
    idx, wb_mean = pick_summer_day(h)
    month, day = int(h[idx[0], 0]), int(h[idx[0], 1])
    hours = [(h[i, 3], h[i, 5], h[i, 4]) for i in idx]

    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]

    print("=" * 78)
    print("MIZAN :: 24-hour diurnal supervisory run")
    print("=" * 78)
    print(f"day selected  : {day:02d}/{month:02d}, the Dhahran TMYx day of "
          f"highest mean wet-bulb ({wb_mean:.2f} C)")
    print(f"wet-bulb range: {min(x[1] for x in hours):.1f} to "
          f"{max(x[1] for x in hours):.1f} C")
    print(f"dry-bulb range: {min(x[0] for x in hours):.1f} to "
          f"{max(x[0] for x in hours):.1f} C")
    print(f"baseline      : fixed {BASELINE_CYCLES:g} cycles, pH "
          f"{BASELINE_PH}, condenser-water setpoint {BASELINE_CW_SETPOINT} C")
    print(f"lambda_water  : {ctl.LAMBDA_WATER_DEFAULT} (WATER_PRESERVING)")
    print()

    out = {"day": f"{day:02d}/{month:02d}", "wb_mean_c": wb_mean,
           "baseline": {"cycles": BASELINE_CYCLES, "ph": BASELINE_PH,
                        "cw_setpoint_c": BASELINE_CW_SETPOINT},
           "lambda_water": ctl.LAMBDA_WATER_DEFAULT,
           "grids": {"fan": list(FAN_GRID), "cycles": list(CYCLES_GRID),
                     "ph": list(PH_GRID)},
           "programmes": {}}

    for programme in (None, "stressed"):
        label = programme or "undeclared"
        print("-" * 78)
        print(f"phosphate programme: {label}"
              + (f"  (SI_tcp <= {chem.PHOSPHATE_PROGRAMME[programme]})"
                 if programme else "  (phosphate screened, binds nothing)"))
        print("-" * 78)
        rows = run(rc.TSE, rc.TARIFFS, rc.PLANT, fc, fn, hours,
                   programme=programme)
        entry = {"rows": rows, "totals": {}, "night_day": {}}
        for tag, mode in (("cost", "COST_MINIMIZING"),
                          ("water", "WATER_PRESERVING"),
                          ("cwater", "CONSTRAINED_WATER")):
            t = totals(rows, tag)
            entry["totals"][mode] = t
            entry["night_day"][mode] = night_day_split(rows, tag)
            if t is None:
                print(f"  {mode:18s} no feasible hours")
                continue
            print(f"  {mode:18s} water {t['water_pct']:+6.2f} %   "
                  f"energy {t['energy_pct']:+6.2f} %   "
                  f"cost {t['cost_pct']:+6.2f} %   "
                  f"cycles {t['min_cycles']:.1f}-{t['max_cycles']:.1f} "
                  f"(mean {t['mean_cycles']:.2f})   "
                  f"{t['hours_solved']}/24 h")
        nd = entry["night_day"].get("WATER_PRESERVING")
        if nd:
            print(f"    night vs day (WATER_PRESERVING): cycles "
                  f"{nd['night_mean_cycles']:.2f} vs {nd['day_mean_cycles']:.2f}"
                  f"   ceiling {nd['night_mean_ceiling']:.2f} vs "
                  f"{nd['day_mean_ceiling']:.2f}"
                  f"   binding night={nd['night_binding']} day={nd['day_binding']}")
        out["programmes"][label] = entry
        print()

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "diurnal_gulf.json").write_text(json.dumps(out, indent=2))
    print(f"written -> {RESULTS / 'diurnal_gulf.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
