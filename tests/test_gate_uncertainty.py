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
    # DEFECT 70: the duplicate Exp3 file was being resampled as a third
    # campaign. On the two real ones the spreads are 4.79 pp and 0.083
    # %/fan%, where three gave 9.71 and 0.232.
    assert len(gu.CAMPAIGN_FITS) == 2 and "Exp3" not in gu.CAMPAIGN_FITS
    assert a_sd == pytest.approx(4.79, abs=0.05)
    assert k_sd == pytest.approx(0.083, abs=0.005)
    assert a_sd > 30 * k_sd, "the cancelling term must be the larger one"
    # and the slope keeps its sign on both real campaigns: the claim that
    # it did not was a property of the repeated file
    assert k_lo < 0 and k_hi < 0


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


def test_twenty_percent_against_the_error_bar_of_what_is_already_computed():
    """DEFECT 70 moved this one, and in the flattering direction, so it is
    pinned rather than left implicit. With the duplicate Exp3 file counted
    as a campaign, 20 % sat INSIDE the one-sigma bar on V7. On the two real
    campaigns the bar is 13.0 to 17.0 % and 20 % is outside it -- a smaller
    interval on a weaker basis, not new information."""
    d = gu.fan_movement_from_gate()
    iv = gu.water_saving_interval(15.01, d)
    assert iv["low"] == pytest.approx(13.0, abs=0.2)
    assert iv["high"] == pytest.approx(17.0, abs=0.2)
    assert not (iv["low"] < 20.0 < iv["high"])
    assert len(gu.CAMPAIGN_FITS) == 2, (
        "the narrower bar comes from REMOVING a duplicate campaign, not "
        "from a better instrument")


def test_a_gate_that_does_not_move_the_fan_carries_none_of_this():
    """The constructive half: hold the fan fixed and the fan-dependent term
    vanishes, leaving a water saving that comes from cycles alone."""
    iv = gu.water_saving_interval(16.7, 0.0)
    assert iv["half_width_pp"] == 0.0
    assert iv["low"] == iv["high"] == pytest.approx(16.7)
