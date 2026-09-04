"""Does the ECONOMIC ceiling survive when the chiller is inside its envelope?

V5b sweeps cycles at a single condition (Dhahran summer humid, fan 90 %) and
reports 'cost falls monotonically to 7 cycles'. At that condition every one of
the ten cycle counts is OUTSIDE the chiller's validity envelope, and
`_cost_at_ph` computes `cost_per_h` unconditionally -- chiller power included.
That is the defect-11 mechanism: above ~32.5 degC plr is clamped and chiller
power is UNDERSTATED, so cost is understated exactly where the condenser is hot.

This probe re-runs the same sweep at conditions where the envelope actually
holds and asks whether the economic ceiling is still 7.

RESULT, 4 September 2026. Five conditions swept:

  condition                       fan   economic   gypsum   envelope
  Dhahran summer humid (PUBLISHED) 90 %      7        8      0 of 10 rows OK
  Dhahran summer humid            100 %      7        8      0 of 10 rows OK
  Dhahran summer peak              70 %      6        7      all rows OK
  Dhahran shoulder                 50 %      6        7      all rows OK
  Gulf winter                      90 %      6        7      all rows OK

The published pair (7, 8) reproduces ONLY at the condition where the machine
cannot operate. At all three conditions V5 finds feasible, both ceilings are
one cycle lower: 6 and 7.

The gypsum wall is NOT corrupted by the chiller clamp -- chemistry feasibility
depends on skin temperature from the thermal solve, not on the chiller model.
It moves because gypsum is PROGRADE in this model: a hotter skin makes it look
safer, so the hottest condition gives the most permissive wall. The published
condition is both the hottest and the one the plant cannot run.

This also explains why the V5 controller lands on 6 cycles at every condition
and calls it "the chemistry constraint boundary": at operable conditions, 6 IS
the last chemistry-feasible cycle count.

Read-only. Writes nothing to results/.
"""
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402
import controller as ctl  # noqa: E402
import run_controller as rc  # noqa: E402

cal = json.loads((ROOT / "results/calibration.json").read_text(encoding="utf-8"))
fill_c, fill_n = cal["fill_c"], cal["fill_n"]
TSE, TARIFFS = rc.TSE, rc.TARIFFS


def sweep(name, T_db, rh, fan):
    cond = dict(rc.PLANT)
    cond.update({"T_db": T_db, "rh": rh})
    seed = ctl._thermal_solve(fan, 4.0, cond, TSE, fill_c, fill_n)
    if seed is not None:
        cond["T_wo_guess"] = seed[2]
    out = []
    for cy in range(3, 13):
        th = ctl._thermal_solve(fan, float(cy), cond, TSE, fill_c, fill_n)
        if th is None:
            continue
        best = None
        env_any = False
        for ph in np.arange(7.0, 9.01, 0.25):
            r = ctl._cost_at_ph(th, fan, float(cy), float(ph), cond, TSE,
                                TARIFFS, 8.0)
            env_any = env_any or bool(r["chiller_envelope_ok"])
            if len(r["violations"]) == 0:
                if best is None or r["cost_per_h"] < best["cost_per_h"]:
                    best = r
        out.append({
            "cycles": cy,
            "chem_ok": best is not None,
            "env_ok": env_any,
            "cost": best["cost_per_h"] if best else float("nan"),
            "T_wo": best["T_wo"] if best else float("nan"),
            "plr": best["chiller_plr_raw"] if best else float("nan"),
        })

    feas = [r for r in out if r["chem_ok"]]
    both = [r for r in out if r["chem_ok"] and r["env_ok"]]
    print(f"\n=== {name}  (T_db {T_db} C, rh {rh}, fan {fan:.0f} %) ===")
    print("  cy  chem  env      cost/h    T_wo   plr")
    for r in out:
        print(f"  {r['cycles']:2d}  {str(r['chem_ok'])[:5]:5s} "
              f"{str(r['env_ok'])[:5]:5s} {r['cost']:9.2f} "
              f"{r['T_wo']:7.2f} {r['plr']:5.3f}")
    if feas:
        econ_all = min(feas, key=lambda r: r["cost"])["cycles"]
        print(f"  economic ceiling, chemistry-feasible only : {econ_all} cycles")
    else:
        print("  no chemistry-feasible point")
    if both:
        econ_env = min(both, key=lambda r: r["cost"])["cycles"]
        print(f"  economic ceiling, ALSO inside envelope    : {econ_env} cycles "
              f"({len(both)} of {len(feas)} feasible rows qualify)")
    else:
        print(f"  NO row is both chemistry-feasible AND inside the envelope")
    infeas = [r for r in out if not r["chem_ok"]]
    if infeas:
        print(f"  physical (gypsum) wall                    : {min(r['cycles'] for r in infeas)} cycles")


# 1. reproduce the published sweep
sweep("PUBLISHED V5b - Dhahran summer humid", 38.0, 0.55, 90.0)

# 2. same weather, fan at 100 % -- the coolest condenser the plant can make
sweep("same condition, fan 100 %", 38.0, 0.55, 100.0)

# 3. the three conditions V5 actually finds feasible
for nm, tdb, r_h, fan in [("Dhahran summer peak", 45.0, 0.20, 70.0),
                          ("Dhahran shoulder", 33.0, 0.40, 50.0),
                          ("Gulf winter", 22.0, 0.45, 90.0)]:
    sweep(f"V5-feasible: {nm}", tdb, r_h, fan)
