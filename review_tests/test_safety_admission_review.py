import dataclasses
import math
import pytest
import safety
import chemistry as chem
import controller as ctl


def layer(mode="active"):
    return safety.SafetyLayer(
        safety.InterlockConfig(5., 4e-4, 8.4e-5, 50000., .005),
        chem.ARAMCO_FIELD_VALIDATED, mode=mode)


def frame(t):
    return safety.Frame(t, 8., 8., 9000., 5., 1., 0., 1., 4.2)


def request(t):
    return safety.Request(80., 5., 4e-4, t)


def proven(mode="active"):
    obj = layer(mode)
    for t in range(70):
        obj.scan(frame(t), request(t))
    return obj


@pytest.mark.parametrize("field,value", [
    ("ph_trip", None), ("ph_control", math.nan),
    ("makeup_flow", math.inf), ("acid_flow", math.inf),
    ("evaporation_estimate", math.nan), ("blowdown_command", math.inf),
    ("t", math.nan), ("age_s", {"ph_trip": math.nan}),
    ("age_s", {"ph_trip": -1.}), ("age_s", None),
])
def test_invalid_telemetry_issues_off_without_raising(field, value):
    obj = proven()
    cmd = obj.scan(dataclasses.replace(frame(70), **{field: value}), request(70))
    assert cmd.tripped and cmd.acid_kg_s == 0.
    assert cmd.acid_isolation_open is False
    assert obj.would_be == cmd
    assert cmd.fan_pct == 80. and cmd.cycles <= 3.
    assert obj._last_acid_cmd == 0.


@pytest.mark.parametrize("field,value", [
    ("acid_kg_s", math.nan), ("acid_kg_s", math.inf),
    ("cycles", math.nan), ("cycles", 1.), ("fan_pct", -100.),
    ("fan_pct", 101.), ("heartbeat", math.nan),
])
def test_invalid_request_is_not_an_actuator_command(field, value):
    obj = proven()
    cmd = obj.scan(frame(70), dataclasses.replace(request(70), **{field: value}))
    assert cmd.tripped and cmd.acid_kg_s == 0.
    assert cmd.acid_isolation_open is False
    assert cmd.fan_pct == 80. and cmd.cycles <= 3.


def test_invalid_shadow_request_cannot_export_nan_command():
    obj = proven("shadow")
    cmd = obj.scan(frame(70), dataclasses.replace(request(70), acid_kg_s=math.nan))
    assert cmd.acid_kg_s == 0. and not cmd.acid_isolation_open


@pytest.mark.parametrize("next_t", [0., -1., 120.])
def test_repeated_backward_or_missing_scans_cannot_prove_continuous_flow(next_t):
    obj = layer()
    obj.scan(frame(0), request(0))
    cmd = obj.scan(frame(next_t), request(120))
    assert cmd.tripped and not cmd.acid_isolation_open
    assert cmd.acid_kg_s == 0. and not obj._proven


def test_invalid_frame_requires_manual_reset_then_fresh_proving():
    obj = proven()
    obj.scan(dataclasses.replace(frame(70), ph_trip=None), request(70))
    assert obj.scan(frame(71), request(71)).acid_kg_s == 0.
    assert obj.manual_reset(71) == []
    for t in range(72, 132):
        assert obj.scan(frame(t), request(t)).acid_kg_s == 0.
    assert obj.scan(frame(132), request(132)).acid_kg_s > 0.


def test_no_feasible_optimizer_result_exports_explicit_isolated_command(monkeypatch):
    obj = proven()
    monkeypatch.setattr(ctl, "optimise", lambda *a, **k: (None, 17))
    result, count = ctl.supervise(safety_layer=obj, frame=frame(70), heartbeat=70)
    assert count == 17 and result["feasible"] is False
    assert result["optimizer_status"] == "NO_FEASIBLE_POINT"
    cmd = result["safety_command"]
    assert cmd.tripped and cmd.acid_kg_s == 0. and not cmd.acid_isolation_open
    assert obj._last_acid_cmd == 0.


def test_no_layer_preserves_legacy_no_feasible_result(monkeypatch):
    monkeypatch.setattr(ctl, "optimise", lambda *a, **k: (None, 17))
    assert ctl.supervise() == (None, 17)


def test_optimizer_exception_with_interlock_still_exports_off(monkeypatch):
    def fail(*a, **k):
        raise RuntimeError("synthetic numerical failure")
    obj = proven()
    monkeypatch.setattr(ctl, "optimise", fail)
    result, count = ctl.supervise(safety_layer=obj, frame=frame(70), heartbeat=70)
    assert count is None and result["feasible"] is False
    assert result["optimizer_status"] == "ERROR"
    assert result["optimizer_error_type"] == "RuntimeError"
    assert result["safety_command"].acid_kg_s == 0.
    assert result["safety_command"].acid_isolation_open is False


def test_optimizer_exception_without_interlock_is_not_hidden(monkeypatch):
    def fail(*a, **k):
        raise RuntimeError("synthetic numerical failure")
    monkeypatch.setattr(ctl, "optimise", fail)
    with pytest.raises(RuntimeError, match="synthetic numerical failure"):
        ctl.supervise()


@pytest.mark.parametrize('bad_result', [{}, {'fan_pct':80., 'cycles':3., 'acid_kg_h':'invalid'}])
def test_malformed_optimizer_record_cannot_bypass_isolation(monkeypatch, bad_result):
    obj = proven()
    monkeypatch.setattr(ctl, 'optimise', lambda *a, **k: (bad_result, 7))
    result, count = ctl.supervise(safety_layer=obj, frame=frame(70), heartbeat=70)
    assert count == 7 and result['optimizer_status'] == 'INVALID_RESULT'
    assert result['safety_command'].acid_kg_s == 0.
    assert result['safety_command'].acid_isolation_open is False
