"""The Modelica basin model against its own analytic solution.

An agreement gate, in the same spirit as the independent reimplementation used
elsewhere in this project: OpenModelica integrates the ODE numerically with
DASSL, and this file solves it in closed form. If they disagree, one of them is
wrong and the disagreement is the finding.

The model itself is modelica/TowerBasin.mo; the stored result is
results/basin_res.csv. Regenerate with:

    omc modelica/run_basin.mos
"""
import math
import pathlib
import pytest

RESULTS = pathlib.Path(__file__).resolve().parent.parent / "results"
CSV = RESULTS / "basin_res.csv"

V, E, D, C0, C1 = 50000.0, 4.2, 0.00478, 3.0, 5.0
T_STEP = 3600.0


def _analytic(t):
    """c(t)/c_m for the step, in closed form."""
    B = E / (C1 - 1.0)
    tau = V / (B + D)
    c_ss = (E + B + D) / (B + D)
    if t <= T_STEP:
        return C0
    return c_ss + (C0 - c_ss) * math.exp(-(t - T_STEP) / tau)


def _load():
    if not CSV.exists():
        pytest.skip("results/basin_res.csv not present; run the Modelica model")
    import csv
    with CSV.open() as f:
        rows = list(csv.DictReader(f))
    return [(float(r["time"]), float(r["cycles"])) for r in rows]


def test_modelica_matches_the_closed_form_solution():
    rows = _load()
    worst = max(abs(cy - _analytic(t)) for t, cy in rows)
    assert worst < 1e-3, f"worst disagreement {worst:.2e} cycles"


def test_the_basin_time_constant_is_thirteen_hours():
    """The number that matters, and the reason it matters.

    tau = V/(B+D) -- the turnover on NON-evaporative losses only, because
    evaporation removes water and leaves the salt behind. At a 50 m3 basin
    and five cycles that is 13.2 h, so 95 % settling takes about 40 h.
    """
    B = E / (C1 - 1.0)
    tau_h = V / (B + D) / 3600.0
    assert tau_h == pytest.approx(13.2, abs=0.1)
    assert 3 * tau_h == pytest.approx(39.5, abs=0.5)


def test_cycles_cannot_be_floated_on_a_diurnal_cycle():
    """Independent confirmation of a hypothesis already falsified on other
    grounds.

    The steady-state work found that floating the cycles target day-to-night
    bought nothing, because cooling loosens the retrograde limits at the skin
    and tightens the prograde one at the basin, and on this water they cancel.

    This is a SECOND and unrelated reason: the basin physically cannot follow.
    Over a 12 h Gulf diurnal half-cycle it completes only about 60 % of a
    commanded step, so a controller reversing the setpoint every twelve hours
    never reaches either target.

    The constructive consequence is a control-architecture rule: fan speed is
    a fast variable and cycles is a slow one. Cycles belong on a seasonal
    schedule, not a diurnal one.
    """
    frac = (_analytic(T_STEP + 12 * 3600.0) - C0) / (_analytic(1e9) - C0)
    assert 0.55 < frac < 0.65, frac


def test_drift_keeps_the_steady_state_just_below_the_setpoint():
    """B = E/(C-1) ignores drift, so the achieved cycles land slightly low.
    Small, correct, and worth pinning so nobody 'fixes' it into an error."""
    assert _analytic(1e9) == pytest.approx(4.982, abs=0.002)
    assert _analytic(1e9) < C1


# ===========================================================================
# TowerSilicaDynamics -- the limit moves faster than the state can follow
# ===========================================================================

SILICA_CSV = RESULTS / "silica_res.csv"
T_MEAN, T_AMP, C_M = 30.0, 5.0, 18.0


def _load_silica():
    if not SILICA_CSV.exists():
        pytest.skip("results/silica_res.csv not present; run the Modelica model")
    import csv
    with SILICA_CSV.open() as f:
        rows = [r for r in csv.DictReader(f)]
    # periodic steady state only: after one week
    return [r for r in rows if float(r["time"]) >= 168 * 3600]


def test_the_silica_limit_swings_and_the_concentration_does_not():
    """The two-timescale collision, measured.

    Amorphous silica is prograde, so the basin cooling overnight lowers the
    LIMIT. The basin concentration can only move via blowdown, and that has a
    thirteen-hour time constant against a twelve-hour forcing. The limit wins
    by three orders of magnitude.
    """
    rows = _load_silica()
    s = [float(r["S_sat"]) for r in rows]
    c = [float(r["c"]) for r in rows]
    span_limit = max(s) - min(s)
    span_state = max(c) - min(c)
    assert span_limit == pytest.approx(25.5, abs=1.0), span_limit
    assert span_state < 0.5, span_state
    assert span_limit / max(span_state, 1e-9) > 100.0


def test_a_fixed_setpoint_is_supersaturated_for_half_of_every_day():
    """THE PRODUCT REQUIREMENT.

    Blowdown fixed at the value that holds saturation at the MEAN basin
    temperature -- exactly what a conductivity controller with a fixed
    setpoint does -- leaves the basin supersaturated for about twelve hours
    in every twenty-four, by up to 10.5 %.
    """
    rows = _load_silica()
    sr = [float(r["SR"]) for r in rows]
    assert max(sr) == pytest.approx(1.105, abs=0.01)
    assert min(sr) == pytest.approx(0.908, abs=0.01)
    frac = sum(1 for x in sr if x > 1.0) / len(sr)
    assert 0.45 < frac < 0.55, f"supersaturated {24*frac:.1f} h/day"


def test_the_python_margin_agrees_with_the_modelica_simulation():
    """An agreement gate across two independent implementations.

    chemistry.diurnal_silica_margin() computes the discount analytically from
    the van 't Hoff expression; the Modelica model integrates the basin ODE
    with a diurnal temperature and reports the excursion it actually reaches.
    They must agree.
    """
    import chemistry as ch
    rows = _load_silica()
    measured = max(float(r["excursion"]) for r in rows)
    analytic = ch.diurnal_silica_margin(T_MEAN, T_AMP)
    assert analytic == pytest.approx(measured, abs=0.005), (
        f"analytic {analytic:.4f} vs simulated {measured:.4f}")


def test_the_margin_grows_with_the_diurnal_swing():
    """And it is not small at any realistic amplitude, which is the point."""
    import chemistry as ch
    prev = -1.0
    for amp in (2.5, 5.0, 7.5, 10.0):
        m = ch.diurnal_silica_margin(30.0, amp)
        assert m > prev
        prev = m
    assert ch.diurnal_silica_margin(30.0, 10.0) > 0.20
    # and the limit it implies is below saturation, never above
    assert ch.silica_limit_with_diurnal_margin(30.0, 5.0) < 0.0
