"""Error bars on the water gates, propagated from the calibration data.

Written after gate V7 returned 15.01 % against a 15.00 % threshold and was
recorded as a PASS on a margin of 0.01 percentage points, with nothing in the
package able to say whether that was a result.
"""
import pytest
import gate_uncertainty as gu


def test_the_offset_is_large_and_the_slope_is_small_and_that_is_the_point():
    """The big error cancels and the small one does not.

    A constant multiplicative error on evaporation cancels in a ratio of two
    makeup figures from the same model at the same site. A fan-dependent one
    does not, because the baseline and the optimised case run at different
    fan speeds.
    """
    a_sd, a_lo, a_hi = gu.offset_spread()
    k_sd, k_lo, k_hi = gu.slope_spread()
    assert a_sd == pytest.approx(9.71, abs=0.05)
    assert k_sd == pytest.approx(0.232, abs=0.005)
    assert a_sd > 30 * k_sd, "the cancelling term must be the larger one"
    # and the slope's sign is not consistent between campaigns, which is why
    # it cannot be corrected for, only propagated
    assert k_lo < 0 < k_hi


def test_v5_fails_decidably():
    """4.38 % against 15 % is a real failure: the interval does not reach the
    threshold, so the verdict survives its own error bar."""
    d = gu.fan_movement_from_gate()
    assert d is not None and d == pytest.approx(24.0, abs=1.0)
    v = gu.verdict_is_decidable(4.38, 15.0, d)
    assert v["point_verdict"] == "FAIL"
    assert v["decidable"], "a failure by 10 points should be decidable"
    assert v["high"] < 15.0


def test_v7_passes_but_is_not_decidable_and_must_say_so():
    """THE TEST THIS MODULE EXISTS FOR.

    15.01 % against 15.00 % is a pass by the rule and a coin toss on the
    physics. The interval straddles the threshold, so the verdict carries no
    information, and anything reporting the verdict must report that too.
    """
    d = gu.fan_movement_from_gate()
    v = gu.verdict_is_decidable(15.01, 15.0, d)
    assert v["point_verdict"] == "PASS"
    assert not v["decidable"], (
        "if this ever becomes decidable the instrument improved and the "
        "claim can be strengthened -- check why before deleting this")
    assert abs(v["margin_in_sigma"]) < 0.01, v["margin_in_sigma"]


def test_twenty_percent_is_inside_the_error_bar_of_what_is_already_computed():
    """The question that kept being asked, answered by the instrument rather
    than by the optimiser: you cannot distinguish 15 % from 20 % here."""
    d = gu.fan_movement_from_gate()
    iv = gu.water_saving_interval(15.01, d)
    assert iv["low"] < 20.0 < iv["high"], (
        f"20 % must sit inside {iv['low']:.1f}-{iv['high']:.1f} for the "
        f"conclusion in src/gate_uncertainty.py to hold")


def test_a_gate_that_does_not_move_the_fan_carries_none_of_this():
    """The constructive half: hold the fan fixed and the fan-dependent term
    vanishes, leaving a water saving that comes from cycles alone."""
    iv = gu.water_saving_interval(16.7, 0.0)
    assert iv["half_width_pp"] == 0.0
    assert iv["low"] == iv["high"] == pytest.approx(16.7)
