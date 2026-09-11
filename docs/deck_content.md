# Mizan — application deck content

*Furqan · Deep physics for hard infrastructure*  
Ordered to DTV's scoring sequence: maturity gate first, then product, market, defensibility, team.

---

## Slide 1 — Title

**Mizan** — supervisory control for Gulf condenser-water loops  
A Furqan venture · TRL 3, validated against measured experimental data  
DTV .dvp Cohort 2 · Energy / Water & Sustainability

## Slide 2 — The maturity gate, answered first

Thresholds fixed before fitting. Campaign-wise holdout, scored once.

| Gate | Threshold | Result |
|---|---|---|
| Outlet water temperature MAE | ≤ 1.00 K | **0.542 K** |
| Heat rejection MAPE | ≤ 6.00 % | **5.94 %** |
| Evaporation vs *measured* water loss | ≤ 8.00 % | **9.90 %** |

n = 50 held-out points from experimental campaigns the model never saw. 100 % solver convergence. Public dataset, MD5-verified, CC BY 4.0.

## Slide 3 — The problem, in one number

A Gulf condenser-water loop is run by three parties setting three handles independently:

- the BMS sets **fan speed** on a fixed condenser-water setpoint
- the water treater sets **blowdown** on a fixed conductivity setpoint
- the water treater sets **acid dose** on a fixed pH setpoint

They are not independent. Concentrating the loop to save water raises scaling risk and changes evaporation. Cooling the condenser to save compressor power costs fan power and evaporates more water.

**Nobody solves them together, because doing so requires the thermal model and the chemistry model to be one problem.**

## Slide 4 — Prior art, disclosed up front

We searched before we claimed. Two of the three ingredients are already taken, and we say so:

| Element | Status |
|---|---|
| Skin-temperature saturation | **Taken.** ChemTreat US 11,780,742 B2, granted Oct 2023 — but empirical LSI-family indices, antiscalant feed only |
| Ion-association speciation | **Taken.** French Creek WaterCycle since 1990 — but offline, at bulk temperature |
| Blowdown on a saturation index | **Public domain.** US 4,460,008 / 4,464,315, 1984, expired |

**What is open, stated precisely:**

> Routing each mineral to its own **governing temperature**, computed live, and closing **three actuators** on the result.

Calcite, gypsum and magnesium silicate are retrograde — they govern at the hot condenser skin. Amorphous silica is **prograde** — it governs at the cold basin. One evaluation temperature is wrong for one group or the other. French Creek works from bulk profiles; ChemTreat evaluates at skin with calcite indices. Neither routes per mineral, and neither actuates.

## Slide 5 — What we found that the single-point model misses

Scale forms where each mineral is least soluble — and the sign differs by mineral:

| Mineral | Solubility vs temperature | Governs at |
|---|---|---|
| Calcite, magnesium silicate | Retrograde | Hot tube skin |
| Gypsum | Maximum near 35–40 °C | Skin, weakly |
| **Amorphous silica** | **Prograde — more soluble hot** | **Cold tower basin** |

Evaluating everything at one temperature is optimistic about silica — the one species with no effective inhibitor in general service. Correcting this moved our predicted silica limit from ~12 cycles to 9.

And the skin offset is computed, not assumed: ΔT = q″/h_i gives ~3.8 K at typical design and ~8.7 K fouled. The bulk basis overstates the safe cycles limit by **7 % typical, 15.2 % fouled** — reported as a band, not a point.

## Slide 6 — Two ceilings, and the setpoint that finds neither

- **The cost curve never turns over.** Cost falls monotonically to 5 cycles, the last feasible point — so the economics point straight at the wall, with no margin.
- **Physical ceiling: 6 cycles.** First saturation violation at the skin — binding mineral **SI_silica_am**.

Different numbers. A fixed conductivity setpoint locates neither: the first needs a coupled cost model, the second needs ion-specific speciation. **The Langelier index the industry runs on describes calcite only — it cannot represent the binding mineral here at all.**

The plant operates between two limits it cannot see. That gap is the product.

## Slide 7 — The constraint that needs all three models at once

Magnesium silicate forms in two steps: brucite precipitates at the hot skin, then reacts with silica. Brucite's saturation pH is **retrograde** — it falls as the surface heats. So:

> deposition occurs when **bulk pH > pH_s(brucite) at the SKIN**

At 4 cycles, Gulf loops running pH 8.5–9.0:

| Skin | Verdict |
|---|---|
| 30 °C | safe across the whole band |
| 38 °C | deposits above pH 8.92 -- band straddles the limit |
| 46 °C | DEPOSITING across the whole band |
| 50 °C | DEPOSITING across the whole band |

**The same tower deposits at high load and not at low load.** A fixed pH setpoint cannot express that. Neither can a fixed conductivity setpoint.

It needs skin temperature (thermal model), bulk pH (chemistry model) and acid (actuator) together — and three independent literature sweeps found **no closed-loop scheme anywhere where a chemical saturation limit bounds a thermal optimiser.**

## Slide 7 — The result

| | Threshold | Result |
|---|---|---|
| Total operating cost | ≥ 3 % | **3.91 %** |
| Makeup water | ≥ 15 % | 4.38 % — **missed** |
| Saturation violations at skin | 0 | **0** |

We report the miss because the reason is the thesis. 4 → 7 cycles is worth exactly 12.50 % of makeup *at constant evaporation*. We achieved 4.38 %. The missing 2.46 points are evaporation the optimiser **chose** to add by running the fan harder, because colder condenser water was worth more than the water it cost.

A water treater would have promised 12.5 % and not delivered it. An energy optimiser would have raised water use and never booked it.

**And the half of this we can defend on our own data is the energy half.** Splitting the Dhahran year at the edge of our test data:

| | hours | water | energy |
|---|---|---|---|
| Inside the validated wet-bulb envelope | 5,475 | **-3.31 %** | +8.84 % |
| Hotter and wetter than any data we hold | 3,285 | +8.23 % | **-0.39 %** |

The water saving is **negative where the model has been validated** and positive only where it has not. Energy is the exact reverse. So we lead with energy, which our own data supports, and treat water as the thesis the pilot exists to test. We would rather say that than have a reviewer find it.

## Slide 8 — Product

A retrofit **edge controller**, not software: sensor skid (conductivity, pH, ORP, temperature, makeup and blowdown flow) + motorised blowdown valve + edge compute, speaking BACnet/Modbus. Sold as capex plus an annual model-recalibration licence.

Ships read-only in shadow mode; blowdown and dosing stay advisory until site validation. Deterministic fixed-step solver, bounded runtime, documented fallback to incumbent setpoints on solver failure or sensor loss.

**The skid deliberately does not measure the chemistry, and that is the central design decision.** Measuring silica, calcium, alkalinity and phosphate online costs **$120,000-185,000 per tower** against an annual water-and-energy saving of order **$89,000** on a 4.2 MW tower. The instruments cost more than the thing they optimise. That is structural, it is why no incumbent sells chemistry-bounded control, and no amount of negotiation closes it.

So the skid buys only what is cheap -- toroidal conductivity, pH, ORP, temperature, two flow meters, a coupon rack -- at about **$15,000 in instruments and $23,000-30,000 installed**, and the chemistry is *computed*. The one measurement that is already there then checks the computation for nothing: specific conductance is a known function of ion composition, so the residual between computed and measured conductance says when the assumed composition has stopped being true. Precipitation removes ions; the residual moves first. See `docs/instrumentation_spec.md`.

## Slide 9 — Why the Gulf, and why now

Saudi and Qatari district cooling is moving onto treated sewage effluent under national reuse policy. TSE at high cycles is exactly the regime where the incumbent index breaks: high ionic strength, and a binding mineral LSI cannot describe. Extreme wet-bulb makes the energy side of the trade unusually valuable at the same time.

Same physics, same equipment, same water policy in Qatar — the Gulf bridge needs no rework.

## Slide 10 — Defensibility

Not data volume, not UI, not AI-applied-to-X. The moat is the coupled model and the calibration library behind it:

- Poppe integration with the **water-activity coupling** that lets chemistry change tower performance at all
- ion-specific speciation at **skin temperature**, not bulk
- the **economic/physical ceiling separation**, which needs both models simultaneously

A generalist team reproduces the tower model in weeks. What they cannot reproduce is knowing that the fan correlation is in hertz, that gypsum binds before calcite on Gulf TSE, or that the water saving must be discounted for the evaporation the energy optimum adds back. Those came from the physics, and each one changed the answer.

## Slide 11 — TRL 4 at KFUPM, and what SAR 200,000 buys

The rig already exists on the DTV campus: KFUPM's Air-Conditioning and Refrigeration Laboratory holds a vertical cooling tower and a wind tunnel with heating, cooling and **humidification**.

That humidification closes the one honest gap in this package — our validation data is from a semi-arid Spanish site whose summer wet-bulb sits below Dhahran's.

In-kind budget buys instrumentation, blowdown valve and edge hardware, ICP-OES water analysis, OT-security assessment, third-party validation. Not runway.

## Slide 12 — Where AI sits

**No AI contributes to any result in this package.** The evidence is first-principles, and we say so.

The load-bearing learned component is the **scaling-kinetics residual**, at TRL 4. Thermodynamics gives the driving force from published constants; precipitation *rate* depends on nucleation, surface and inhibitor residual and is not derivable. Remove that term and the controller still says whether scale is possible, but not when it will cost money — which is the product.

We rejected reinforcement learning (no hard-constraint guarantee), chemistry soft-sensing (we showed the signal sits an order of magnitude below the noise floor), and a weather LSTM (numerical weather prediction already exists).

## Slide 13 — Team and ask

**Engr. Furqan Shakeel** — Co-founder & CTO · engr.furqan.shakeel@gmail.com · linkedin.com/in/furqan-shakeel  
**Engr. Damia Baig** — Co-founder & CEO · [contact details to be added]  
**Engr. Muhammad Ahsan** — Co-founder, Commercial Development · muhammadahsan4203@gmail.com

Three energy engineers, all full-time. One owns the physics core and controller; two own customer development. That ratio is deliberate: the technical risk is now largely retired and the binding risk is commercial.

Ask: DTV Cohort 2 place, lab access for the TRL 4 programme above, and introductions to Saudi district-cooling and industrial-cooling operators through the DTVC corporate partner network.

---

## Speaker note on honesty

This deck reports a failed criterion and a defect we found in our own first run. That is deliberate. DTV screens the maturity gate first, and a team that inflates TRL is finished in this ecosystem permanently. Everything claimed here is reproducible with four commands against a public dataset.