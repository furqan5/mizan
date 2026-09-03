"""Is the optimiser selecting duties the chiller cannot actually deliver?

    python src/chiller_feasibility_audit.py

FOUND WHILE BUILDING `fouling_energy.py`. Gate G-F4 there required both chiller
models to be monotonic in fouling. The biquad was not -- and not because of
extrapolation past its temperature range, which `run_controller` already guards,
but for a reason the temperature guard cannot see.

THE MECHANISM. `chiller_power_biquad` computes

    q_avail = Q_ref * capft(T_chws, T_cws)
    plr_raw = Q_evap / q_avail
    plr     = min(max(plr_raw, 0.1), 1.0)          <-- silent clamp

`capft` is the machine's capacity as a function of temperature, and it falls as
condenser water gets hotter. Above about 32.5 degC entering condenser water this
York YT cannot make 10 MW at all: q_avail drops below the duty and plr_raw rises
past 1.0, reaching 1.15 at 35 degC. The clamp then evaluates the machine as
though it were merely at full load.

Two things are wrong with that, and the second is worse than the first:

  1. Power is UNDER-reported. Above ~32.5 degC, capft falls faster than eirft
     rises, so computed chiller power DECREASES with rising condenser
     temperature. That is backwards.
  2. The duty is INFEASIBLE. A real plant at that condenser temperature does not
     quietly draw less power -- it fails to make the cooling. Chilled water
     temperature rises, or another machine starts, or capacity is lost.

WHY IT MATTERS HERE RATHER THAN IN GENERAL. The optimiser's main energy lever is
fan speed, and lowering the fan RAISES condenser water temperature. So the one
region where the chiller model under-states cost is precisely the region the
optimiser is being pushed toward. The fan saving is real; the chiller penalty
that should offset it is under-computed.

`run_controller` already rejects points outside the fitted TEMPERATURE range and
says so -- "rejected, not extrapolated". `CHILLER_RANGE_LOG` also counts
`PLR_out`, but nothing reads it and nothing rejects on it.

THIS SCRIPT DOES NOT CHANGE ANY PUBLISHED RESULT. It quantifies the exposure and
writes its own file. Whether to enforce the constraint and re-run the headline
numbers is a decision with consequences -- the annual figures, the deck, the
figures and a published post all rest on them -- so it is left to the founder.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import controller as ctl   # noqa: E402


def capacity_state(Q_evap_kw: float, T_cws_c: float, T_chws_c: float = 7.0):
    """capft, available duty and raw part-load ratio at this condition."""
    capft_ref = ctl._biquad(ctl.CHILLER_CAPFT, 6.67, 29.44)
    capft = ctl._biquad(ctl.CHILLER_CAPFT, T_chws_c, T_cws_c) / capft_ref
    q_avail = Q_evap_kw * capft
    return capft, q_avail, Q_evap_kw / max(q_avail, 1e-6)


def main() -> int:
    cs = json.loads((RESULTS / "controller_summary.json").read_text())
    Q = cs["plant"]["Q_evap_kw"]
    plr_hi = ctl.CHILLER_PLR_RANGE[1]
    t_lo, t_hi = ctl.CHILLER_TCWS_RANGE

    df = pd.read_csv(RESULTS / "v5_controller.csv")

    print("=" * 76)
    print("CHILLER FEASIBILITY AUDIT")
    print("=" * 76)
    print(f"   duty {Q:.0f} kW, biquad fitted for T_cws {t_lo:.2f}-{t_hi:.2f} C"
          f" and PLR {ctl.CHILLER_PLR_RANGE[0]}-{plr_hi}")
    print(f"   the TEMPERATURE guard is enforced by run_controller.")
    print(f"   the CAPACITY guard is logged as PLR_out and never enforced.\n")

    rows = []
    print(f"   {'condition':22} {'which':>5} {'T_cws':>7} {'capft':>7} "
          f"{'q_avail':>9} {'PLR':>7}  ")
    for _, r in df.iterrows():
        for which, col in (("base", "base_T_cws_C"), ("opt", "opt_T_cws_C")):
            t = float(r[col])
            capft, q_avail, plr = capacity_state(Q, t)
            ok = plr <= plr_hi
            short = max(0.0, Q - q_avail)
            print(f"   {str(r['condition'])[:22]:22} {which:>5} {t:>7.2f} "
                  f"{capft:>7.4f} {q_avail:>9.0f} {plr:>7.4f}  "
                  f"{'ok' if ok else 'INFEASIBLE'}")
            rows.append({"condition": r["condition"], "which": which,
                         "T_cws_C": t, "capft": capft, "q_avail_kW": q_avail,
                         "plr_raw": plr, "feasible": bool(ok),
                         "capacity_shortfall_kW": short})

    base = [x for x in rows if x["which"] == "base"]
    opt = [x for x in rows if x["which"] == "opt"]
    nb = sum(not x["feasible"] for x in base)
    no = sum(not x["feasible"] for x in opt)

    print(f"\n   baseline   {nb} of {len(base)} conditions infeasible")
    print(f"   OPTIMISED  {no} of {len(opt)} conditions infeasible")
    print(f"   worst shortfall {max(x['capacity_shortfall_kW'] for x in opt):.0f} kW"
          f" of {Q:.0f} kW duty")

    if no > nb:
        print(f"\n   *** The optimiser moves the plant INTO the infeasible region,")
        print(f"       from {nb} conditions to {no}. Its main energy lever is fan")
        print(f"       speed, and lowering the fan raises condenser water")
        print(f"       temperature -- so it is being rewarded in exactly the")
        print(f"       region where the chiller model under-states its cost.")

    # How wrong is the power, in the region the optimiser chose?
    print(f"\n   POWER ERROR IN THE CLAMPED REGION")
    print(f"   {'T_cws':>7} {'P_biquad':>10} {'dP/dT':>10}   sign")
    prev = None
    for t in (30.0, 31.0, 32.0, 33.0, 34.0, 35.0):
        p, _ = ctl.chiller_power_biquad(Q, t, Q_ref_kw=Q)
        slope = "" if prev is None else f"{p - prev:>10.2f}"
        sign = "" if prev is None else ("rising  ok" if p > prev
                                        else "FALLING -- backwards")
        print(f"   {t:>7.2f} {p:>10.1f} {slope}   {sign}")
        prev = p

    out = {
        "duty_kW": Q,
        "biquad_fitted": {"T_cws_C": list(ctl.CHILLER_TCWS_RANGE),
                          "PLR": list(ctl.CHILLER_PLR_RANGE)},
        "rows": rows,
        "n_infeasible_base": nb, "n_infeasible_opt": no, "n_conditions": len(base),
        "optimiser_moves_into_infeasible": bool(no > nb),
        "finding": ("chiller_power_biquad clamps plr_raw to 1.0 when the machine "
                    "cannot make the duty, so computed power FALLS with rising "
                    "condenser temperature above ~32.5 C. The optimiser's main "
                    "lever (fan speed down -> T_cws up) drives it into that "
                    "region, where the chiller cost that should offset the fan "
                    "saving is under-computed."),
        "recommended_fix": ("Reject operating points with plr_raw > "
                            f"{plr_hi} the same way out-of-range temperatures "
                            "are already rejected. CHILLER_RANGE_LOG['PLR_out'] "
                            "already counts them; nothing reads it."),
        "not_done_here": ("No published result is modified. Enforcing the "
                          "constraint changes the headline annual figures, the "
                          "deck, the figures and a published post, so the "
                          "re-run is the founder's call."),
    }
    (RESULTS / "chiller_feasibility.json").write_text(json.dumps(out, indent=1))
    print(f"\nwritten -> results/chiller_feasibility.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
