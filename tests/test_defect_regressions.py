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

import pathlib

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


def test_defect_15_si_gypsum_can_turn_over_with_temperature(aramco):
    """Defect 15's real content: the temperature function must be ABLE to turn
    over. A single-enthalpy van 't Hoff is monotonic by construction and could
    not represent gypsum at all.

    Renamed 10 Sep 2026. It was called `..._is_most_saturated_at_the_hot_skin`,
    which defect 23 showed is false on this water: the interior MINIMUM means
    the skin is the LEAST saturated point, not the most. The old name asserted
    the opposite of what the test measures."""
    conc = ch.Water(**{**aramco.__dict__,
                       **{k: getattr(aramco, k) * 6.0 for k in
                          ("Ca", "Mg", "Na", "K", "HCO3", "SO4", "Cl", "NO3",
                           "TDS")}})
    T = np.linspace(25.0, 80.0, 120)
    si = np.array([ch.saturation_state(conc, t, pH=8.0)["SI_gypsum"]
                   for t in T])
    i = int(si.argmin())
    assert 0 < i < len(T) - 1, (
        "SI_gypsum must have an INTERIOR extremum; a monotonic van 't Hoff "
        "cannot represent gypsum solubility (defect 15)")
    assert si[-1] > si[i], "SI_gypsum must rise again above the minimum"
    # Defect 23: the minimum sits ABOVE the condenser skin band (38-48 C),
    # so the skin is in the trough. After defect 24 it moved further out.
    assert T[i] > 48.0, (
        f"the SI_gypsum minimum is at {T[i]:.1f} C; defect 23 records that it "
        "lies above the skin band, which is why routing gypsum to the skin is "
        "the permissive choice on this water")


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
# Defect 17 -- RESOLVED 10 Sep 2026, as a category error rather than a number.
# ---------------------------------------------------------------------------
def test_defect_17_the_source_table_is_marginals_not_an_analysis():
    """The xfail that used to live here asserted `ARAMCO_RECLAIMED` would one
    day close its charge balance and TDS. It never will, and that is not a
    fault in the transcription.

    Badruzzaman et al. (2022) Table 1 reports "Reclaimed Min | Ave | Max" as
    INDEPENDENT PER-ION MARGINALS over a monitoring campaign. The Max column's
    ions sum to 3557 mg/L against its own stated TDS of 1800 -- no sample
    contains twice its own dissolved solids. The Raw Groundwater column, which
    IS a sample, closes cleanly, so the laboratory method is sound.

    A permanent xfail is the wrong shape: an xfail should mark something
    fixable. The real defect was that the CONTROLLER ran on a column that is
    not a water, and that is fixed."""
    from conftest import charge_balance_pct, ion_sum_mg_l
    w = ch.ARAMCO_RECLAIMED
    assert abs(charge_balance_pct(w)) > 5.0
    assert ion_sum_mg_l(w) > w.TDS
    # And the Max column, which is what proves the diagnosis.
    mx = ch.Water(name="Table 1 Reclaimed Max", Na=840.0, K=57.0, Ca=99.0,
                  Mg=74.0, Cl=1233.0, SO4=1110.0, HCO3=131.0, NO3=13.0,
                  SiO2=0.0, pH=7.4, TDS=1800.0)
    assert sum(getattr(mx, s) for s in ch.SPECIES) > 1.9 * mx.TDS


def test_defect_17_the_controller_runs_on_a_water_that_closes():
    """The resolution: a coherent analysis of the SAME pilot exists (Water
    Technology, Jan 2021) and the controller runs on it."""
    import run_controller as rc
    from conftest import charge_balance_pct, ion_sum_mg_l
    assert abs(charge_balance_pct(rc.TSE)) <= 5.0
    assert ion_sum_mg_l(rc.TSE) <= rc.TSE.TDS * 1.05


def test_the_register_declares_its_open_count_honestly():
    """Guards both directions. The register must state an open count, and it
    must match its own OPEN rows -- an honest empty register passes, an honest
    non-empty one passes, and a table with an undeclared OPEN row fails.

    This is defect 12's lesson: the audit once required the literal string
    "Open defects: none", which passed for an honest empty register and failed
    for an honest non-empty one, quietly rewarding concealment."""
    import re as _re
    reg = (pathlib.Path(__file__).resolve().parents[1]
           / "docs" / "defect_register.md").read_text(encoding="utf-8",
                                                      errors="replace")
    n_open = len(_re.findall(r"\|\s*\*\*OPEN\*\*\s*\|", reg))
    m = _re.search(r"\*\*Open defects:\s*([A-Za-z]+|\d+)", reg)
    assert m, "the register must declare an open-defect count"
    words = {"none": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    tok = m.group(1).lower()
    declared = int(tok) if tok.isdigit() else words.get(tok)
    assert declared == n_open, (
        f"register declares {declared} open, table shows {n_open}")


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


def test_defect_36_a_break_even_is_checked_against_a_real_costed_system():
    """DEFECT 36. `sidestream.py` returned a break-even and nothing compared
    it to what treatment actually costs, so the module recommended capital
    that cannot pay back on water value -- and the Ceiling Report printed
    those recommendations to a customer.

    The benchmark is a costed engineering study: a precipitation softener
    plus media filtration and WAC polishing, 1 MGD of cooling tower blowdown,
    $25,440,000 installed and $2,793,000/yr in chemicals for 1.38 Mm3/yr.

    Every technology in the module must be recorded as NOT paying at Gulf
    water tariffs, because that is the finding.
    """
    import sidestream as ss
    import run_controller as rc

    real = ss.real_cost_per_m3()
    assert real["chemicals_per_m3"] == pytest.approx(2.02, abs=0.05)
    assert real["total_per_m3"] == pytest.approx(2.94, abs=0.05)

    surveyed = [t for t in ss.survey(rc.TSE, 4.2, rc.TARIFFS, 45.0, 32.0,
                                     baseline_cycles=3.0, pH=8.25)
                if t["raises_ceiling"]]
    assert surveyed, "the survey must return something to check"
    for t in surveyed:
        c = ss.passes_cost_reality_check(t["break_even_per_m3"])
        assert not c["pays"], (
            f"{t['technology']} now claims to pay; if that is real it is a "
            f"finding, and this test must be rewritten rather than deleted")
        assert c["shortfall_ratio"] > 3.0, t["technology"]


def test_defect_36_the_measured_silica_removal_replaced_an_assumption():
    """The same study reports 176 -> 18 mg/L across the softening train."""
    import sidestream as ss
    b = ss.REAL_COST_BENCHMARK
    assert b["silica_removed_pct"] == pytest.approx(89.8, abs=0.1)
    assert 100.0 * (1 - 18.0 / 176.0) == pytest.approx(b["silica_removed_pct"],
                                                       abs=0.1)


def test_defect_37_the_diurnal_margin_is_enforced_not_merely_reported():
    """DEFECT 37, and the fourth instance of one pattern.

    `diurnal_silica_margin()` was computed, documented, and agreed with an
    independent Modelica simulation to better than half a percentage point --
    and no limit set used it. The optimiser pushed cycles against a ceiling
    that holds only at mean basin temperature, which the simulation shows is
    supersaturated for 11.8 hours of every 24.

    Same shape as defect 11 (chiller capacity logged, not enforced), defect 26
    (Davies validity computed, not enforced) and defect 31 (cache key).
    """
    import chemistry as ch
    import sidestream as ss
    import run_controller as rc

    plain = ch.limits_for_programme()
    marg = ch.limits_with_diurnal_margin(30.0, 5.0)

    assert plain["SI_silica_am"] == 0.0
    assert marg["SI_silica_am"] < plain["SI_silica_am"], (
        "the margin must LOWER the silica limit, or it is not a margin")
    assert marg["SI_silica_am"] == pytest.approx(-0.0434, abs=0.002)

    # and it must actually cost cycles, or enforcing it changed nothing
    c_plain, _ = ss.ceiling_with(rc.TSE, 45.0, 32.0, pH=8.25, limits=plain)
    c_marg, _ = ss.ceiling_with(rc.TSE, 45.0, 32.0, pH=8.25, limits=marg)
    assert c_marg < c_plain - 0.25, (
        f"margin cost only {c_plain - c_marg:.3f} cycles; if that is right "
        f"the margin is immaterial and this test should say so")
    assert c_marg == pytest.approx(4.55, abs=0.1)

    # the other limits must be untouched -- this is a silica correction only
    for k in ("SI_calcite", "SI_gypsum"):
        assert marg[k] == plain[k]


# ---------------------------------------------------------------------------
# Defect 38 -- the silica index has no pH term, and was silently wrong above
# pH 9.
# ---------------------------------------------------------------------------
def test_defect_38_silica_index_declares_its_pH_range():
    """SI_silica_am is pH-free. That is right below pH 9 and wrong above it.

    SiO2(a) + 2H2O = H4SiO4 produces a NEUTRAL species, so below about pH 9
    the saturation of amorphous silica really is pH-independent. That fact is
    load-bearing across this package: it is why acid buys cycles against
    calcite and buys nothing against silica.

    Above pH 9 H4SiO4 deprotonates to H3SiO4- and total solubility climbs.
    The industry uses exactly that -- Aquatech's HERO process runs the loop
    alkaline and reports silica above 1,600 ppm in the reject, an order of
    magnitude past where this model calls the water supersaturated. The engine
    still returns a number there. What it must not do is return it silently.
    """
    conc = ch.ARAMCO_RIYADH_REFINERY_TSE.concentrate(3.0)

    # the index itself does not move with pH, anywhere -- that is the model
    lo = ch.saturation_state(conc, 30.0, pH=7.5)["SI_silica_am"]
    hi = ch.saturation_state(conc, 30.0, pH=10.5)["SI_silica_am"]
    assert lo == pytest.approx(hi, abs=1e-12), (
        "SI_silica_am acquired a pH term; if that is deliberate this test "
        "and the acid-cannot-buy-silica claim both need rewriting")

    # but the flag does
    assert ch.saturation_state(conc, 30.0, pH=8.25)["silica_index_valid"] is True
    assert ch.saturation_state(conc, 30.0, pH=9.0)["silica_index_valid"] is True
    assert ch.saturation_state(conc, 30.0, pH=9.6)["silica_index_valid"] is False

    # and it survives the split, which is the path the ceiling report uses.
    # Silica is evaluated COLD, so the cold pH is the one that decides.
    sp = ch.saturation_state_split(conc, 45.0, 30.0, pH_hot=8.0, pH_cold=10.0)
    assert sp["silica_index_valid"] is False

    # the flag must not leak into the SI_ namespace -- ceiling_report.py
    # selects on that prefix and would format a bool as a saturation index
    assert all(isinstance(v, float) for k, v in sp.items()
               if k.startswith("SI_") and not k.endswith("_at"))
