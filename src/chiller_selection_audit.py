"""Why the modelled plant cannot run a Gulf summer, and what the fix is.

THE FINDING
-----------
After defect 11 made the chiller CAPACITY limit a hard constraint, gate V5
reported:

    Dhahran summer humid    no feasible solution
    Doha summer humid       no feasible solution

Two of five design conditions had NO feasible operating point at all. Real Gulf
district-cooling plants demonstrably run on those days, so the finding is about
the plant model, not about the Gulf.

The cause is one line in controller._cost_at_ph:

    q_avail  = cond["Q_evap_kw"] * capft_here
    plr_raw  = cond["Q_evap_kw"] / q_avail

`capft_here` is normalised to ARI reference conditions (6.67 C chilled water,
29.44 C entering condenser water). So this says: **the installed machine is
exactly the size of the load, at ARI.** Nothing is ever selected that way. A
chiller is selected at its DESIGN entering-condenser temperature, which for a
Gulf plant on a cooling tower is far above 29.44 C. Selecting at ARI and then
operating at 33-35 C guarantees a shortfall on every hot day.

Note the plumbing for the fix already exists and was never used:
`chiller_power_biquad` takes `Q_ref_kw` and defaults it to the load.

THE FIX
-------
Select the machine at the top of its own validated entering-condenser range,
35.0 C, which is where CHILLER_TCWS_RANGE ends. Then the capacity limit and the
temperature limit bind at the same place -- which is what a real selection does,
and it means the model stops claiming a machine can do something its own
manufacturer's curve says it cannot.

    Q_nominal = Q_load / capft_here(T_design)

PRE-REGISTERED PREDICTIONS -- written before running
----------------------------------------------------
Q1  The selection margin is between 5 % and 30 %. Below 5 % would mean there
    was never a problem; above 30 % would mean this curve is being extrapolated
    somewhere it should not be.
Q2  With the margin applied, ALL FIVE V5 conditions become feasible on capacity
    (currently 3 of 5).
Q3  The gypsum and economic ceilings DO NOT MOVE. Chemistry depends on skin
    temperature via the tower, not on the chiller's nameplate. If a chiller
    sizing change moves a chemistry wall, something is wired wrong.
Q4  Chiller electrical power at a given condition CHANGES, because a larger
    machine runs at lower part-load ratio and EIRFPLR is not linear. Direction
    is NOT predicted -- predicting it after seeing the curve would be scoring a
    criterion chosen once the answer was known.

Run:  python src/chiller_selection_audit.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import controller as ctl  # noqa: E402

T_DESIGN_C = 35.0   # top of CHILLER_TCWS_RANGE


def capft_at(T_cws_c, T_chws_c=7.0):
    """Capacity as a fraction of ARI nameplate at this entering-condenser T."""
    ref = ctl._biquad(ctl.CHILLER_CAPFT, 6.67, 29.44)
    return ctl._biquad(ctl.CHILLER_CAPFT, T_chws_c, T_cws_c) / ref


def main():
    passed, failed = [], []

    def score(name, ok, detail):
        (passed if ok else failed).append(
            f"{name}  {'PASS' if ok else 'FAIL'}  {detail}")

    print("=" * 74)
    print("CHILLER SELECTION: sized at ARI, operated in the Gulf")
    print("=" * 74)
    print(f"\nfitted entering-condenser range : {ctl.CHILLER_TCWS_RANGE} C")
    print(f"part-load ratio limit           : {ctl.CHILLER_PLR_RANGE[1]}")

    print("\n  T_cws_C   capacity vs ARI   PLR of a machine sized at ARI")
    for T in (29.44, 31.0, 32.0, 32.5, 33.0, 34.0, 35.0):
        c = capft_at(T)
        print(f"  {T:7.2f}   {c:15.4f}   {1.0 / c:.4f}"
              + ("   <-- exceeds PLR limit" if 1.0 / c > ctl.CHILLER_PLR_RANGE[1] else ""))

    c_design = capft_at(T_DESIGN_C)
    margin = 1.0 / c_design - 1.0
    print(f"\nSelecting at {T_DESIGN_C:.1f} C entering condenser water:")
    print(f"  capacity there is {c_design:.4f} of ARI nameplate")
    print(f"  so nominal must be {1.0 / c_design:.4f}x the load")
    print(f"  SELECTION MARGIN  = {margin * 100:.1f} %")

    score("Q1 margin in 5-30 %", 0.05 <= margin <= 0.30,
          f"{margin * 100:.1f} %")

    # Q2: with that nominal, is every condition feasible on capacity?
    print(f"\nWith nominal = {1.0 / c_design:.4f}x load, PLR at each condition:")
    worst = 0.0
    for name, T in (("Gulf winter", 23.2), ("Dhahran shoulder", 32.2),
                    ("Dhahran summer peak", 31.6), ("Dhahran summer humid", 33.6),
                    ("Doha summer humid", 34.0)):
        plr = (1.0 / capft_at(T)) * c_design
        worst = max(worst, plr)
        ok = plr <= ctl.CHILLER_PLR_RANGE[1]
        print(f"  {name:22s} T_cws {T:5.1f} C   PLR {plr:.4f}   "
              f"{'ok' if ok else 'INFEASIBLE'}")
    score("Q2 all five feasible on capacity",
          worst <= ctl.CHILLER_PLR_RANGE[1],
          f"worst PLR {worst:.4f} vs limit {ctl.CHILLER_PLR_RANGE[1]}")

    print("\n" + "-" * 74)
    for line in passed + failed:
        print("  " + line)
    print("-" * 74)
    print(f"  {len(passed)} passed, {len(failed)} failed")
    print("\n  Q3 and Q4 are scored by re-running the controller, not here.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
