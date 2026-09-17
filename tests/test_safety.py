"""The acid-dosing interlock layer, held to its pre-registration.

Every row of the fault-injection matrix in
docs/staged/safety_preregistration.md is asserted here exactly as it was
registered before the first simulation run. A row that fails is reported as
failing; the matrix is not edited to make it pass.

This is a software specification plus a simulation. It is NOT a certified
safety function and claims no SIL; the independent low-pH trip must be built in
hardware (see src/safety.py).
"""
import functools
import pathlib
import pickle
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chemistry as chem          # noqa: E402
import controller as ctl          # noqa: E402
import safety                     # noqa: E402
import safety_sim as sim          # noqa: E402

TF = sim.T_FAULT_S
SCAN = 1.0


@functools.lru_cache(maxsize=None)
def _run(row, mode="active", hours=8.0, reset_at_s=None):
    return sim.run(sim.Scenario(row, mode=mode, hours=hours,
                                reset_at_s=reset_at_s))


def _trips(res):
    return [e for e in res["events"] if e["kind"] == "TRIP"]


def _first(res, kind, cause=None):
    for e in res["events"]:
        if e["kind"] == kind and (cause is None or e["cause"] == cause):
            return e
    return None


def _acid_stop_abs(res):
    return TF + res["acid_stop_after_fault_s"]


# ===========================================================================
# The chemistry the harness stands on
# ===========================================================================
@pytest.mark.parametrize("ph", [6.5, 7.0, 7.5, 8.0, 8.5])
def test_titration_curve_is_the_engines_closure_in_the_bicarbonate_region(ph):
    """The pH curve is not invented: where bicarbonate carries the alkalinity
    it reproduces chemistry.ph_atmospheric_equilibrium."""
    K, K2, Kw = sim._carbonate_constants(sim.T_BASIN_C)
    h = 10.0 ** -ph
    hco3 = K / h                                  # mol/kg bicarbonate at this pH
    w = chem.Water(HCO3=hco3 * 61017.0)
    engine = chem.ph_atmospheric_equilibrium(w, sim.T_BASIN_C)
    assert engine == pytest.approx(ph, abs=1e-9)
    ours = sim.ph_from_alkalinity(sim.alkalinity_at_ph(ph))
    assert ours == pytest.approx(ph, abs=1e-9)
    # and on the engine's own input (HCO3 treated as the whole alkalinity)
    assert sim.ph_from_alkalinity(hco3) == pytest.approx(engine, abs=0.02)


def test_the_engines_closure_cannot_represent_excess_acid():
    """Staged defect 55. At zero alkalinity the engine returns a negative pH;
    the proton balance returns CO2-saturated water. A safety simulation cannot
    use the engine closure past the equivalence point."""
    import dataclasses
    w = dataclasses.replace(chem.ARAMCO_FIELD_VALIDATED, HCO3=0.0)
    assert chem.ph_atmospheric_equilibrium(w, 30.0) < 0.0
    assert 5.4 < sim.ph_from_alkalinity(0.0) < 5.8
    assert sim.ph_from_alkalinity(-1e-3) == pytest.approx(3.0, abs=0.01)


def test_the_bound_is_charged_per_defect_25():
    """Acid per kg circulating times makeup/C, never times makeup."""
    mk, C = chem.ARAMCO_FIELD_VALIDATED, 5.0
    per_circ, _ = ctl.acid_dose_for_ph(mk, C, 6.5, 30.0)
    per_makeup = safety.stoichiometric_acid_bound(mk, C, 6.5, 30.0)
    assert per_makeup == pytest.approx(per_circ / C, rel=1e-12)
    # and it is about the makeup alkalinity, diprotic: a_m * 98.079/2 g/mol
    a_m = mk.molality()["HCO3"]
    assert per_makeup == pytest.approx(a_m * 98.079e-3 / 2.0, rel=0.02)


def test_normal_dosing_sits_inside_the_bound():
    ss = sim.steady_state()
    bound = safety.stoichiometric_acid_bound(sim.MAKEUP, sim.CYCLES0, 6.5,
                                             sim.T_BASIN_C)
    ratio = ss["acid_kg_s"] / (1.20 * bound * ss["makeup"])
    assert 0.5 < ratio < 1.0, ratio


def test_failsafe_cycles_is_the_repository_baseline():
    txt = (ROOT / "src" / "run_controller.py").read_text(encoding="utf-8")
    m = re.search(r"^V7_BASELINE_CYCLES\s*=\s*([0-9.]+)", txt, re.MULTILINE)
    assert m and float(m.group(1)) == safety.FAILSAFE_CYCLES_DEFAULT == 3.0


# ===========================================================================
# Unit behaviour on synthetic frames
# ===========================================================================
def _layer(mode="active", **over):
    cfg = safety.InterlockConfig(design_makeup_kg_s=5.0, design_acid_kg_s=4e-4,
                                 acid_bound_kg_per_kg_makeup=8.4e-5,
                                 basin_kg=50000.0, drift_kg_s=0.005, **over)
    return safety.SafetyLayer(cfg, chem.ARAMCO_FIELD_VALIDATED, mode=mode)


def _frame(t, ph=8.0, ph_trip=None, M=5.0, acid=0.0, cond=9000.0, B=1.0,
           Bcmd=1.0, **kw):
    import random
    r = random.Random(int(t))
    j = r.uniform(-1e-3, 1e-3)
    return safety.Frame(t=t, ph_control=ph + j,
                        ph_trip=(ph if ph_trip is None else ph_trip) - j,
                        conductivity=cond * (1 + j), makeup_flow=M * (1 + j),
                        blowdown_flow=B * (1 + j), acid_flow=acid,
                        blowdown_command=Bcmd,
                        evaporation_estimate=4.2, **kw)


def _req(t, acid=4e-4, cycles=5.0):
    return safety.Request(fan_pct=80.0, cycles=cycles, acid_kg_s=acid,
                          heartbeat=int(t))


def test_default_mode_is_shadow():
    cfg = safety.InterlockConfig(1.0, 1.0, 1.0, 1.0, 0.0)
    assert safety.SafetyLayer(cfg, chem.ARAMCO_FIELD_VALIDATED).mode == "shadow"


def test_acid_waits_for_the_proving_time():
    L = _layer()
    for t in range(0, 60):
        assert L.scan(_frame(t), _req(t)).acid_kg_s == 0.0
    assert L.scan(_frame(60), _req(60)).acid_kg_s > 0.0
    assert not _trips_of(L)


def _trips_of(L):
    return [e for e in L.events if e.kind == "TRIP"]


def test_low_ph_trip_latches_alarms_first_and_resets_only_on_recovery():
    L = _layer()
    t = 0
    for t in range(0, 100):
        L.scan(_frame(t), _req(t))
    # fall through the alarm, then the trip
    for ph in (6.9, 6.75, 6.7, 6.4, 6.4, 6.4):
        t += 1
        cmd = L.scan(_frame(t, ph=ph), _req(t))
    kinds = [(e.kind, e.cause) for e in L.events if e.kind in ("ALARM", "TRIP")]
    assert kinds.index(("ALARM", safety.LOW_PH_ALARM)) < kinds.index(("TRIP", safety.LOW_PH))
    assert cmd.acid_kg_s == 0.0 and not cmd.acid_isolation_open and cmd.tripped
    assert cmd.cycles == 3.0 and cmd.fan_pct == 80.0
    # recovery above the trip but below the alarm: reset refused
    for _ in range(5):
        t += 1
        L.scan(_frame(t, ph=6.6), _req(t))
    assert safety.LOW_PH in L.manual_reset(t)
    # it stays latched when pH recovers on its own. (These synthetic steps are
    # abrupt, so the rate-of-change check latches too; wait out its window.)
    for _ in range(15):
        t += 1
        cmd = L.scan(_frame(t, ph=7.8), _req(t))
    assert cmd.tripped and cmd.acid_kg_s == 0.0
    assert L.manual_reset(t) == []
    # acid still waits for makeup to be re-proven
    t += 1
    assert L.scan(_frame(t, ph=7.8), _req(t)).acid_kg_s == 0.0
    for _ in range(61):
        t += 1
        cmd = L.scan(_frame(t, ph=7.8), _req(t))
    assert cmd.acid_kg_s > 0.0 and not cmd.tripped


def test_failsafe_keeps_a_lower_requested_cycles_setpoint():
    L = _layer()
    for t in range(0, 70):
        L.scan(_frame(t), _req(t, cycles=1.8))
    for t in range(70, 80):
        cmd = L.scan(_frame(t, ph_trip=6.0), _req(t, cycles=1.8))
    assert cmd.tripped and cmd.cycles == 1.8


def test_dosing_integral_clamps_an_overdose_with_flow_proven():
    L = _layer()
    bound_rate = 1.20 * 8.4e-5 * 5.0                       # kg/s
    total, t = 0.0, 0
    for t in range(0, 7200):
        cmd = L.scan(_frame(t), _req(t, acid=3.0 * bound_rate))
        total_window = cmd.acid_kg_s
        total += cmd.acid_kg_s
    assert _first_event(L, "ALARM", safety.DOSING_BOUND_LIMITED)
    # over the last full hour, granted acid never exceeded the earned bound
    # (the synthetic makeup flow carries +/-0.1 % jitter, hence 1.001)
    assert total <= bound_rate * 1.001 * 7200
    assert total_window <= bound_rate * 1.001
    assert not _trips_of(L)


def _first_event(L, kind, cause):
    return next((e for e in L.events if e.kind == kind and e.cause == cause), None)


@pytest.mark.parametrize("bad,cause", [
    (dict(age_s={"ph_trip": 6.0}), safety.SENSOR_STALE),
    (dict(cond=1.0), safety.SENSOR_RANGE),
    (dict(ph=15.0), safety.SENSOR_RANGE),
])
def test_implausible_sensors_trip(bad, cause):
    L = _layer()
    for t in range(0, 70):
        L.scan(_frame(t), _req(t))
    cmd = L.scan(_frame(70, **bad), _req(70))
    assert cmd.tripped and cmd.acid_kg_s == 0.0
    assert any(e.cause == cause for e in _trips_of(L))


def test_a_frozen_ph_value_trips_after_the_frozen_time():
    L = _layer()
    for t in range(0, 70):
        L.scan(_frame(t), _req(t))
    for t in range(70, 70 + 901):
        f = _frame(t)
        f.ph_control = 7.95
        cmd = L.scan(f, _req(t))
    assert any(e.cause == safety.SENSOR_FROZEN for e in _trips_of(L))
    assert cmd.acid_kg_s == 0.0


def test_a_flow_meter_holding_exactly_zero_is_not_frozen():
    L = _layer()
    for t in range(0, 2000):
        L.scan(_frame(t, B=0.0, Bcmd=0.0), _req(t))
    assert not any(e.cause == safety.SENSOR_FROZEN for e in _trips_of(L))


# ===========================================================================
# The pre-registered incident
# ===========================================================================
def test_incident_A1_acid_stops_within_proving_time_plus_one_scan():
    r = _run("F1")
    assert r["acid_stop_after_fault_s"] <= 60.0 + SCAN


def test_incident_A2_basin_ph_stays_above_the_trip_setpoint():
    r = _run("F1")
    assert r["ph_min_after_fault"] > 6.5


def test_incident_without_interlocks_crosses_every_threshold_before_low_level():
    """Report row, and prior P1: pH crosses 6.5 before the low-level pump trip."""
    r = _run("S1", mode="shadow")
    c = r["cross_after_fault_s"]
    assert all(c[k] is not None for k in ("6.5", "5.5", "4.0"))
    assert c["6.5"] < c["5.5"] < c["4.0"]
    assert r["low_level_after_fault_s"] is not None
    assert c["6.5"] < r["low_level_after_fault_s"]


# ===========================================================================
# The fault-injection matrix, row by row
# ===========================================================================
def test_F0_normal_operation_no_trip_no_alarm():
    r = _run("F0", hours=24.0)
    assert not [e for e in r["events"] if e["kind"] in ("TRIP", "ALARM")], \
        [e for e in r["events"] if e["kind"] in ("TRIP", "ALARM")][:5]
    assert r["passthrough_after_proving"]


def test_F1_makeup_trip():
    r = _run("F1")
    first = _trips(r)[0]
    assert first["cause"] == safety.MAKEUP_NOT_PROVEN
    assert r["acid_stop_after_fault_s"] <= 60.0 + SCAN
    assert r["ph_min_after_fault"] > 6.5
    fc = r["final_command"]
    assert fc["cycles"] == 3.0 and fc["fan_pct"] == 90.0 and fc["acid_kg_s"] == 0.0


def test_F2_ph_control_probe_stuck_high():
    r = _run("F2")
    trips = _trips(r)
    assert trips, "no trip"
    assert trips[0]["cause"] in (safety.PH_PROBE_DISAGREE, safety.SENSOR_RATE,
                                 safety.SENSOR_FROZEN, safety.SENSOR_RANGE,
                                 safety.SENSOR_STALE)
    assert r["first_disagree_t_s"] is not None
    assert _acid_stop_abs(r) <= r["first_disagree_t_s"] + 60.0 + SCAN
    assert r["final_latched"]
    assert r["ph_min_after_fault"] > 6.5


_DWELL_RESTARTS = (
    "PRE-REGISTERED ROW FAILS. The bound was registered as 'N s + 1 scan after "
    "the signal FIRST exceeds its threshold', but the setpoint requires the "
    "signal to stay over it CONTINUOUSLY for N s. A slow drift crosses the "
    "threshold inside the measurement noise, the dwell timer restarts each time "
    "noise pulls it back under, and the trip lands later than registered. The "
    "row is reported as failing and is not rewritten; see "
    "docs/staged/safety-interlocks_defects.md.")


@pytest.mark.xfail(strict=True, reason=_DWELL_RESTARTS)
def test_F3_ph_probes_disagree():
    r = _run("F3", reset_at_s=TF + 2 * 3600.0)
    trips = _trips(r)
    assert trips and trips[0]["cause"] == safety.PH_PROBE_DISAGREE
    assert _acid_stop_abs(r) <= r["first_disagree_t_s"] + 60.0 + SCAN
    assert r["reset_refused"] and safety.PH_PROBE_DISAGREE in r["reset_refused"]
    assert safety.PH_PROBE_DISAGREE in r["final_latched"]
    assert r["final_command"]["acid_kg_s"] == 0.0


@pytest.mark.xfail(strict=True, reason=_DWELL_RESTARTS)
def test_F4a_conductivity_cell_fouled_reading_low():
    r = _run("F4a")
    alarm = _first(r, "ALARM", safety.SCI_ALARM)
    trip = _first(r, "TRIP", safety.COND_CELL_FAULT)
    assert alarm and trip and alarm["t_s"] < trip["t_s"]
    assert _trips(r)[0]["cause"] == safety.COND_CELL_FAULT
    assert trip["t_s"] <= r["first_sci_over_trip_t_s"] + 600.0 + SCAN
    assert _acid_stop_abs(r) <= trip["t_s"] + SCAN
    fc = r["final_command"]
    assert fc["basis"] == "flow_ratio" and fc["cycles"] == 3.0 and fc["acid_kg_s"] == 0.0


def test_F4b_conductivity_drop_with_blowdown_closed():
    r = _run("F4b")
    trip = _first(r, "TRIP", safety.COND_CELL_FAULT)
    assert trip and _trips(r)[0]["cause"] == safety.COND_CELL_FAULT
    assert trip["t_s"] <= TF + 60.0 + SCAN
    assert r["acid_stop_after_fault_s"] <= 60.0 + SCAN
    fc = r["final_command"]
    assert fc["basis"] == "flow_ratio" and fc["cycles"] == 3.0


def test_F5_controller_heartbeat_lost():
    r = _run("F5")
    trip = _first(r, "TRIP", safety.HEARTBEAT_LOST)
    assert trip and _trips(r)[0]["cause"] == safety.HEARTBEAT_LOST
    assert trip["t_s"] <= TF + 10.0 + SCAN
    assert r["acid_stop_after_fault_s"] <= 10.0 + SCAN
    fc = r["final_command"]
    assert fc["cycles"] == 3.0 and fc["fan_pct"] == 90.0 and fc["acid_kg_s"] == 0.0


def test_F6_acid_pump_stuck_on_after_a_trip():
    r = _run("F6")
    causes = [e["cause"] for e in _trips(r)]
    assert causes[:2] == [safety.MAKEUP_NOT_PROVEN, safety.ACID_PUMP_STUCK], causes
    assert r["acid_stop_after_fault_s"] <= 5 * SCAN
    assert not r["final_command"]["isolation_open"]
    assert r["ph_min_after_fault"] > 6.5


def test_F7_blowdown_valve_stuck_closed():
    r = _run("F7")
    trip = _first(r, "TRIP", safety.BLOWDOWN_VALVE_FAILED)
    assert trip and _trips(r)[0]["cause"] == safety.BLOWDOWN_VALVE_FAILED
    assert trip["t_s"] <= TF + 120.0 + SCAN
    assert r["acid_stop_after_fault_s"] <= 120.0 + SCAN
    fc = r["final_command"]
    assert fc["cycles"] == 3.0 and fc["fan_pct"] == 90.0 and fc["acid_kg_s"] == 0.0


def test_F8_every_software_layer_defeated_the_independent_trip_holds():
    r = _run("F8")
    trips = _trips(r)
    assert trips and trips[0]["cause"] == safety.LOW_PH, [e["cause"] for e in trips]
    alarm = _first(r, "ALARM", safety.LOW_PH_ALARM)
    assert alarm and alarm["t_s"] < trips[0]["t_s"]
    assert trips[0]["t_s"] <= r["first_trip_probe_below_t_s"] + 3 * SCAN + SCAN
    assert _acid_stop_abs(r) <= trips[0]["t_s"] + SCAN
    assert r["ph_min_after_fault"] >= 6.0


def test_S1_shadow_mode_actuates_nothing_and_logs_the_same_trip():
    shadow, active = _run("S1", mode="shadow"), _run("F1")
    assert shadow["commands_equal_requests"]
    assert shadow["acid_flowing_at_end"]
    s_trip = _first(shadow, "TRIP", safety.MAKEUP_NOT_PROVEN)
    a_trip = _first(active, "TRIP", safety.MAKEUP_NOT_PROVEN)
    assert s_trip and a_trip and s_trip["t_s"] == a_trip["t_s"]


# ===========================================================================
# The controller hook: off by default, and byte-identical when off
# ===========================================================================
@pytest.fixture(scope="module")
def controller_setup():
    import json
    import numpy as np
    import run_controller as rc
    cal = json.loads((ROOT / "results" / "calibration.json").read_text())
    cond = dict(rc.PLANT)
    cond.update({"T_db": 38.0, "rh": 0.40, "T_wi": 26.0 + 12.0})
    grids = dict(fan_grid=np.array([50.0, 90.0]),
                 cycles_grid=np.array([3.0, 5.0]),
                 ph_grid=np.array([7.75, 8.25]))
    return (cond, rc.TSE, rc.TARIFFS, cal["fill_c"], cal["fill_n"]), grids


def test_controller_outputs_are_byte_identical_with_the_hook_off(controller_setup):
    args, grids = controller_setup
    direct = ctl.optimise(*args, **grids)
    hooked = ctl.supervise(*args, **grids)          # safety_layer=None
    assert pickle.dumps(hooked) == pickle.dumps(direct)


def test_the_hook_is_not_reachable_from_optimise():
    import inspect
    src = inspect.getsource(ctl.optimise)
    assert "safety" not in src and "supervise" not in src


def test_the_hook_passes_setpoints_through_a_shadow_layer(controller_setup):
    args, grids = controller_setup
    best, _ = ctl.optimise(*args, **grids)
    layer = _layer(mode="shadow")
    guarded, _ = ctl.supervise(*args, **grids, safety_layer=layer,
                               frame=_frame(0.0), heartbeat=1)
    assert guarded["safety_command"].cycles == best["cycles"]
    assert guarded["safety_command"].acid_kg_s == pytest.approx(best["acid_kg_h"] / 3600.0)
    assert {k: guarded[k] for k in best} == best


# ---------------------------------------------------------------------------
# What F3 and F4a actually do. NOT the pre-registered criteria -- those are the
# xfail tests above. These pin the measured behaviour so a change to it shows.
# ---------------------------------------------------------------------------
def test_F3_measured_trips_on_disagreement_later_than_registered_but_safely():
    r = _run("F3", reset_at_s=TF + 2 * 3600.0)
    trip = _first(r, "TRIP", safety.PH_PROBE_DISAGREE)
    assert trip and _trips(r)[0]["cause"] == safety.PH_PROBE_DISAGREE
    late = _acid_stop_abs(r) - (r["first_disagree_t_s"] + 60.0 + SCAN)
    assert 0.0 < late < 600.0, late
    assert r["reset_refused"] and safety.PH_PROBE_DISAGREE in r["reset_refused"]
    assert r["final_command"]["acid_kg_s"] == 0.0
    assert r["ph_min_after_fault"] > 7.5          # the true basin never moved


def test_F4a_measured_alarm_then_trip_later_than_registered():
    r = _run("F4a")
    alarm = _first(r, "ALARM", safety.SCI_ALARM)
    trip = _first(r, "TRIP", safety.COND_CELL_FAULT)
    assert alarm and trip and alarm["t_s"] < trip["t_s"]
    late = trip["t_s"] - (r["first_sci_over_trip_t_s"] + 600.0 + SCAN)
    assert 0.0 < late < 1800.0, late
    fc = r["final_command"]
    assert fc["basis"] == "flow_ratio" and fc["cycles"] == 3.0 and fc["acid_kg_s"] == 0.0


# ---------------------------------------------------------------------------
# Staged defect 56. NOT a pre-registered row: found by the incident run.
# ---------------------------------------------------------------------------
def test_registered_failsafe_empties_the_basin_sooner_on_makeup_loss():
    """Blowdown to 3.0 cycles on ANY trip opens the bleed on the one trip where
    no makeup can replace what it throws away."""
    shadow = _run("S1", mode="shadow")
    active = _run("F1")
    assert active["low_level_after_fault_s"] < shadow["low_level_after_fault_s"]


def test_holding_blowdown_on_makeup_loss_keeps_the_inventory_longer():
    held = sim.run(sim.Scenario("F1", hold_blowdown_on_makeup_loss=True))
    shadow = _run("S1", mode="shadow")
    assert held["acid_stop_after_fault_s"] <= 60.0 + SCAN
    assert held["ph_min_after_fault"] > 6.5
    ll = held["low_level_after_fault_s"]
    assert ll is None or ll > shadow["low_level_after_fault_s"]
    assert not _first(held, "TRIP", safety.BLOWDOWN_VALVE_FAILED) or         _first(held, "TRIP", safety.BLOWDOWN_VALVE_FAILED)["t_s"] > TF + ll
