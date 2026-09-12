# Mizan — external session handoff

*For pasting into a fresh assistant (ChatGPT or similar) that has **no access to the repository**. Everything needed to reason about this venture is in this file. Written 12 September 2026.*

---

## 1. Who and what

Three energy engineers in Lahore, Pakistan.

- **Furqan** — the parent company. Deep physics and physics-informed AI for energy infrastructure. From the Arabic root *f-r-q*, to separate: the criterion distinguishing true from false.
- **Mizan** — the first product. *"The limit, computed."* A **retrofit supervisory controller** for cooling-tower / condenser-water loops. It co-optimises **fan speed, blowdown rate and acid dose** against **first-principles mineral saturation limits**.

Founders: Furqan Shakeel (CEO, physics core), Damia Baig (commercial), Muhammad Ahsan (commercial development).

Repository: `github.com/furqan5/mizan`, branch `water-modes-and-cdu`. Private.

---

## 2. The technical thesis, in one page

A cooling tower evaporates water. The dissolved minerals left behind concentrate. **Cycles of concentration** `C` = circulating TDS ÷ makeup TDS. Higher `C` means less blowdown and less makeup water:

```
makeup M = E·C/(C−1)          E = evaporation
```

so the **maximum** water saving available by raising cycles from a baseline `C₀` is exactly `1/C₀`. At `C₀ = 3` that is 33.3 %, and no controller can beat it. Everything is a fraction of that.

**Why plants don't just raise cycles:** they don't know where the limit is. The industry uses the **Langelier Saturation Index (LSI)**, which is a calcium-carbonate-only index. Real limits come from whichever mineral saturates first, and on recycled water that is usually **not** calcium carbonate.

**What Mizan computes instead:** full aqueous speciation — ion association, Davies activity coefficients, free vs total ions — benchmarked against **PHREEQC 3.9.0**, giving saturation indices for calcite, gypsum, amorphous silica, tricalcium phosphate, hydroxyapatite and brucite.

**The insight that organises the product — minerals bind at different places in the loop:**

| Mineral | Solubility vs temperature | Binds at |
|---|---|---|
| Calcite, calcium phosphate, brucite | **Retrograde** (less soluble hot) | the **hot condenser skin** |
| Amorphous silica | **Prograde** (less soluble cold) | the **cold basin** |

So a single-temperature index is structurally wrong. And because dissolved silica below pH 9 is neutral H₄SiO₄, **acid cannot buy cycles against silica** — only against carbonate. That is why acid-based programmes hit a wall on recycled water.

---

## 3. Hard numbers (all computed; signs are honest)

### The headline finding — and it cuts against us

Annual Dhahran study, split at the edge of the experimental data the evaporation model was calibrated on (Almeria, Spain, wet-bulb ≤ 21.9 °C):

| | hours | water | energy | cost |
|---|---|---|---|---|
| **Inside** the validated envelope | 5,475 | **−3.31 %** | +8.84 % | +5.32 % |
| **Extrapolated** (wet-bulb > 21.9 °C) | 3,285 | +8.23 % | −0.39 % | +2.90 % |
| Whole year | 8,760 | +2.37 % | +4.52 % | +4.17 % |

**The water saving is negative where the model has been validated, and positive only where it has not.** Energy is the exact reverse. The two halves of the product are validated to opposite degrees.

**Strategic consequence: lead with energy; treat water as the thesis a pilot exists to test.**

### Cycle Ceiling Report, on a *measured* Saudi TSE assay

Water: Aramco Riyadh Refinery secondary treated sewage effluent, NACE Paper 577 Table 1. SiO₂ **18.0 mg/L measured** (not assumed).

| | |
|---|---|
| Scaling ceiling | **4.52 cycles**, bound by calcite |
| Currently running at | 3.0 → **14.4 %** water saving available |
| Hard arithmetic ceiling | 33.3 % |
| Water value at this duty | **$88,976/yr** |
| Capex bound for 3-yr payback | **$266,928 installed** — a *bound*, not a price |
| **Discharge permit** | **3.33 cycles** (daily max) on **nitrate**, if RCER-2015 applies |

Note the last row: **the permit binds before the chemistry does**, and on a parameter (nitrate) that no scaling index can see. RCER-2015 covers Jubail and Yanbu; this assay is from Riyadh, so it is reported and explicitly **not** imposed.

### Corrosion — the result inverted the objection

EPRI warns that raising cycles *and* dosing acid is corrosive. Implementing the standard indices showed the two levers are **not** both guilty:

- **Larson–Skold** is a *ratio* of aggressive anions to alkalinity. Concentrating a water multiplies every ion equally, so **cycles move it by exactly zero**. Acid moves it from **4.60 → 55.0** by destroying alkalinity.
- **Chloride pitting** is the mirror: cycles move it, acid does not.

So the corrosion exposure rides on the acid lever alone — and a Jubail site under RCER **may not dose acid anyway**, so it carries none of it. The regulation that costs the acid lever also removes the objection to it.

**Open, and needs a laboratory:** a corrosion *rate*. Acceptance criteria (UFC 3-230-13 Table 5-9) and a coupon rack are specified; nothing has been in water.

### A finding that constrains the data-centre case

On this water a **316 stainless** condenser reaches its chloride pitting threshold at **1.85 cycles** — *below* the 3.0 baseline being recommended, and far below the 4.52 scaling ceiling. CDU plate exchangers are routinely 316. **If a pilot site has stainless tubing, the cycles recommendation must be re-derived.**

### Instrumentation economics — this shapes the product

| | |
|---|---|
| Online silica + calcium + alkalinity + phosphate | **$120,000–185,000 per tower** + $20–30k/yr consumables |
| Annual saving on a 4.2 MW tower | **$89,000** |

**The instruments cost more than the thing they optimise.** That is structural and it is why no incumbent sells chemistry-bounded control.

So the skid buys only cheap instruments — toroidal conductivity, pH/ORP, Pt100, two magmeters, an industrial edge computer, a coupon rack — at roughly **$15k in instruments, $23–30k installed**, and **computes** the chemistry. Specific conductance is a known function of ion composition, so the residual between computed and measured conductance is a **free scaling alarm**: precipitation removes ions, and the measured value falls below prediction.

*(Toroidal, not contacting, for a specific reason: a fouled contacting cell **reads low**, so a bleed controller stops blowing down — the sensor failure drives the system deeper into scaling.)*

---

## 4. What is validated, and what is not

**Validated:**
- Chemistry engine against PHREEQC 3.9.0
- Tower thermal model against 165 experimental points (Almeria, Spain)
- Chiller model against EnergyPlus `Chiller:Electric:EIR` (York YT, 1758 kW)
- Dynamic basin and silica behaviour independently reimplemented in **OpenModelica**, agreeing with the Python to better than half a percentage point
- Operating-cycles baseline: **five independent operators**, all 2–4 cycles

**Not validated — and this is the honest list:**
- **No water has ever been in front of an instrument.** All chemistry is computed from published constants.
- **37.5 % of a Dhahran year is hotter and more humid than any calibration data.**
- **No corrosion rate.** Indices only.
- **Skin temperature rise** is now *derived* (7.45 K at the TEMA fouling allowance) rather than assumed, and shown not to be load-bearing (0.055 cycles per kelvin) — but not measured.
- **No pilot, no letter of intent, no patent.**

**Gates that fail, and are reported as failing:** evaporation model error 9.9 % against an 8 % threshold; V5 water saving 4.38 % against a 15 % threshold.

**A measurement limit worth knowing:** the water figures carry **±5.6 percentage points** from fan-movement uncertainty propagated through the calibration. **20 % is inside the error bar of the 15 % already computed.** Improving the water number is a *calibration* problem — one metered tower across a fan range — not a control problem.

---

## 5. Method rules this project runs on

These exist because each was bought with a mistake. Anyone reasoning about this work should hold to them:

1. **Pre-register thresholds before running the gate.** Gates that fail stay failed and get reported.
2. **Before "fixing" a missed threshold, check it against the physical ceiling.** One gate here demanded 8.5 cycles on a water that saturates at 7 — it was mis-specified, not missed.
3. **Suspect a defect in your own code before blaming the model.** Fifty defects found this way; forty-eight of them changed a number.
4. **Never quote a test count, or any figure, from memory** — only by copy from output in the same session.
5. **A constraint that is computed but not enforced is worse than one that doesn't exist**, because it reads like coverage. This failure mode occurred **eight times**, and once the fix for it reproduced it.
6. **Never attribute a quotation to a source you have not read.** This was violated twice and corrected both times.

---

## 6. Where outside help is actually useful

Ranked by how much it would move things:

1. **Market and pricing for a $25–30k retrofit device** in Gulf district cooling and Pakistani industry. Who buys, through what budget line, and against what incumbent contract?
2. **How to structure a paid pilot** that yields the one metered dataset the water claim needs — a single tower, metered, across a fan range.
3. **Chloride and stainless steel.** Is 1.85 cycles for 316 credible in practice, or is the pitting threshold used too conservative for a flowing, inhibited, oxygenated loop?
4. **Whether the energy-led framing survives** the fact that condenser-water optimisation is prior art seven times over — while none of that prior art carries any water chemistry.
5. **Ammonium in secondary treated effluent.** The measured Riyadh assay fails its charge balance by −5.25 % on the cation side; ~11 mg/L as N would close it. Is that the right reading?

**What is *not* useful:** suggestions to improve the water saving by better control. That is settled — it is inside the measurement error bar.

---

## 7. Current status

- 193 tests pass; internal consistency audit passes; defect register **50 found, 50 fixed, 0 open**.
- Branch pushed to `origin`, 26 commits ahead of `main`.
- **Customer interviews: 4 completed against a pre-registered target of 15 by 15 September 2026.** This is the binding constraint on accelerator applications, and no amount of engineering closes it.
- Sanabil (Saudi) applications close **1 October 2026**; a16z SPEEDRUN window **12 October – 1 November 2026**.
