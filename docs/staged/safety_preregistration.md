# Safety interlocks: pre-registration

**Written and committed before the first simulation run, 17 September 2026.**
Branch `feat/safety-interlocks`. Nothing in this file may be edited after the
simulation has been run except to append a clearly dated results section. A row
of the fault matrix that fails is reported as failing; the matrix is not
changed to make it pass.

## What this is, and what it is not

A **software interlock specification** (`src/safety.py`) and a **simulation**
(`src/safety_sim.py`) of it on the repository's basin model. It is **not a
certified safety function** and claims **no SIL**. IEC 61511 (functional safety,
safety instrumented systems for the process industry) is cited as the reference
framework only; no compliance with it is claimed, and the standard was not read
clause by clause for this work. In that framework the protection layer must be
independent of the control system it protects. Here that means the
**independent low-pH trip must be built in hardware**: its own probe, its own
trip amplifier or relay, and a de-energise-to-trip contact in the acid pump
supply, independent of the edge computer that runs the optimiser and this
layer. The simulation models that trip as part of the layer so it can be tested
at all; that is a modelling convenience, not an architecture.

## Plant and chemistry used (all from the repository, none fitted)

| quantity | value | source |
|---|---|---|
| basin inventory | 50,000 kg | `modelica/TowerBasin.mo` |
| evaporation | 4.2 kg/s | `modelica/TowerBasin.mo` |
| circulating flow, drift | 478 kg/s, drift 1e-5 of it | `modelica/TowerBasin.mo`, `tower.DRIFT_FRACTION` |
| cycles before the fault | 5.0 (time constant 13.2 h, `modelica/README.md`) | steady balance `controller.water_balance` |
| makeup water | `chemistry.ARAMCO_FIELD_VALIDATED` (HCO3 105, SO4 300 mg/L) | field-validated analysis |
| basin temperature | 30 °C [J] | the mean used by `tests/test_basin_dynamics.py` |
| pH setpoint | 8.0 | the optimum band 8.00–8.25, `docs/defect_register.md` Part 3 |
| acid command before the fault | engine steady dose: `controller.acid_dose_for_ph` × (blowdown + drift), defect 25 | computed, not simulated |

**pH response.** The state variable is total alkalinity (eq/kg), which CO2
exchange with air does not change. pH follows from the proton balance of an
open carbonate system at atmospheric pCO2,

    Alk = K1·KH·pCO2/[H+] + 2·K1·K2·KH·pCO2/[H+]² + Kw/[H+] − [H+]

using the engine's own `log_k1_carbonic`, `log_k2_carbonic`, `log_kh_co2` and
`P_CO2_ATM`, and Kw from phreeqc.dat (log_k −14.000, ΔH 13.362 kcal/mol). In the
bicarbonate region this reduces to `chemistry.ph_atmospheric_equilibrium`, and a
test holds that agreement. Beyond it, it carries the excess strong acid that the
engine's closure cannot represent. Activity coefficients are ignored, as in the
engine. Sulfuric acid is **diprotic**: 1 mol H2SO4 removes 2 eq of alkalinity
and adds 1 mol of SO4.

**Direction of the open-system assumption.** Assuming the tower strips the CO2
the acid releases gives the **highest** pH for a given alkalinity. So the
no-interlock times below are **upper bounds**: the real loop gets there no
later. The interlocked acceptance does not depend on it, because the interlocks
stop the acid before alkalinity is consumed.

**Harness-only stand-ins [J]:** a proportional conductivity bleed controller;
pH probes with a 30 s first-order lag; seeded measurement noise (±0.005 pH,
±0.2 % conductivity, ±0.5 % flow); a well-mixed basin (local low pH at the
injection point is not modelled); circulating pumps trip on basin low level at
20 % of inventory, after which evaporation, blowdown and drift stop.

## Incident scenario

**Makeup flow trips to zero at 02:00:00 with the acid pump commanded on**, at
the pre-trip steady dose, and the command does not adapt. That is what a
supervisory acid setpoint is; it is also what a pH feedback loop does with a
probe stuck high. Evaporation continues. Simulated from 00:00 to 08:00, or until
the low-level pump trip.

**Acceptance, with interlocks (active mode):**
- **A1.** Delivered acid is zero no later than **proving time + one scan**
  after 02:00:00, i.e. by 02:01:01.
- **A2.** True basin pH stays **above the low-pH trip setpoint, 6.5**, over the
  whole horizon.

**Report, without interlocks (the same plant, layer in shadow mode):** the pH
trajectory, and the time from 02:00 to cross each threshold:

| threshold | meaning | source |
|---|---|---|
| **pH 6.5 (primary)** | onset of EN 206 exposure class XA1 (pH ≤ 6.5) for concrete in contact with water | EN 206 Table 2, as reproduced by Whittaker & Black (2015), *Adv. Cem. Res.*, University of Leeds eprint 84114 [C, verified from the reproduction, not the standard] |
| pH 5.5 | onset of XA2 | same table |
| pH 4.0 | below about pH 4 the corrosion rate of iron in aerated water rises steeply (Whitman, Russell & Altieri, 1924) | **[UNVERIFIED]**: secondary reference US Navy NCEL Technical Note N-907 returned HTTP 403 and was not read |

**Priors, stated before running:** P1, without interlocks pH crosses 6.5 before
the low-level pump trip. P2, A1 and A2 both pass.

## Setpoints

| setpoint | value | justification |
|---|---|---|
| scan period | 1 s | [J] fast against every process time here; the shortest is minutes |
| makeup proving threshold | 20 % of design makeup at the operating point | [J] below any legitimate part-load makeup the dose is computed for, and above the insertion magmeter's 0.05 m/s floor (GF Signet 2551, `docs/instrumentation_spec.md` §3) |
| **proving time** | **60 s** continuous above threshold before acid is permitted | [J] rejects a start-up surge and meter noise; negligible against the 13.2 h basin time constant |
| loss of proving | permissive removed on the **first** scan below threshold | [J] no debounce on the safe side |
| **low-pH trip** | **6.5**, independent probe, 3 consecutive scans, **latched, manual reset only**, reset refused while the trip probe is below the alarm setpoint | EN 206 XA1 onset (above); 0.5 pH below the optimiser's lowest permitted setpoint, pH 7.0 (`controller.optimise` `ph_grid`) |
| **pre-trip alarm** | **6.8**, either probe | [J] between the optimiser's floor 7.0 and the trip; 0.3 pH is the same tolerance as probe disagreement. No vendor publishes pH drift (`docs/instrumentation_spec.md` §8) |
| dosing window | rolling 3,600 s | [J] |
| **dosing bound** | window acid ≤ **margin** × Σ proven makeup × `acid_dose_for_ph(makeup, C, 6.5, T)` / C | Engine stoichiometry. The engine's per-kg figure is on the circulating basis, so it is multiplied by makeup/C = blowdown + drift (**defect 25**), never by makeup. At target pH 6.5 it is the dose that would hold the loop at the trip setpoint at steady state; only proven makeup flow earns allowance |
| **margin** | **1.20** | [J] flow meter ±1 % of reading + 0.01 m/s (§3), makeup alkalinity varying between monthly laboratory analyses (§5) with no measured spread, acid strength and pump calibration |
| heartbeat timeout | 10 s | [J] ten scans |
| stale value | not updated for 5 s | [J] |
| frozen value | bit-identical for 900 s | [J] a live digital sensor carries noise |
| out of range | pH outside 0–14; conductivity outside 2 µS/cm – 2,000 mS/cm; flow negative | instrument ranges, `docs/instrumentation_spec.md` §3 |
| rate of change | pH faster than 1.0 pH/min over 10 s | [J]; a failure removes the acid permissive, so it cannot mask a real crash |
| pH probe disagreement | > 0.3 pH for 60 s | [J] |
| conductivity residual | SCI alarm > 5 %; trip > 15 % for 600 s, measured below prediction | alarm = `conductivity.residual_is_precipitation` default; trip [J]. Prediction from a mass-balance observer on measured flows and measured acid; suspended while makeup is unproven |
| sudden conductivity drop | > 5 % in 60 s with blowdown flow < 0.05 kg/s | [J] about ten times the fastest dilution the `TowerBasin.mo` balance allows at design makeup (≈ 0.5 %/min on 50 t at five cycles) |
| acid pump stuck on | acid flow feedback > 5 % of design dose with command zero, 3 scans | [J] |
| blowdown valve stuck closed | measured < 20 % of a command above 0.1 kg/s, for 120 s | [J] allows valve stroke time |
| **fail-safe cycles** | **3.0**, or the requested setpoint if lower | the repository's baseline, `src/run_controller.py` `V7_BASELINE_CYCLES`, justified in `docs/v7_preregistration.md` by what operators on treated effluent actually run (Qatar Cool maximum 3; Aramco pilot 2.0 and 3.5). **Not conservative for austenitic stainless**: defect 46 puts 316 at 1.85 cycles on the Riyadh water, so a site with 316 tubing must configure lower |

**Fail-safe state on any trip:** acid command zero **and** acid isolation
de-energised; blowdown to the fail-safe cycles setpoint, on flow ratio if the
conductivity cell is untrusted; fan passes the requested value unchanged. Every
trip is logged with cause and timestamp.

**Latching.** Loss of makeup proving is a self-clearing permissive: it re-arms
after the proving time. Every other trip latches until manual reset, and reset
is refused while its cause persists.

## Fault-injection matrix

Onset 02:00:00 unless stated. *Acid stops* means delivered acid (pump output
through the isolation valve) is zero. "Onset" for a detection bound is the
instant the named signal first crosses its threshold as the layer sees it.

| id | fault | expected safe state | cause logged | time bound |
|---|---|---|---|---|
| F0 | none, 24 h normal operation with noise | no trip, no alarm; acid, cycles and fan pass through | none | — |
| F1 | makeup trips to zero, acid commanded on | acid stops; cycles setpoint 3.0; fan unchanged; true pH > 6.5 throughout | `MAKEUP_NOT_PROVEN` | proving time + 1 scan = **61 s** |
| F2 | control pH probe stuck high: frozen at 8.2 while the pH loop, reading above setpoint, commands twice the steady dose | acid stops; latched; true pH > 6.5 throughout | `PH_PROBE_DISAGREE` (or an earlier plausibility trip) | 60 s + 1 scan after disagreement first exceeds 0.3 |
| F3 | pH probes disagree: control probe drifts +0.5 pH over 1 h, dose unchanged | acid stops; latched; reset refused while the disagreement persists | `PH_PROBE_DISAGREE` | 60 s + 1 scan after disagreement first exceeds 0.3 |
| F4a | conductivity cell fouls and reads low: reading × (1 − f), f ramping 0 → 0.4 over 6 h; bleed controller on the fouled reading | alarm first; then acid stops, blowdown to 3.0 cycles **on flow ratio** | `COND_CELL_FAULT` | 600 s + 1 scan after SCI first exceeds 15 % |
| F4b | conductivity reading steps down 30 % with the blowdown valve closed | acid stops; blowdown to 3.0 cycles on flow ratio | `COND_CELL_FAULT` | 60 s + 1 scan |
| F5 | controller heartbeat lost; requested setpoints freeze at their last values | acid stops; cycles 3.0; fan holds last request | `HEARTBEAT_LOST` | 10 s + 1 scan |
| F6 | acid pump stuck on after a trip: makeup trips at 02:00 and the pump keeps delivering the steady dose regardless of command | isolation closes; acid stops; true pH > 6.5 throughout | `MAKEUP_NOT_PROVEN` then `ACID_PUMP_STUCK` | delivered acid zero within 1 + 3 + 1 = **5 scans** of 02:00 |
| F7 | blowdown valve stuck closed | acid stops; cycles setpoint 3.0; fan unchanged | `BLOWDOWN_VALVE_FAILED` | 120 s + 1 scan |
| F8 | makeup trips to zero **and** the makeup meter keeps reading a normal flow with noise, so proving and the dosing bound are both defeated | the independent trip is the last layer: pre-trip alarm first, then acid stops, latched | `LOW_PH` | 3 scans + 1 scan after the trip-probe reading first falls below 6.5; true pH stays ≥ 6.0 [J: probe lag plus confirmation] |
| S1 | F1 in **shadow** mode | nothing actuated: every command equals the request; the would-be trip is logged at the same time as in active mode | `MAKEUP_NOT_PROVEN` | same as F1 |

Tests in `tests/test_safety.py` assert every row. F8 is the only row whose
acceptance lets the basin fall below the trip setpoint, because it is the row
where every software layer has already been defeated.

---

## Results, appended 17 September 2026, after the run

Nothing above this line was edited after the simulation ran.

- **Incident, A1:** acid stopped 0 s after the trip (bound 61 s). **PASS.**
- **Incident, A2:** minimum basin pH 8.000 (trip setpoint 6.5). **PASS.**
- **Without interlocks:** pH below 6.5 at 51.5 min, below 5.5 at 52.6 min, below 4.0 at 58.4 min, low-level pump trip at 101.1 min, pH 1.82 by 08:00. **P1 held.**
- **Matrix:** F0, F1, F2, F4b, F5, F6, F7, F8 and S1 **PASS**. **F3 FAILS** (149 s against 61 s). **F4a FAILS** (768 s against 601 s). Both fail for the same reason: the registered bound counts from the first threshold crossing, while the setpoint needs a continuous dwell that noise resets. Recorded in `docs/staged/safety-interlocks_defects.md`. The rows were not rewritten.
- **Not predicted:** the registered fail-safe reaches low level sooner than no interlocks at all (90.8 against 101.1 min). Staged defect 56.
