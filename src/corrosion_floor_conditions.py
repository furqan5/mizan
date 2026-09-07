"""Does the corrosion floor bind ANYWHERE, or only at Dhahran summer peak?

`src/corrosion_floor_audit.py` sweeps the floor at ONE condition and finds the
optimum completely insensitive to it: identical cycles, fan, pH, makeup and
cost from -0.5 all the way to +1.0. That is a strong result -- it says the EPRI
corrosion objection does not change the answer -- but a one-condition sweep is
thin evidence for a claim that broad, and `docs/robustness_gaps.md` is the file
that exists to say so.

This runs the same sweep at ALL FIVE conditions the V5 gate scores.

WHY IT MATTERS. The floor is enforced at bulk temperature, where LSI practice
sits. The optimum lands at pH 8.00-8.25, which puts SI_calcite well above 1.0,
so the floor should be slack everywhere. But the conditions differ in how much
fan headroom the chiller envelope leaves, and in Gulf summer the binding limit
on fan speed is the CHILLER, not chemistry -- so it is not obvious a priori
that the floor stays slack when the optimiser is already cornered.

PRE-REGISTERED, written before the first run:

  C1  The floor does not bind at any of the five conditions: for each
      condition, cycles / fan / pH / cost are identical across every floor
      from -0.5 to +1.0.

  C2  If C1 fails anywhere, the condition where it fails is one where the
      chiller envelope is already binding -- i.e. a Gulf summer condition,
      not the winter one.

C1 failing is a FINDING, not an error: it would mean the corrosion floor has a
price, and that price belongs in the commercial documents.

Run:  python src/corrosion_floor_conditions.py
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import controller as ctl                                        # noqa: E402
import corrosion_floor_audit as cfa                             # noqa: E402
import psychro as ps                                            # noqa: E402
import run_controller as rc                                     # noqa: E402

FLOORS = cfa.FLOORS          # same ladder, so the two artefacts are comparable
KEYS = ("cycles", "fan_pct", "target_ph", "makeup_m3_h", "cost_per_h")


def main() -> int:
    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    fill_c, fill_n = cal["fill_c"], cal["fill_n"]

    print("=" * 78)
    print("CORROSION FLOOR ACROSS ALL FIVE V5 CONDITIONS")
    print("=" * 78)
    print("Pre-registered C1/C2 are in this file's docstring.\n")

    out = {"floors": [f for f in FLOORS],
           "enforced_at": "bulk temperature (T_basin), where LSI practice sits",
           "default_in_use": ctl.CORROSION_FLOOR_SI,
           "status": ("Extends results/corrosion_floor.json from one condition "
                      "to five. Not a pre-registered GATE; C1/C2 are "
                      "predictions and are scored honestly."),
           "conditions": []}

    for name, T_db, rh_pct in rc.AMBIENTS:
        rh = rh_pct / 100.0
        T_wb = float(ps.wetbulb_from_rh(T_db, rh))
        cond = dict(rc.PLANT)
        cond.update({"T_db": T_db, "rh": rh, "T_wi": T_wb + 12.0})
        seed = ctl._thermal_solve(70.0, 4.0, cond, rc.TSE, fill_c, fill_n)
        if seed is not None:
            cond["T_wo_guess"] = seed[2]

        print(f"{name}  ({T_db:.0f} C, {rh_pct:.0f} % RH, wb {T_wb:.1f} C)")
        print(f"  {'floor':>10}{'cycles':>9}{'fan %':>8}{'pH':>7}"
              f"{'makeup':>11}{'cost $/h':>11}")

        rows = []
        for floor in FLOORS:
            b = cfa.best_at(cond, floor, fill_c, fill_n)
            label = "none" if floor is None else f"{floor:+.2f}"
            if b is None:
                print(f"  {label:>10}{'INFEASIBLE':>46}")
                rows.append({"floor": floor, "feasible": False})
                continue
            print(f"  {label:>10}{b['cycles']:>9.0f}{b['fan_pct']:>8.0f}"
                  f"{b['target_ph']:>7.2f}{b['makeup_m3_h']:>11.2f}"
                  f"{b['cost_per_h']:>11.2f}")
            rows.append({"floor": floor, "feasible": True,
                         **{k: float(b[k]) for k in KEYS}})

        ok = [r for r in rows if r.get("feasible")]
        binds = False
        if len(ok) > 1:
            ref = ok[0]
            for r in ok[1:]:
                if any(abs(r[k] - ref[k]) > 1e-6 for k in KEYS):
                    binds = True
                    break
        n_infeasible = sum(1 for r in rows if not r.get("feasible"))
        print(f"  -> floor {'BINDS' if binds else 'is slack'} here"
              f"{f' ({n_infeasible} infeasible)' if n_infeasible else ''}\n")

        out["conditions"].append({"condition": name, "T_db": T_db,
                                  "RH_pct": rh_pct, "T_wb": T_wb,
                                  "floor_binds": binds,
                                  "n_infeasible": n_infeasible,
                                  "rows": rows})

    binding = [c["condition"] for c in out["conditions"] if c["floor_binds"]]
    print("=" * 78)
    print("PRE-REGISTERED PREDICTIONS, SCORED")
    print("=" * 78)
    c1 = not binding
    print(f"  {'HELD' if c1 else 'FAILED':>6}  C1 the floor does not bind at "
          f"any of the five conditions")
    print(f"          {'no condition is floor-sensitive' if c1 else binding}")
    if not c1:
        summer = [b for b in binding if "winter" not in b.lower()]
        c2 = len(summer) == len(binding)
        print(f"  {'HELD' if c2 else 'FAILED':>6}  C2 binding conditions are "
              f"summer ones, where the chiller envelope already binds")
        out["C2_binding_are_summer"] = bool(c2)
    out["C1_floor_never_binds"] = bool(c1)
    out["binding_conditions"] = binding
    print()
    print("A failed prediction is a finding. If the floor binds, it has a "
          "price\nand that price belongs in commercialisation.md.")

    (RESULTS / "corrosion_floor_conditions.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print("\nwritten -> results/corrosion_floor_conditions.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
