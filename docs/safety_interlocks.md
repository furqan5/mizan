# Acid-dosing interlocks, and concrete-basin sulfate exposure

**17 September 2026.** Closes, in software and in simulation, the second safety gap in `docs/robustness_gaps.md` section 7: *makeup tripped overnight, acid kept pumping, the tubes were destroyed.* Also answers section 10, the concrete basin, with cited thresholds.

Pre-registration, committed before the first simulation run: `docs/staged/safety_preregistration.md`. Code: `src/safety.py`, `src/safety_sim.py`, `src/concrete.py`. Tests: `tests/test_safety.py`, `tests/test_concrete.py`. Regenerate the incident with `python src/safety_sim.py`.

---

## 1. What this is not

**This is a software interlock specification plus a simulation. It is not a certified safety function and it claims no SIL.** IEC 61511, the functional-safety standard for safety instrumented systems in the process industry, is the reference framework it was written against. It is cited as a framework only. No compliance is claimed and none has been assessed.

In that framework a protection layer has to be independent of the control system it protects. So **the independent low-pH trip must be built in hardware**: its own probe, its own trip relay, and a de-energise-to-trip contact in the acid pump supply, all independent of the edge computer. The simulation puts that trip in the same Python object as the software checks only so it can be tested at all. If the edge computer fails, everything in `safety.py` fails with it. The hardware trip and a hardware watchdog relay must not.

Until that hardware exists and has been proof-tested on a real skid, the section 7 rule still stands: this controller is not connected to a dosing pump.

---

## 2. Where it sits

```
optimiser (controller.optimise)  ->  requested fan, cycles, acid
                                         |
                           safety.SafetyLayer.scan()   every 1 s
                                         |
                    actuators: fan VFD, bleed controller, acid pump + isolation valve
```

- **Shadow mode is the default.** The layer computes and logs everything and actuates nothing: each command equals the request, and the would-be command is kept in `layer.would_be`. **Active mode** applies it.
- **`controller.supervise()`** is the only link to the optimiser. It calls `optimise()` unchanged, and only when a layer is passed does it send the result through `scan()`. With no layer its output is byte-identical to `optimise()`, and a test checks that.

| function | rule | setpoint |
|---|---|---|
| makeup proving | acid is allowed only after makeup has stayed above threshold for the proving time. The permission is lost on the first scan below threshold, and it re-arms itself when flow returns | 20 % of design makeup, **60 s** |
| independent low-pH trip | separate probe, 3 consecutive scans. It latches, resets only by hand, and refuses the reset while pH is below the alarm | **6.5** |
| pre-trip alarm | either probe | **6.8** |
| dosing bound | acid over a rolling hour ≤ **1.20** × the proven makeup × `acid_dose_for_ph(makeup, C, 6.5, T)` / C | engine stoichiometry, defect 25 basis |
| plausibility | stale 5 s · frozen 900 s (a flow held at exactly zero is exempt) · out of instrument range · pH changing faster than 1 pH/min · probes disagreeing by more than 0.3 pH for 60 s | |
| conductivity cell | residual (SCI, `conductivity.py`) against a mass-balance observer running on measured flows: alarm above 5 %, trip above 15 % held for 600 s · a drop of more than 5 % in 60 s with blowdown closed | |
| heartbeat | optimiser counter unchanged | 10 s |
| final elements | pump delivering while commanded off for 3 scans · blowdown below 20 % of command for 120 s | |
| **fail-safe, any trip** | acid zero and isolation de-energised · blowdown to **3.0 cycles**, or lower if requested, on flow ratio when the conductivity cell is untrusted · fan unchanged | |

**The dosing bound and defect 25.** `acid_dose_for_ph` gives kilograms of acid per kilogram of *circulating* water. Alkalinity leaves the loop with blowdown plus drift, which equals makeup/C, so the allowance earned per kilogram of *makeup* is that dose divided by C. Charging it against makeup would loosen the bound by exactly the factor C, which was the original mistake behind defect 25. At the trip pH, the dose is the most acid the loop could take at steady state without being held at the trip. With the 1.20 margin, normal dosing at pH 8.0 uses between half and all of the allowance (tested).

**Why 3.0 cycles.** `src/run_controller.py` `V7_BASELINE_CYCLES`, justified in `docs/v7_preregistration.md` by what operators on treated effluent actually run. **This value is not conservative for a condenser with 316 stainless tubes.** Defect 46 puts 316 at 1.85 cycles on the Riyadh water, so a site with that tubing must set `failsafe_cycles` lower.

**Why a separate makeup proof matters.** The incumbent panel's interlock is a flow switch on the *sample* line. The Walchem WDT310 manual says the switch *"prevents controlling based upon a stagnant sample"*. A makeup trip leaves the circulating water, and so the sample flow, running, so that switch never sees it.

---

## 3. The incident, simulated

The plant is `modelica/TowerBasin.mo`: a 50 t basin, 4.2 kg/s evaporation, 5 cycles, 30 °C, the field-validated makeup, and a pH 8.0 setpoint. Before the trip the engine's steady acid dose is **1.492 kg/h**. Makeup goes to zero at 02:00 and the acid command stays on.

pH comes from the proton balance of an open carbonate system, using the engine's own constants. Where bicarbonate carries the alkalinity, it matches `chemistry.ph_atmospheric_equilibrium`. It also covers excess acid, which the engine's formula cannot (staged defect 55). Letting the tower strip CO2 gives the highest pH possible for a given alkalinity, so **every time below is the latest the real loop could get there.**

**Without interlocks** (shadow mode):

| | after the trip | clock |
|---|---|---|
| basin pH below 6.5 (onset of EN 206 class XA1) | **51.5 min** | 02:51:29 |
| below 5.5 (XA2) | **52.6 min** | 02:52:39 |
| below 4.0 (steel regime, source unverified) | **58.4 min** | 02:58:21 |
| low-level pump trip (20 % of inventory) | 101.1 min | 03:41:08 |
| minimum pH, 08:00 | **1.82** | |

Basin pH every 10 minutes: 7.999 at 02:00, 7.724 at 02:30, 7.507 at 02:40, 6.858 at 02:50, **3.880 at 03:00**, 2.970 at 03:30, 2.550 at 04:00 and 2.232 at 05:00. For fifty minutes the curve looks harmless. The loop spends its last alkalinity in the next ten and falls three pH units. Nobody watching a trend at 02:40 would have acted, and pH was already below 4 before the basin reached low level.

**With interlocks** (active mode): acid stopped **0 s** after the trip, on the same scan the flow was lost, against a pre-registered bound of 61 s. Basin pH never went below **8.000**. **A1 and A2 pass.**

---

## 4. Fault matrix, as registered

| row | fault | first trip (s after onset) | registered bound | result |
|---|---|---|---|---|
| F0 | none, 24 h with noise | no trip, no alarm | — | **PASS** |
| F1 | makeup trip | `MAKEUP_NOT_PROVEN` +0; acid stopped +0; min pH 8.000 | 61 s | **PASS** |
| F2 | control probe stuck at 8.2, dose doubled | `SENSOR_RATE` +0 (from the step to the stuck value); min pH 8.000 | 61 s after disagreement | **PASS** |
| F3 | control probe drifts +0.5 pH/h | `PH_PROBE_DISAGREE` +2248; disagreement first seen at +2099, so **149 s** later; reset refused | 61 s after first disagreement | **FAIL** |
| F4a | fouled cell, reading falls to 60 % over 6 h | `SCI_ALARM` +2473, `COND_CELL_FAULT` +7720; SCI first above 15 % at +6952, so **768 s** later | 601 s after first crossing | **FAIL** |
| F4b | reading drops 30 % with blowdown closed | `COND_CELL_FAULT` +0; flow-ratio blowdown | 61 s | **PASS** |
| F5 | heartbeat lost | `HEARTBEAT_LOST` +11 | 11 s | **PASS** |
| F6 | pump stuck on after the trip | `MAKEUP_NOT_PROVEN` +0, `ACID_PUMP_STUCK` +3; delivered acid zero +0 | 5 scans | **PASS** |
| F7 | blowdown valve stuck closed | `BLOWDOWN_VALVE_FAILED` +120 | 121 s | **PASS** |
| F8 | makeup trip with the meter still reading normal flow | `LOW_PH_ALARM` +3093; trip-probe reading below 6.5 at +3158; `LOW_PH` +3160; min pH **6.288** | +4 s, pH ≥ 6.0 | **PASS** |
| S1 | F1 in shadow mode | nothing actuated; would-be trip logged at +0, the same time as F1 | — | **PASS** |

**F3 and F4a fail as registered, and the matrix has not been changed.** Each bound was written as *N seconds after the signal first crosses its threshold*. Each setpoint needs the signal to stay over the threshold *continuously* for N seconds. A slow drift crosses the threshold inside the measurement noise, so every time noise pulls it back under, the dwell timer starts again. Both are marked `xfail(strict=True)` with that reason, and separate tests pin what actually happens. Neither fault moved the true basin pH. F8 is the row that matters most: with every software layer defeated, the independent trip held the basin at 6.288.

---

## 5. What the simulation found that was not asked

- **The registered fail-safe drains the basin faster in the exact incident the layer exists for.** "Blowdown to 3.0 cycles on any trip" opens the bleed when makeup is gone, and there is nothing to replace the water it throws away. The basin reached low level at **90.8 min** with interlocks, against **101.1 min** without them. `hold_blowdown_on_makeup_loss` (off by default, not pre-registered) holds the bleed closed while makeup is unproven, and pushes low level out to **158.6 min**. Staged defect 56.
- **The conductivity-residual alarm chatters.** With no hysteresis it sets and clears repeatedly near 5 %. It needs a deadband before an operator sees it.
- **Stuck-pump detection needs a flow signal at the pump discharge, upstream of the isolation valve.** Downstream of the valve it reads zero once the valve closes, and the fault would never be seen.
- **The optimiser's gypsum index leaves out the sulfate its own acid adds.** Staged defect 54.

---

## 6. Concrete-basin sulfate exposure

`src/concrete.py`. Each threshold is taken from an authoritative reproduction, and the module says exactly how far it was verified.

| class | sulfate in water, mg/L (≈ ppm) | source |
|---|---|---|
| ACI 318-19 S0 / S1 / S2 / S3 | < 150 / 150–<1,500 (or seawater) / 1,500–10,000 / > 10,000 | Table 19.3.1.1, reproduced in *Concrete International*, May 2023 (Obla & Lobo, NRMCA; copy provided with ACI's permission). **That reproduction repeats the S1 range in its S2 water cell, a typesetting error.** S2 is taken from ACI CRC 117 (ACI Foundation, 2020) Table 9 |
| EN 206 XA1 / XA2 / XA3 | 200–600 / >600–3,000 / >3,000–6,000 | Table 2, reproduced in Whittaker & Black (2015), *Advances in Cement Research* Table 1 (University of Leeds deposit). The numbers are read directly. **Whether each boundary value is included is decoded from a symbol font and is [UNVERIFIED]**, as is the table's temperature and flow scope |

`concrete_sulfate_exposure(so4)` returns both classes. `cycles_at_class_boundaries()` returns the cycles at which basin water crosses each boundary, optionally counting the acid's sulfate. `concrete_sulfate_constraint()` **binds only when a site declares a concrete basin and its cement type**, checked against ACI Table 19.3.2.1. If nothing is declared the constraint is inactive, which is not the same as satisfied. The Ceiling Report prints the exposure class either way.

**On the field-validated makeup (SO4 300 mg/L):**

| | ACI S2 | EN XA2 | EN XA3 |
|---|---|---|---|
| cycles, no acid | **5.00** | 2.00 | 10.00 |
| cycles, acid to pH 8.0 | **3.99** | 1.64 | 7.91 |

The makeup itself is already **S1 and XA1**. At 5 cycles the basin carries 1,500 mg/L without acid and 1,886 with it; at 6 cycles, 1,800 and 2,269. **An ordinary Type II cement basin is outside its ACI specification from 3.99 cycles once acid is dosed**, below the operating band the optimiser recommends. The Ceiling Report's own worked example, the Riyadh refinery water, reads 1,472 mg/L at its ceiling: S1 and XA2.

The robustness_gaps figure of about 3,400 ppm at 6 cycles came from the 566 mg/L sulfate in `ARAMCO_RECLAIMED`. On the field-validated water the figure is 1,800 without acid, and the acid adds more.

---

## 7. Not established

- **Nothing here has run on hardware.** The low-pH trip, the watchdog relay and the isolation valve have not been specified to a part number or proof-tested.
- **No common-cause case.** No row has the pump and the isolation valve failing together.
- **Probe noise and lag are assumptions** (±0.005 pH, 30 s). No vendor publishes pH drift (`docs/instrumentation_spec.md` §8).
- **The model is simplified.** The observer assumes a level-controlled basin, so the residual check is suspended while makeup is unproven. The basin is taken as well mixed, so the low pH at the injection point is not modelled. Activity coefficients are ignored, as in the engine.
- **One threshold has no verified source.** The pH 4.0 steel threshold (Whitman, Russell & Altieri) is [UNVERIFIED]; the secondary source refused access.
- **The concrete check is partial.** It covers sulfate only: EN 206 also classifies magnesium, ammonium, aggressive CO2 and pH, and none of those is implemented. Gypsum precipitation, which would cap sulfate, is not modelled.
