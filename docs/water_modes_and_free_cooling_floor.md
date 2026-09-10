# Water-preserving control, and the chemical free-cooling floor

*11 September 2026. Covers `src/diurnal.py`, `src/models/cdu_model.py`,
`src/hybrid_supervisor.py` and `scripts/generate_pitch_artifacts.py`.*

Two pieces of work. The first asks whether the controller can be made to save
materially more water by being told that water is worth more than its tariff.
The second extends the boundary to a liquid-cooled data centre and finds the
constraint that makes the whole package matter there.

One of the two hypotheses under test was **falsified**, and that is recorded
here rather than quietly dropped.

---

## 1. Three objectives, not one

`controller.optimise()` now takes an `optimization_mode`:

| mode | objective | when it is the right question |
|---|---|---|
| `COST_MINIMIZING` | money | a plant on a flat tariff. **This is what the pre-registered V5 gate was scored on** |
| `WATER_PRESERVING` | money, with water weighted by a shadow price `lambda_water` | water scarcer than its tariff says: an allocation, a discharge consent, a WUE commitment |
| `CONSTRAINED_WATER` | minimise makeup volume subject to a declared energy-penalty ceiling | "how much water can I save if I accept N % more power?" |

`lambda_water` is a **policy input, not a physical constant**, and must be
declared wherever a number derived from it is quoted. At `lambda_water = 1.0`
the water-preserving objective reduces exactly to the cost-minimising one;
that identity is asserted in `tests/test_water_saving.py` and is the reason
the antiscalant term sits inside the water group even though it is a chemical
— it is billed per cubic metre of makeup, so it scales with water.

### What these results are NOT

The V5 gate returned **4.38 % makeup-water reduction against a 15 %
threshold** and failed. Nothing here revises that. These are different
objectives on a different experiment, and a number from either must never be
quoted against that threshold. There is deliberately no test asserting that
any of them clears a target.

### The 24-hour result

A real Dhahran TMYx day — 7 July, the day of highest mean wet-bulb, swinging
26.9 to 34.2 °C. Baseline is incumbent practice: fixed 4 cycles, fixed pH 7.8,
fan modulated to hold a 29 °C condenser-water setpoint. 22 of 24 hours
feasible.

| objective | water | energy | cost |
|---|---|---|---|
| `COST_MINIMIZING` | 8.97 % | +1.31 % | +4.15 % |
| `WATER_PRESERVING` (λ = 3) | 9.72 % | +0.73 % | +3.96 % |
| **`CONSTRAINED_WATER`** (≤ 5 % penalty) | **10.16 %** | **−0.66 %** | +3.10 % |

Double digits, at **10.16 %**, bought by accepting 0.66 % *more* energy. The
trade is real and it is small: three points of water for two points of energy.

### The hypothesis that failed

The diurnal idea was that a fixed conductivity setpoint leaves margin on the
table at night, because the saturation limit it protects against is a function
of temperature and temperature moves 15 K over a Gulf day. Float the cycle
target up in the cool hours, throttle back in the afternoon.

**It bought nothing. Cycles sat at 5.0 for every solved hour — minimum,
maximum and mean all 5.00.** The uncontrolled ceiling moved from 1.92 in the
afternoon to 2.02 at night: one tenth of a cycle.

The reason was predicted before the run and is the same sign problem that runs
through this whole package. Mineral solubilities do not share a direction:

```
calcite, calcium phosphate   RETROGRADE  least soluble HOT   -> bind at the skin
amorphous silica             PROGRADE    least soluble COLD  -> binds at the basin
```

Cooling loosens the retrograde limits at the tube skin and tightens the
prograde one at the basin. On this water they very nearly cancel. **"Float
cycles up at night" is only correct while a retrograde mineral binds, and on
this water it does not.**

---

## 2. The chemical free-cooling floor

This is the finding.

A thermal-only economizer drives facility water as cold as the wet bulb
allows, because colder water is compressor work avoided. It is the single
largest energy lever in a liquid-cooled data centre. On a silica-bearing
makeup water it is also precisely the wrong direction.

`chemistry.temperature_floor_for_silica()` returns the minimum temperature at
which amorphous silica stays at or below saturation. On the validated Aramco
TSE analysis:

| cycles of concentration | minimum safe facility-water temperature |
|---|---|
| 3 | 7.6 °C |
| 4 | 20.7 °C |
| **5** | **31.8 °C** |
| **6** | **41.4 °C** |
| 7 | 50.1 °C |

**Every cycle of concentration won — which is water saved — costs about ten
kelvin of free-cooling headroom.**

Two properties make this different from every other limit in the package.
It is a **floor**, not a ceiling: every other constraint here bounds
temperature from above. And it **cannot be bought with acid**, because silica
saturation is pH-independent below about pH 9. Acid is the lever an operator
reaches for when scaling appears, and against silica it does nothing at all.

Of fourteen data-centre thermal-control papers surveyed, eleven mention water
and **none model chemistry**. A controller in that literature cannot see this
constraint, and one of the papers optimises a **Las Vegas** data centre for
energy over 240 days without mentioning water once.

### What it costs to enforce it

`hybrid_supervisor.compare_blind_vs_bounded()` runs both policies. `blind`
takes the coldest water the tower can make; `bounded` refuses to cool below
the floor by slowing the fan, and pays for the warmer supply on the CDU side
by raising secondary flow to hold the cold-plate return at 42 °C.

Gulf summer, 9 MW IT load, dry-bulb 32 °C, RH 45 %:

| cycles | blind SI_silica | bounded SI_silica | fan | secondary pump | PUE |
|---|---|---|---|---|---|
| 4 | −0.057 ✓ | −0.057 ✓ | unchanged | unchanged | 1.048 → 1.048 |
| 5 | **+0.040 ✗** | 0.000 ✓ | −100 kW | **+1068 kW** | 1.048 → 1.155 |
| 6 | **+0.119 ✗** | **+0.061 ✗** | −106 kW | **+6211 kW** | 1.048 → 1.726 |

**Two negative results, both worth more than a headline saving.**

**Hydraulic compensation cannot pay for the floor at 5–6 cycles.** Pump power
is cubic in flow, so holding the return limit against a 5 K warmer supply
costs an order of magnitude more than the fan saves. The correct supervisory
response is to **lower cycles**, not to raise flow — which is a real control
decision, and not one an energy-only or a water-only optimiser would reach.

**At 6 cycles the floor is above what the tower produces even at minimum
fan.** Bounded still violates at +0.061, because 29 % fan speed only lifts the
supply to 34.0 °C against a 41.4 °C floor. That plant needs a bypass or a
lower cycles target; no controller setting fixes it.

**Caveat.** The secondary pump nameplate is 2 % of IT load `[A]`, an archetype
rather than a measured pump curve, and the *magnitude* of the penalty scales
linearly with it. The sign of the trade and the 6-cycle infeasibility do not.

### At 4 cycles nothing binds, and that matters too

In Gulf summer the wet bulb is high enough that the tower cannot overcool. The
floor bites in **mild and cold weather** — which is to say in Europe and the
northern United States, and at night everywhere. It is a temperate-climate
constraint that shows up hardest exactly where free cooling is most valuable.

---

## 3. The CDU model

`models/cdu_model.py` is deliberately small. A plate heat exchanger between
the facility water and a 50/50 glycol secondary loop, cubic pump law, the
42 °C cold-plate return invariant, and one number that justifies its
existence: **the plate wall temperature on the primary side.**

That wall is a heat-transfer surface in contact with concentrated makeup
water, exactly like a condenser tube, and it is hotter than the bulk for the
same reason. `scaling_state()` hands it to `chemistry.saturation_state_split()`
so the retrograde species are evaluated at the wall and the prograde one at
the tower basin. A liquid-cooling vendor sizing a CDU has no reason to compute
this and no tool that would.

No chip model, no DVFS, no two-phase behaviour, no rack allocation, no CFD.
The boundary is the GPU coolant supply temperature and it stops there.

---

## 4. Status

- `src/diurnal.py` → `results/diurnal_gulf.json`
- `scripts/generate_pitch_artifacts.py` → four regional archetypes, every
  parameter carrying an evidence tag. The Gulf profile is **real hourly
  weather**; the other three are sinusoids anchored on design conditions and
  are tagged `[A]`. A sine is not a climate and annual figures derived from
  one are indicative only.
- The Pakistan archetype is sized on a **real, currently-commissioning plant**
  — three induced-draught closed-loop towers, 328 m³/hr each, 38/31 °C,
  giving 8.0 MW — rather than on a round number. That figure assumes the
  posted flow is the process circuit, which is **not yet confirmed**.

26 new tests in `tests/test_water_saving.py` and `tests/test_cdu_controller.py`.
Suite total 122, audit passing, register 32 found / 32 fixed / none open.
