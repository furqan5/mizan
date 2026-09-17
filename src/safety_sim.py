"""
MIZAN :: safety-interlock simulation harness
============================================

Runs `safety.SafetyLayer` against a basin mass balance under the fault matrix
pre-registered in `docs/staged/safety_preregistration.md`.

THE PLANT. The balance is modelica/TowerBasin.mo's, extended to what an acid
incident needs -- basin inventory, a conservative tracer, total alkalinity and
the sulfate the acid adds:

    dV/dt      = M - E - B - D
    d(V x)/dt  = M      - (B + D) x              x = c / c_makeup (cycles)
    d(V A)/dt  = M A_m  - (B + D) A - 2 n        A alkalinity eq/kg, n mol/s H2SO4
    d(V s)/dt  =        - (B + D) s + n MW_SO4   s = acid-derived sulfate

Sulfuric acid is diprotic: one mole removes two equivalents of alkalinity.

THE pH. Not a curve of our own. Total alkalinity is the state, because CO2
exchange with air does not change it, and pH follows from the proton balance of
an open carbonate system at atmospheric pCO2 using the engine's own constants:

    A = K1 KH pCO2/h + 2 K1 K2 KH pCO2/h^2 + Kw/h - h

In the bicarbonate region this IS `chemistry.ph_atmospheric_equilibrium`
(tests/test_safety.py holds the agreement). Beyond it, it carries the excess
strong acid that the engine's closure cannot: at zero alkalinity the engine
returns pH -0.75, this returns the pH of CO2-saturated water. Kw is from
phreeqc.dat (log_k -14.000, delta_h 13.362 kcal/mol), the one constant the
engine did not already carry. Activity coefficients are ignored, as in the
engine. Open system = CO2 stripped as fast as acid releases it = the HIGHEST pH
for a given alkalinity, so every time-to-threshold without interlocks is an
upper bound.

Harness stand-ins, all [J] and all pre-registered: a proportional conductivity
bleed controller, a 30 s probe lag, seeded measurement noise, a well-mixed
basin, and a low-level pump trip at 20 % of inventory.
"""
from __future__ import annotations

import json
import math
import pathlib
import random
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem
import conductivity as cond_model
import controller as ctl
import safety

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# --- plant, modelica/TowerBasin.mo ------------------------------------------
BASIN_KG = 50_000.0
EVAP_KG_S = 4.2
CIRC_KG_S = 478.0
DRIFT_KG_S = ctl.DRIFT_FRACTION * CIRC_KG_S
CYCLES0 = 5.0
T_BASIN_C = 30.0
PH_SETPOINT = 8.0
MAKEUP = chem.ARAMCO_FIELD_VALIDATED
LOW_LEVEL_FRACTION = 0.20
PROBE_LAG_S = 30.0
NOISE_PH, NOISE_COND, NOISE_FLOW = 0.005, 0.002, 0.005
T_FAULT_S = 2 * 3600.0
BLEED_KP = 5.0
BLEED_MAX_FACTOR = 3.0

# the thresholds the no-interlock run is reported against (pre-registered)
THRESHOLDS = (6.5, 5.5, 4.0)

LOG_KW_25, DH_KW_KCAL = -14.000, 13.362      # phreeqc.dat, H2O = OH- + H+


# ---------------------------------------------------------------------------
# Carbonate chemistry from the engine's constants
# ---------------------------------------------------------------------------
def _carbonate_constants(T_c):
    K = 10.0 ** (chem.log_k1_carbonic(T_c) + chem.log_kh_co2(T_c)
                 + math.log10(chem.P_CO2_ATM))
    K2 = 10.0 ** chem.log_k2_carbonic(T_c)
    Kw = 10.0 ** chem._vant_hoff(LOG_KW_25, DH_KW_KCAL, T_c)
    return K, K2, Kw


def alkalinity_at_ph(pH, T_c=T_BASIN_C):
    """Total alkalinity (eq/kg) of an open carbonate system at this pH."""
    K, K2, Kw = _carbonate_constants(T_c)
    h = 10.0 ** (-pH)
    return K / h + 2.0 * K * K2 / h ** 2 + Kw / h - h


def ph_from_alkalinity(alk, T_c=T_BASIN_C, _k=None):
    """Invert the proton balance. f(h) is strictly decreasing and convex, so
    Newton from the no-carbonate root converges monotonically."""
    K, K2, Kw = _k if _k is not None else _carbonate_constants(T_c)
    h = (-alk + math.sqrt(alk * alk + 4.0 * (K + Kw))) / 2.0
    for _ in range(50):
        f = K / h + 2.0 * K * K2 / h ** 2 + Kw / h - h - alk
        fp = -K / h ** 2 - 4.0 * K * K2 / h ** 3 - Kw / h ** 2 - 1.0
        step = f / fp
        h -= step
        if abs(step) < 1e-12 * h:
            break
    return -math.log10(h)


# ---------------------------------------------------------------------------
# Steady state before the fault
# ---------------------------------------------------------------------------
def steady_state(cycles=CYCLES0, ph=PH_SETPOINT, T_c=T_BASIN_C):
    wb = ctl.water_balance(EVAP_KG_S, CIRC_KG_S, cycles)
    per_kg, _ = ctl.acid_dose_for_ph(MAKEUP, cycles, ph, T_c)
    acid_kg_s = per_kg * (wb["blowdown"] + wb["drift"])     # defect 25 basis
    n = acid_kg_s / safety.MW_H2SO4_KG
    return {
        "makeup": wb["makeup"], "blowdown": wb["blowdown"], "drift": wb["drift"],
        "acid_kg_s": acid_kg_s,
        "alkalinity": alkalinity_at_ph(ph, T_c),
        "acid_so4_mg_kg": n * safety.MW_SO4_MG / (wb["blowdown"] + wb["drift"]),
    }


def water_state(x, alk, so4_acid, pH):
    w = MAKEUP.concentrate(x)
    w.HCO3 = max(alk, 0.0) * safety.MW_HCO3_MG
    w.SO4 = w.SO4 + max(so4_acid, 0.0)
    w.pH = pH
    return w


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
FAULTS = {
    "F0": None,
    "F1": "makeup_trip",
    "F2": "ph_control_stuck_high",
    "F3": "ph_control_drift",
    "F4a": "cond_fouling",
    "F4b": "cond_step_blowdown_closed",
    "F5": "heartbeat_lost",
    "F6": "pump_stuck_after_trip",
    "F7": "blowdown_stuck_closed",
    "F8": "makeup_trip_meter_reads_normal",
    "S1": "makeup_trip",
}


@dataclass
class Scenario:
    row: str
    mode: str = "active"
    hours: float = 8.0
    seed: int = 20260917
    reset_at_s: float = None       # optional operator reset attempt

    @property
    def fault(self):
        return FAULTS[self.row]


def run(sc):
    fault = sc.fault
    tf = T_FAULT_S
    rng = random.Random(sc.seed)
    ss = steady_state()
    kc = _carbonate_constants(T_BASIN_C)
    cfg = safety.config_for_site(MAKEUP, CYCLES0, ss["makeup"], ss["acid_kg_s"],
                                 BASIN_KG, DRIFT_KG_S, T_BASIN_C)
    layer = safety.SafetyLayer(cfg, MAKEUP, mode=sc.mode,
                               initial_cycles=CYCLES0,
                               initial_alkalinity_eq_kg=ss["alkalinity"],
                               initial_acid_so4_mg_kg=ss["acid_so4_mg_kg"])

    V, x, alk, s = BASIN_KG, CYCLES0, ss["alkalinity"], ss["acid_so4_mg_kg"]
    pH = ph_from_alkalinity(alk, _k=kc)
    ph_ctrl_r = ph_trip_r = pH
    sc_ratio = (cond_model.specific_conductance(water_state(x, alk, s, pH))
                / cond_model.specific_conductance(MAKEUP.concentrate(CYCLES0)))
    sp_cache = {}

    def sc_setpoint(C):
        if C not in sp_cache:
            sp_cache[C] = sc_ratio * cond_model.specific_conductance(
                MAKEUP.concentrate(C))
        return sp_cache[C]

    pumps_on = True
    heartbeat = 0
    frozen_req = None
    B_cmd = ss["blowdown"]
    B_ff0 = ss["blowdown"]
    dt = cfg.scan_s
    n_steps = int(round(sc.hours * 3600.0 / dt))

    out = {"row": sc.row, "mode": sc.mode, "fault": fault, "t_fault_s": tf,
           "steady": ss, "trajectory": [], "delivered_acid_kg": 0.0}
    last_acid_positive_t = None
    ph_min_after = pH
    ph_min_t = tf
    cross = {th: None for th in THRESHOLDS}
    low_level_t = None
    first_disagree_t = None
    first_sci_trip_t = None
    first_trip_probe_below_t = None
    first_alarm_t = None
    cmd_equals_request = True
    passthrough_after_proving = True
    reset_result = None

    for k in range(n_steps + 1):
        t = k * dt
        after = t >= tf

        # --- actual plant flows at this instant ----------------------------
        E = EVAP_KG_S if pumps_on else 0.0
        D = DRIFT_KG_S if pumps_on else 0.0
        B_act = B_cmd if pumps_on else 0.0
        if fault == "blowdown_stuck_closed" and after:
            B_act = 0.0
        makeup_lost = fault in ("makeup_trip", "pump_stuck_after_trip",
                                "makeup_trip_meter_reads_normal") and after
        if makeup_lost:
            M_act = 0.0
        else:
            # level control: the float valve holds the basin full
            M_act = max(E + B_act + D + (BASIN_KG - V) / dt, 0.0)

        # --- measurements ---------------------------------------------------
        true_sc = cond_model.specific_conductance(water_state(x, alk, s, pH))
        cond_meas = true_sc * (1.0 + rng.uniform(-NOISE_COND, NOISE_COND))
        if fault == "cond_fouling" and after:
            cond_meas *= 1.0 - 0.4 * min((t - tf) / 21600.0, 1.0)
        if fault == "cond_step_blowdown_closed" and after:
            cond_meas *= 0.7
        m_meas = M_act * (1.0 + rng.uniform(-NOISE_FLOW, NOISE_FLOW))
        if fault == "makeup_trip_meter_reads_normal" and after:
            m_meas = ss["makeup"] * (1.0 + rng.uniform(-NOISE_FLOW, NOISE_FLOW))
        b_meas = B_act * (1.0 + rng.uniform(-NOISE_FLOW, NOISE_FLOW))
        ph_c = ph_ctrl_r + rng.uniform(-NOISE_PH, NOISE_PH)
        ph_t = ph_trip_r + rng.uniform(-NOISE_PH, NOISE_PH)
        if fault == "ph_control_stuck_high" and after:
            ph_c = 8.2
        if fault == "ph_control_drift" and after:
            ph_c += 0.5 * min((t - tf) / 3600.0, 1.0)

        # --- the optimiser's request ----------------------------------------
        acid_req = ss["acid_kg_s"]
        if fault == "ph_control_stuck_high" and after:
            acid_req = 2.0 * ss["acid_kg_s"]
        req = safety.Request(fan_pct=90.0, cycles=CYCLES0, acid_kg_s=acid_req,
                             heartbeat=heartbeat)
        if fault == "heartbeat_lost" and after:
            if frozen_req is None:
                frozen_req = req
            req = frozen_req
        else:
            heartbeat += 1

        # acid pump output this scan is known only after the command; the
        # frame carries last scan's pump output, as a real flow signal would
        frame = safety.Frame(
            t=t, ph_control=ph_c, ph_trip=ph_t, conductivity=cond_meas,
            makeup_flow=m_meas, blowdown_flow=b_meas,
            acid_flow=out.get("_pump_prev", ss["acid_kg_s"]),
            blowdown_command=B_cmd, evaporation_estimate=EVAP_KG_S)
        cmd = layer.scan(frame, req)
        if sc.reset_at_s is not None and abs(t - sc.reset_at_s) < dt / 2:
            reset_result = layer.manual_reset(t)
        if (cmd.acid_kg_s != req.acid_kg_s or cmd.cycles != req.cycles
                or cmd.fan_pct != req.fan_pct or not cmd.acid_isolation_open):
            cmd_equals_request = False
            if t > cfg.proving_time_s + dt:
                passthrough_after_proving = False

        # --- actuators ------------------------------------------------------
        pump = cmd.acid_kg_s
        if fault == "pump_stuck_after_trip" and after:
            pump = ss["acid_kg_s"]
        out["_pump_prev"] = pump * (1.0 + rng.uniform(-NOISE_FLOW, NOISE_FLOW))
        delivered = pump if cmd.acid_isolation_open else 0.0

        C_sp = cmd.cycles
        B_ff = max(EVAP_KG_S / (C_sp - 1.0) - DRIFT_KG_S, 0.0)
        if fault == "cond_step_blowdown_closed" and t >= tf - 600.0:
            B_cmd = 0.0                      # operator has the bleed closed
        elif cmd.blowdown_basis == "flow_ratio":
            B_cmd = B_ff
        else:
            e = (cond_meas - sc_setpoint(C_sp)) / sc_setpoint(C_sp)
            B_cmd = min(max(B_ff * (1.0 + BLEED_KP * e), 0.0),
                        BLEED_MAX_FACTOR * B_ff0)

        # --- integrate one scan ----------------------------------------------
        n = delivered / safety.MW_H2SO4_KG
        L = B_act + D
        V_new = V + (M_act - E - B_act - D) * dt
        xV = x * V + (M_act - L * x) * dt
        aV = alk * V + (M_act * layer._a_m - L * alk - 2.0 * n) * dt
        sV = s * V + (-L * s + n * safety.MW_SO4_MG) * dt
        V = min(V_new, BASIN_KG)
        x, alk, s = xV / V, aV / V, sV / V
        pH = ph_from_alkalinity(alk, _k=kc)
        ph_ctrl_r += (pH - ph_ctrl_r) * dt / PROBE_LAG_S
        ph_trip_r += (pH - ph_trip_r) * dt / PROBE_LAG_S
        if pumps_on and V < LOW_LEVEL_FRACTION * BASIN_KG:
            pumps_on = False
            low_level_t = t + dt
        out["delivered_acid_kg"] += delivered * dt

        # --- bookkeeping -----------------------------------------------------
        if delivered > 0.0:
            last_acid_positive_t = t
        if after:
            if pH < ph_min_after:
                ph_min_after, ph_min_t = pH, t + dt
            for th in THRESHOLDS:
                if cross[th] is None and pH < th:
                    cross[th] = t + dt - tf
            if first_disagree_t is None and abs(ph_c - ph_t) > cfg.ph_disagree:
                first_disagree_t = t
            if (first_sci_trip_t is None and layer.sci_pct is not None
                    and layer.sci_pct > cfg.sci_trip_pct):
                first_sci_trip_t = t
            if first_trip_probe_below_t is None and ph_t < cfg.low_ph_trip:
                first_trip_probe_below_t = t
        if first_alarm_t is None and safety.LOW_PH_ALARM in layer.alarms:
            first_alarm_t = t
        if k % 60 == 0:
            out["trajectory"].append({
                "t_s": t, "pH": round(pH, 4), "V_kg": round(V, 1),
                "cycles": round(x, 4), "acid_kg_h": round(delivered * 3600, 4),
                "blowdown_kg_s": round(B_act, 4), "tripped": cmd.tripped})

    out.pop("_pump_prev", None)
    acid_stop_t = (tf if last_acid_positive_t is None or last_acid_positive_t < tf
                   else last_acid_positive_t + dt)
    out.update({
        "acid_stop_after_fault_s": acid_stop_t - tf,
        "acid_flowing_at_end": last_acid_positive_t is not None
                               and last_acid_positive_t >= n_steps * dt - dt,
        "ph_min_after_fault": ph_min_after,
        "ph_min_t_s": ph_min_t,
        "cross_after_fault_s": {str(k): v for k, v in cross.items()},
        "low_level_after_fault_s": (None if low_level_t is None
                                    else low_level_t - tf),
        "first_disagree_t_s": first_disagree_t,
        "first_sci_over_trip_t_s": first_sci_trip_t,
        "first_trip_probe_below_t_s": first_trip_probe_below_t,
        "first_low_ph_alarm_t_s": first_alarm_t,
        "commands_equal_requests": cmd_equals_request,
        "passthrough_after_proving": passthrough_after_proving,
        "reset_refused": reset_result,
        "events": [{"t_s": e.t, "kind": e.kind, "cause": e.cause,
                    "detail": e.detail} for e in layer.events],
        "final_command": {"cycles": cmd.cycles, "acid_kg_s": cmd.acid_kg_s,
                          "isolation_open": cmd.acid_isolation_open,
                          "basis": cmd.blowdown_basis, "fan_pct": cmd.fan_pct},
        "final_latched": sorted(layer.latched),
        "config": {k: getattr(cfg, k) for k in (
            "makeup_proving_kg_s", "proving_time_s", "low_ph_trip",
            "low_ph_alarm", "dosing_margin", "acid_bound_kg_per_kg_makeup",
            "failsafe_cycles", "scan_s")},
    })
    return out


def first_trip(res, cause=None):
    for e in res["events"]:
        if e["kind"] == "TRIP" and (cause is None or e["cause"] == cause):
            return e
    return None


def hhmm(t_s):
    t = int(round(t_s))
    return f"{t // 3600:02d}:{(t % 3600) // 60:02d}:{t % 60:02d}"


def main() -> int:
    ss = steady_state()
    print("SAFETY INTERLOCK SIMULATION -- pre-registered in "
          "docs/staged/safety_preregistration.md\n")
    print(f"plant: {BASIN_KG/1000:.0f} t basin, E {EVAP_KG_S} kg/s, "
          f"{CYCLES0:g} cycles, pH {PH_SETPOINT}, {T_BASIN_C:g} C, "
          f"makeup {ss['makeup']:.3f} kg/s, blowdown {ss['blowdown']:.3f} kg/s")
    print(f"steady acid (engine, defect-25 basis): {ss['acid_kg_s']*3600:.3f} kg/h; "
          f"alkalinity at pH {PH_SETPOINT}: {ss['alkalinity']*1e3:.4f} meq/kg\n")

    no = run(Scenario("S1", mode="shadow"))
    yes = run(Scenario("F1", mode="active"))
    print("INCIDENT -- makeup to zero at 02:00, acid commanded on")
    print("  without interlocks (shadow):")
    for th in THRESHOLDS:
        c = no["cross_after_fault_s"][str(th)]
        print(f"    pH < {th}: " + ("not reached" if c is None else
                                   f"{c/60:.1f} min after the trip ({hhmm(T_FAULT_S + c)})"))
    ll = no["low_level_after_fault_s"]
    print("    low-level pump trip: " + ("not reached" if ll is None else
                                         f"{ll/60:.1f} min ({hhmm(T_FAULT_S + ll)})"))
    print(f"    minimum pH {no['ph_min_after_fault']:.2f} at {hhmm(no['ph_min_t_s'])}")
    print("    trajectory (true basin pH):")
    for r in no["trajectory"]:
        if T_FAULT_S - 1 <= r["t_s"] <= T_FAULT_S + 3 * 3600 and r["t_s"] % 600 == 0:
            print(f"      {hhmm(r['t_s'])}  pH {r['pH']:6.3f}  V {r['V_kg']/1000:5.1f} t"
                  f"  acid {r['acid_kg_h']:.3f} kg/h")
    print("  with interlocks (active):")
    print(f"    acid stopped {yes['acid_stop_after_fault_s']:.0f} s after the trip "
          f"(bound {yes['config']['proving_time_s'] + yes['config']['scan_s']:.0f} s)")
    print(f"    minimum pH after the trip {yes['ph_min_after_fault']:.3f} "
          f"(trip setpoint {yes['config']['low_ph_trip']})")
    ll = yes["low_level_after_fault_s"]
    print("    low-level pump trip: " + ("not reached" if ll is None else
                                         f"{ll/60:.1f} min"))
    t0 = first_trip(yes)
    print(f"    first trip: {t0['cause']} at {hhmm(t0['t_s'])}\n")

    summary = {"incident_without_interlocks": {k: no[k] for k in (
                   "cross_after_fault_s", "low_level_after_fault_s",
                   "ph_min_after_fault", "delivered_acid_kg")},
               "incident_with_interlocks": {k: yes[k] for k in (
                   "acid_stop_after_fault_s", "ph_min_after_fault",
                   "low_level_after_fault_s", "delivered_acid_kg")},
               "steady": ss,
               "trajectory_without_interlocks": no["trajectory"],
               "trajectory_with_interlocks": yes["trajectory"]}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "safety_incident.json").write_text(json.dumps(summary, indent=1))
    print("wrote results/safety_incident.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
