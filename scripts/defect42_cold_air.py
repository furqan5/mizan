"""
MIZAN :: does fan turndown alone fail to hold the silica floor in cold air?
===========================================================================
Defect 42 left a finding behind: in cold air the tower over-cools even at its
slowest fan, so a site that needs the 31.76 C silica floor needs a tower
bypass, and the four-region study put it at 8 hours a day at Frankfurt.

`hybrid_supervisor.fan_for_target_fws` reports a miss in two different ways,
and the four-region artefact keeps only the miss, not which way:

  low_fan_unexplorable False  the solver converged down to the slowest fan it
                              was asked about and the water was still too
                              cold. That is the physical claim.
  low_fan_unexplorable True   a solve failed below the slowest fan that
                              converged, so whether the floor was reachable
                              is UNKNOWN. That is the solver's limit.

This asks again, with the four-region run's own arguments, for every Frankfurt
hour, and classifies the result by the rule fixed before the run in
docs/staged/plant_scale_site_pressure_preregistration.md, section 6:

  SURVIVES        at least one solved hour misses with the flag False
  SOLVER-LIMITED  every miss carries the flag True
  WITHDRAWN       no solved hour misses

Unsolved hours (defect 43) count for neither side and are listed apart.

Run:  python scripts/defect42_cold_air.py   (after scripts/generate_pitch_artifacts.py)
Writes: results/defect42_cold_air.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
RESULTS = ROOT / "results"

import chemistry as ch  # noqa: E402
import generate_pitch_artifacts as gpa  # noqa: E402
import hybrid_supervisor as hs  # noqa: E402
import run_controller as rc  # noqa: E402

REGION = "Europe_Frankfurt"


def main() -> int:
    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    fc, fn = cal["fill_c"], cal["fill_n"]
    art = json.loads((RESULTS / "pitch_artifacts.json").read_text(encoding="utf-8"))
    rows = art["regions"][REGION]["rows"]
    cfg = gpa.REGIONS[REGION]
    q_it = cfg["q_it_kw"]
    # the arguments run_region hands compare_blind_vs_bounded, and the duty
    # evaluate() hands the inversion
    m_w_pri, m_a_rated = q_it / 20.0, q_it / 22.5
    q_total = q_it * hs.LOOP_HEAT_FACTOR
    floor = ch.temperature_floor_for_silica(rc.TSE, cfg["cycles"])

    hours = []
    for r in rows:
        T_db, rh = r["T_db"], r["rh"]
        grid = []
        for f in hs.fan_grid():
            st = hs.solve_free_cooling(T_db, rh, m_w_pri, q_total, f,
                                       m_a_rated, fc, fn)
            grid.append({"fan_pct": f,
                         "T_fws_c": None if st is None else st["T_fws"]})
        b = r["bounded"]
        row = {"hour": r["hour"], "T_db": T_db, "rh": rh,
               "solved": bool(r["blind"] and b),
               "floor_unreachable": bool(b and b["floor_unreachable"]),
               "fan_grid": grid,
               "slowest_grid_fan_solving": min(
                   (g["fan_pct"] for g in grid if g["T_fws_c"] is not None),
                   default=None)}
        if row["floor_unreachable"]:
            got = hs.fan_for_target_fws(floor, T_db, rh, m_w_pri, q_total,
                                        m_a_rated, fc, fn)
            fan, st = got
            row.update(fan_pct=fan, T_fws_c=st["T_fws"],
                       shortfall_k=st["target_shortfall_k"],
                       low_fan_unexplorable=bool(st["low_fan_unexplorable"]),
                       agrees_with_artefact=abs(st["T_fws"] - b["T_fws_c"]) < 1e-6)
        hours.append(row)

    misses = [h for h in hours if h["floor_unreachable"]]
    physical = [h for h in misses if not h["low_fan_unexplorable"]]
    solver = [h for h in misses if h["low_fan_unexplorable"]]
    unsolved = [h for h in hours if not h["solved"]]
    if physical:
        verdict = "SURVIVES"
    elif misses:
        verdict = "SOLVER-LIMITED"
    else:
        verdict = "WITHDRAWN"

    print(f"fill law c {fc:.4f}, n {fn:.4f}; silica floor {floor:.2f} C; "
          f"Frankfurt sine 14-22 C, RH 0.62")
    print(f"{'h':>3}{'T_db':>7}  {'slowest fan solving':>20}  result")
    for h in hours:
        if not h["solved"]:
            res = "UNSOLVED (defect 43)"
        elif h["floor_unreachable"]:
            res = (f"MISS {h['shortfall_k']:.2f} K at {h['fan_pct']:.1f} % fan, "
                   + ("solver limit" if h["low_fan_unexplorable"]
                      else "slowest fan still too cold"))
        else:
            res = "floor held"
        slow = h["slowest_grid_fan_solving"]
        print(f"{h['hour']:>3}{h['T_db']:>7.2f}  "
              f"{'none' if slow is None else f'{slow:.1f} %':>20}  {res}")
    print(f"\nmisses {len(misses)} (physical {len(physical)}, solver-limited "
          f"{len(solver)}); unsolved {len(unsolved)}")
    print(f"VERDICT: {verdict}")
    (RESULTS / "defect42_cold_air.json").write_text(json.dumps({
        "fill_c": fc, "fill_n": fn, "region": REGION,
        "silica_floor_c": floor, "verdict": verdict,
        "rule": "docs/staged/plant_scale_site_pressure_preregistration.md s6",
        "hours_solved": sum(1 for h in hours if h["solved"]),
        "hours_unsolved": len(unsolved),
        "hours_floor_unreachable": len(misses),
        "hours_floor_unreachable_physical": len(physical),
        "hours_floor_unreachable_solver_limited": len(solver),
        "hours": hours}, indent=1), encoding="utf-8")
    print("written -> results/defect42_cold_air.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
