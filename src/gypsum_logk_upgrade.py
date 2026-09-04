"""Gypsum log_k: van 't Hoff -> phreeqc.dat analytic expression.

WHY THIS EXISTS
---------------
`chemistry.py` evaluates minerals at the condenser skin because scale forms on
the hottest surface, and the whole two-ceilings result turns on gypsum being the
binding mineral there. But gypsum's log_k was a single-enthalpy van 't Hoff:

    log_k_gypsum(T) = vant_hoff(log_k25 = -4.58, dH = -0.109 kcal)

A single-enthalpy van 't Hoff is MONOTONIC BY CONSTRUCTION. The module's own
comment says gypsum has a "maximum near 35-40 C, weakly retrograde above it" --
a shape that form cannot produce. Measured before the change: strictly
decreasing over 10-80 C, total movement across 25->70 C of only 0.0105 log
units, while the full SI moved ~10x that in the same direction from activity
coefficients alone. Net effect: gypsum looked LESS saturated at the hot skin
than in the bulk, which is the opposite of the story the product tells.

The fix needs no new source. `phreeqc.dat` -- already cited for gypsum's log_k
and delta_h, and already used in analytic form for CALCITE (chemistry.py line
~53) and for carbonic K2 -- supplies an analytic expression for gypsum too:

    Gypsum   -analytic  68.2401  0.0  -3221.51  -25.0627

So this is not a new model. It is the same database, the same treatment calcite
already had, applied to the mineral the product's central claim rests on.

Literature context for the shape (not used numerically, only to say the shape is
real): the gypsum-anhydrite transition in pure water is near 42 C, and gypsum
solubility passes through a maximum in that region rather than falling
monotonically from 0 C.

PRE-REGISTERED PREDICTIONS -- written before running, scored below
-----------------------------------------------------------------
P1  log_k at 25 C moves by < 0.01 log units. Both forms are anchored to the
    same log_k25 = -4.58, so if this fails the arithmetic is wrong.
P2  log_k becomes NON-MONOTONIC over 10-80 C, i.e. it has an interior maximum.
    This is the entire point; if it stays monotonic the change achieved nothing.
P3  log_k(70) - log_k(25) becomes more negative than the van 't Hoff -0.0105,
    by at least a factor of 5.
P4  SI_gypsum vs temperature reverses or flattens: the 25->70 C change, which
    was -0.095 at 6 cycles, ends up ABOVE -0.02 (i.e. flat or rising).
P5  The gypsum wall at an operable condition moves by AT MOST 1 cycle. A change
    to a temperature function should not rewrite the chemistry wholesale; if it
    moves more than that, something else is wrong.

Run:  python src/gypsum_logk_upgrade.py
"""
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402

T_K0 = 273.15

# phreeqc.dat, PHASES block:
#   Gypsum
#       CaSO4:2H2O = Ca+2 + SO4-2 + 2 H2O
#       -log_k   -4.58
#       -delta_h -0.109 kcal
#       -analytic  68.2401  0.0  -3221.51  -25.0627
GYPSUM_ANALYTIC = (68.2401, 0.0, -3221.51, -25.0627, 0.0, 0.0)


def phreeqc_analytic(A, T_c):
    """log_K = A1 + A2*T + A3/T + A4*log10(T) + A5/T^2 + A6*T^2, T in kelvin."""
    T = T_c + T_K0
    a1, a2, a3, a4, a5, a6 = (list(A) + [0.0] * 6)[:6]
    return (a1 + a2 * T + a3 / T + a4 * math.log10(T)
            + a5 / T ** 2 + a6 * T ** 2)


def log_k_gypsum_analytic(T_c):
    return phreeqc_analytic(GYPSUM_ANALYTIC, T_c)


def log_k_gypsum_vant_hoff(T_c):
    """The form that was in use before 4 September 2026."""
    R = 8.314462
    T = T_c + T_K0
    return -4.58 - (-0.109 * 4184.0) / (2.302585 * R) * (1.0 / T - 1.0 / 298.15)


def main():
    passed, failed = [], []

    def score(name, ok, detail):
        (passed if ok else failed).append(f"{name}  {'PASS' if ok else 'FAIL'}  {detail}")

    print("=" * 74)
    print("GYPSUM log_k: van 't Hoff -> phreeqc.dat analytic expression")
    print("=" * 74)

    print("\n  T_C     van't Hoff      analytic     difference")
    for T in (10, 20, 25, 30, 40, 50, 60, 70, 80):
        v = log_k_gypsum_vant_hoff(T)
        a = log_k_gypsum_analytic(T)
        print(f"  {T:4.0f}    {v: .5f}     {a: .5f}    {a - v:+.5f}")

    # P1 -- anchored at 25 C
    d25 = abs(log_k_gypsum_analytic(25.0) - log_k_gypsum_vant_hoff(25.0))
    score("P1 anchored at 25 C", d25 < 0.01, f"|d| = {d25:.5f} log units")

    # P2 -- non-monotonic
    ks = [log_k_gypsum_analytic(T) for T in range(10, 81)]
    ups = [b > a for a, b in zip(ks, ks[1:])]
    non_monotonic = len(set(ups)) > 1
    if non_monotonic:
        turn = 10 + ups.index(False)
        detail = f"maximum near {turn} C"
    else:
        detail = "still monotonic"
    score("P2 has an interior maximum", non_monotonic, detail)

    # P3 -- bigger temperature response
    dv = log_k_gypsum_vant_hoff(70) - log_k_gypsum_vant_hoff(25)
    da = log_k_gypsum_analytic(70) - log_k_gypsum_analytic(25)
    score("P3 response >= 5x van 't Hoff",
          da < 5 * dv, f"van 't Hoff {dv:+.5f} -> analytic {da:+.5f} "
                       f"({da / dv:.1f}x)")

    # P4 / P5 need the full SI, which requires chemistry.py to be switched over.
    using_analytic = abs(chem.log_k_gypsum(70.0) - log_k_gypsum_analytic(70.0)) < 1e-9
    print(f"\nchemistry.log_k_gypsum currently uses the "
          f"{'ANALYTIC' if using_analytic else 'van t HOFF'} form.")

    if using_analytic:
        TSE = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
        print("\nSI_gypsum on the modelled TSE at 6 cycles:")
        print("  T_C    SI_gypsum")
        si = {}
        for T in (25, 30, 40, 50, 60, 70):
            si[T] = chem.saturation_state(TSE.concentrate(6.0), T_c=T)["SI_gypsum"]
            print(f"  {T:4.0f}   {si[T]: .4f}")
        change = si[70] - si[25]
        score("P4 SI flat or rising with T", change > -0.02,
              f"SI(70) - SI(25) = {change:+.4f}, was -0.0949")
    else:
        print("\n  P4/P5 not scored: chemistry.py still on the old form.")

    print("\n" + "-" * 74)
    for line in passed + failed:
        print("  " + line)
    print("-" * 74)
    print(f"  {len(passed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
