"""
MIZAN :: how much of the gypsum wall is the skin-temperature assumption?
=======================================================================
Every chemistry gate in this package -- V3, V5, V5b, V6 -- runs with the
wall-to-bulk temperature rise fixed at 8.0 K. That number is a hardcoded
literal in `controller.py` (the `skin_delta_k=8.0` default) and in the
`_cost_at_ph(..., 8.0)` call inside gate V5b. It is never computed.

`chemistry.wall_bulk_delta_t` exists to compute it from duty and geometry
by q''/h_i with a Dittus-Boelter film coefficient, and its own docstring
records that external review narrowed the credible condenser heat flux to
20-30 kW/m2, which at 2 m/s gives a CLEAN-surface rise of 2.4-3.7 K. Values
near 8 K correspond to a FOULED surface or to velocities near the TEMA
minimum. That function is defined and never called.

So the package reports a fouled-surface skin temperature as though it were
the typical case, while the report and deck both state that the offset is
"computed, not assumed". Both halves of that need fixing, and the size of
the error needs to be on the record before either is claimed.

This sweeps the skin rise across the clean-to-fouled band and reports where
the physical ceiling actually lands. It changes no gate. The V5b result
stands as scored, at 8 K; this measures how much of it is the assumption.

Run:  python src/skin_sensitivity.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem                                        # noqa: E402
import controller as ctl                                        # noqa: E402
import run_controller as rc                                     # noqa: E402

# Clean-surface band from the corrected heat-flux range, the value the
# documents quote as "typical", and the value every gate actually used.
SKIN_CASES = [
    (2.4, "clean, 20 kW/m2 at 2 m/s"),
    (3.0, "clean, mid-range"),
    (3.7, "clean, 30 kW/m2 at 2 m/s"),
    (5.0, "lightly fouled"),
    (8.0, "FOULED -- the value every gate in this package used"),
]


def wall_for(skin_dt, fill_c, fill_n, fan=90.0, T_db=38.0, rh=0.55):
    """First cycles count at which no pH in the grid is feasible."""
    cond = dict(rc.PLANT)
    cond.update({"T_db": T_db, "rh": rh})
    seed = ctl._thermal_solve(fan, 4.0, cond, rc.TSE, fill_c, fill_n)
    if seed is not None:
        cond["T_wo_guess"] = seed[2]

    last_ok, wall, mineral, cost_at_last = None, None, "", float("nan")
    for cy in range(3, 16):
        th = ctl._thermal_solve(fan, float(cy), cond, rc.TSE, fill_c, fill_n)
        if th is None:
            continue
        best, blocking = None, None
        for ph in np.arange(7.0, 9.01, 0.25):
            r = ctl._cost_at_ph(th, fan, float(cy), float(ph), cond, rc.TSE,
                                rc.TARIFFS, skin_dt)
            if r["feasible"]:
                if best is None or r["cost_per_h"] < best["cost_per_h"]:
                    best = r
            elif blocking is None:
                blocking = sorted(r["violations"])
        if best is not None:
            last_ok, cost_at_last = cy, best["cost_per_h"]
        elif wall is None:
            wall, mineral = cy, ",".join(blocking or [])
            break
    return last_ok, wall, mineral, cost_at_last


def water_saving_from_cycles(c, base=4.0):
    """Makeup saving against the incumbent baseline available from cycles
    alone: makeup = evaporation * C/(C-1), so this is fixed arithmetic."""
    return 100.0 * (1.0 - (c / (c - 1.0)) / (base / (base - 1.0)))


def main() -> int:
    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]

    # What the film calculation actually says, for the record.
    print("=" * 78)
    print("SKIN-TEMPERATURE SENSITIVITY  --  how much of the wall is the assumption?")
    print("=" * 78)
    print()
    print("Computed wall-to-bulk rise, q''/h_i, Dittus-Boelter at 2.0 m/s:")
    for q in (20_000.0, 25_000.0, 30_000.0):
        dt, h = chem.wall_bulk_delta_t(q, velocity_m_s=2.0)
        print(f"   q'' = {q/1000:4.0f} kW/m2   h_i = {h:6.0f} W/m2K   "
              f"dT = {dt:4.2f} K")
    print()
    print("Every chemistry gate in this package used dT = 8.00 K, hardcoded.")
    print()

    print(f"{'skin dT':>8s}  {'case':<44s} {'last OK':>8s} {'wall':>6s} "
          f"{'binding':>12s} {'water % at last OK':>19s}")
    print("-" * 106)

    rows = []
    for dt, label in SKIN_CASES:
        last_ok, wall, mineral, cost = wall_for(dt, fc, fn)
        wsav = water_saving_from_cycles(last_ok) if last_ok else float("nan")
        rows.append({"skin_delta_k": dt, "case": label, "last_feasible": last_ok,
                     "wall_cycles": wall, "binding_mineral": mineral,
                     "water_pct_from_cycles_at_last_feasible": wsav,
                     "cost_per_h_at_last_feasible": cost})
        print(f"{dt:8.2f}  {label:<44s} {str(last_ok):>8s} {str(wall):>6s} "
              f"{mineral:>12s} {wsav:18.2f} %")

    print()
    print("WHAT THIS MEANS, STATED PLAINLY")
    print()
    base = next(r for r in rows if r["skin_delta_k"] == 8.0)
    clean = next(r for r in rows if r["skin_delta_k"] == 3.0)
    print(f"   At the fouled 8.0 K the package reports, the wall is at "
          f"{base['wall_cycles']} cycles and the")
    print(f"   best feasible point is {base['last_feasible']} cycles, worth "
          f"{base['water_pct_from_cycles_at_last_feasible']:.2f} % on cycles alone.")
    print()
    print(f"   At a clean-surface 3.0 K, the wall moves to "
          f"{clean['wall_cycles']} cycles and the best feasible")
    print(f"   point is {clean['last_feasible']} cycles, worth "
          f"{clean['water_pct_from_cycles_at_last_feasible']:.2f} % on cycles alone.")
    print()
    need = 8.5
    print(f"   The pre-registered 15 % water criterion needs {need} cycles.")
    for r in rows:
        if r["last_feasible"] is None:
            continue
        verdict = ("REACHABLE" if r["last_feasible"] >= need else "unreachable")
        print(f"      dT = {r['skin_delta_k']:.1f} K -> last feasible "
              f"{r['last_feasible']} cycles -> 15 % is {verdict}")
    print()
    print("   MECHANISM, because the direction is counter-intuitive.")
    print()
    print("   Gypsum's solubility product is very nearly temperature-independent:")
    print("   log_K moves only from -4.5800 at 25 C to -4.5873 at 55 C. Almost the")
    print("   whole temperature effect therefore runs through the Debye-Huckel A")
    print("   parameter, which RISES with temperature and suppresses the activity")
    print("   coefficients of the 2:2 Ca/SO4 pair harder. So the ion activity")
    print("   product falls as the evaluation point gets hotter:")
    print()
    conc = rc.TSE.concentrate(7.0)
    print(f"      {'T_C':>5s} {'SI_gypsum':>10s} {'D-H A':>8s}   (limit "
          f"{chem.OPERATING_LIMITS['SI_gypsum']})")
    for T in (36, 40, 44, 48, 50):
        st = chem.saturation_state(conc, T, pH=8.0)
        flag = "VIOLATION" if st["SI_gypsum"] > chem.OPERATING_LIMITS["SI_gypsum"] else "ok"
        print(f"      {T:5.0f} {st['SI_gypsum']:10.4f} "
              f"{chem.debye_huckel_A(T):8.4f}   {flag}")
    print()
    print("   A HOTTER assumed skin therefore makes gypsum look SAFER. The 8 K")
    print("   value is NOT conservative for the mineral that actually binds here:")
    print("   it buys about one extra cycle of apparent headroom over the clean-")
    print("   surface value the film calculation gives.")
    print()
    print("   TWO CONSEQUENCES, and the second is the serious one.")
    print()
    print("   1. The 'threshold written beyond a physical wall' diagnosis SURVIVES")
    print("      and gets stronger. 15 % needs 8.5 cycles; at a clean skin the wall")
    print("      is at 7, not 8, so the criterion is further out of reach, not")
    print("      closer. V5 stays failed and is not rescored.")
    print()
    print("   2. The V5 optimum operates at 7 cycles, and 7 cycles is feasible")
    print("      ONLY at the fouled 8 K. At the clean-surface 2.4-3.7 K that this")
    print("      package's own film calculation produces, 7 cycles is a gypsum")
    print("      violation. The reported '0 saturation violations' is therefore")
    print("      conditional on a fouled condenser, and that condition is not")
    print("      currently stated anywhere in the documents.")
    print()
    print("   The fix is not to change the number. It is to (a) call")
    print("   wall_bulk_delta_t instead of hardcoding 8.0, (b) report the gate at")
    print("   a stated skin condition, and (c) stop writing that the offset is")
    print("   'computed' while a literal 8.0 sits in the call.")

    out = {"skin_cases": rows,
           "hardcoded_value_used_by_all_gates": 8.0,
           "computed_clean_band_K": [2.4, 3.7],
           "direction": ("A hotter assumed skin makes gypsum look SAFER, because "
                         "its log_K is nearly temperature-independent and the "
                         "Debye-Huckel A parameter rises with temperature, "
                         "suppressing the 2:2 Ca/SO4 activity coefficients. The "
                         "8 K value is therefore NOT conservative for the binding "
                         "mineral; it buys about one extra cycle of apparent "
                         "headroom."),
           "consequence": ("The V5 optimum operates at 7 cycles, which is feasible "
                           "only at 8 K. At the clean-surface 2.4-3.7 K this "
                           "package's own film calculation gives, 7 cycles is a "
                           "gypsum violation. The reported zero saturation "
                           "violations is conditional on a fouled condenser."),
           "note": ("Sensitivity only. No gate is rescored. V5 was scored at "
                    "8.0 K and remains failed at 14.83 % against 15 %. The "
                    "mis-specified-threshold diagnosis survives and strengthens: "
                    "at a clean skin the wall is at 7 cycles, so the 15 % "
                    "criterion is further out of reach, not closer.")}
    (RESULTS / "skin_sensitivity.json").write_text(json.dumps(out, indent=1))
    print()
    print("written -> results/skin_sensitivity.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
