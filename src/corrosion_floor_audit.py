"""What does a corrosion floor cost, and where should it be set?

Customer discovery produced two facts that the optimiser did not know:

  * a plant chemist holds LSI at **0.8-1.0 deliberately**, because a thin
    calcium-carbonate film is the corrosion defence;
  * a 1992 training syllabus lists "calcium carbonate protective scale" as a
    corrosion-control METHOD, not a nuisance.

Until 4 September 2026 the optimiser searched pH 7.0-9.0 against saturation
ceilings only. Nothing stopped it driving the water aggressive to buy cycles,
which is not a conservative omission -- it is an error in the direction that
destroys the plant.

The floor is now enforced at bulk temperature (`CORROSION_FLOOR_SI`). This
sweeps it, because the RIGHT value is a plant decision and the honest thing is
to price it rather than assert one number.

Read this alongside `results/field_validation.json`: the Aramco pilot ran a
clean condenser on TSE at a reported LSI of 0 to 0.5, and this model puts that
same water at SI_calcite 0.484 at 25 C. So a floor at 0.0 is comfortably below
observed safe practice; a floor at 0.8 is above what that pilot ran.

Run:  python src/corrosion_floor_audit.py
"""
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402
import controller as ctl  # noqa: E402
import run_controller as rc  # noqa: E402

FLOORS = (None, -0.5, 0.0, 0.3, 0.5, 0.8, 1.0)


def best_at(cond, floor, fill_c, fill_n, cycles_grid=range(3, 11)):
    """Least-cost feasible point at this condition, under this floor."""
    TSE, TAR = rc.TSE, rc.TARIFFS
    best = None
    for cy in cycles_grid:
        for fan in (40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0):
            th = ctl._thermal_solve(fan, float(cy), cond, TSE, fill_c, fill_n)
            if th is None:
                continue
            for ph in np.arange(7.0, 9.01, 0.25):
                r = ctl._cost_at_ph(th, fan, float(cy), float(ph), cond, TSE,
                                    TAR, 8.0, corrosion_floor_si=floor)
                if r["violations"] or not r["chiller_envelope_ok"]:
                    continue
                if best is None or r["cost_per_h"] < best["cost_per_h"]:
                    best = r
    return best


def main():
    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    fill_c, fill_n = cal["fill_c"], cal["fill_n"]

    cond = dict(rc.PLANT)
    cond.update({"T_db": 45.0, "rh": 0.20})
    seed = ctl._thermal_solve(70.0, 4.0, cond, rc.TSE, fill_c, fill_n)
    if seed is not None:
        cond["T_wo_guess"] = seed[2]

    print("=" * 74)
    print("CORROSION FLOOR -- what protecting the film costs")
    print("=" * 74)
    print("condition: Dhahran summer peak (45 C, 20 % RH)\n")
    print(f"{'floor SI_calcite':>18}{'cycles':>9}{'fan %':>8}{'pH':>7}"
          f"{'makeup m3/h':>14}{'cost $/h':>11}")

    rows = []
    for floor in FLOORS:
        b = best_at(cond, floor, fill_c, fill_n)
        label = "none (pre-4 Sep)" if floor is None else f"{floor:+.2f}"
        if b is None:
            print(f"{label:>18}{'INFEASIBLE':>49}")
            rows.append({"floor": floor, "feasible": False})
            continue
        print(f"{label:>18}{b['cycles']:>9.0f}{b['fan_pct']:>8.0f}"
              f"{b['target_ph']:>7.2f}{b['makeup_m3_h']:>14.2f}"
              f"{b['cost_per_h']:>11.2f}")
        rows.append({"floor": floor, "feasible": True,
                     "cycles": b["cycles"], "fan_pct": b["fan_pct"],
                     "target_ph": b["target_ph"],
                     "makeup_m3_h": b["makeup_m3_h"],
                     "cost_per_h": b["cost_per_h"]})

    ok = [r for r in rows if r.get("feasible")]
    base = next((r for r in ok if r["floor"] is None), None)
    if base and ok:
        print("\n  cost of the floor, against no floor at all:")
        for r in ok:
            if r["floor"] is None:
                continue
            d = (r["cost_per_h"] - base["cost_per_h"]) / base["cost_per_h"] * 100
            dw = (r["makeup_m3_h"] - base["makeup_m3_h"]) / base["makeup_m3_h"] * 100
            print(f"    floor {r['floor']:+.2f}   cost {d:+6.2f} %   "
                  f"makeup {dw:+6.2f} %")

    out = {
        "condition": "Dhahran summer peak, 45 C, 20 % RH",
        "enforced_at": "bulk temperature (T_basin), where LSI practice sits",
        "default_in_use": ctl.CORROSION_FLOOR_SI,
        "why": ("A plant chemist holds LSI 0.8-1.0 deliberately as corrosion "
                "protection; the optimiser previously had no floor at all. The "
                "right value is a plant decision, so it is swept rather than "
                "asserted."),
        "field_anchor": ("Aramco pilot ran a CLEAN condenser on TSE at a "
                         "reported LSI of 0 to 0.5; this model puts that water "
                         "at SI_calcite 0.484 at 25 C."),
        "rows": rows,
    }
    (RESULTS / "corrosion_floor.json").write_text(json.dumps(out, indent=2),
                                                  encoding="utf-8")
    print("\nwritten -> results/corrosion_floor.json")


if __name__ == "__main__":
    main()
