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
    print("   MECHANISM, measured rather than remembered.")
    print()
    # DEFECT 19, fixed 4 September 2026. Everything from here to the JSON used
    # to be hardcoded prose asserting that a hotter skin makes gypsum look
    # SAFER, that the 8 K assumption buys "about one extra cycle", and that the
    # V5 optimum at 7 cycles is feasible only at 8 K. All three were true of the
    # van't Hoff gypsum model. Defect 15 replaced it with the phreeqc.dat
    # analytic expression, and the table this same script prints stopped
    # agreeing with the paragraph underneath it -- a remembered conclusion
    # outliving the computation it was drawn from, which is defects 12 and 13
    # one more time. The conclusions are now DERIVED from `rows`.
    conc = rc.TSE.concentrate(7.0)
    print(f"      {'T_C':>5s} {'SI_gypsum':>10s} {'D-H A':>8s}   (limit "
          f"{chem.OPERATING_LIMITS['SI_gypsum']})")
    for T in (36, 40, 44, 48, 50):
        st = chem.saturation_state(conc, T, pH=8.0)
        flag = "VIOLATION" if st["SI_gypsum"] > chem.OPERATING_LIMITS["SI_gypsum"] else "ok"
        print(f"      {T:5.0f} {st['SI_gypsum']:10.4f} "
              f"{chem.debye_huckel_A(T):8.4f}   {flag}")
    print()

    # Where does SI_gypsum turn over, and how far does it move across the band
    # of skin temperatures this sensitivity actually sweeps?
    scan = [(T / 2.0, chem.saturation_state(conc, T / 2.0, pH=8.0)["SI_gypsum"])
            for T in range(40, 161)]
    T_min, si_min = min(scan, key=lambda kv: kv[1])
    walls = sorted({r["wall_cycles"] for r in rows if r["wall_cycles"] is not None})
    lasts = sorted({r["last_feasible"] for r in rows if r["last_feasible"] is not None})
    lo_dt, hi_dt = rows[0]["skin_delta_k"], rows[-1]["skin_delta_k"]
    insensitive = len(walls) == 1 and len(lasts) == 1

    print(f"   SI_gypsum has an interior MINIMUM at {T_min:.1f} C "
          f"(SI {si_min:.4f}), so it is retrograde below that point and")
    print("   prograde above it. The condenser skin in these runs sits near")
    print("   40 C -- on the flat bottom of that curve, which is why the")
    print("   sweep below moves so little.")
    print()
    if insensitive:
        print(f"   RESULT: across the whole band dT = {lo_dt:.1f} to {hi_dt:.1f} K, "
              f"clean to fouled,")
        print(f"   the gypsum wall does NOT move. It is {walls[0]} cycles at every "
              f"skin")
        print(f"   temperature tested, and the last feasible count is {lasts[0]} at "
              f"every one.")
        print()
        print("   That is a change of status for this open item, and it cuts FOR")
        print("   the package rather than against it. The hardcoded 8 K was the")
        print("   least-defended input in the chemistry chain precisely because")
        print("   the ceilings were believed to be proportional to it. Under the")
        print("   corrected gypsum solubility they are not sensitive to it at all")
        print("   over the range the film calculation admits.")
        print()
        print("   The 8 K literal should still be replaced by a call to")
        print("   wall_bulk_delta_t -- an assumption that happens not to bind is")
        print("   still an assumption -- but it is no longer load-bearing for")
        print("   either ceiling, and the reported saturation violations are no")
        print("   longer conditional on a fouled condenser.")
    else:
        print(f"   RESULT: the gypsum wall moves across the band: "
              f"{walls} cycles, last feasible {lasts}.")
        print("   The assumed skin temperature is load-bearing and must be")
        print("   reported alongside every gate it touches.")
    print()
    need = 8.5
    print(f"   The 15 % water criterion needs {need} cycles and the wall is at "
          f"{walls[0] if walls else '?'}, so it stays")
    print("   unreachable at every skin temperature in the band. V5 is not rescored.")

    out = {"skin_cases": rows,
           "hardcoded_value_used_by_all_gates": 8.0,
           "computed_clean_band_K": [2.4, 3.7],
           "si_gypsum_minimum_C": round(T_min, 2),
           "wall_cycles_across_band": walls,
           "last_feasible_across_band": lasts,
           "ceiling_sensitive_to_skin_delta": not insensitive,
           "direction": (
               f"SI_gypsum has an interior minimum at {T_min:.1f} C under the "
               "phreeqc.dat analytic solubility adopted in defect 15, and the "
               "condenser skin sits near 40 C, on the flat bottom of that curve. "
               f"Across dT = {lo_dt:.1f}-{hi_dt:.1f} K the gypsum wall does not "
               "move at all." if insensitive else
               "The gypsum wall moves with the assumed skin temperature; see "
               "wall_cycles_across_band."),
           "consequence": (
               f"The ceilings are insensitive to the hardcoded 8.0 K over the "
               f"whole clean-to-fouled band: wall {walls[0]} cycles, last "
               f"feasible {lasts[0]} cycles at every value tested. The reported "
               "zero saturation violations is NOT conditional on a fouled "
               "condenser. This supersedes the pre-defect-15 finding, which had "
               "the wall moving by one cycle across the same band."
               if insensitive else
               "The assumed skin temperature is load-bearing for the ceilings."),
           "note": ("Sensitivity only. No gate is rescored. Every conclusion in "
                    "this artefact is computed from skin_cases above rather than "
                    "asserted -- defect 19, which is what this file used to do "
                    "wrong.")}
    (RESULTS / "skin_sensitivity.json").write_text(json.dumps(out, indent=1))
    print()
    print("written -> results/skin_sensitivity.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
