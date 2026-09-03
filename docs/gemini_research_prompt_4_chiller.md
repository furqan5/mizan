# Deep-research prompt #4 — CHILLER PERFORMANCE CURVES — paste into Gemini Deep Research

> Narrow and specific. I need real performance data for one water-cooled chiller so I can replace the last significant assumption in my energy model. Everything else in the model is now sourced.

---

## CONTEXT

I am modelling the condenser-water loop of a Gulf district-cooling plant. The chiller power model drives the central trade-off in my optimiser: cooling the condenser water saves compressor power but costs cooling-tower fan power, so **the accuracy of dP_chiller/dT_condenser is the accuracy of the whole result.**

**Where I am now.** I originally used a Carnot-referenced COP (`COP = η·T_evap/(T_cond−T_evap)`, η = 0.55). External review established that constant-Carnot extrapolation at reduced condenser temperature produces large errors because real centrifugals hit aerodynamic surge limits and non-constant mechanical losses. I replaced it with the EnergyPlus `Chiller:Electric:EIR` bi-quadratic form:

```
CAPFT   = a1 + b1·Tchws + c1·Tchws² + d1·Tcws + e1·Tcws² + f1·Tchws·Tcws
EIRFT   = a2 + b2·Tchws + c2·Tchws² + d2·Tcws + e2·Tcws² + f2·Tchws·Tcws
EIRFPLR = a3 + b3·PLR + c3·PLR²
P       = P_ref · CAPFT · EIRFT · EIRFPLR
```

normalised to the AHRI rating point (6.67 °C leaving chilled water, 29.44 °C entering condenser water) with a reference COP of 6.1. That currently gives a sensitivity of **2.1–3.1 % power per K** of condenser water temperature, which matches the industry rule of thumb — but **my coefficients are not traced to any named machine.** That is the gap.

---

# TASK

**Rules:** never invent a coefficient or a citation. Every number needs a working URL or a named, locatable document. Tag `[C]` / `[A]` / `[UNVERIFIED]`. If you cannot find real coefficients, say so plainly — a clear negative is more useful than plausible-looking numbers.

## Priority 1 — Actual bi-quadratic coefficients

1. **Published `Chiller:Electric:EIR` or `Chiller:Electric:ReformulatedEIR` coefficient sets** for **water-cooled centrifugal** chillers. Sources to mine:
   - the EnergyPlus dataset files `Chillers.idf` and `ASHRAE90.1_2010_Chillers.idf` shipped with EnergyPlus;
   - DOE Commercial Prototype Building Models (the chiller objects inside the large-office and hospital models);
   - OpenStudio Standards `chiller_electric_eir` JSON data;
   - California Title 24 / ACM appendices;
   - CIBSE or ASHRAE published curve sets.

   **Give me the actual six CAPFT coefficients, six EIRFT coefficients and three EIRFPLR coefficients**, plus the reference COP, reference capacity, and the temperature ranges over which the curves are valid.

2. Do the same for **water-cooled screw** chillers, so I can compare machine types.

3. **What Carnot fraction do real water-cooled centrifugals actually achieve** at AHRI rating conditions and at part load? I assumed a constant 0.55. Give measured or certified values and show how the fraction varies with lift.

## Priority 2 — Certified ratings for a named machine

4. **AHRI 550/590 certified performance for one specific water-cooled centrifugal chiller in the 500–5,000 TR range.** The AHRI Directory of Certified Product Performance is searchable. I want: full-load kW/ton, IPLV, NPLV, reference conditions, and — if available — the part-load points (100/75/50/25 %).

5. **Manufacturer selection data or engineering catalogues** for York YK/YMC², Trane CenTraVac, Carrier 19XR/19DV, or Daikin WMC/WME, showing **kW/ton versus entering condenser water temperature**. Public engineering bulletins and application guides often tabulate this.

6. **The minimum entering condenser water temperature** each manufacturer permits, and what happens below it (surge, oil return, expansion-valve control). This is a hard bound on how far my optimiser may push condenser water down and I currently have no value for it.

## Priority 3 — Gulf-specific and district-cooling context

7. **Chiller performance at Gulf design conditions** — entering condenser water of 32–37 °C, which is well above the 29.44 °C AHRI point. Do published curves even extend there, and what derate applies?

8. **kW/ton actually achieved by Gulf district-cooling plants**, chiller-only and plant-total, from Tabreed, Qatar Cool, Empower, Marafiq or Marafeq disclosures, IDEA or ASHRAE conference papers.

9. **Typical condenser-water design conditions in Gulf district cooling** — entering and leaving temperature, range, and gpm/ton or L/s per kW.

---

## OUTPUT FORMAT

- **A coefficient table I can paste straight into code**, with every value and its source.
- A statement of the validity range of each curve set.
- Where a value could not be found, say so under **"What I could not find"**.
- **"What contradicts the thesis"** — in particular, anything suggesting the condenser-water-temperature sensitivity is materially different from the 2–3 %/K I currently model.
- Full source list with working URLs.
