"""Preregistered 21 Sep 2026 before execution; see control_timeline_scope.md.

Energy equality: absolute 1e-9 kWh plus relative 1e-12. Time/shape/mask
checks are exact. All values are synthetic, not site or OEM limits.
"""
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import math

import pytest

import control_timeline as ct


T = datetime(2026, 9, 21, 10, 7, 30, tzinfo=timezone.utc)


def plan(first=None):
    rows = [[0.] * 10 for _ in range(96)]
    for name, value in (first or {"f_fan": 40.}).items():
        rows[0][ct.CHANNELS.index(name)] = value
    return ct.PredictionPlan(ct.ActivationHorizon(T), rows, T-timedelta(seconds=30))


def load(start, end, power, **kwargs):
    return ct.IssuedLoadInterval(
        T+timedelta(seconds=start), T+timedelta(seconds=end), power,
        kwargs.get("issued_at", T-timedelta(minutes=10)),
        kwargs.get("available_at", T-timedelta(minutes=9)),
    )


def propose(**kwargs):
    args = dict(plan=plan(), actual_commands={"f_fan": 10.},
                capabilities=ct.CapabilityMask({"f_fan"}),
                limits={"f_fan": ct.ChannelLimits(0., 100., .1)},
                actual_at=T-timedelta(seconds=1), checked_at=T,
                expires_at=T+timedelta(seconds=300), max_feedback_age_s=2.)
    args.update(kwargs)
    return ct.propose_first_move(**args)


def applied(event, start, end, **kwargs):
    return ct.AppliedControlInterval(
        event, T+timedelta(seconds=start), T+timedelta(seconds=end),
        kwargs.get("commands", {"f_fan": 20.}),
        kwargs.get("recorded_at", T+timedelta(seconds=end)),
    )


def test_horizon_is_activation_anchored_immutable_24_hours():
    local = T.astimezone(timezone(timedelta(hours=5)))
    horizon = ct.ActivationHorizon(local)
    assert horizon.activation_at == T
    assert horizon.activation_at.tzinfo is timezone.utc
    assert len(horizon.boundaries) == 97
    assert all((b-a).total_seconds() == 900
               for a, b in zip(horizon.boundaries, horizon.boundaries[1:]))
    assert horizon.end_at == T+timedelta(days=1)
    assert horizon.channels == ct.CHANNELS
    assert len(horizon.channels) == 10
    with pytest.raises(FrozenInstanceError):
        horizon.activation_at = T+timedelta(seconds=1)


@pytest.mark.parametrize("bad", [T.replace(tzinfo=None), None, "2026-09-21", math.nan, True])
def test_horizon_rejects_naive_or_malformed_datetime(bad):
    with pytest.raises(ct.TimelineError):
        ct.ActivationHorizon(bad)


def test_horizon_rejects_datetime_overflow():
    with pytest.raises(ct.TimelineError):
        ct.ActivationHorizon(datetime.max.replace(tzinfo=timezone.utc))


def test_plan_snapshots_nested_lists():
    rows = [[1.] * 10 for _ in range(96)]
    result = ct.PredictionPlan(ct.ActivationHorizon(T), rows, T)
    rows[0][0] = 99.
    assert result.values[0][0] == 1.
    assert isinstance(result.values, tuple)
    assert isinstance(result.values[0], tuple)
    with pytest.raises(TypeError):
        result.values[0][0] = 2.


@pytest.mark.parametrize("rows", [[], [[0.]*10]*95, [[0.]*9]*96, [[0.]*11]*96,
                                  "bad", None, [[math.nan]*10]*96,
                                  [[math.inf]*10]*96, [[True]*10]*96])
def test_bad_plan_shape_and_values_reject(rows):
    with pytest.raises(ct.TimelineError):
        ct.PredictionPlan(ct.ActivationHorizon(T), rows, T)


def test_plan_future_issuance_rejected():
    with pytest.raises(ct.TimelineError):
        ct.PredictionPlan(ct.ActivationHorizon(T), [[0.]*10]*96,
                           T+timedelta(microseconds=1))


def test_load_resampling_preserves_clipped_energy_and_short_spike():
    # First cell: 600 s at 10 kW + 60 s at 100 kW + 240 s at 20 kW.
    # Padding before activation is excluded, as is padding after 24 hours.
    rows = [load(-120, 600, 10), load(600, 660, 100), load(660, 86460, 20)]
    result = ct.resample_load(rows, ct.ActivationHorizon(T), as_of=T)
    first_energy = (600*10 + 60*100 + 240*20)/3600
    expected = (600*10 + 60*100 + (86400-660)*20)/3600
    assert result.energy_kwh[0] == pytest.approx(first_energy, abs=1e-9, rel=1e-12)
    assert result.mean_kw[0] == pytest.approx(first_energy/.25, abs=1e-9, rel=1e-12)
    assert result.source_min_kw[0] == 10.
    assert result.source_max_kw[0] == 100.
    assert result.source_min_kw[1:] == (20.,)*95
    assert result.source_max_kw[1:] == (20.,)*95
    assert math.fsum(result.energy_kwh) == pytest.approx(expected, abs=1e-9, rel=1e-12)
    assert result.covered_source_energy_kwh == pytest.approx(expected, abs=1e-9, rel=1e-12)
    assert result.energy_residual_kwh == pytest.approx(0., abs=1e-9)


def test_resampling_handles_noninteger_seconds_and_timezone_equivalence():
    offset = timezone(timedelta(hours=-4))
    a = load(0, .5, 40)
    b = load(.5, 86400, 12)
    shifted = [ct.IssuedLoadInterval(*(dt.astimezone(offset) for dt in
                   (row.start_at, row.end_at)), row.load_kw,
                   row.issued_at.astimezone(offset), row.available_at.astimezone(offset))
               for row in (a, b)]
    expected = ct.resample_load([a, b], ct.ActivationHorizon(T), as_of=T)
    result = ct.resample_load(shifted, ct.ActivationHorizon(T.astimezone(offset)),
                              as_of=T.astimezone(offset))
    assert result == expected
    assert result.source_max_kw[0] == 40.


@pytest.mark.parametrize("rows", [[], [load(0, 300, 10)],
    [load(1, 86400, 10)], [load(0, 400, 10), load(401, 86400, 10)],
    [load(0, 401, 10), load(400, 86400, 10)],
    [load(0, 86400, 10), load(0, 86400, 20)], [plan()], None])
def test_load_gap_overlap_and_missing_coverage_rejected(rows):
    with pytest.raises(ct.TimelineError):
        ct.resample_load(rows, ct.ActivationHorizon(T), as_of=T)


@pytest.mark.parametrize("power", [-1., math.inf, -math.inf, math.nan, True, None, "1"])
def test_load_power_rejects_invalid_values(power):
    with pytest.raises(ct.TimelineError):
        load(0, 86400, power)


@pytest.mark.parametrize("start,end", [(0, 0), (1, 0)])
def test_load_nonpositive_duration_rejects(start, end):
    with pytest.raises(ct.TimelineError):
        load(start, end, 10)


def test_load_future_issue_or_availability_rejects():
    for issued, available in ((T+timedelta(seconds=1), T+timedelta(seconds=1)),
                              (T-timedelta(seconds=1), T+timedelta(seconds=1))):
        rows = [load(0, 86400, 10, issued_at=issued, available_at=available)]
        with pytest.raises(ct.TimelineError):
            ct.resample_load(rows, ct.ActivationHorizon(T), as_of=T)
    with pytest.raises(ct.TimelineError):
        ct.resample_load([load(0, 86400, 10)], ct.ActivationHorizon(T),
                          as_of=T+timedelta(seconds=1))
    with pytest.raises(ct.TimelineError):
        load(0, 86400, 10, issued_at=T, available_at=T-timedelta(seconds=1))


def test_actual_interval_is_immutable_and_only_300_seconds_elapsed():
    commands = {"f_fan": 20.}
    row = applied("event1", 0, 300, commands=commands)
    commands["f_fan"] = 50.
    rows = ct.validate_actual_intervals([row], start_at=T,
             end_at=T+timedelta(seconds=300), as_of=T+timedelta(seconds=301))
    assert sum(r.elapsed_seconds for r in rows) == 300.
    assert row.commands["f_fan"] == 20.
    with pytest.raises(TypeError):
        row.commands["f_fan"] = 30.
    with pytest.raises(ct.TimelineError):
        ct.validate_actual_intervals([plan()], start_at=T,
             end_at=T+timedelta(seconds=300), as_of=T+timedelta(seconds=301))


@pytest.mark.parametrize("rows", [
    [applied("same", 0, 150), applied("same", 150, 300)],
    [applied("a", 0, 149), applied("b", 150, 300)],
    [applied("a", 0, 151), applied("b", 150, 300)],
    [applied("a", 0, 150)],
    [applied("a", 0, 150), applied("b", 150, 300, commands={"u_BD": .2})],
    [applied("a", 0, 300, recorded_at=T+timedelta(seconds=1000))],
])
def test_invalid_actual_coverage_rejected(rows):
    with pytest.raises(ct.TimelineError):
        ct.validate_actual_intervals(rows, start_at=T,
             end_at=T+timedelta(seconds=300), as_of=T+timedelta(seconds=301))


@pytest.mark.parametrize("kwargs", [dict(event="", start=0, end=1),
    dict(event="x", start=1, end=0), dict(event="x", start=0, end=0),
    dict(event="x", start=0, end=300, recorded_at=T),
    dict(event="x", start=0, end=300, commands={"lift": 10}),
    dict(event="x", start=0, end=300, commands={"f_fan": math.nan})])
def test_bad_actual_record_rejected(kwargs):
    with pytest.raises(ct.TimelineError):
        applied(**kwargs)


def test_first_move_300_second_slew_and_expiry_are_exact():
    proposal = propose()
    assert proposal.duration_seconds == 300.
    assert dict(proposal.commands) == {"f_fan": 40.}
    assert proposal.requires_activation_recheck is True
    assert not proposal.active_at(T-timedelta(microseconds=1))
    assert proposal.active_at(T)
    assert proposal.active_at(T+timedelta(seconds=299.999))
    assert not proposal.active_at(T+timedelta(seconds=300))
    with pytest.raises(TypeError):
        proposal.commands["f_fan"] = 100.


def test_first_move_cannot_use_900_second_slew_allowance():
    # Target 80 Hz is inside explicit bounds and reachable in 900 s, not 300 s.
    with pytest.raises(ct.TimelineError, match="unreachable"):
        propose(plan=plan({"f_fan": 80.}))
    with pytest.raises(ct.TimelineError, match="unreachable"):
        propose(expires_at=T+timedelta(seconds=100))
    assert propose(plan=plan({"f_fan": 20.}),
                   expires_at=T+timedelta(seconds=100)).duration_seconds == 100.


@pytest.mark.parametrize("expiry", [T, T-timedelta(seconds=1),
    T+timedelta(seconds=300, microseconds=1), T.replace(tzinfo=None), None, math.nan, True])
def test_invalid_first_move_expiration_rejects(expiry):
    with pytest.raises(ct.TimelineError):
        propose(expires_at=expiry)


@pytest.mark.parametrize("enabled", [{"f_fan", "T_CW_sp"}, {"lift"}, {"C_target"},
    {"unknown"}, "f_fan", ["f_fan", "f_fan"], [None]])
def test_invalid_capability_mask_rejects(enabled):
    with pytest.raises(ct.TimelineError):
        ct.CapabilityMask(enabled)


def test_mask_excludes_auxiliary_and_disabled_values_from_commands():
    result = propose(plan=plan({"f_fan": 40., "C_target": 3., "lift": 20., "u_BD": .8}))
    assert set(result.commands) == {"f_fan"}
    assert dict(propose(plan=plan({"T_CW_sp": 31.}),
         actual_commands={"T_CW_sp": 30.}, capabilities=ct.CapabilityMask({"T_CW_sp"}),
         limits={"T_CW_sp": ct.ChannelLimits(20., 40., .01)}).commands) == {"T_CW_sp": 31.}


@pytest.mark.parametrize("kwargs", [
    dict(checked_at=T+timedelta(microseconds=1)),
    dict(checked_at=T-timedelta(seconds=31), actual_at=T-timedelta(seconds=31)),
    dict(actual_at=T+timedelta(seconds=1)),
    dict(actual_at=T-timedelta(seconds=3)),
    dict(actual_at=T.replace(tzinfo=None)),
    dict(max_feedback_age_s=-1), dict(max_feedback_age_s=math.nan),
    dict(actual_commands={"u_BD": .1}), dict(actual_commands={"f_fan": math.inf}),
    dict(actual_commands={"f_fan": True}), dict(actual_commands={"f_fan": 101.}),
    dict(limits={}), dict(limits={"f_fan": (0., 100., .1)}),
    dict(capabilities=ct.CapabilityMask(set())), dict(plan=plan({"f_fan": 101.})),
])
def test_first_move_rejects_stale_missing_or_invalid_inputs(kwargs):
    with pytest.raises(ct.TimelineError):
        propose(**kwargs)


@pytest.mark.parametrize("bounds", [(2., 1., 1.), (0., 100., -1.),
    (math.nan, 100., 1.), (0., math.inf, 1.), (0., 100., True), (None, 1., 1.)])
def test_invalid_machine_limits_reject(bounds):
    with pytest.raises(ct.TimelineError):
        ct.ChannelLimits(*bounds)


def test_zero_slew_allows_only_actual_command_and_inputs_remain_unchanged():
    actual = {"f_fan": 10.}
    limit = {"f_fan": ct.ChannelLimits(0., 100., 0.)}
    result = propose(plan=plan({"f_fan": 10.}), actual_commands=actual, limits=limit)
    assert result.commands["f_fan"] == 10.
    with pytest.raises(ct.TimelineError):
        propose(actual_commands=actual, limits=limit)
    assert actual == {"f_fan": 10.}
    assert limit["f_fan"].max_slew_per_second == 0.


def test_direct_proposal_construction_freezes_commands_and_checks_lease():
    commands = {"f_fan": 20.}
    result = ct.FirstMoveProposal(T, T+timedelta(seconds=300), T, T, commands)
    commands["f_fan"] = 99.
    assert result.commands["f_fan"] == 20.
    with pytest.raises(TypeError):
        result.commands["f_fan"] = 30.
    with pytest.raises(ct.TimelineError):
        ct.FirstMoveProposal(T, T+timedelta(seconds=301), T, T, commands)
    with pytest.raises(ct.TimelineError):
        ct.FirstMoveProposal(T, T+timedelta(seconds=300), T,
                              T+timedelta(seconds=1), commands)


def test_direct_resampled_construction_freezes_series():
    values = [10.]*96
    result = ct.ResampledLoad(ct.ActivationHorizon(T), T, values, [2.5]*96,
                               values, values, 240.)
    values[0] = 99.
    assert result.mean_kw[0] == result.source_min_kw[0] == result.source_max_kw[0] == 10.
    with pytest.raises(TypeError):
        result.mean_kw[0] = 20.


def test_large_representable_load_and_energy_overflow_boundary():
    result = ct.resample_load([load(0, 86400, 1e306)], ct.ActivationHorizon(T), as_of=T)
    assert result.mean_kw[0] == pytest.approx(1e306, rel=1e-12)
    assert math.fsum(result.energy_kwh) == pytest.approx(2.4e307, rel=1e-12)
    with pytest.raises(ct.TimelineError):
        ct.resample_load([load(0, 86400, 1e308)], ct.ActivationHorizon(T), as_of=T)
    with pytest.raises(ct.TimelineError):
        load(0, 86400, 10**1000)


@pytest.mark.parametrize("start,end", [(-1, 300), (0, 301)])
def test_actual_padding_cannot_overcount_requested_elapsed_time(start, end):
    with pytest.raises(ct.TimelineError, match="endpoints exactly"):
        ct.validate_actual_intervals([applied("padded", start, end)], start_at=T,
             end_at=T+timedelta(seconds=300), as_of=T+timedelta(seconds=302))
