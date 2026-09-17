"""
FURQAN :: hours-weighted annual performance, from real Dhahran weather
======================================================================
The V5 gate scores an UNWEIGHTED mean over five hand-picked conditions.
That is not a physical quantity: a Gulf plant spends far more hours in
August than in January, and the five conditions were chosen to span the
envelope rather than to represent it.

With an hourly TMY file that objection can finally be answered. This bins a
real Dhahran year by wet-bulb, runs the controller at each bin's centroid,
and weights by the hours actually spent there.

IMPORTANT, AND THE REASON THIS IS REPORTED SEPARATELY:

  This is a DIFFERENT METRIC from the pre-registered V5 gate. It is not a
  re-scoring of that gate and it does not change its verdict. V5 was
  registered as an unweighted mean over five conditions, it scored 14.83 %
  against a 15 % threshold, and it failed. That stands.

  What this adds is the number a customer conversation actually needs, and
  an honest statement of how much of it rests on extrapolation.

DEFECT 60, 17 Sep 2026. The envelope split classified WHOLE BINS by their
centroid wet bulb. The fifth equal-hour bin had a centroid of 21.38 C and was
called "inside", while 266 of its 1,095 hours were above 21.9 C. So the split
reported 3,285 extrapolated hours (a bin count, 37.5 %) where the year holds
3,551 (40.5 %), and it booked those 266 hours' savings to the validated side.
Bins are now cut AT the envelope edge: the inside hours and the extrapolated
hours are binned separately, so every hour is classified by its own wet bulb
and every bin is pure. `envelope_bins()` is the one place that rule lives.

Run:  python src/annual.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def _v5_water_pct():
    """The V5 gate figure, READ FROM THE ARTEFACT rather than typed here.

    This was hardcoded as 14.83 in four places. When defect 11 was fixed the
    controller re-ran and the figure moved to 10.02, and every one of those
    four would have gone on asserting 14.83 -- in the JSON this script writes,
    which the audit then checks other documents against. A constant duplicated
    into a file that other files are validated against is a slow-acting fault.
    """
    import json as _json
    return float(_json.loads((RESULTS / "controller_summary.json").read_text())
                 ["summary"]["water_pct"])

sys.path.insert(0, str(pathlib.Path(__file__).parent))

ALMERIA_WB_MAX_C = 21.9
N_BINS = 8


def envelope_bins(T_wb, n_bins: int = N_BINS,
                  limit_c: float = ALMERIA_WB_MAX_C) -> list[np.ndarray]:
    """Equal-hour wet-bulb bins that never straddle the envelope edge.

    The hours at or below `limit_c` and the hours above it are binned
    SEPARATELY, each into equal-hour bins sorted by wet bulb. The `n_bins`
    are shared out in proportion to the hours on each side (at least one bin
    per non-empty side), so the resolution stays close to the old
    8 x 1,095 h layout. The inside bins come first, coolest first.

    Every returned bin is pure: all its hours are inside, or all are outside.
    That is what makes an hour-by-hour envelope split possible from bin-level
    controller runs. DEFECT 60.
    """
    T_wb = np.asarray(T_wb, float)
    n = T_wb.size
    order = np.argsort(T_wb, kind="stable")
    inside = order[T_wb[order] <= limit_c]
    outside = order[T_wb[order] > limit_c]
    if outside.size == 0:
        n_out = 0
    elif inside.size == 0:
        n_out = n_bins
    else:
        n_out = int(round(n_bins * outside.size / n))
        n_out = min(max(n_out, 1), n_bins - 1)
    n_in = n_bins - n_out
    bins = []
    if n_in:
        bins += [b for b in np.array_split(inside, n_in) if b.size]
    if n_out:
        bins += [b for b in np.array_split(outside, n_out) if b.size]
    return bins


def hourly_sha256(h: np.ndarray) -> str:
    """Hash of the hourly weather ARRAY the study was run on, so a result can
    be tied to its input without trusting a file name."""
    return hashlib.sha256(np.ascontiguousarray(h, dtype=np.float64)
                          .tobytes()).hexdigest()


def run_annual(h: np.ndarray, verbose: bool = True,
               title: str = "Dhahran TMYx 2011-2025") -> dict:
    """The hours-weighted annual study on any 8,760-row hourly array in the
    `tmy_hourly.npy` layout (month, day, hour, T_db, rh fraction, T_wb, p).

    Returns the dict `main()` writes to `results/annual_dhahran.json`, minus
    the source label. The weather-source sensitivity calls this on each
    scenario, so every scenario is scored by exactly this code.
    """
    import controller as ctl                                    # noqa: E402
    import run_controller as rc                                 # noqa: E402

    say = print if verbose else (lambda *a, **k: None)
    T_db, rh, T_wb = h[:, 3], h[:, 4], h[:, 5]

    cal = json.loads((RESULTS / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]

    # Cooling load follows dry-bulb, as it does in every real plant. Anchored
    # so the design load lands at the ASHRAE 0.4 % dry-bulb and the minimum is
    # the plant's base load. [A -- a load model, not a measurement]
    T_lo, T_hi = 18.0, 46.0
    load = np.clip(0.55 + 0.45 * (T_db - T_lo) / (T_hi - T_lo), 0.35, 1.0)

    # Bin by wet-bulb: it is what sets the tower's capability, so it is the
    # right axis to bin on. Equal-hour bins rather than equal-width, so no
    # bin is so sparse that its centroid is meaningless -- and cut at the
    # envelope edge, so no bin is half validated (defect 60).
    bins = envelope_bins(T_wb)

    say("=" * 76)
    say(f"HOURS-WEIGHTED ANNUAL PERFORMANCE  --  {title}")
    say("=" * 76)
    say("This is NOT the pre-registered V5 gate and does not change its")
    say("verdict. V5 is an unweighted mean over five conditions; it scored")
    say(f"{_v5_water_pct():.2f} % against 15 % and failed. This is the "
        f"annual figure.")
    say()
    say(f"{'bin':>4s} {'hours':>6s} {'T_wb C':>8s} {'T_db C':>8s} {'RH':>6s} "
        f"{'load':>6s} {'energy %':>9s} {'water %':>9s} "
        f"{'cost %':>8s} {'in envlp':>9s}")
    say("-" * 76)

    rows, unsolved_hours = [], 0
    for i, idx in enumerate(bins):
        wb_c = float(T_wb[idx].mean())
        db_c = float(T_db[idx].mean())
        rh_c = float(rh[idx].mean())
        ld_c = float(load[idx].mean())
        hrs = int(len(idx))
        n_above = int((T_wb[idx] > ALMERIA_WB_MAX_C).sum())
        # Pure by construction; asserted, because the split below is only an
        # hour-by-hour split while this holds.
        assert n_above in (0, hrs), f"bin {i} straddles the envelope edge"
        inside = n_above == 0

        cond = dict(rc.PLANT)
        cond.update({"T_db": db_c, "rh": rh_c, "T_wi": wb_c + 12.0})
        cond["Q_evap_kw"] = rc.PLANT["Q_evap_kw"] * ld_c

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
            unsolved_hours += hrs
            say(f"{i:4d} {hrs:6d} {wb_c:8.1f} {db_c:8.1f} {rh_c:6.2f} "
                f"{ld_c:6.2f}   no feasible solution")
            continue

        w = 100.0 * (base["makeup_m3_h"] - best["makeup_m3_h"]) / base["makeup_m3_h"]
        c = 100.0 * (base["cost_per_h"] - best["cost_per_h"]) / base["cost_per_h"]
        e = 100.0 * (base["P_total_kW"] - best["P_total_kW"]) / base["P_total_kW"]
        rows.append({"bin": i, "hours": hrs, "T_wb_C": wb_c, "T_db_C": db_c,
                     "T_wb_min_C": float(T_wb[idx].min()),
                     "T_wb_max_C": float(T_wb[idx].max()),
                     "rh": rh_c, "load": ld_c, "water_pct": w, "cost_pct": c,
                     "energy_pct": e,
                     "base_kW": base["P_total_kW"],
                     "opt_kW": best["P_total_kW"],
                     # Absolutes, so the annual figure can be computed as a
                     # ratio of totals rather than a mean of ratios. Storing
                     # only the percentages made the second impossible.
                     "base_makeup_m3_h": base["makeup_m3_h"],
                     "opt_makeup_m3_h": best["makeup_m3_h"],
                     "base_cost_h": base["cost_per_h"],
                     "opt_cost_h": best["cost_per_h"],
                     "inside_validated_envelope": bool(inside),
                     "pct_hours_above_almeria": float(100.0 * n_above / hrs)})
        say(f"{i:4d} {hrs:6d} {wb_c:8.1f} {db_c:8.1f} {rh_c:6.2f} "
            f"{ld_c:6.2f} {e:9.2f} {w:9.2f} {c:8.2f} "
            f"{'yes' if inside else 'NO':>9s}")

    if not rows:
        raise RuntimeError("no bins solved")

    hrs = np.array([r["hours"] for r in rows], float)
    wt = hrs / hrs.sum()
    w_ann = float(np.sum(wt * [r["water_pct"] for r in rows]))
    c_ann = float(np.sum(wt * [r["cost_pct"] for r in rows]))
    e_ann = float(np.sum(wt * [r["energy_pct"] for r in rows]))

    # The three figures above are hour-weighted MEANS OF RATIOS. That is not
    # the saving a plant sees over a year. A mean of ratios gives an hour in
    # January, when the plant draws 682 kW, the same vote as an hour in August
    # at 1,492 kW -- so it is biased by whatever correlation exists between the
    # percentage saving and the load. Here that correlation is real and it runs
    # in OPPOSITE directions: the energy saving is largest when the plant is
    # coldest and drawing least, and the water saving is largest when it is
    # hottest and evaporating most. So the mean of ratios FLATTERS the energy
    # number and UNDERSTATES the water one.
    #
    # The physically meaningful quantity is the ratio of annual totals:
    # kWh saved over kWh consumed. Both are reported; the ratio-of-totals
    # figures are the ones to quote outside this repository.
    def _ratio(base_key: str, opt_key: str) -> float:
        b = float(np.sum(hrs * [r[base_key] for r in rows]))
        o = float(np.sum(hrs * [r[opt_key] for r in rows]))
        return 100.0 * (b - o) / b

    w_tot = _ratio("base_makeup_m3_h", "opt_makeup_m3_h")
    c_tot = _ratio("base_cost_h", "opt_cost_h")
    e_tot = _ratio("base_kW", "opt_kW")
    inside_frac = float(np.sum(hrs[[r["inside_validated_envelope"] for r in rows]])
                        / hrs.sum())

    # DEFECT 48. Reporting the extrapolated FRACTION is not the same as
    # reporting what the extrapolation is worth, and on this study they point
    # in opposite directions. Split every headline by envelope.
    # DEFECT 60. The split is by HOUR: every bin is pure, so these hour sums
    # equal the hour counts of the weather file itself.
    ins = np.array([r["inside_validated_envelope"] for r in rows])

    def _ratio_over(sel, base_key, opt_key):
        b = float(np.sum(hrs[sel] * np.array([r[base_key] for r in rows])[sel]))
        o = float(np.sum(hrs[sel] * np.array([r[opt_key] for r in rows])[sel]))
        return 100.0 * (b - o) / b if b else float("nan")

    split = {}
    for tag, sel in (("inside", ins), ("extrapolated", ~ins)):
        split[tag] = {
            "hours": int(hrs[sel].sum()),
            "water_pct": _ratio_over(sel, "base_makeup_m3_h", "opt_makeup_m3_h"),
            "energy_pct": _ratio_over(sel, "base_kW", "opt_kW"),
            "cost_pct": _ratio_over(sel, "base_cost_h", "opt_cost_h"),
        }
    hours_above = int((T_wb > ALMERIA_WB_MAX_C).sum())

    say("-" * 76)
    say(f"{'ANNUAL':>4s} {int(hrs.sum()):6d} {'':8s} {'':8s} {'':6s} {'':6s} "
        f"{e_ann:9.2f} {w_ann:9.2f} {c_ann:8.2f}")
    say()
    say("WHAT THIS IS, AND WHAT IT RESTS ON")
    say(f"   hours-weighted annual total-power reduction  : {e_ann:.2f} %")
    say(f"   hours-weighted annual makeup water reduction : {w_ann:.2f} %")
    say(f"   hours-weighted annual cost reduction         : {c_ann:.2f} %")
    say()
    say("   Those three are means of ratios. As RATIOS OF ANNUAL TOTALS,")
    say("   which is what a plant actually banks over a year:")
    say(f"   annual electrical energy reduction           : {e_tot:.2f} %"
        f"   ({e_tot - e_ann:+.2f} pts)")
    say(f"   annual makeup water reduction                : {w_tot:.2f} %"
        f"   ({w_tot - w_ann:+.2f} pts)")
    say(f"   annual operating cost reduction              : {c_tot:.2f} %"
        f"   ({c_tot - c_ann:+.2f} pts)")
    opposite = (e_tot - e_ann) * (w_tot - w_ann) < 0
    say("   The energy and water corrections have "
        + ("OPPOSITE signs." if opposite else "the SAME sign."))
    say(f"   for comparison, the five-condition unweighted mean the V5 gate")
    say(f"   scores                                        : "
        f"{_v5_water_pct():.2f} % water")
    say()
    say(f"   fraction of the year INSIDE the validated wet-bulb envelope")
    say(f"   (<= {ALMERIA_WB_MAX_C} C), counted hour by hour           : "
        f"{100*inside_frac:.1f} %")
    say(f"   fraction resting on EXTRAPOLATION            : "
        f"{100*(1-inside_frac):.1f} %   ({hours_above} h)")
    say()
    say("   AND WHAT THE EXTRAPOLATION IS ACTUALLY WORTH -- defects 48 and 60.")
    say()
    say(f"   {'':30}{'hours':>7}{'water %':>10}{'energy %':>10}{'cost %':>9}")
    say(f"   {'whole year':30}{int(hrs.sum()):>7}{w_tot:>10.2f}"
        f"{e_tot:>10.2f}{c_tot:>9.2f}")
    for tag in ("inside", "extrapolated"):
        d = split[tag]
        lab = ("inside the validated envelope" if tag == "inside"
               else f"EXTRAPOLATED (wb > {ALMERIA_WB_MAX_C} C)")
        say(f"   {lab:30}{d['hours']:>7}{d['water_pct']:>10.2f}"
            f"{d['energy_pct']:>10.2f}{d['cost_pct']:>9.2f}")
    say()

    # The conclusion is DERIVED from the signs, not typed. Defect 19 was a
    # paragraph of hardcoded prose printed under a table that had stopped
    # supporting it.
    wi, wx = split["inside"]["water_pct"], split["extrapolated"]["water_pct"]
    ei, ex = split["inside"]["energy_pct"], split["extrapolated"]["energy_pct"]
    parts = []
    if wi < 0 <= wx:
        parts.append("The water saving is NEGATIVE inside the validated "
                     "wet-bulb envelope and positive only outside it, so the "
                     "annual water figure is carried entirely by extrapolated "
                     "hours.")
    elif wi >= 0:
        parts.append("The water saving is not negative inside the validated "
                     f"envelope ({wi:+.2f} %); re-derive the defect-48 reading "
                     "before quoting it.")
    else:
        parts.append(f"The water saving is negative on BOTH sides of the "
                     f"envelope (inside {wi:+.2f} %, outside {wx:+.2f} %).")
    if ei > ex:
        parts.append("The energy saving is the reverse: larger inside the "
                     "envelope than outside it.")
    else:
        parts.append("The energy saving is NOT larger inside the envelope "
                     "than outside it.")
    parts.append("Quote neither without this split.")
    warning = " ".join(parts)
    for ln in warning.split(". "):
        say("   " + ln.strip() + ("" if ln.endswith(".") else "."))

    return {"n_bins": len(rows), "bins": rows,
            "binning": ("equal-hour wet-bulb bins cut at the envelope edge "
                        f"({ALMERIA_WB_MAX_C} C): inside and extrapolated "
                        "hours are binned separately, so every bin is pure "
                        "and the envelope split is hour by hour (defect 60)"),
            "input_hourly_sha256": hourly_sha256(h),
            "unsolved_hours": unsolved_hours,
            "annual_water_pct": w_ann, "annual_cost_pct": c_ann,
            "annual_energy_pct": e_ann,
            "annual_water_pct_ratio_of_totals": w_tot,
            "annual_cost_pct_ratio_of_totals": c_tot,
            "annual_energy_pct_ratio_of_totals": e_tot,
            "weighting_note": (
                "annual_*_pct are hour-weighted MEANS OF RATIOS and are kept "
                "because published figures cite them. annual_*_ratio_of_totals "
                "are ratios of hour-weighted totals -- kWh saved over kWh "
                "consumed -- and are the figures to quote outside this "
                "repository. They differ because the percentage saving "
                "correlates with load."),
            "fraction_inside_validated_envelope": inside_frac,
            "hours_above_almeria": hours_above,
            "by_envelope": split,
            "envelope_warning": warning,
            "v5_gate_unweighted_mean_water_pct": _v5_water_pct(),
            "note": ("A different metric from the pre-registered V5 gate, "
                     "reported alongside it and not in place of it. V5 remains "
                     f"failed at {_v5_water_pct():.2f} % against a 15 % "
                     "threshold.")}


def main() -> int:
    hp = RESULTS / "tmy_hourly.npy"
    if not hp.exists():
        print("results/tmy_hourly.npy missing. Run src/tmy.py first.")
        return 1
    h = np.load(hp)
    try:
        res = run_annual(h)
    except RuntimeError as exc:
        print(exc)
        return 1
    print()
    print("   Roughly two fifths of this TMYx year is hotter and wetter than")
    print("   anything the model was validated against, and no amount of")
    print("   weighting changes that. It is what the KFUPM wind tunnel is for.")
    print("   How much of that fraction is the TMYx file's humidity rather than")
    print("   Dhahran's is docs/weather_source_sensitivity.md.")

    out = {"source": "SAU_SH_Dhahran-Abdulaziz.AB.404160_TMYx.2011-2025"}
    out.update(res)
    (RESULTS / "annual_dhahran.json").write_text(json.dumps(out, indent=1))
    print()
    print("written -> results/annual_dhahran.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
