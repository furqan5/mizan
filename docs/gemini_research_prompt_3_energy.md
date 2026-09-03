# Deep-research prompt #3 — ENERGY SIDE — paste into Gemini Deep Research

> Rounds 1 and 2 closed the water chemistry. This round targets the energy half and, more importantly, **the coupling between them**. Paste the whole thing including the context and the parameter table — I want my assumed values corrected, not just supplemented.

---

## CONTEXT — the venture, and why the energy side now matters differently

**Mizan** is a retrofit supervisory controller for condenser-water loops in Gulf district cooling. It co-optimises **cooling-tower fan speed, blowdown (cycles of concentration) and acid dose** against ion-specific mineral saturation, with each mineral evaluated at the temperature where it is least soluble.

A validated physics core already exists: Poppe/Rögener heat-and-mass transfer (Kloppers & Kröger formulation, fixed-step RK4, unsaturated and supersaturated air branches), coupled to an ion-association speciation engine on USGS PHREEQC constants. Held-out accuracy: **0.542 K outlet-temperature MAE, 5.94 % heat-rejection MAPE, 7.11 % on measured water consumption**, against thresholds fixed before fitting. *(As sent. That water figure was later corrected to 9.90 % when a drift-rate defect was found.)*

### The finding that makes this round necessary

Magnesium silicate scaling is the binding chemistry constraint on Gulf treated-sewage-effluent makeup. It forms in two steps: brucite Mg(OH)₂ precipitates at the **hot condenser tube skin**, then reacts with silica in the boundary layer. Brucite's saturation pH is retrograde, giving the criterion:

> **deposition occurs when bulk pH > pH_s(brucite) evaluated at the SKIN temperature**

Computed on measured Saudi Aramco reclaimed water at 4 cycles, with Gulf loops running pH 8.5–9.0:

| Skin temperature | Verdict |
|---|---|
| ≤ 34 °C | safe across the operating band |
| 38–42 °C | band straddles the limit |
| ≥ 46 °C | **depositing across the whole band** |

**Skin temperature is therefore the coupling variable**, and it is set by ΔT = q″/h_i — heat flux over water-side film coefficient. Both are controlled by *energy-side* decisions: load, condenser-water temperature, and tube velocity. So the energy optimiser moves the chemistry constraint, and the chemistry constraint bounds the energy optimiser. **Running the condenser colder or the tubes faster buys chemistry headroom at an energy cost.** I have found nobody who models this bidirectionally, and that is what I need this round to confirm or destroy.

### Already established — do NOT re-research

- Gulf TSE silica ~20–60 mg/L; Salbukh (Riyadh) 26.8 mg/L measured.
- Empirical magnesium-silica product limits: 35,000 (standard), 25,000 (utility), with Mg as ppm Mg²⁺.
- Amorphous silica is prograde, ceiling 95→143 mg/L across a 15–35 °C basin; industry uses a static 150 mg/L rule.
- Aramco reclaimed-water full ion analysis (Badruzzaman et al. 2022) in hand.
- Saudi tariffs: electricity $0.074/kWh all-in; water $3.11/m³ avoided (Marafiq/RCJY, process water SAR 8.04 + industrial wastewater SAR 3.64); bulk sulphuric acid ~$0.19/kg.
- **No published time-of-use electricity tariff exists** for Saudi commercial/industrial — so no peak-shifting arbitrage is claimed.
- Incumbents: Nalco 3D TRASAR (raises cycles 2.5–3.5 → 4–5, ~30 % blowdown reduction); French Creek and OLI Systems do offline speciation; ChemTreat US 11,780,742 B2 claims skin-temperature saturation → antiscalant dose. Whole-plant optimisers: Johnson Controls, Trane, Optimum Energy.

---

## MY CURRENT ASSUMPTIONS — please correct these, with sources

These are the energy-side numbers the model runs on. Most are tagged `[A]`. **Tell me which are wrong.**

| Parameter | My value | Basis |
|---|---|---|
| Chiller COP model | Carnot-referenced, `COP = η · T_evap/(T_cond − T_evap)`, **η = 0.55** | `[A]` chosen over a fitted bi-quadratic for extrapolation safety |
| Condenser approach | **4.0 K** | `[A]` |
| Chilled-water supply | **7.0 °C** | `[A]` |
| Plant archetype | 10 MW condenser module, m_w **478 kg/s**, ~6 K range | `[A]` |
| Fan rated power | **110 kW** for the cell bank; air flow ∝ speed, power ∝ speed³ | `[A]` affinity law |
| Rated air mass flow | **400 kg/s** | `[A]` |
| Condenser heat flux q″ | **15.8 – 47.3 kW/m²** | `[C]` Veolia Water Handbook Ch. 23 (5,000–15,000 Btu/ft²·hr) |
| Water-side film coeff. | Dittus–Boelter, tube ID **17.6 mm**, velocity **2.0 m/s** → h ≈ 8,186 W/m²K | `[A]` |
| Resulting skin ΔT | **3.8 K** typical, **8.7 K** at low velocity / high flux | derived |
| Drift loss | 0.05 % of circulating flow | `[A]` |

---

# TASK

**Rules:** never invent a citation; every claim gets a working URL and a `[C]` / `[A]` / `[UNVERIFIED]` tag; report negatives explicitly; end with **"What I could not find"** and **"What contradicts the thesis"**, unsoftened.

## Priority 1 — The coupling (the reason for this round)

1. **Does any published work link a water-chemistry constraint to an energy setpoint in cooling systems?** Condenser-water temperature reset that accounts for scaling risk; fouling-aware condenser optimisation; any control scheme where the chemistry limit bounds the thermal optimiser or vice versa. Search HVAC, process control, water treatment, and power-plant condenser literature. **A clean negative is a valuable answer here** — but look hard before concluding it.

2. **Tube water velocity: the two-sided effect.** Higher velocity raises the film coefficient (lowering skin ΔT, buying chemistry headroom) *and* suppresses particulate fouling — but costs pump power. I need:
   - published fouling-rate versus velocity data for condenser tubes (the classic "minimum 0.9–1.2 m/s to avoid deposition" guidance and its provenance);
   - film coefficient versus velocity for typical condenser tube geometries and materials;
   - pump power versus velocity for real condenser-water circuits.

3. **Condenser tube skin/wall temperature in operating chillers** — measured or computed values, and how they vary with load. My 3.8 K typical / 8.7 K fouled comes from q″/h_i with Dittus–Boelter. Corroborate or correct.

4. **How condenser heat flux varies with part load** in centrifugal and screw chillers. If q″ falls with load, skin temperature falls, and the chemistry constraint relaxes at part load — which would make the whole coupling load-dependent in a way I can exploit.

## Priority 2 — Chiller performance, real data

5. **Chiller COP / kW-per-ton as a function of entering condenser water temperature**, for water-cooled centrifugal and screw machines in the 500–5,000 TR range. I want actual manufacturer or AHRI-certified curves, not rules of thumb. York, Trane, Carrier, Daikin selection data; AHRI 550/590 certified ratings; ASHRAE 90.1 reference curves.

6. **Is my Carnot-referenced COP with η = 0.55 defensible?** What Carnot fraction do real machines achieve at full and part load? Would a bi-quadratic (ASHRAE/EnergyPlus form) be materially better, and what are typical coefficients?

7. **The condenser-water temperature optimum.** Lowering condenser water saves compressor power but costs fan power, and every chiller has a minimum entering condenser water temperature. What is current best practice for condenser-water reset, what savings are documented, and what are the machine-side limits?

8. **Chiller derate at Gulf ambient conditions** — performance at 45–50 °C dry bulb and 30 °C+ wet bulb, and how district cooling plants are sized for it.

## Priority 3 — Plant-level benchmarks

9. **kW/TR benchmarks for Gulf district cooling plants** — total plant, and broken down by chiller / condenser-water pump / chilled-water pump / cooling-tower fan. Tabreed, Qatar Cool, Empower, Marafiq, Marafeq, or ASHRAE/IDEA published data.

10. **Cooling-tower fan power as a fraction of plant power**, and typical rated fan power per cell for towers serving 1,000–10,000 TR.

11. **Part-load profiles for Gulf district cooling** — annual load duration curves, or typical seasonal and diurnal shapes. I currently weight five ambient scenarios by assumption and would rather use a real profile.

12. **Condenser-water flow rates and ranges actually used** — gpm/ton or L/s per kW, design range, and whether variable condenser-water flow is common in the Gulf.

## Priority 4 — The energy cost of fouling

13. **Energy penalty per unit of condenser fouling** — kW/TR degradation versus fouling factor or scale thickness, and the fouling factors used in design (ASHRAE, TEMA, HEI standards). This converts a chemistry event into an energy number, which is the bridge my business case needs.

14. **Condenser approach temperature as a fouling indicator** — published relationships between approach rise and cleanliness factor, and what approach rise triggers cleaning in practice.

15. **Documented cost of condenser cleaning** at district-cooling or power-plant scale — cost, downtime, frequency. Round 2 could not find this; try wider, including power-plant condenser practice and EPRI material.

## Priority 5 — Competitive, energy side

16. **What Johnson Controls, Trane and Optimum Energy actually control** in condenser-water optimisation — the manipulated variables, whether they touch blowdown or water chemistry at all, and how they are priced. I need to know exactly where their scope ends and mine begins.

17. **Any product that co-optimises tower fan speed and water treatment together.** If it exists, my differentiation collapses and I need to know now.

---

## OUTPUT FORMAT

- Answer in the priority order above.
- Numeric findings in tables with units and a source URL per row.
- Where you correct one of my assumptions, state my value, the corrected value, and the source side by side.
- **"What I could not find"** — every question returning nothing.
- **"What contradicts the thesis"** — unsoftened.
- Full source list with working URLs.
