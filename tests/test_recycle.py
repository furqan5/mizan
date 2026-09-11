"""Blowdown recycle, and the arithmetic ceiling on any water saving."""
import pytest
import recycle as rc
import run_controller as rcn

E = 4.2   # kg/s evaporation, the 10 MW archetype


def test_the_hard_ceiling_is_one_over_cycles():
    """No measure of any kind can save more than the blowdown, because
    evaporation is the heat rejection. This is arithmetic, and it is the
    single most useful number in the water story."""
    for c, expect in ((2, 50.0), (3, 100/3), (4, 25.0), (5, 20.0), (6, 100/6)):
        assert rc.max_possible_saving_pct(c) == pytest.approx(expect, abs=1e-9)
    with pytest.raises(ValueError):
        rc.max_possible_saving_pct(1.0)


def test_a_plant_at_six_cycles_can_never_reach_twenty_percent():
    """The question that keeps being asked, answered once. At six cycles the
    entire blowdown is 16.7 % of makeup, so 20 % is unreachable by better
    control, by treatment, by recycle, or by any combination."""
    assert rc.max_possible_saving_pct(6.0) < 20.0
    assert rc.recovery_needed_for_saving(E, 6.0, 6.0, 20.0) is None
    assert rc.recovery_needed_for_saving(E, 6.0, 12.0, 20.0) is None
    # and at five cycles it is exactly reachable only in the limit
    assert rc.max_possible_saving_pct(5.0) == pytest.approx(20.0)


def test_zero_recovery_reduces_to_the_textbook_water_balance():
    """M = E*C/(C-1) must fall out, or the recycle algebra is wrong."""
    for c in (2.0, 3.0, 4.5, 6.0, 10.0):
        _, _, m = rc.blowdown_for_cycles(E, c, 0.0)
        assert m == pytest.approx(E * c / (c - 1.0), rel=1e-12)


def test_recycle_beats_raising_cycles_and_that_is_awkward():
    """The finding this package would rather not have.

    Against a 3-cycle incumbent, raising cycles to 5 -- everything the
    controller can do -- buys 16.7 %. Leaving the setpoint alone and recycling
    the blowdown at 85 % recovery buys 29.8 %. Almost all of the water benefit
    is capital, not control.

    Recorded as a test so it cannot quietly disappear from the pitch."""
    control_only = rc.saving_vs_baseline_pct(E, 3.0, 5.0, recovery=0.0)
    recycle_only = rc.saving_vs_baseline_pct(E, 3.0, 3.0, recovery=0.85)
    both = rc.saving_vs_baseline_pct(E, 3.0, 5.0, recovery=0.85)
    assert control_only == pytest.approx(16.67, abs=0.05)
    assert recycle_only == pytest.approx(29.82, abs=0.05)
    assert both == pytest.approx(31.27, abs=0.05)
    assert recycle_only > control_only + 10.0, (
        "recycle must dominate control on water, or the honest framing in "
        "src/recycle.py is wrong")
    # and nothing may exceed the hard ceiling
    assert both < rc.max_possible_saving_pct(3.0)


def test_twenty_percent_is_reachable_from_three_cycles_and_how():
    r = rc.recovery_needed_for_saving(E, 3.0, 3.0, 20.0)
    assert r is not None and 0.45 < r < 0.55, r
    r5 = rc.recovery_needed_for_saving(E, 3.0, 5.0, 20.0)
    assert r5 is not None and r5 < r, "raising cycles should lower the RO duty"


def test_the_ro_brine_silica_constraint_is_what_sizes_the_scheme():
    """Silica concentrates in the brine by 1/(1-recovery). This is the
    constraint the chemistry engine is uniquely able to evaluate, and it is
    the reason a controller company has anything to say about a capex item."""
    d = rc.ro_brine_silica_ok(rcn.TSE, 5.0, 0.85)
    assert d["brine_SiO2_mg_l"] == pytest.approx(
        d["SiO2_into_RO_mg_l"] / (1 - 0.85), rel=1e-9)
    assert d["ok"]
    # without the EC stage in front, the same scheme fails
    bare = rc.ro_brine_silica_ok(rcn.TSE, 5.0, 0.85, ec_silica_removal=0.0)
    assert not bare["ok"], "EC is load-bearing; without it the brine scales"


def test_recovered_water_beats_bought_water_on_energy_but_that_proves_little():
    d = rc.recycle_pays(0.85, rcn.TARIFFS)
    assert d["pays_on_energy_alone"]
    assert d["margin_per_m3"] > 0
    # the point of the test is the caveat: capital, membranes, electrodes and
    # sludge are all excluded, so this is necessary and nowhere near sufficient
    assert "pays_on_energy_alone" in d


def test_recovery_is_bounded():
    with pytest.raises(ValueError):
        rc.blowdown_for_cycles(E, 5.0, 1.0)
    with pytest.raises(ValueError):
        rc.blowdown_for_cycles(E, 1.0, 0.5)
