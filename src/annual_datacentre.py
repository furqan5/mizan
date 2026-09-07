"""
FURQAN :: the same Dhahran year, run at a DATA CENTRE load profile
==================================================================
`annual.py` bins a real Dhahran year and runs the controller at each bin's
centroid with a COMFORT-DRIVEN load:

    load = clip(0.55 + 0.45 * (T_db - 18) / (46 - 18), 0.35, 1.0)

which is correct for district cooling and is tagged in that file as
`[A -- a load model, not a measurement]`. It ties load to ambient: cold hours
are also low-load hours.

A data centre does not work that way. Its cooling load is set by IT draw, not
by weather, so it sits near design load in January as well as in August. That
is a genuinely different operating envelope, and it is the ONLY thing this
script changes. Same weather file, same calibration, same controller, same
chemistry, same chiller envelope.

WHY IT MATTERS. `HANDOFF.md` records that the energy and water savings are
anti-correlated across the year (r = -0.548): energy 10.37 % across the cool
half against 2.06 % across the hot half, water 7.18 % against 9.79 %. That
finding is called "the strongest argument in the package for coupling the two
models" -- but a large part of it may be a LOAD effect rather than a WEATHER
effect, because in `annual.py` cold hours are also light hours. Flattening the
load separates the two. If the anti-correlation survives at flat load it is
about the weather and the coupling argument holds for data centres. If it
collapses, the coupling argument is really an argument about part-load
district cooling and does not transfer.

------------------------------------------------------------------------
PRE-REGISTERED PREDICTIONS -- written and committed BEFORE the first run.
Recorded here so they cannot be revised after the answer is known, per
docs/defect_register.md and the pre-registration rule that governs every
gate in this package. These are PREDICTIONS, not gates: nothing in the
product passes or fails on them.

  P1  Cool-half energy saving will be LOWER than the district-cooling
      10.37 %, because flat high load raises the condenser return
      temperature and pushes entering condenser water toward the 35 C
      chiller ceiling even at low wet-bulb, shrinking the fan lever.
      (This is the UNFAVOURABLE prediction and it is the expected one.)

  P2  Annual water saving (ratio of totals) will land within +/- 2.0
      points of the district-cooling 8.81 %, because the water saving is
      bought by cycles (6 against a baseline 4) and cycles are set by
      chemistry, which is load-independent.

  P3  The energy/water anti-correlation across the eight bins will WEAKEN,
      |r| < 0.548, because the load variation that helps drive it has been
      removed.

  P4  MORE hours will sit hard against the chiller ECWT ceiling than in the
      district-cooling case -- at least one bin that was previously clear of
      it will now be pinned.

  P5  Absolute annual money saved will be HIGHER than the district-cooling
      $76,236/yr at the same 10 MW nameplate, even if the percentages fall,
      because the plant now runs near design load all year.

Any of these can fail. A failure is a finding and gets reported as one.
------------------------------------------------------------------------

Run:  python src/annual_datacentre.py            (defaults to load = 0.90)
      python src/annual_datacentre.py 0.75       (sensitivity)
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import controller as ctl                                        # noqa: E402
import run_controller as rc                                     # noqa: E402

ALMERIA_WB_MAX_C = 21.9
N_BINS = 8

# The district-cooling reference figures, READ FROM THE ARTEFACT rather than
# typed here. Defect 12 in this package was a constant hardcoded into four
# files that then went stale; do not reintroduce that pattern.
def _dc_reference() -> dict:
    p = RESULTS / "annual_dhahran.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def main(flat_load: float = 0.90) -> int:
    hp = RESULTS / "tmy_hourly.npy"
    if not hp.exists():
        print("results/tmy_hourly.npy missing. Run src/tmy.py first.")
        return 1
    h = np.load(hp)
    T_db, rh, T_wb = h[:, 3], h[:, 4], h[:, 5]

    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]

    ref = _dc_reference()

    print("=" * 78)
    print("ANNUAL PERFORMANCE AT A DATA CENTRE LOAD PROFILE -- Dhahran TMYx")
    print("=" * 78)
    print(f"IT-driven load held FLAT at {flat_load:.2f} of nameplate in every")
    print("wet-bulb bin. Everything else is identical to src/annual.py.")
    print()
    print("This is NOT a pre-registered gate and changes no gate verdict.")
    print("V5 remains failed on water. See docs/defect_register.md.")
    print()
    print("Pre-registered predictions P1-P5 are in this file's docstring and")
    print("were committed before the first run. They are scored at the end.")
    print()

    order = np.argsort(T_wb)
    bins = np.array_split(order, N_BINS)

    print(f"{'bin':>4s} {'hours':>6s} {'T_wb C':>8s} {'T_db C':>8s} {'RH':>6s} "
          f"{'load':>6s} {'energy %':>9s} {'water %':>9s} {'cost %':>8s} "
          f"{'ECWT C':>8s} {'in envlp':>9s}")
    print("-" * 78)

    rows = []
    for i, idx in enumerate(bins):
        wb_c = float(T_wb[idx].mean())
        db_c = float(T_db[idx].mean())
        rh_c = float(rh[idx].mean())
        hrs = int(len(idx))

        cond = dict(rc.PLANT)
        cond.update({"T_db": db_c, "rh": rh_c, "T_wi": wb_c + 12.0})
        cond["Q_evap_kw"] = rc.PLANT["Q_evap_kw"] * flat_load

        seed = ctl._thermal_solve(70.0, 4.0, cond, rc.TSE, fc, fn)
        if seed is not None:
            cond["T_wo_guess"] = seed[2]

        base = ctl.baseline(cond, rc.TSE, rc.TARIFFS, fc, fn,
                            fixed_cycles=4.0, fixed_ph=7.8, cw_setpoint_c=32.0,
                            fan_grid=np.arange(30, 101, 10.0))
        best, _ = ctl.optimise(cond, rc.TSE, rc.TARIFFS, fc, fn,
                               fan_grid=np.arange(30, 101, 10.0),
                               cycles_grid=np.arange(2.0, 10.01, 1.0),
                               ph_grid=np.arange(7.0, 9.01, 0.25))
        if base is None or best is None:
            print(f"{i:4d} {hrs:6d} {wb_c:8.1f} {db_c:8.1f} {rh_c:6.2f} "
                  f"{flat_load:6.2f}   NO FEASIBLE SOLUTION")
            rows.append({"bin": i, "hours": hrs, "T_wb_C": wb_c,
                         "T_db_C": db_c, "rh": rh_c, "load": flat_load,
                         "feasible": False})
            continue

        w = 100.0 * (base["makeup_m3_h"] - best["makeup_m3_h"]) / base["makeup_m3_h"]
        c = 100.0 * (base["cost_per_h"] - best["cost_per_h"]) / base["cost_per_h"]
        e = 100.0 * (base["P_total_kW"] - best["P_total_kW"]) / base["P_total_kW"]

        # Entering condenser water at the optimum: the quantity that reveals
        # whether the chiller envelope is the binding constraint. HANDOFF.md
        # records all four Gulf-summer optima sitting at 33.9-34.7 C against a
        # 35 C ceiling; P4 asks whether flat load pins more bins there.
        ecwt = best.get("T_wo_C", best.get("T_wo", float("nan")))
        inside = wb_c <= ALMERIA_WB_MAX_C

        rows.append({"bin": i, "hours": hrs, "T_wb_C": wb_c, "T_db_C": db_c,
                     "rh": rh_c, "load": flat_load, "feasible": True,
                     "water_pct": w, "cost_pct": c, "energy_pct": e,
                     "ecwt_C": float(ecwt),
                     "cycles_at_opt": float(best.get("cycles", float("nan"))),
                     "fan_pct_at_opt": float(best.get("fan_pct", float("nan"))),
                     "base_kW": base["P_total_kW"],
                     "opt_kW": best["P_total_kW"],
                     "base_makeup_m3_h": base["makeup_m3_h"],
                     "opt_makeup_m3_h": best["makeup_m3_h"],
                     "base_cost_h": base["cost_per_h"],
                     "opt_cost_h": best["cost_per_h"],
                     "inside_validated_envelope": bool(inside),
                     "pct_hours_above_almeria":
                         float(100 * (T_wb[idx] > ALMERIA_WB_MAX_C).mean())})
        print(f"{i:4d} {hrs:6d} {wb_c:8.1f} {db_c:8.1f} {rh_c:6.2f} "
              f"{flat_load:6.2f} {e:9.2f} {w:9.2f} {c:8.2f} {ecwt:8.2f} "
              f"{'yes' if inside else 'NO':>9s}")

    solved = [r for r in rows if r.get("feasible")]
    if not solved:
        print("no bins solved")
        return 1

    hrs = np.array([r["hours"] for r in solved], float)
    wt = hrs / hrs.sum()
    w_ann = float(np.sum(wt * [r["water_pct"] for r in solved]))
    c_ann = float(np.sum(wt * [r["cost_pct"] for r in solved]))
    e_ann = float(np.sum(wt * [r["energy_pct"] for r in solved]))

    # Ratios of hour-weighted totals. The mean-of-ratios figures are kept for
    # comparability with annual.py, but these are the ones to quote.
    def _ratio(bk: str, ok: str) -> float:
        b = float(np.sum(hrs * [r[bk] for r in solved]))
        o = float(np.sum(hrs * [r[ok] for r in solved]))
        return 100.0 * (b - o) / b

    w_tot = _ratio("base_makeup_m3_h", "opt_makeup_m3_h")
    c_tot = _ratio("base_cost_h", "opt_cost_h")
    e_tot = _ratio("base_kW", "opt_kW")

    # Absolute annual money, computed the same way annual.py's split is.
    money = float(np.sum(hrs * (np.array([r["base_cost_h"] for r in solved])
                                - np.array([r["opt_cost_h"] for r in solved]))))

    # Cool half / hot half, split at the median bin, matching HANDOFF.md.
    half = len(solved) // 2
    def _half(rs):
        hh = np.array([r["hours"] for r in rs], float)
        def rt(bk, ok):
            b = float(np.sum(hh * [r[bk] for r in rs]))
            o = float(np.sum(hh * [r[ok] for r in rs]))
            return 100.0 * (b - o) / b
        return (rt("base_kW", "opt_kW"),
                rt("base_makeup_m3_h", "opt_makeup_m3_h"),
                rt("base_cost_h", "opt_cost_h"))
    cool = _half(solved[:half])
    hot = _half(solved[half:])

    e_arr = np.array([r["energy_pct"] for r in solved])
    w_arr = np.array([r["water_pct"] for r in solved])
    r_ew = float(np.corrcoef(e_arr, w_arr)[0, 1]) if len(solved) > 2 else float("nan")

    print("-" * 78)
    print(f"{'ANNUAL':>4s} {int(hrs.sum()):6d} {'':8s} {'':8s} {'':6s} "
          f"{flat_load:6.2f} {e_ann:9.2f} {w_ann:9.2f} {c_ann:8.2f}")
    print()
    print("RATIOS OF ANNUAL TOTALS (the figures to quote):")
    print(f"   electrical energy reduction : {e_tot:6.2f} %")
    print(f"   makeup water reduction      : {w_tot:6.2f} %")
    print(f"   operating cost reduction    : {c_tot:6.2f} %")
    print(f"   annual cost saved           : ${money:,.0f}/yr at 10 MW nameplate")
    print()
    print(f"   cool half : energy {cool[0]:6.2f} %   water {cool[1]:6.2f} %"
          f"   cost {cool[2]:6.2f} %")
    print(f"   hot  half : energy {hot[0]:6.2f} %   water {hot[1]:6.2f} %"
          f"   cost {hot[2]:6.2f} %")
    print(f"   energy/water correlation across bins : r = {r_ew:+.3f}")
    print()

    # ---- score the pre-registered predictions ----------------------------
    print("=" * 78)
    print("PRE-REGISTERED PREDICTIONS, SCORED")
    print("=" * 78)
    preds = []
    if ref:
        dc_e_tot = ref.get("annual_energy_pct_ratio_of_totals")
        dc_w_tot = ref.get("annual_water_pct_ratio_of_totals")
        dc_bins = [b for b in ref.get("bins", []) if "energy_pct" in b]
        dh = len(dc_bins) // 2
        def _rt(rs, bk, ok):
            hh = np.array([r["hours"] for r in rs], float)
            b = float(np.sum(hh * [r[bk] for r in rs]))
            o = float(np.sum(hh * [r[ok] for r in rs]))
            return 100.0 * (b - o) / b
        dc_cool_e = _rt(dc_bins[:dh], "base_kW", "opt_kW") if dc_bins else float("nan")
        dc_r = float(np.corrcoef([b["energy_pct"] for b in dc_bins],
                                 [b["water_pct"] for b in dc_bins])[0, 1]) \
            if len(dc_bins) > 2 else float("nan")

        preds.append(("P1 cool-half energy BELOW district cooling",
                      cool[0] < dc_cool_e,
                      f"{cool[0]:.2f} % vs {dc_cool_e:.2f} %"))
        preds.append(("P2 annual water within +/-2.0 pts of district cooling",
                      abs(w_tot - dc_w_tot) <= 2.0,
                      f"{w_tot:.2f} % vs {dc_w_tot:.2f} % "
                      f"(delta {w_tot - dc_w_tot:+.2f})"))
        preds.append(("P3 energy/water anti-correlation WEAKENS",
                      abs(r_ew) < abs(dc_r),
                      f"|r| {abs(r_ew):.3f} vs {abs(dc_r):.3f}"))
    n_pinned = sum(1 for r in solved if r["ecwt_C"] >= 33.5)
    preds.append(("P4 more bins pinned against the 35 C chiller ceiling",
                  None, f"{n_pinned} of {len(solved)} bins at ECWT >= 33.5 C "
                        f"-- compare against the 4-of-5 summer conditions in "
                        f"HANDOFF.md by hand"))
    preds.append(("P5 absolute annual money saved above $76,236",
                  money > 76236.0, f"${money:,.0f}/yr"))

    for name, ok, detail in preds:
        verdict = "MANUAL" if ok is None else ("HELD" if ok else "FAILED")
        print(f"   {verdict:>6s}  {name}")
        print(f"           {detail}")
    print()
    print("A failed prediction is a finding, not an error. Report it.")

    out = {"source": "SAU_SH_Dhahran-Abdulaziz.AB.404160_TMYx.2011-2025",
           "load_model": "FLAT (data centre, IT-driven)",
           "flat_load_fraction": flat_load,
           "differs_from_annual_dhahran_only_by": "the load profile",
           "n_bins": len(solved), "bins": rows,
           "annual_water_pct": w_ann, "annual_cost_pct": c_ann,
           "annual_energy_pct": e_ann,
           "annual_water_pct_ratio_of_totals": w_tot,
           "annual_cost_pct_ratio_of_totals": c_tot,
           "annual_energy_pct_ratio_of_totals": e_tot,
           "annual_cost_saved_usd": money,
           "cool_half": {"energy_pct": cool[0], "water_pct": cool[1],
                         "cost_pct": cool[2]},
           "hot_half": {"energy_pct": hot[0], "water_pct": hot[1],
                        "cost_pct": hot[2]},
           "energy_water_correlation_across_bins": r_ew,
           "predictions": [{"name": n,
                            "held": (None if ok is None else bool(ok)),
                            "detail": d} for n, ok, d in preds],
           "status": ("EXPLORATORY. Not a pre-registered gate and it changes "
                      "no gate verdict. The load profile is an assumption "
                      "[A], as it is in annual.py. No data-centre plant data "
                      "was used.")}
    (RESULTS / "annual_datacentre.json").write_text(json.dumps(out, indent=1))
    print("written -> results/annual_datacentre.json")
    return 0


if __name__ == "__main__":
    load = float(sys.argv[1]) if len(sys.argv) > 1 else 0.90
    sys.exit(main(load))
