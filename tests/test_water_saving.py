"""MILESTONE 1 -- the three optimisation objectives.

WHAT THESE TESTS ARE ALLOWED TO ASSERT, AND WHAT THEY ARE NOT.

The pre-registered V5 gate scored COST_MINIMIZING operation and returned a
4.38 % makeup-water reduction against a 15 % threshold. It failed, it is
reported as a failure, and nothing here revises it.

WATER_PRESERVING and CONSTRAINED_WATER are DIFFERENT OBJECTIVES, not a second
attempt at the same one. A number from either must never be quoted against
that threshold, because a threshold is only meaningful against the experiment
it was written for.

So these tests assert STRUCTURE and DIRECTION -- that the modes are internally
consistent, that they trade in the direction they claim to, that constraints
bind -- plus one pinned magnitude taken from an actual run. There is
deliberately no `assert water_pct >= 12`. A test that demands a result is not
a test, it is an instruction to the model, and this package has spent a month
removing exactly that pattern.
"""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

import chemistry as ch
import controller as ctl

RESULTS = pathlib.Path(__file__).resolve().parent.parent / "results"

# Small grids. These tests check behaviour, not headline numbers, and a fine
# grid would only make them slow.
FAN = np.array([50.0, 70.0, 90.0])
CYCLES = np.array([3.0, 4.0, 5.0])
PH = np.array([7.75, 8.25])


@pytest.fixture(scope="module")
def setup():
    import run_controller as rc
    cal = json.loads((RESULTS / "calibration.json").read_text())
    cond = dict(rc.PLANT)
    cond.update({"T_db": 38.0, "rh": 0.40, "T_wi": 26.0 + 12.0})
    return cond, rc.TSE, rc.TARIFFS, cal["fill_c"], cal["fill_n"]


def _opt(setup, mode, **kw):
    cond, water, tariffs, fc, fn = setup
    return ctl.optimise(cond, water, tariffs, fc, fn, fan_grid=FAN,
                        cycles_grid=CYCLES, ph_grid=PH,
                        optimization_mode=mode, **kw)[0]


# ---------------------------------------------------------------------------
# the identity that makes the shadow price interpretable
# ---------------------------------------------------------------------------

def test_lambda_one_reproduces_cost_minimizing_exactly(setup):
    """A shadow price of 1.0 means "water is worth exactly its tariff", which
    is the cost-minimising problem. If these two ever disagree, the water
    group in the objective has drifted away from the water group in the cost
    function and every lambda would be measuring something unstated."""
    cost = _opt(setup, "COST_MINIMIZING")
    water1 = _opt(setup, "WATER_PRESERVING", lambda_water=1.0)
    assert cost is not None and water1 is not None
    assert water1["cycles"] == cost["cycles"]
    assert water1["fan_pct"] == cost["fan_pct"]
    assert water1["target_ph"] == cost["target_ph"]
    assert water1["cost_per_h"] == pytest.approx(cost["cost_per_h"], rel=1e-12)


def test_the_objective_reduces_to_cost_at_lambda_one(setup):
    _, _, tariffs, _, _ = setup
    r = _opt(setup, "COST_MINIMIZING")
    assert ctl.objective(r, tariffs, "WATER_PRESERVING", 1.0) == pytest.approx(
        r["cost_per_h"], rel=1e-12)
    assert ctl.objective(r, tariffs, "COST_MINIMIZING") == r["cost_per_h"]


def test_a_higher_shadow_price_never_lowers_the_objective(setup):
    """The water group is non-negative, so J must be non-decreasing in
    lambda at a fixed operating point. A sign error here would make the
    optimiser chase water in the wrong direction and would be invisible in
    the headline numbers."""
    _, _, tariffs, _, _ = setup
    r = _opt(setup, "COST_MINIMIZING")
    prev = -np.inf
    for lam in (0.5, 1.0, 2.0, 3.0, 10.0):
        j = ctl.objective(r, tariffs, "WATER_PRESERVING", lam)
        assert j >= prev
        prev = j


# ---------------------------------------------------------------------------
# the trade has to be real in both directions
# ---------------------------------------------------------------------------

def test_water_preserving_buys_water_and_pays_for_it(setup):
    """The whole claim of the mode. It must use no more water than the
    cost-minimising answer, and it must not be free -- if it were strictly
    better on both axes the cost-minimising search would already have found
    it, and one of the two is then broken."""
    cost = _opt(setup, "COST_MINIMIZING")
    water = _opt(setup, "WATER_PRESERVING", lambda_water=5.0)
    assert cost is not None and water is not None

    assert water["makeup_m3_h"] <= cost["makeup_m3_h"] + 1e-9, (
        f"water-preserving used MORE water: {water['makeup_m3_h']:.4f} vs "
        f"{cost['makeup_m3_h']:.4f} m3/h")
    assert water["cost_per_h"] >= cost["cost_per_h"] - 1e-9, (
        "water-preserving came out cheaper than the cost-minimising answer, "
        "which means the cost search missed a feasible point")


def test_constrained_water_respects_its_energy_ceiling(setup):
    cost = _opt(setup, "COST_MINIMIZING")
    for pen in (0.0, 0.02, 0.10):
        r = _opt(setup, "CONSTRAINED_WATER", max_energy_penalty_pct=pen,
                 p_baseline_kw=cost["P_total_kW"])
        if r is None:
            continue
        ceiling = (1.0 + pen) * cost["P_total_kW"]
        assert r["P_total_kW"] <= ceiling * (1 + 1e-9), (
            f"penalty {pen}: drew {r['P_total_kW']:.2f} kW against a ceiling "
            f"of {ceiling:.2f}")
        assert r["energy_ceiling_kW"] == pytest.approx(ceiling)


def test_a_looser_energy_ceiling_can_only_help_water(setup):
    """Monotonicity of a relaxation: widening a constraint set can never make
    the optimum worse on the objective being minimised."""
    cost = _opt(setup, "COST_MINIMIZING")
    prev = np.inf
    for pen in (0.0, 0.05, 0.20):
        r = _opt(setup, "CONSTRAINED_WATER", max_energy_penalty_pct=pen,
                 p_baseline_kw=cost["P_total_kW"])
        if r is None:
            continue
        assert r["makeup_m3_h"] <= prev + 1e-9
        prev = r["makeup_m3_h"]


# ---------------------------------------------------------------------------
# refusing bad inputs, which is how six of this package's defects were caught
# ---------------------------------------------------------------------------

def test_an_unknown_mode_is_refused_by_name(setup):
    with pytest.raises(ValueError, match="unknown optimization_mode"):
        _opt(setup, "MINIMIZE_EVERYTHING")
    with pytest.raises(ValueError, match="unknown optimization_mode"):
        ctl.objective({"cost_per_h": 1.0}, {}, "nonsense")


def test_constrained_water_refuses_to_run_without_a_baseline(setup):
    """A percentage penalty against an undeclared baseline is not a
    constraint, it is a number. Refuse rather than pick one."""
    with pytest.raises(ValueError, match="declared baseline"):
        _opt(setup, "CONSTRAINED_WATER", max_energy_penalty_pct=0.05)
    with pytest.raises(ValueError, match="declared baseline"):
        _opt(setup, "CONSTRAINED_WATER", p_baseline_kw=1500.0)


# ---------------------------------------------------------------------------
# the pre-registered gate must be untouched
# ---------------------------------------------------------------------------

def test_the_default_mode_is_the_one_the_gate_was_scored_on(setup):
    assert ctl.OPTIMIZATION_MODES[0] == "COST_MINIMIZING"
    default = _opt(setup, "COST_MINIMIZING")
    cond, water, tariffs, fc, fn = setup
    unnamed = ctl.optimise(cond, water, tariffs, fc, fn, fan_grid=FAN,
                           cycles_grid=CYCLES, ph_grid=PH)[0]
    assert unnamed["cost_per_h"] == pytest.approx(default["cost_per_h"],
                                                  rel=1e-12)
    assert unnamed["optimization_mode"] == "COST_MINIMIZING"


def test_the_v5_water_gate_still_reads_its_failure(setup):
    """Guards the separation directly: whatever the new modes achieve, the
    artefact the gate is scored from still says 4.38 % and still fails."""
    s = json.loads((RESULTS / "controller_summary.json").read_text())["summary"]
    assert s["water_pct"] == pytest.approx(4.38, abs=0.05)
    assert s["water_pct"] < s["pre_registered"]["makeup_water_reduction_pct_min"]


# ---------------------------------------------------------------------------
# the phosphate programme, as a declared site input
# ---------------------------------------------------------------------------

def test_declaring_a_phosphate_programme_can_only_tighten(setup):
    """Adding a limit can never widen the feasible set, so the ceiling under
    a declared programme must be at or below the undeclared one."""
    water = setup[1]
    base = ch.max_cycles_split(water, 45.0, 32.0,
                               limits=ch.limits_for_programme(None))
    for prog in ("stressed", "standard"):
        c = ch.max_cycles_split(water, 45.0, 32.0,
                                limits=ch.limits_for_programme(prog))
        assert c <= base + 1e-9, f"{prog} gave {c} against undeclared {base}"


def test_the_programme_limits_are_the_published_ones(setup):
    """These are transcribed from IWC-11-77 Table 7 and corroborated by the
    DOE study's two bracketing observations. They are NOT model outputs, and
    in particular are not the 4.40 this engine happens to compute at seven
    cycles -- fitting a limit to the thing it constrains is the failure this
    whole register exists to prevent."""
    assert ch.PHOSPHATE_PROGRAMME["standard"] == pytest.approx(3.18)
    assert ch.PHOSPHATE_PROGRAMME["stressed"] == pytest.approx(5.10)
    assert ch.PHOSPHATE_PROGRAMME["standard"] == ch.PHOSPHATE_SCREEN[
        "typical_inhibited"]
    assert ch.PHOSPHATE_PROGRAMME["stressed"] == ch.PHOSPHATE_SCREEN[
        "stressed_inhibited"]
    with pytest.raises(ValueError, match="unknown phosphate programme"):
        ch.limits_for_programme("aggressive")


def test_an_undeclared_programme_leaves_phosphate_binding_nothing(setup):
    assert "SI_tcp" not in ch.limits_for_programme(None)
    assert ch.limits_for_programme(None) == ch.OPERATING_LIMITS
    assert ch.limits_for_programme("standard")["SI_tcp"] == pytest.approx(3.18)
