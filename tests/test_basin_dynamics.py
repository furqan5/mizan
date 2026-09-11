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
