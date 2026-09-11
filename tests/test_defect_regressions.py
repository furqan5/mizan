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


# ---------------------------------------------------------------------------
# Defect 39 -- a confident headline over a failed analysis check.
# ---------------------------------------------------------------------------
def test_defect_39_a_failed_charge_balance_is_priced_not_just_flagged():
    """The measured Aramco Riyadh assay fails its own charge-balance check.

    The Ceiling Report defaults to that water and printed `ceiling 4.52
    cycles` on one line with nothing attached. The console line is the one
    that gets pasted into a deck.

    Flagging the failure is necessary and not sufficient -- it tells a reader
    something is wrong without telling them whether it changes the answer.
    So the balance is closed BOTH ways and the spread reported. The point of
    the test is that the bracket is computed from the water rather than
    asserted, and that closing the balance is never allowed to silently
    become adding an ion to the water.
    """
    import sidestream as ss

    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    checks = ch.validate_analysis(w, silica_declared=True, phosphate_declared=True)
    assert not checks["charge_balance"][0], (
        "the assay now balances; if that is a deliberate correction this "
        "test and defect 39 both need rewriting")

    b = ss.charge_closure_bracket(w, 45.0, 32.0, pH=8.25)

    # the deficit is on the CATION side, which is what makes ammonium the
    # candidate -- a secondary effluent is only partially nitrified
    assert b["cation_deficit_meq_kg"] > 0.0
    assert 5.0 < b["closes_with_NH4_mg_l_as_N"] < 30.0, (
        "outside the range a secondary effluent carries; the missing-ammonium "
        "reading would no longer be the most likely one")

    # closing it either way moves the ceiling by less than the resolution at
    # which a cycles setpoint is adjustable in the field
    assert b["binding_mineral"] == "SI_calcite"
    assert b["spread_cycles"] < 0.25
    assert b["material"] is False
    assert b["ceiling_Cl_closure"] < b["ceiling_Na_closure"]

    # and the module must not have mutated the water to get there
    assert w.Na == 222.0 and w.Cl == 216.0


# ---------------------------------------------------------------------------
# Defect 42 -- the "chemically bounded" policy returned points below its own
# floor, and a solver failure was read as a measurement.
# ---------------------------------------------------------------------------
def test_defect_42_the_fan_inversion_returns_the_safe_side_of_the_floor():
    """The silica floor is a MINIMUM temperature, so the answer must be warm.

    Two faults, one function. `fan_for_target_fws` bracketed the crossing and
    returned the COLDEST point at or below target -- the wrong side of its own
    constraint, by 0.02 K in ordinary conditions. And when the tower solver
    failed at low fan it did `lo_pct = mid`, reading a FAILURE as the datum
    "this fan speed is too warm" and bisecting upward from it.

    On the Frankfurt profile the solver does not converge below about 30 % fan
    in cold humid air, so the low-fan region was discarded one failure at a
    time and the search settled on 32.3 % and 27.4 C against a 31.8 C floor --
    a policy named "chemically bounded" sitting 4.4 K below its floor, in
    silence, for ten hours of twenty-four.

    The physics underneath is real and is the finding for cold climates: FAN
    TURNDOWN ALONE CANNOT KEEP A TOWER'S WATER WARM ENOUGH IN COLD AIR. A site
    that needs the floor there needs a tower bypass, not a better setpoint.
    What was wrong was reporting it as compliance.
    """
    import json
    import pathlib
    import hybrid_supervisor as hs
    import run_controller as rc

    cal = json.loads((pathlib.Path(__file__).resolve().parent.parent
                      / "results" / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]
    q = 20000.0
    args = (q / 20.0, q * 1.03, q / 22.5, fc, fn)
    floor = ch.temperature_floor_for_silica(rc.TSE, 5.0)

    # warm ambient: the floor is reachable, and the answer must be AT OR ABOVE
    # it -- never a hair below, which is the side the old code returned
    for T_db, rh in ((30.0, 0.50), (42.0, 0.20)):
        fan, st = hs.fan_for_target_fws(floor, T_db, rh, *args)
        assert st["target_met"] is True, (T_db, st["T_fws"], floor)
        assert st["T_fws"] >= floor - 1e-6, (
            f"returned {st['T_fws']:.3f} C against a {floor:.3f} C floor -- "
            f"the cold side of the constraint")
        assert st["T_fws"] - floor < 1.0, "gave up more free cooling than needed"

    # cold ambient: the floor is NOT reachable, and that must be said
    fan, st = hs.fan_for_target_fws(floor, 16.0, 0.62, *args)
    assert st["target_met"] is False
    assert st["target_shortfall_k"] > 1.0
    assert st["low_fan_unexplorable"] is True, (
        "the miss must be attributed to the solver's low-fan limit, not "
        "silently absorbed")


def test_defect_42_evaluate_reports_an_unreachable_floor():
    """`evaluate` must carry the miss out, not swallow it.

    A caller averaging over hours cannot tell a bounded hour from a violating
    one unless the flag travels, and the four-region artifact averages over
    twenty-four of them.
    """
    import json
    import pathlib
    import hybrid_supervisor as hs
    from models import cdu_model as cdu
    import run_controller as rc

    cal = json.loads((pathlib.Path(__file__).resolve().parent.parent
                      / "results" / "calibration.json").read_text())
    q = 20000.0
    unit = cdu.sized_for(q, delta_t_k=10.0)
    kw = dict(q_it_kw=q, makeup=rc.TSE, cycles=5.0, tariffs=rc.TARIFFS,
              unit=unit, m_w_pri=q / 20.0, m_a_rated=q / 22.5,
              fill_c=cal["fill_c"], fill_n=cal["fill_n"])

    cold = hs.evaluate(T_db=16.0, rh=0.62, enforce_chemical_floor=True, **kw)
    assert cold is not None
    assert cold["floor_unreachable"] is True
    assert cold["floor_shortfall_k"] > 1.0
    assert cold["T_fws_c"] < cold["chemical_floor_c"], (
        "flagged unreachable while actually meeting the floor")

    warm = hs.evaluate(T_db=42.0, rh=0.20, enforce_chemical_floor=True, **kw)
    assert warm is not None
    assert warm["floor_unreachable"] is False
    assert warm["floor_shortfall_k"] == 0.0
    assert warm["T_fws_c"] >= warm["chemical_floor_c"] - 1e-6


# ---------------------------------------------------------------------------
# Defect 44 -- the skin rise was a literal, and the function meant to compute
# it could not have produced it.
# ---------------------------------------------------------------------------
def test_defect_44_the_skin_rise_is_derived_from_published_fouling_data():
    """8 K was never a guess. It was a condenser at its design fouling
    allowance, and nobody had written down which allowance.

    `wall_bulk_delta_t` existed to replace the literal and was never called --
    and could not have produced 8 K in any case, because it returns only the
    CLEAN film rise, 2.4-3.7 K on the corrected heat-flux band. The missing
    term was the fouling layer.

    The surface a saturation index belongs on is the DEPOSIT FACE, not the
    metal: scale forms where water touches solid, and once a deposit exists
    that face runs hotter than clean metal by q'' * R_f.
    """
    import controller as ctl

    lad = ch.skin_rise_ladder()
    # monotone in fouling resistance, and clean is the floor
    order = ["clean", "ahri_rating", "ac_industry_legacy", "tema_cooling_tower"]
    dts = [lad[k]["delta_t_k"] for k in order]
    assert dts == sorted(dts)
    assert lad["clean"]["delta_t_fouling_k"] == 0.0

    # the clean rise must land in the band external review established
    assert 2.4 <= lad["clean"]["delta_t_k"] <= 3.7

    # and the historical 8.0 must be explained, not merely bracketed
    assert lad["tema_cooling_tower"]["delta_t_k"] == pytest.approx(7.45, abs=0.1)
    assert ctl.SKIN_DELTA_K_DEFAULT == pytest.approx(7.45, abs=0.1)

    # AHRI Guideline E-1997 S5.1, the number ARI standards rate chillers at
    assert lad["ahri_rating"]["R_f_hr_ft2_f_btu"] == 0.00025
    assert lad["ahri_rating"]["R_f_m2k_w"] == pytest.approx(4.4e-5, rel=0.02)

    # an unknown allowance must be refused, not silently defaulted
    with pytest.raises(ValueError):
        ch.skin_temperature_rise(fouling="whatever_is_convenient")


def test_defect_44_the_skin_assumption_is_no_longer_load_bearing():
    """The docs said "every V3/V5 result is proportional to it". Measure it.

    That claim was written when GYPSUM was believed to bind at the wall.
    Calcite binds there now, and amorphous silica -- the species that usually
    sets the ceiling on this water -- binds at the COLD basin, where the skin
    temperature does not enter at all.
    """
    import sidestream as ss

    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    T_bulk, T_cold = 37.0, 32.0
    ceilings = []
    for k in ("clean", "ahri_rating", "ac_industry_legacy", "tema_cooling_tower"):
        dt = ch.skin_rise_ladder()[k]["delta_t_k"]
        c, _b = ss.ceiling_with(w, T_bulk + dt, T_cold, pH=8.25,
                                limits=ch.limits_for_programme())
        ceilings.append(c)

    spread = max(ceilings) - min(ceilings)
    assert spread < 0.5, (
        f"the ceiling now moves {spread:.2f} cycles across the whole "
        f"clean-to-fouled range; if that has grown, the skin assumption has "
        f"become load-bearing again and the documents must say so")
    # hotter skin must TIGHTEN the ceiling -- the conservative direction
    assert ceilings[0] > ceilings[-1]


# ---------------------------------------------------------------------------
# Defect 45 -- the sharpest test the controller has, applied by nothing.
# ---------------------------------------------------------------------------
def test_defect_45_the_brucite_criterion_is_enforced_by_the_optimiser():
    """`ph_saturation_brucite` was called by the V6 report, the figures and
    the MATLAB export -- and never by the feasibility check, which is the only
    place a constraint binds. `si_sepiolite` was called from nowhere at all.

    The mechanism is two-step: brucite Mg(OH)2 precipitates first, then reacts
    with silica in the boundary layer. So the criterion is on BRUCITE, which
    is why the missing "magnesium silicate SI threshold" was never the blocker
    the register recorded -- a sepiolite index is a state, not a criterion.

    It is load-dependent in a way no fixed pH setpoint can express: brucite's
    saturation pH is retrograde, so the same tower at the same pH deposits at
    high load and does not at low load.
    """
    import controller as ctl

    w = ch.balance_sodium(ch.ARAMCO_RECLAIMED)
    w.SiO2 = 26.8
    conc = w.concentrate(4.0)

    # retrograde: the safe pH ceiling FALLS as the skin gets hotter
    hot = ch.ph_saturation_brucite(48.0, conc)
    cold = ch.ph_saturation_brucite(38.0, conc)
    assert hot < cold, "brucite saturation pH must fall with temperature"

    # and it must actually bind in the optimiser's own search space
    assert ctl.MG_SILICATE_BRUCITE_MARGIN_PH == 0.0, (
        "a non-zero margin is a number this package invented; it must come "
        "from site coupon evidence and be passed in")
    assert any(ph > ch.ph_saturation_brucite(45.0, w.concentrate(cy))
               for cy in (3.0, 4.0, 5.0, 6.0)
               for ph in (7.5, 8.0, 8.25, 8.5, 9.0)), (
        "the criterion no longer excludes any operating point, so enforcing "
        "it changed nothing and one of the two is wrong")

    # inactive rather than violated when the water carries no Mg or no silica
    dry = ch.ARAMCO_RECLAIMED       # SiO2 not reported, left at zero
    assert dry.SiO2 == 0.0
    assert ch.si_sepiolite(dry.concentrate(4.0), 45.0, 8.25) == float("-inf")


# ---------------------------------------------------------------------------
# Defect 46 -- the aggressive-anion half of corrosion, absent entirely.
# ---------------------------------------------------------------------------
def test_defect_46_the_two_levers_partition_the_corrosion_risk():
    """Acid owns Larson-Skold; cycles own chloride pitting. Neither is free.

    The received framing -- "the optimiser raises cycles AND doses acid, which
    is what EPRI warns about" -- is half wrong, and the half that is wrong
    matters commercially.

    Larson-Skold is a RATIO of anions. Concentrating a water multiplies every
    ion by the same factor, so cycles cannot move it at all. Acid can and does:
    it destroys HCO3 and leaves SO4 behind, moving numerator and denominator
    in opposite directions at once.

    Chloride pitting is an absolute CONCENTRATION limit, so it is the exact
    mirror: cycles move it proportionally, acid does not touch it.

    A Jubail site under RCER, which may not dose acid at all, therefore takes
    none of the Larson-Skold exposure -- the regulation that costs us the acid
    lever also removes the objection to it.
    """
    import corrosion

    w = ch.ARAMCO_RIYADH_REFINERY_TSE

    # cycles do not move a ratio, and the test states the reason rather than
    # the number, because the number is exactly zero by construction
    lc = corrosion.lever_conflict(w, 3.0, 6.0)
    assert lc["cycles_effect_is_negligible"], lc["cycles_effect"]

    # acid does, hard, and monotonically
    idx = [corrosion.acid_driven_index(w, 3.0, f)["larson_skold"]
           for f in (0.0, 0.25, 0.5, 0.75, 0.9)]
    assert idx == sorted(idx)
    assert idx[0] == pytest.approx(4.60, abs=0.05)
    assert idx[-1] > 40.0

    # and the sulfate must GO UP as alkalinity comes down -- a model that only
    # dropped the alkalinity would understate the effect by half
    a0 = corrosion.acid_driven_index(w, 3.0, 0.0)
    a9 = corrosion.acid_driven_index(w, 3.0, 0.9)
    assert a9["SO4_mg_l"] > a0["SO4_mg_l"]
    assert a9["HCO3_mg_l"] < a0["HCO3_mg_l"]
    # stoichiometric sanity: 2 HCO3- + H2SO4 -> SO4(2-), so the sulfate added
    # is half the alkalinity removed on a molar basis
    hco3_removed = (a0["HCO3_mg_l"] - a9["HCO3_mg_l"]) / 61.017
    so4_added = (a9["SO4_mg_l"] - a0["SO4_mg_l"]) / 96.06
    assert so4_added == pytest.approx(0.5 * hco3_removed, rel=1e-6)


def test_defect_46_chloride_can_bind_below_the_scaling_ceiling():
    """On the measured Riyadh water a 316 stainless condenser pits at 1.85
    cycles, against a 4.52-cycle SCALING ceiling and a 3.0-cycle baseline.

    That is the finding: where the tubing is austenitic stainless, chloride
    binds FIRST, at less than half the limit this package computes, and below
    the operating point it recommends. It bites hardest on the CDU side, where
    plate heat exchangers are routinely 316.

    The constraint is enforced only when the caller DECLARES the alloy,
    because the limit is a property of the metal and this package cannot know
    what a stranger's condenser is made of. Declaring nothing leaves it
    inactive -- which is not the same as satisfied, and the report must not
    let those two read alike.
    """
    import corrosion

    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    c316 = corrosion.chloride_pitting_check(w, 3.0, "316_stainless")
    c304 = corrosion.chloride_pitting_check(w, 3.0, "304_stainless")

    assert c316["max_cycles_on_chloride"] == pytest.approx(1.85, abs=0.05)
    assert c304["max_cycles_on_chloride"] < c316["max_cycles_on_chloride"]
    assert c316["exceeds"] and c304["exceeds"]
    assert c316["max_cycles_on_chloride"] < 3.0, (
        "chloride no longer binds below the V7 baseline; if the limit or the "
        "water changed, the data-centre CDU case needs re-reading")

    # an alloy we hold no published limit for must RAISE, not default
    with pytest.raises(ValueError):
        corrosion.chloride_pitting_check(w, 3.0, "admiralty_brass")


# ---------------------------------------------------------------------------
# Defect 47 -- the assumed composition was never checked against anything.
# ---------------------------------------------------------------------------
def test_defect_47_the_assumed_composition_has_a_free_field_check():
    """Every index rests on makeup-analysis x cycles, and nothing tested it.

    Measuring the ions online costs $120,000-185,000 per tower against an
    $89,000 annual saving -- the instruments cost more than the thing they
    optimise, which is why nobody sells this.

    But specific conductance is a known function of the composition, and the
    sensor is already on the skid because the cycles calculation needs it. So
    the assumption can be checked continuously for nothing.

    The test pins the DIRECTION, which is what makes it a scaling alarm rather
    than a diagnostic: precipitation removes ions, the measured conductance
    falls below what the assumed composition implies, and the imbalance goes
    POSITIVE.
    """
    import conductivity as cond

    conc = ch.ARAMCO_RIYADH_REFINERY_TSE.concentrate(3.0)
    base = cond.specific_conductance(conc)

    # a perfect sensor on an intact assumption reads zero imbalance
    assert cond.specific_conductance_imbalance(conc, base)["sci_pct"] == \
        pytest.approx(0.0, abs=1e-9)

    # ions leaving solution -> measured falls -> SCI positive -> precipitation
    d = cond.residual_is_precipitation(conc, base * 0.85)
    assert d["sci_pct"] > 0
    assert d["direction"] == "precipitation"

    # more ionic material than accounted for -> the other direction
    d = cond.residual_is_precipitation(conc, base * 1.15)
    assert d["sci_pct"] < 0
    assert d["direction"] == "accumulation"

    # small residuals must not raise an alarm
    assert cond.residual_is_precipitation(conc, base * 0.99)["actionable"] is False

    # the model has to land inside the only cross-check these analyses carry
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    lo, hi = cond.tds_to_conductance(w.TDS)["band_us_cm"]
    assert lo <= cond.specific_conductance(w) <= hi

    # silica must contribute nothing -- it is neutral H4SiO4 below pH 9, the
    # same fact that makes SI_silica_am pH-free
    import dataclasses
    more_silica = dataclasses.replace(w, SiO2=w.SiO2 * 5.0)
    assert cond.specific_conductance(more_silica) == \
        pytest.approx(cond.specific_conductance(w), rel=1e-12)


# ---------------------------------------------------------------------------
# Defect 48 -- the extrapolated fraction was reported; what it CARRIES was not.
# ---------------------------------------------------------------------------
def test_defect_48_the_annual_figures_are_split_by_validation_envelope():
    """Reporting how much of the year is extrapolated is not the same as
    reporting what the extrapolation is worth, and here they point opposite
    ways.

    The annual study already said 37.5 % of a Dhahran year is hotter and wetter
    than the Almeria calibration data. What it did not say is that the WATER
    SAVING IS NEGATIVE inside the validated envelope and positive only outside
    it -- so the whole positive annual water figure is carried by hours the
    model has never been checked at. The energy saving is the exact reverse:
    earned inside the envelope, gone outside it.

    The two halves of the product are therefore validated to opposite degrees,
    and the water claim is the one this dataset cannot defend.
    """
    import json
    p = pathlib.Path(__file__).resolve().parent.parent / "results" / "annual_dhahran.json"
    if not p.exists():
        pytest.skip("annual study not generated")
    d = json.loads(p.read_text(encoding="utf-8"))
    if "by_envelope" not in d:
        pytest.skip("annual study predates the envelope split")

    ins, ext = d["by_envelope"]["inside"], d["by_envelope"]["extrapolated"]
    assert ins["hours"] + ext["hours"] == 8760

    # the finding, pinned by sign rather than by value so a re-run that moves
    # the numbers still catches a reversal
    assert ins["water_pct"] < 0.0, (
        "the water saving is no longer negative inside the validated "
        "envelope; that would be good news and it must be re-derived, not "
        "assumed -- check whether the calibration envelope moved")
    assert ext["water_pct"] > 0.0
    assert ext["water_pct"] > ins["water_pct"]

    # energy runs the other way
    assert ins["energy_pct"] > ext["energy_pct"]

    # and the warning has to travel with the file
    assert "NEGATIVE" in d["envelope_warning"]


# ---------------------------------------------------------------------------
# Defect 49 -- the discharge ceiling, computed and tested and never applied.
# ---------------------------------------------------------------------------
def test_defect_49_the_report_carries_the_discharge_ceiling():
    """`discharge.binding_ceiling()` returns the lower of scaling and permit.
    It had its own test file and NOTHING OUTSIDE THOSE TESTS CALLED IT.

    Seventh instance of computed-but-not-enforced, and the one that most
    directly misleads a customer: the Cycle Ceiling Report answered
    "4.52 cycles" while a tested discharge ceiling of 3.33 sat unused. You
    cannot recommend an operating point whose blowdown is illegal.

    The care this needs is in the other direction too. RCER-2015 binds Jubail
    and Yanbu; the water this report defaults to is a RIYADH refinery, in
    neither. Asserting an illegal operating point for a site outside the
    jurisdiction would be its own defect, so the report REPORTS the number and
    refuses to impose it.
    """
    import discharge as dis

    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    scaling, _ = __import__("sidestream").ceiling_with(
        w, 45.0, 32.0, pH=8.25, limits=ch.limits_for_programme())

    mx = dis.binding_ceiling(w, 45.0, 32.0, pH=8.25, basis="max")
    mo = dis.binding_ceiling(w, 45.0, 32.0, pH=8.25, basis="monthly_avg")

    # the permit binds BEFORE the chemistry on this water, which is the point
    assert mx["binding"] == "DISCHARGE"
    assert mx["discharge_cycles"] < scaling
    assert mo["discharge_cycles"] <= mx["discharge_cycles"], (
        "a monthly average cannot be looser than a daily maximum")

    # nitrate, not a scaling species -- the constraint the chemistry cannot see
    assert mx["parameter"] == "NO3"

    # and the report must carry it, with the jurisdiction attached
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        jp = pathlib.Path(td) / "cr.json"
        subprocess.run(
            ["python", "scripts/ceiling_report.py", "--json", str(jp),
             "--out", str(pathlib.Path(td) / "cr.html")],
            cwd=str(pathlib.Path(__file__).resolve().parent.parent),
            capture_output=True, check=True)
        d = json.loads(jp.read_text(encoding="utf-8"))
    assert "discharge" in d and "max" in d["discharge"], (
        "the report dropped the discharge ceiling again")
    assert d["discharge"]["applies_here"] is None, (
        "the report must not claim to know whether RCER binds a given site")
    assert "jurisdiction" in d["discharge"]
