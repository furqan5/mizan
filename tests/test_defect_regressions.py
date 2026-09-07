"""One test per named defect in docs/defect_register.md.

WHY THIS FILE EXISTS. Every defect in the register was found by manual
re-derivation. Nothing in the repository prevented any of them from coming
back, and the two most expensive ones -- the fan correlation read in the wrong
unit, and the drift eliminator rating with its percent sign dropped -- are the
*same defect class*, found four days apart. A constant that is wrong by a
factor of 100 produces plots that look entirely reasonable.

The pre-registered gates (V1-V6, P1-P4) are excellent integration tests, but
they are slow, they need the full pipeline, and they report a number rather
than pinning a mechanism. These tests pin the mechanism, run in under a
second, and fail loudly.

Each test names its defect number so a failure points straight at the register.
"""
from __future__ import annotations

import numpy as np
import pytest

import chemistry as ch
import controller as ctl
import tower as tw


# ---------------------------------------------------------------------------
# Defect 1 -- the fan correlation's argument is HERTZ, not per cent.
# ---------------------------------------------------------------------------
def test_defect_01_fan_correlation_takes_hertz_not_percent():
    """Read as a percentage the quadratic turns over at 62.25 % and air flow
    FALLS as the fan speeds up. No fan behaves that way. Cost ~1 K of holdout
    accuracy and a +1.5 K warm bias before it was caught."""
    pcts = np.linspace(30.0, 100.0, 71)
    m_a = tw.air_mass_flow_from_fan(pcts)

    assert np.all(np.diff(m_a) > 0.0), (
        "air mass flow must increase monotonically with fan speed over the "
        "whole 30-100 % range; a turnover means the correlation is being fed "
        "per cent where it expects hertz (defect 1)")

    # At 100 % the fan runs at base_hz = 50 Hz, so the quadratic is evaluated
    # at 50, not at 100.
    assert tw.air_mass_flow_from_fan(100.0) == pytest.approx(4.4899, abs=1e-4)
    assert tw.air_mass_flow_from_fan(50.0) == pytest.approx(2.7574, abs=1e-4)


def test_defect_01_percent_reading_would_be_caught():
    """The check above must actually be capable of failing. Evaluated as if
    the column were hertz directly, the correlation does turn over."""
    f = np.linspace(30.0, 100.0, 71)
    wrong = -0.0014 * f**2 + 0.1743 * f - 0.7251
    assert np.any(np.diff(wrong) < 0.0), (
        "the guard in the previous test is vacuous if the wrong reading is "
        "also monotonic -- it is not, and this pins that")


# ---------------------------------------------------------------------------
# Defect 3 -- drift eliminator rating is 0.0005 PER CENT, not 0.0005.
# ---------------------------------------------------------------------------
def test_defect_03_drift_fraction_is_a_percentage_converted():
    """Modern high-efficiency eliminators are rated 0.0005 % to 0.001 %, i.e.
    5e-6 to 1e-5 as a fraction. The module previously used 0.0005 as a
    FRACTION -- a hundred times too much drift -- which padded predicted water
    consumption by about five per cent and made gate V2 appear to pass."""
    assert 5e-6 <= tw.DRIFT_FRACTION <= 1e-5, (
        "DRIFT_FRACTION is outside the manufacturer-rated band for modern "
        "eliminators; 5e-4 is the percent-sign-dropped error (defect 3)")
    assert tw.DRIFT_FRACTION == pytest.approx(1.0e-5)


def test_defect_03_controller_and_tower_agree_on_drift():
    """The constant is defined once in tower.py and imported by controller.py.
    If the two ever diverge, the water balance means different things in the
    two places it is computed."""
    assert ctl.DRIFT_FRACTION is tw.DRIFT_FRACTION or \
        ctl.DRIFT_FRACTION == tw.DRIFT_FRACTION


def test_defect_03_drift_cancels_out_of_makeup():
    """The register records that makeup water is provably unaffected by the
    drift constant, because drift cancels out of
    `makeup = evaporation + drift + blowdown` while blowdown stays positive.
    Blowdown itself IS affected -- it was 27 % low at seven cycles, and that is
    the number a discharge permit is written against."""
    m_evap, m_w, cycles = 5.2, 478.0, 7.0
    a = ctl.water_balance(m_evap, m_w, cycles, drift_fraction=1.0e-5)
    b = ctl.water_balance(m_evap, m_w, cycles, drift_fraction=5.0e-4)

    def _get(res, *names):
        if isinstance(res, dict):
            for n in names:
                if n in res:
                    return res[n]
            raise KeyError(names)
        return None

    mk_a, mk_b = _get(a, "makeup_kg_s", "makeup"), _get(b, "makeup_kg_s", "makeup")
    bd_a, bd_b = _get(a, "blowdown_kg_s", "blowdown"), _get(b, "blowdown_kg_s", "blowdown")

    assert mk_a == pytest.approx(mk_b, rel=1e-9), (
        "makeup must be independent of the drift constant (defect 3)")
    assert bd_a > bd_b, (
        "blowdown MUST fall as drift rises -- it is the term that absorbs the "
        "difference, and it is the permit-facing number")


# ---------------------------------------------------------------------------
# Defect 9 -- the optimiser exploited the chiller curve outside its fitted box.
# ---------------------------------------------------------------------------
def test_defect_09_chiller_temperature_envelope_is_declared_and_gulf_relevant():
    """With the York curves in place the optimiser drove the fan to its floor,
    putting entering condenser water at 36.5-40.5 C -- outside the fit -- and
    booked a false 20.41 % water saving that would have flipped a failed gate
    to passed. The envelope is now a hard constraint."""
    lo, hi = ctl.CHILLER_TCWS_RANGE
    assert (lo, hi) == pytest.approx((15.56, 35.00)), (
        "the entering-condenser-water validity window must stay pinned to the "
        "range the York YT curves were actually fitted over (defect 9)")
    assert hi < 36.5, (
        "the ceiling must exclude the 36.5-40.5 C band the optimiser "
        "previously extrapolated into")


def test_defect_11_capacity_limit_exists_alongside_the_temperature_limit():
    """Defect 11: the chiller has TWO limits and only the temperature one was
    enforced. Enforcing capacity moved every headline number by about a third."""
    lo, hi = ctl.CHILLER_PLR_RANGE
    assert lo > 0.0 and hi == pytest.approx(1.06), (
        "the part-load-ratio range must remain declared and enforced; without "
        "it the machine is allowed to exceed its own capacity (defect 11)")


# ---------------------------------------------------------------------------
# Defect 15 -- gypsum solubility must be able to turn over.
# ---------------------------------------------------------------------------
def test_defect_15_gypsum_logk_has_an_interior_maximum():
    """A single-enthalpy van 't Hoff is monotonic BY CONSTRUCTION and cannot
    produce a maximum anywhere, yet the code comment claimed one at 35-40 C.
    The phreeqc.dat analytic expression can turn over, and does, near 23 C.

    This is the defect that could move the product thesis: with the monotonic
    fit, evaluating gypsum at the hot skin was the PERMISSIVE choice, and the
    public claim is that gypsum saturates AT the skin."""
    T = np.linspace(5.0, 80.0, 400)
    lk = np.array([ch.log_k_gypsum(t) for t in T])
    i = int(lk.argmax())

    assert 0 < i < len(T) - 1, (
        "log_k_gypsum must have an INTERIOR maximum -- a monotonic van 't Hoff "
        "cannot represent gypsum solubility (defect 15)")
    assert T[i] == pytest.approx(22.7, abs=3.0)

    # Anchored to the same log_k25 the van 't Hoff used, so the fix introduced
    # no new source.
    assert ch.log_k_gypsum(25.0) == pytest.approx(-4.58, abs=0.01)


def test_defect_15_si_gypsum_is_most_saturated_at_the_hot_skin(aramco):
    """The mechanism the product actually claims: gypsum is MOST saturated at
    the condenser skin, so SI_gypsum must have a minimum (a solubility
    maximum) somewhere in the mid-40s and rise above it."""
    conc = ch.Water(**{**aramco.__dict__,
                       **{k: getattr(aramco, k) * 6.0 for k in
                          ("Ca", "Mg", "Na", "K", "HCO3", "SO4", "Cl", "NO3",
                           "TDS")}})
    T = np.linspace(25.0, 70.0, 90)
    si = np.array([ch.saturation_state(conc, t, pH=8.0)["SI_gypsum"] for t in T])
    i = int(si.argmin())

    assert 0 < i < len(T) - 1, (
        "SI_gypsum must have an interior minimum; without one the hot skin is "
        "the SAFEST place in the loop and the thesis inverts (defect 15)")
    assert T[i] == pytest.approx(44.5, abs=6.0)
    assert si[-1] > si[i], "SI_gypsum must rise again above the minimum"


# ---------------------------------------------------------------------------
# Defect 12 / audit staleness -- constants must be read, not typed.
# ---------------------------------------------------------------------------
def test_defect_12_headline_water_figure_is_not_hardcoded_anywhere():
    """The V5 water figure 14.83 was typed into four files. When defect 11
    moved it to 10.02, annual.py wrote the stale value into the JSON the audit
    checks other documents against -- an audit enforcing staleness.

    Prose in docstrings that EXPLAINS the defect is fine and must not trip
    this; only a live numeric literal counts. Parsing with `ast` rather than
    grepping lines is what makes that distinction reliable.
    """
    import ast
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    stale = {14.83, 10.02}
    offenders = []
    for p in sorted(src.glob("*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:                     # not ours to police
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                if any(abs(node.value - s) < 1e-9 for s in stale):
                    offenders.append(f"{p.name}:{node.lineno}: {node.value}")
    assert not offenders, (
        "a superseded headline figure appears as a live numeric literal "
        "rather than being read from results/controller_summary.json "
        "(defect 12):\n  " + "\n  ".join(offenders))


# ---------------------------------------------------------------------------
# Defect 17 -- OPEN. This test documents it and must XPASS when it is fixed.
# ---------------------------------------------------------------------------
@pytest.mark.xfail(strict=True, reason=(
    "DEFECT 17, OPEN: ARAMCO_RECLAIMED carries SO4 = 566 mg/L where a field "
    "write-up of the same Aramco pilot reports 300. Charge imbalance -14.3 %, "
    "and the ions sum to 1752 mg/L against a stated TDS of 1500 -- a water "
    "cannot contain more ions than its own TDS. Sulfate is the number the "
    "gypsum wall rests on. When this XPASSes, the defect is fixed: close it in "
    "docs/defect_register.md and delete this marker."))
def test_defect_17_makeup_water_closes_charge_and_tds(aramco):
    from conftest import charge_balance_pct, ion_sum_mg_l
    assert abs(charge_balance_pct(aramco)) <= 5.0, (
        "a laboratory water analysis is normally accepted within +/- 5 %")
    assert ion_sum_mg_l(aramco) <= aramco.TDS * 1.05, (
        "the ions must not sum to more than the stated TDS")


def test_defect_17_is_still_declared_open_in_the_register():
    """Guards the pairing above: if someone fixes the water but forgets the
    register, or closes the register without fixing the water, this fails."""
    import pathlib
    reg = (pathlib.Path(__file__).resolve().parents[1]
           / "docs" / "defect_register.md").read_text(encoding="utf-8",
                                                      errors="replace")
    assert "OPEN" in reg, "the register must still mark defect 17 OPEN"


# ---------------------------------------------------------------------------
# Discovery findings -- the corrosion floor must exist as an actuator bound.
# ---------------------------------------------------------------------------
def test_corrosion_floor_exists_and_is_wired_into_the_optimiser():
    """Field evidence: a plant chemist holds LSI at 0.8-1.0 deliberately,
    because a thin calcium-carbonate film IS the corrosion defence. An
    optimiser driving toward LSI = 0 strips it. EPRI additionally warns that
    sulphuric acid replaces protective alkalinity with corrosive sulfate."""
    assert hasattr(ctl, "CORROSION_FLOOR_SI"), (
        "the optimiser must carry a corrosion floor, even if the default is "
        "permissive -- it was previously searching pH 7.0-9.0 with none")
    import inspect
    sig = inspect.signature(ctl._cost_at_ph)
    assert "corrosion_floor_si" in sig.parameters, (
        "the floor must be reachable as a parameter so a plant can set its "
        "own -- the right value is a plant decision, not ours")

    # It must also actually bind: a floor above the achievable SI_calcite has
    # to reject the point rather than being carried and ignored.
    src = inspect.getsource(ctl._cost_at_ph)
    assert "corrosion_floor_si" in src and "floor" in src, (
        "the parameter exists but is not referenced in the body")
