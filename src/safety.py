"""
MIZAN :: acid-dosing interlocks -- a software specification, simulated
=====================================================================

WHAT THIS IS NOT, FIRST.

This is NOT a certified safety function and it claims NO safety integrity
level. IEC 61511 (safety instrumented systems for the process industry) is the
reference framework it was written against, cited as a framework only: no
clause-level compliance is claimed and none has been assessed. In that
framework a protection layer must be independent of the control system it
protects. So:

    THE INDEPENDENT LOW-pH TRIP MUST BE BUILT IN HARDWARE -- its own probe,
    its own trip relay, a de-energise-to-trip contact in the acid pump supply
    -- independent of the edge computer that runs the optimiser and this file.

It is modelled here, in the same object as the software checks, only so that
the simulation can exercise it. If the edge computer dies, everything in this
file dies with it; the hardware trip and a hardware watchdog relay must not.

WHY IT EXISTS. `docs/robustness_gaps.md` section 7.2, from customer discovery:
makeup tripped overnight, acid kept pumping, and the condenser tubes were
destroyed. The optimiser computes an acid dose from a steady model; nothing
stood between that number and a pump. Until something does, the controller
must not be connected to a dosing pump on a real plant.

WHAT IT DOES. A deterministic, stateful layer with a fixed scan period that
sits between the optimiser's REQUESTED setpoints (fan, cycles, acid) and the
actuators:

  * makeup-flow proving  -- acid is permitted only after makeup flow has been
    above a threshold continuously for the proving time; lost on the first scan
    below it
  * independent low-pH trip -- separate probe, latched, manual reset only,
    with a pre-trip alarm
  * bounded dosing integral -- acid over a rolling window may not exceed a
    stoichiometric bound earned only by PROVEN makeup flow, computed with the
    engine's own acid stoichiometry and charged per defect 25
  * sensor plausibility  -- stale, frozen, out of range, rate of change,
    redundant-probe disagreement, the conductivity residual against a
    mass-balance observer, and a conductivity drop the mass balance forbids
  * heartbeat watchdog on the optimiser
  * fail-safe on any trip -- acid off and isolated, blowdown to a conservative
    cycles setpoint, fan untouched; every trip logged with cause and time
  * SHADOW mode (compute and log, actuate nothing) and ACTIVE mode. Shadow is
    the default, because the product ships read-only in shadow mode.

Every setpoint below is pre-registered, with its source or a [J] reason, in
`docs/staged/safety_preregistration.md`. The full description is in
`docs/safety_interlocks.md`.
"""
from __future__ import annotations

import math
import numbers
from collections import deque
from dataclasses import dataclass, field, replace

import conductivity as cond_model

# ---------------------------------------------------------------------------
# Causes
# ---------------------------------------------------------------------------
MAKEUP_NOT_PROVEN = "MAKEUP_NOT_PROVEN"      # self-clearing permissive
LOW_PH = "LOW_PH"                            # independent trip (hardware)
PH_PROBE_DISAGREE = "PH_PROBE_DISAGREE"
SENSOR_STALE = "SENSOR_STALE"
SENSOR_FROZEN = "SENSOR_FROZEN"
SENSOR_RANGE = "SENSOR_RANGE"
SENSOR_RATE = "SENSOR_RATE"
COND_CELL_FAULT = "COND_CELL_FAULT"
HEARTBEAT_LOST = "HEARTBEAT_LOST"
ACID_PUMP_STUCK = "ACID_PUMP_STUCK"
BLOWDOWN_VALVE_FAILED = "BLOWDOWN_VALVE_FAILED"
INVALID_INPUT = "INVALID_INPUT"
SCAN_TIMING_FAULT = "SCAN_TIMING_FAULT"
OPTIMIZER_UNAVAILABLE = "OPTIMIZER_UNAVAILABLE"

SELF_CLEARING = frozenset({MAKEUP_NOT_PROVEN})

# alarms: logged, never actuate
LOW_PH_ALARM = "LOW_PH_ALARM"
SCI_ALARM = "SCI_ALARM"
DOSING_BOUND_LIMITED = "DOSING_BOUND_LIMITED"

CHANNELS = ("ph_control", "ph_trip", "conductivity", "makeup_flow",
            "blowdown_flow", "acid_flow")
_FLOW_CHANNELS = ("makeup_flow", "blowdown_flow", "acid_flow")

MW_H2SO4_KG = 0.098079       # kg/mol, as in controller.acid_dose_for_ph
MW_SO4_MG = 96060.0          # mg/mol, chemistry.SPECIES
MW_HCO3_MG = 61017.0         # mg/mol, chemistry.SPECIES

# The repository's conservative cycles baseline. src/run_controller.py
# V7_BASELINE_CYCLES = 3.0, justified in docs/v7_preregistration.md by what
# operators on treated effluent actually run (Qatar Cool maximum 3; Aramco
# pilot 2.0 on groundwater, 3.5 on TSE). NOT conservative for austenitic
# stainless: defect 46 puts 316 at 1.85 cycles on the Riyadh water, so a site
# with 316 tubing must configure `failsafe_cycles` lower.
FAILSAFE_CYCLES_DEFAULT = 3.0


# ---------------------------------------------------------------------------
# The stoichiometric bound -- engine stoichiometry, defect 25 basis
# ---------------------------------------------------------------------------
def stoichiometric_acid_bound(makeup, cycles, ph_floor, T_c):
    """kg H2SO4 per kg of MAKEUP that would hold the loop at `ph_floor`.

    `controller.acid_dose_for_ph` returns kg per kg of CIRCULATING water, on
    the basis (C * a_makeup - a_target). DEFECT 25: that figure must be
    multiplied by the stream that carries alkalinity OUT, blowdown + drift,
    which is makeup / C -- never by makeup, which overstated the dose by
    exactly C. Here the bound is earned per kg of proven makeup, so the
    per-kg-circulating figure is divided by C.

    At `ph_floor` = the low-pH trip setpoint this is the most acid the loop can
    consume at steady state without its alkalinity being driven to the trip.
    Sulfuric acid is diprotic; the engine's 98.079/2 carries that.
    """
    import controller as ctl            # config time only, not in the scan
    per_kg_circulating, _ = ctl.acid_dose_for_ph(makeup, float(cycles),
                                                 float(ph_floor), float(T_c))
    return per_kg_circulating / float(cycles)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class InterlockConfig:
    """Setpoints. Defaults are the pre-registered values; see
    docs/staged/safety_preregistration.md for the source of each."""
    design_makeup_kg_s: float
    design_acid_kg_s: float
    acid_bound_kg_per_kg_makeup: float
    basin_kg: float
    drift_kg_s: float

    scan_s: float = 1.0
    makeup_proving_fraction: float = 0.20
    proving_time_s: float = 60.0
    low_ph_trip: float = 6.5
    low_ph_trip_scans: int = 3
    low_ph_alarm: float = 6.8
    dosing_window_s: float = 3600.0
    dosing_margin: float = 1.20
    heartbeat_timeout_s: float = 10.0
    stale_s: float = 5.0
    frozen_s: float = 900.0
    ph_range: tuple = (0.0, 14.0)
    cond_range_us_cm: tuple = (2.0, 2.0e6)     # 2 uS/cm - 2000 mS/cm
    ph_rate_max_per_min: float = 1.0
    ph_rate_window_s: float = 10.0
    ph_disagree: float = 0.3
    ph_disagree_s: float = 60.0
    sci_alarm_pct: float = 5.0
    sci_trip_pct: float = 15.0
    sci_trip_s: float = 600.0
    cond_drop_frac: float = 0.05
    cond_drop_window_s: float = 60.0
    blowdown_closed_kg_s: float = 0.05
    pump_stuck_frac: float = 0.05
    pump_stuck_scans: int = 3
    blowdown_fail_frac: float = 0.20
    blowdown_fail_min_cmd_kg_s: float = 0.1
    blowdown_fail_s: float = 120.0
    failsafe_cycles: float = FAILSAFE_CYCLES_DEFAULT
    # NOT pre-registered; added after the incident run, default OFF so the
    # registered fail-safe is what the matrix tests. On loss of makeup a
    # blowdown valve can only throw away inventory that cannot be replaced:
    # the simulation found the registered fail-safe empties the basin sooner.
    # See docs/defect_register.md, defect 56.
    hold_blowdown_on_makeup_loss: bool = False

    @property
    def makeup_proving_kg_s(self):
        return self.makeup_proving_fraction * self.design_makeup_kg_s


def config_for_site(makeup, design_cycles, design_makeup_kg_s,
                    design_acid_kg_s, basin_kg, drift_kg_s, T_c, **overrides):
    """Build a config whose dosing bound comes from the engine's chemistry."""
    ph_trip = overrides.get("low_ph_trip", InterlockConfig.low_ph_trip)
    bound = stoichiometric_acid_bound(makeup, design_cycles, ph_trip, T_c)
    return InterlockConfig(design_makeup_kg_s=float(design_makeup_kg_s),
                           design_acid_kg_s=float(design_acid_kg_s),
                           acid_bound_kg_per_kg_makeup=bound,
                           basin_kg=float(basin_kg),
                           drift_kg_s=float(drift_kg_s), **overrides)


# ---------------------------------------------------------------------------
# I/O records
# ---------------------------------------------------------------------------
@dataclass
class Request:
    """What the optimiser asks for this scan."""
    fan_pct: float
    cycles: float
    acid_kg_s: float
    heartbeat: int


@dataclass
class Frame:
    """What the instruments say this scan. `age_s` gives per-channel time
    since the value was last refreshed (0 if fresh)."""
    t: float
    ph_control: float
    ph_trip: float
    conductivity: float           # uS/cm at 25 C, as the transmitter reports
    makeup_flow: float            # kg/s
    blowdown_flow: float          # kg/s
    acid_flow: float              # kg/s at the pump discharge, upstream of isolation
    blowdown_command: float       # kg/s the bleed controller is asking the valve for
    evaporation_estimate: float   # kg/s, from the tower model
    age_s: dict = field(default_factory=dict)


@dataclass
class Command:
    # None means no validated previous request exists for that actuator.
    # It is not a numerical actuator setting and must never be written as one.
    fan_pct: float | None
    cycles: float | None
    acid_kg_s: float
    acid_isolation_open: bool
    blowdown_basis: str           # "conductivity" | "flow_ratio"
    tripped: bool
    causes: tuple
    blowdown_hold: bool = False   # close the bleed regardless of basis


@dataclass
class Event:
    t: float
    kind: str                     # TRIP | CLEAR | ALARM | RESET | RESET_REFUSED | INFO
    cause: str
    detail: str = ""


# ---------------------------------------------------------------------------
# The layer
# ---------------------------------------------------------------------------
class SafetyLayer:
    """Deterministic interlock layer. Call `scan()` once per `cfg.scan_s`."""

    def __init__(self, cfg, makeup_water, mode="shadow",
                 initial_cycles=None, initial_alkalinity_eq_kg=None,
                 initial_acid_so4_mg_kg=0.0):
        if mode not in ("shadow", "active"):
            raise ValueError("mode must be 'shadow' or 'active'")
        if not _finite_number(cfg.scan_s) or cfg.scan_s <= 0:
            raise ValueError("scan_s must be finite and positive")
        self.cfg = cfg
        self.makeup = makeup_water
        self.mode = mode
        self.events = []

        self._a_m = makeup_water.molality()["HCO3"]        # eq/kg
        # mass-balance observer, initialised from the commissioning analysis
        self._obs_x = float(initial_cycles) if initial_cycles else None
        self._obs_alk = (float(initial_alkalinity_eq_kg)
                         if initial_alkalinity_eq_kg is not None else None)
        self._obs_so4 = float(initial_acid_so4_mg_kg)

        self._t_prev = None
        self._proven = False
        self._above_since = None
        self._trip_low_count = 0
        self._disagree_since = None
        self._sci_since = None
        self._sci = None
        self._pump_stuck_count = 0
        self._bd_fail_since = None
        self._hb_value = None
        self._hb_changed_t = None
        self._last_val = {}
        self._last_change_t = {}
        self._ph_hist = {"ph_control": deque(), "ph_trip": deque()}
        self._cond_hist = deque()
        self._window = deque()          # (t, acid_kg, allowance_kg)
        self._win_acid = 0.0
        self._win_allow = 0.0
        self._last_acid_cmd = 0.0
        self._last_isolation_open = False
        self._last_valid_request = None

        self.latched = set()            # latched trip causes
        self.active = set()             # causes whose condition holds now
        self.alarms = set()
        self.would_be = None            # the command active mode would issue

    # -- logging -----------------------------------------------------------
    def _log(self, t, kind, cause, detail=""):
        self.events.append(Event(float(t), kind, cause, detail))

    def _set_condition(self, t, cause, holds, detail=""):
        was = cause in self.active
        if holds and not was:
            self.active.add(cause)
            if cause not in self.latched:
                self._log(t, "TRIP", cause, detail)
            if cause not in SELF_CLEARING:
                self.latched.add(cause)
        elif not holds and was:
            self.active.discard(cause)
            if cause in SELF_CLEARING:
                self._log(t, "CLEAR", cause, detail)

    def _set_alarm(self, t, alarm, holds, detail=""):
        if holds and alarm not in self.alarms:
            self.alarms.add(alarm)
            self._log(t, "ALARM", alarm, detail)
        elif not holds and alarm in self.alarms:
            self.alarms.discard(alarm)
            self._log(t, "CLEAR", alarm, detail)

    # -- checks ------------------------------------------------------------
    def _plausibility(self, f):
        c = self.cfg
        bad_stale, bad_frozen, bad_range, bad_rate = [], [], [], []
        for ch in CHANNELS:
            v = getattr(f, ch)
            if f.age_s.get(ch, 0.0) > c.stale_s:
                bad_stale.append(ch)
            if v is None or (isinstance(v, float) and math.isnan(v)):
                bad_range.append(ch)
                continue
            # frozen: bit-identical for frozen_s. A flow meter's low-flow
            # cutoff legitimately holds exactly zero, so zero is exempt there.
            if ch not in self._last_val or v != self._last_val[ch]:
                self._last_val[ch] = v
                self._last_change_t[ch] = f.t
            elif not (ch in _FLOW_CHANNELS and v == 0.0):
                if f.t - self._last_change_t[ch] >= c.frozen_s:
                    bad_frozen.append(ch)
            if ch.startswith("ph_"):
                if not (c.ph_range[0] <= v <= c.ph_range[1]):
                    bad_range.append(ch)
            elif ch == "conductivity":
                if not (c.cond_range_us_cm[0] <= v <= c.cond_range_us_cm[1]):
                    bad_range.append(ch)
            elif v < 0.0:
                bad_range.append(ch)
        for ch in ("ph_control", "ph_trip"):
            h = self._ph_hist[ch]
            h.append((f.t, getattr(f, ch)))
            while h and f.t - h[0][0] > c.ph_rate_window_s:
                h.popleft()
            if len(h) >= 2 and f.t - h[0][0] >= c.ph_rate_window_s - 1e-9:
                rate = abs(h[-1][1] - h[0][1]) / (f.t - h[0][0]) * 60.0
                if rate > c.ph_rate_max_per_min:
                    bad_rate.append(ch)
        self._set_condition(f.t, SENSOR_STALE, bool(bad_stale), ",".join(bad_stale))
        self._set_condition(f.t, SENSOR_FROZEN, bool(bad_frozen), ",".join(bad_frozen))
        self._set_condition(f.t, SENSOR_RANGE, bool(bad_range), ",".join(bad_range))
        self._set_condition(f.t, SENSOR_RATE, bool(bad_rate), ",".join(bad_rate))
        return not (bad_range or bad_stale)

    def _makeup_proving(self, f):
        c = self.cfg
        if f.makeup_flow >= c.makeup_proving_kg_s:
            if self._above_since is None:
                self._above_since = f.t
            if not self._proven and f.t - self._above_since >= c.proving_time_s:
                self._proven = True
                if MAKEUP_NOT_PROVEN in self.active:
                    self._set_condition(f.t, MAKEUP_NOT_PROVEN, False,
                                        "makeup re-proven")
                else:
                    # first proving, or re-proving after a manual reset:
                    # a permissive being ESTABLISHED is not a trip clearing
                    self._log(f.t, "INFO", MAKEUP_NOT_PROVEN,
                              "makeup proven; acid permitted")
        else:
            # lost on the FIRST scan below threshold: no debounce on the safe side
            self._above_since = None
            if self._proven:
                self._proven = False
                self._set_condition(f.t, MAKEUP_NOT_PROVEN, True,
                                    f"makeup {f.makeup_flow:.3f} kg/s below "
                                    f"{c.makeup_proving_kg_s:.3f}")

    def _low_ph(self, f):
        c = self.cfg
        self._set_alarm(f.t, LOW_PH_ALARM,
                        min(f.ph_control, f.ph_trip) < c.low_ph_alarm,
                        f"control {f.ph_control:.2f}, trip probe {f.ph_trip:.2f}")
        if f.ph_trip < c.low_ph_trip:
            self._trip_low_count += 1
        else:
            self._trip_low_count = 0
        holds = self._trip_low_count >= c.low_ph_trip_scans
        if LOW_PH in self.latched:
            # latched: the condition for RESET is recovery above the alarm
            self._set_condition(f.t, LOW_PH, f.ph_trip < c.low_ph_alarm)
        else:
            self._set_condition(f.t, LOW_PH, holds,
                                f"independent probe {f.ph_trip:.2f} < {c.low_ph_trip}")

    def _disagreement(self, f):
        c = self.cfg
        d = abs(f.ph_control - f.ph_trip)
        if d > c.ph_disagree:
            if self._disagree_since is None:
                self._disagree_since = f.t
        else:
            self._disagree_since = None
        if PH_PROBE_DISAGREE in self.latched:
            self._set_condition(f.t, PH_PROBE_DISAGREE, d > c.ph_disagree)
        else:
            holds = (self._disagree_since is not None
                     and f.t - self._disagree_since >= c.ph_disagree_s)
            self._set_condition(f.t, PH_PROBE_DISAGREE, holds,
                                f"|{f.ph_control:.2f} - {f.ph_trip:.2f}| > {c.ph_disagree}")

    def _observer_step(self, f, dt, acid_delivered_kg_s):
        """Mass-balance prediction of the loop from measured flows, the same
        balance as modelica/TowerBasin.mo, level-controlled basin."""
        if self._obs_x is None or dt <= 0:
            return
        c = self.cfg
        V = c.basin_kg
        M, L = f.makeup_flow, f.blowdown_flow + c.drift_kg_s
        n = acid_delivered_kg_s / MW_H2SO4_KG
        self._obs_x += (M - L * self._obs_x) / V * dt
        if self._obs_alk is not None:
            self._obs_alk += (M * self._a_m - L * self._obs_alk - 2.0 * n) / V * dt
        self._obs_so4 += (-L * self._obs_so4 + n * MW_SO4_MG) / V * dt

    def predicted_water(self, pH):
        w = self.makeup.concentrate(self._obs_x)
        if self._obs_alk is not None:
            w.HCO3 = max(self._obs_alk, 0.0) * MW_HCO3_MG
        w.SO4 = w.SO4 + max(self._obs_so4, 0.0)
        w.pH = pH
        return w

    def _conductivity(self, f, valid):
        c = self.cfg
        # (a) residual against the mass-balance observer. Suspended while
        # makeup is unproven: the level-controlled-basin assumption fails.
        sci_holds = False
        if valid and self._obs_x is not None and self._proven:
            w = self.predicted_water(f.ph_control)
            self._sci = cond_model.specific_conductance_imbalance(
                w, f.conductivity)["sci_pct"]
            self._set_alarm(f.t, SCI_ALARM, self._sci > c.sci_alarm_pct,
                            f"SCI {self._sci:+.1f} %")
            if self._sci > c.sci_trip_pct:
                if self._sci_since is None:
                    self._sci_since = f.t
                sci_holds = f.t - self._sci_since >= c.sci_trip_s
            else:
                self._sci_since = None
        # (b) a drop the mass balance forbids, with blowdown closed
        h = self._cond_hist
        h.append((f.t, f.conductivity))
        while h and f.t - h[0][0] > c.cond_drop_window_s:
            h.popleft()
        peak = max(v for _, v in h)
        drop = (peak - f.conductivity) / peak if peak > 0 else 0.0
        drop_holds = (f.blowdown_flow < c.blowdown_closed_kg_s
                      and drop > c.cond_drop_frac)
        if COND_CELL_FAULT in self.latched:
            still = (self._sci is not None and self._sci > c.sci_alarm_pct) or drop_holds
            self._set_condition(f.t, COND_CELL_FAULT, still)
        else:
            detail = (f"SCI {self._sci:+.1f} % for {c.sci_trip_s:.0f} s"
                      if sci_holds else
                      f"conductivity fell {100*drop:.1f} % in "
                      f"{c.cond_drop_window_s:.0f} s with blowdown closed")
            self._set_condition(f.t, COND_CELL_FAULT, sci_holds or drop_holds, detail)

    def _heartbeat(self, f, req):
        if self._hb_value is None or req.heartbeat != self._hb_value:
            self._hb_value = req.heartbeat
            self._hb_changed_t = f.t
        lost = f.t - self._hb_changed_t > self.cfg.heartbeat_timeout_s
        self._set_condition(f.t, HEARTBEAT_LOST, lost,
                            f"heartbeat unchanged {f.t - self._hb_changed_t:.0f} s")

    def _final_elements(self, f):
        c = self.cfg
        # acid pump delivering while commanded off
        if (self._last_acid_cmd == 0.0
                and f.acid_flow > c.pump_stuck_frac * c.design_acid_kg_s):
            self._pump_stuck_count += 1
        else:
            self._pump_stuck_count = 0
        if ACID_PUMP_STUCK in self.latched:
            self._set_condition(f.t, ACID_PUMP_STUCK,
                                f.acid_flow > c.pump_stuck_frac * c.design_acid_kg_s)
        else:
            self._set_condition(f.t, ACID_PUMP_STUCK,
                                self._pump_stuck_count >= c.pump_stuck_scans,
                                f"acid flow {f.acid_flow*3600:.2f} kg/h with command off")
        # blowdown valve not passing what it is commanded
        failing = (f.blowdown_command > c.blowdown_fail_min_cmd_kg_s
                   and f.blowdown_flow < c.blowdown_fail_frac * f.blowdown_command)
        if failing:
            if self._bd_fail_since is None:
                self._bd_fail_since = f.t
        else:
            self._bd_fail_since = None
        if BLOWDOWN_VALVE_FAILED in self.latched:
            self._set_condition(f.t, BLOWDOWN_VALVE_FAILED, failing)
        else:
            self._set_condition(f.t, BLOWDOWN_VALVE_FAILED,
                                failing and f.t - self._bd_fail_since >= c.blowdown_fail_s,
                                f"blowdown {f.blowdown_flow:.2f} kg/s against "
                                f"command {f.blowdown_command:.2f}")

    def _dosing_bound(self, f, acid_request_kg_s, dt):
        c = self.cfg
        allow = (c.dosing_margin * c.acid_bound_kg_per_kg_makeup
                 * f.makeup_flow * c.scan_s) if self._proven else 0.0
        while self._window and f.t - self._window[0][0] >= c.dosing_window_s:
            _, a, al = self._window.popleft()
            self._win_acid -= a
            self._win_allow -= al
        remaining = self._win_allow + allow - self._win_acid
        granted = min(acid_request_kg_s, max(remaining, 0.0) / c.scan_s)
        limited = granted < acid_request_kg_s - 1e-15
        self._set_alarm(f.t, DOSING_BOUND_LIMITED, limited,
                        f"window acid at stoichiometric bound x{c.dosing_margin}")
        return granted, allow

    # -- the scan ----------------------------------------------------------
    def _admission_errors(self, f, req):
        """Reject malformed data before it reaches observers or histories.

        Empty age_s retains the existing simulation convention of fresh
        channels; supplied ages must be finite and nonnegative. A physical
        adapter must supply independently measured freshness metadata.
        """
        bad = []
        for name in ("t", *CHANNELS, "blowdown_command", "evaporation_estimate"):
            value = getattr(f, name, None)
            if not _finite_number(value):
                bad.append(name)
            elif name in ("t", *_FLOW_CHANNELS, "blowdown_command",
                           "evaporation_estimate") and value < 0:
                bad.append(name)
        ages = getattr(f, "age_s", None)
        if not isinstance(ages, dict):
            bad.append("age_s")
        else:
            for name, value in ages.items():
                if name not in CHANNELS or not _finite_number(value) or value < 0:
                    bad.append(f"age_s.{name}")
        for name in ("fan_pct", "cycles", "acid_kg_s"):
            value = getattr(req, name, None)
            if not _finite_number(value):
                bad.append(f"request.{name}")
            elif ((name == "fan_pct" and not 0 <= value <= 100)
                  or (name == "cycles" and value <= 1)
                  or (name == "acid_kg_s" and value < 0)):
                bad.append(f"request.{name}")
        heartbeat = getattr(req, "heartbeat", None)
        if (isinstance(heartbeat, bool) or not isinstance(heartbeat, numbers.Integral)
                or heartbeat < 0):
            bad.append("request.heartbeat")
        return bad

    def reject_request(self, f, cause=OPTIMIZER_UNAVAILABLE, detail=""):
        """Issue an explicit acid-off result when no trustworthy request exists.

        This is an acid interlock only, not a thermally qualified plant
        fallback. Other actuators retain the last validated request where
        available. The fault latches until a valid scan and manual reset.
        Both modes expose a finite, isolated command on malformed input;
        the shadow harness must still perform no physical writes.
        """
        value = getattr(f, "t", None)
        t = value if _finite_number(value) and value >= 0 else self._t_prev
        t = 0.0 if t is None else t
        self._set_condition(t, cause, True, detail)
        if self._t_prev is None or t > self._t_prev:
            self._t_prev = t
        self._proven = False
        self._above_since = None
        self._ph_hist = {"ph_control": deque(), "ph_trip": deque()}
        self._cond_hist.clear()
        previous = self._last_valid_request
        self.would_be = Command(
            fan_pct=previous.fan_pct if previous is not None else None,
            cycles=min(previous.cycles, self.cfg.failsafe_cycles)
                   if previous is not None else None,
            acid_kg_s=0.0, acid_isolation_open=False,
            blowdown_basis="flow_ratio", tripped=True,
            causes=tuple(sorted(self.latched | (self.active & SELF_CLEARING))))
        self._last_acid_cmd = 0.0
        self._last_isolation_open = False
        return self.would_be

    def scan(self, f, req):
        c = self.cfg
        bad = self._admission_errors(f, req)
        if bad:
            return self.reject_request(f, INVALID_INPUT, ",".join(bad))
        dt = c.scan_s if self._t_prev is None else f.t - self._t_prev
        # The registered harness uses a fixed scan period. Missing,
        # repeated, backward or faster scans cannot establish continuous
        # flow or safely use the fixed-period rolling dose accounting.
        if not math.isclose(dt, c.scan_s, rel_tol=1e-6, abs_tol=1e-9):
            return self.reject_request(f, SCAN_TIMING_FAULT,
                                       f"interval {dt:g} s; expected {c.scan_s:g} s")
        self._t_prev = f.t
        for cause in (INVALID_INPUT, SCAN_TIMING_FAULT, OPTIMIZER_UNAVAILABLE):
            self._set_condition(f.t, cause, False)
        self._last_valid_request = replace(req)

        # observer runs on what was actually commanded last scan
        delivered_est = (f.acid_flow if self._last_isolation_open else 0.0)
        self._observer_step(f, dt, delivered_est)

        valid = self._plausibility(f)
        self._heartbeat(f, req)
        self._makeup_proving(f)
        self._low_ph(f)
        self._disagreement(f)
        self._conductivity(f, valid)
        self._final_elements(f)

        tripped = bool(self.latched) or bool(self.active & SELF_CLEARING)
        causes = tuple(sorted(self.latched | (self.active & SELF_CLEARING)))
        if tripped or not self._proven:
            acid, allow = 0.0, 0.0
            isolation_open = False
        else:
            acid, allow = self._dosing_bound(f, max(req.acid_kg_s, 0.0), dt)
            isolation_open = True
        self._window.append((f.t, acid * c.scan_s, allow))
        self._win_acid += acid * c.scan_s
        self._win_allow += allow

        untrusted_cond = bool({COND_CELL_FAULT, SENSOR_RANGE, SENSOR_STALE,
                               SENSOR_FROZEN} & self.latched)
        cycles = min(req.cycles, c.failsafe_cycles) if tripped else req.cycles
        hold = (c.hold_blowdown_on_makeup_loss
                and MAKEUP_NOT_PROVEN in self.active)
        self.would_be = Command(
            fan_pct=req.fan_pct, cycles=cycles, acid_kg_s=acid,
            acid_isolation_open=isolation_open,
            blowdown_basis="flow_ratio" if untrusted_cond else "conductivity",
            tripped=tripped, causes=causes, blowdown_hold=hold)

        if self.mode == "active":
            out = self.would_be
        else:
            out = Command(fan_pct=req.fan_pct, cycles=req.cycles,
                          acid_kg_s=req.acid_kg_s, acid_isolation_open=True,
                          blowdown_basis="conductivity", tripped=False, causes=())
        self._last_acid_cmd = out.acid_kg_s if out.acid_isolation_open else 0.0
        self._last_isolation_open = out.acid_isolation_open
        return out

    # -- operator ----------------------------------------------------------
    def manual_reset(self, t):
        """Clear latched trips whose cause no longer holds. Returns the causes
        that were refused. Acid still waits for makeup to be re-proven."""
        refused = []
        for cause in sorted(self.latched):
            if cause in self.active:
                refused.append(cause)
                self._log(t, "RESET_REFUSED", cause, "condition still present")
            else:
                self.latched.discard(cause)
                self._log(t, "RESET", cause)
        if not refused:
            self._proven = False
            self._above_since = None
        return refused

    @property
    def sci_pct(self):
        return self._sci

    def trips(self):
        return [e for e in self.events if e.kind == "TRIP"]


def _finite_number(value):
    return (not isinstance(value, bool) and isinstance(value, numbers.Real)
            and math.isfinite(value))
