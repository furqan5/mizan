# Mizan — external session handoff

*For pasting into a fresh assistant (ChatGPT or similar) that has **no access to the repository**. Everything needed to reason about this venture is in this file. Written 12 September 2026; every number rewritten from the artefacts on 18 September 2026.*

---

## 1. Who and what

Three energy engineers in Lahore, Pakistan.

- **Furqan** — the parent company. Deep physics and physics-informed AI for energy infrastructure. From the Arabic root *f-r-q*, to separate: the criterion distinguishing true from false.
- **Mizan** — the first product. *"The limit, computed."* A **retrofit supervisory controller** for cooling-tower / condenser-water loops. It co-optimises **fan speed, blowdown rate and acid dose** against **first-principles mineral saturation limits**.

Founders: Furqan Shakeel (CEO, physics core), Damia Baig (commercial), Muhammad Ahsan (commercial development).

Repository: `github.com/furqan5/mizan`, branch `integrate/sep17`. Public, under PolyForm Noncommercial.

---

## 2. The technical thesis, in one page

A cooling tower evaporates water. The dissolved minerals left behind concentrate. **Cycles of concentration** `C` = circulating TDS ÷ makeup TDS. Higher `C` means less blowdown and less makeup water:

```
makeup M = E·C/(C−1)          E = evaporation
```

so the **maximum** water saving available by raising cycles from a baseline `C₀` is exactly `1/C₀`. At `C₀ = 3` that is 33.3 %, and no controller can beat it. Everything is a fraction of that.

**Why plants don't just raise cycles:** they don't know where the limit is. The industry uses the **Langelier Saturation Index (LSI)**, which is a calcium-carbonate-only index. Real limits come from whichever mineral saturates first, and on recycled water that is usually **not** calcium carbonate.

**What Mizan computes instead:** full aqueous speciation — ion association, Davies activity coefficients, free vs total ions — compared with **PHREEQC 3.9.0** (95.7 % of 416 saturation indices (4 waters x 8 cycles x 4 temperatures) within a pre-registered tolerance of PHREEQC 3.9.0; the registered criterion FAILS because calcite agrees at only 89.1 %, worst -0.10 log units at 45-55 C), giving saturation indices for calcite, gypsum, amorphous silica, tricalcium phosphate, hydroxyapatite and brucite.

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
| **Inside** the validated envelope | 5,209 | **−3.22 %** | +8.82 % | +5.32 % |
| **Extrapolated** (wet-bulb > 21.9 °C) | 3,551 | +5.41 % | +0.95 % | +2.75 % |
| Whole year | 8,760 | +1.31 % | +4.86 % | +4.01 % |

Ratios of hour-weighted totals, from `results/annual_dhahran.json`. The split was
previously reported as 5,475 / 3,285 hours with −3.31 / +8.23 % water and
+8.84 / −0.39 % energy, and the whole year as +2.37 / +4.52 / +4.17 %. That
version classified whole wet-bulb bins by their centroid and so booked 266
unvalidated hours to the validated side (defect 60).

**The water saving is negative where the model has been validated, and positive only where it has not.** Energy runs the other way: it is earned inside the envelope and falls to about one per cent outside it. The two halves of the product are validated to opposite degrees.

**And the annual water figure does not survive a change of weather source.** On the TMYx file's humidity it is **+1.31 %**; on Dhahran station dew point it is **−2.64 %** (inside −4.77 %, outside +1.91 %). The pre-registered rule is that a claim true in one source and not in the other is weather-source-dependent, and a positive annual makeup-water saving is exactly that. Every claim the energy framing rests on holds in both.

**Strategic consequence: lead with energy; treat water as the thesis a pilot exists to test.**

### Cycle Ceiling Report, on a *measured* Saudi TSE assay

Water: Aramco Riyadh Refinery secondary treated sewage effluent, NACE Paper 577 Table 1. SiO₂ **8 mg/L measured** — as the page prints it. The repository carried 18.0 mg/L until 17 September 2026, when a high-resolution render of the page showed that the table's vertical rule had been read by OCR as a leading "1" (defect 67).

**This is the single most important correction in this document.** The one measured Gulf TSE analysis this package holds is **not silica-bound**. At 8 mg/L calcite binds first at every condition scored and at every acid pH scored, and this report's ceiling stays 4.52 cycles, calcite-bound. The only silica-bound water in the package carries an **assumed** 26.8 mg/L imported from brackish groundwater, and the data-centre silica floor rests on that same assumption — at 8 mg/L there is no floor at 3–7 cycles at all. So the silica thesis on Gulf TSE now rests on an assumption that the single measurement contradicts, and **one site assay decides it**.

| | |
|---|---|
| Scaling ceiling | **4.52 cycles**, bound by calcite |
| Currently running at | 3.0 → **14.4 %** water saving available |
| Hard arithmetic ceiling | 33.3 % |
| Water value at this duty | **$88,984/yr** |
| Capex bound for 3-yr payback | **$266,953 installed** — a *bound*, not a price |
| **Discharge permit** | **no cycle count complies** on the **nitrate monthly average** (makeup 3 mg/L against a 1 mg/L limit); the daily maximum alone would bind at **3.33 cycles**, if RCER-2015 applies |

Note the last row: **the permit binds before the chemistry does**, and on a parameter (nitrate) that no scaling index can see. On the monthly average it admits nothing at all. The package quoted 3.33 cycles for weeks because it had taken the daily-maximum column as the headline, and the search routine then returned its own lower bound, printing "complies at 1.00 cycles" where nothing complies (defect 69). RCER-2015 covers Jubail and Yanbu; this assay is from Riyadh, so it is reported and explicitly **not** imposed.

### Corrosion — the result inverted the objection

EPRI warns that raising cycles *and* dosing acid is corrosive. Implementing the standard indices showed the two levers are **not** both guilty:

- **Larson–Skold** is a *ratio* of aggressive anions to alkalinity. Concentrating a water multiplies every ion equally, so **cycles move it by exactly zero**. Acid moves it from **4.60 → 55.0** by destroying alkalinity.
- **Chloride pitting** is the mirror: cycles move it, acid does not.

So the corrosion exposure rides on the acid lever alone — and a Jubail site under RCER **may not dose acid anyway**, so it carries none of it. The regulation that costs the acid lever also removes the objection to it.

**Open, and needs a laboratory:** a corrosion *rate*. Acceptance criteria (UFC 3-230-13 Table 5-9) and a coupon rack are specified; nothing has been in water.

### A finding that constrains the data-centre case

On this water a **316 stainless** condenser reaches a published chloride **screen** at **1.85 cycles** — *below* the 3.0 baseline being recommended, and far below the 4.52 scaling ceiling. Three qualifications, all found on 17 September 2026 (defect 65), and all of them needed before this is repeated to anyone:

- It is a **guidance screen, not a measured onset**: 400 mg/L for 316 at neutral pH, 35 °C, clean flowing water. A plate vendor's own SS316 table gives 1050 mg/L at 50 °C and pH 8.25, which is 4.86 cycles on this same water.
- **1.85 is this water.** On the Dhahran field TSE, at 528 mg/L chloride, the same screen gives **0.76 cycles** — the makeup exceeds it before any concentration at all.
- **It does not automatically reach a CDU.** The CDU's technology-cooling side is a closed loop that never carries tower water; tower water wets a plate only where the facility loop is open to the tower rather than isolated by an exchanger. The package's data-centre model assumes the open topology and never said so.

**If a pilot site has stainless tubing, the cycles recommendation must be re-derived** — against the site's own chloride, pH, temperature and loop topology.

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
- Chemistry engine against PHREEQC 3.9.0 on 416 saturation indices: 95.7 % within a pre-registered tolerance, criterion failed on calcite (89.1 %)
- Tower thermal model against 147 distinct experimental points (Almeria, Spain; 165 rows as published)
- Chiller model against EnergyPlus `Chiller:Electric:EIR` (York YT, 1758 kW)
- Dynamic basin and silica behaviour independently reimplemented in **OpenModelica**, agreeing with the Python to better than half a percentage point
- Operating-cycles baseline: **five independent operators**, all 2–4 cycles

**Not validated — and this is the honest list:**
- **No water has ever been in front of an instrument.** All chemistry is computed from published constants.
- **40.5 % of a Dhahran year is hotter and more humid than any calibration data** — on the TMYx file's humidity. On Dhahran station dew point it is **24.3 %**, and across complete station years 2011–2024 it ranges 16.1–36.7 %. This was reported as 37.5 % until defect 60; that figure was a bin count, not an hour count.
- **No corrosion rate.** Indices only.
- **Skin temperature rise** is now *derived* (7.45 K at the TEMA fouling allowance) rather than assumed, and shown not to be load-bearing (0.055 cycles per kelvin) — but not measured.
- **No pilot, no letter of intent, no patent.**

**Gates that fail, and are reported as failing — there are now three of six:** heat-rejection error **6.27 %** against a 6.00 % threshold; evaporation model error **10.80 %** against an 8.00 % threshold; V5 water saving **4.38 %** against a 15 % threshold.

Heat rejection is the new one, and it is a data result rather than a model change. It read 5.94 % and passed on a 50-row holdout that turned out to contain 18 repeated measurements and one row the model had been trained on. On the 32 distinct rows it reads 6.27 %. The de-duplication was pre-registered before it was run and no threshold moved (defect 51).

**A measurement limit worth knowing:** the water figures carry a between-tower bar from fan-movement uncertainty propagated through the calibration. That bar was **±5.6 percentage points** while the error model treated the duplicated Exp3 file as a third campaign; on the two real campaigns it is **±2.0 pp** (defect 70). **Do not read that as the instrument having improved.** The Monte Carlo interval WIDENED at the same time, because the duplicate also carried the smallest residual scatter: V7's standard deviation moved 5.51 → 5.79 pp and P(true ≥ 20 %) fell 0.094 → 0.072. The population is now two campaigns, which the module itself says is not a population. Improving the water number is a *calibration* problem — one metered tower across a fan range — not a control problem.

---

## 5. Method rules this project runs on

These exist because each was bought with a mistake. Anyone reasoning about this work should hold to them:

1. **Pre-register thresholds before running the gate.** Gates that fail stay failed and get reported.
2. **Before "fixing" a missed threshold, check it against the physical ceiling.** One gate here demanded 8.5 cycles on a water that saturates at 7 — it was mis-specified, not missed.
3. **Suspect a defect in your own code before blaming the model.** Seventy-four defects found this way; most of them changed a number, and ten are still open.
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
5. **Which bases did the laboratory report?** The measured Riyadh assay fails its charge balance by −5.25 % on the cation side. The package used to say that about 11 mg/L of ammonium as N closes it — but the same table prints **nitrite at 31 mg/L**, an anion, and states no basis for either species. Counting both: with nitrite as NO₂⁻ the balance closes within ±5 % on *every* ammonia basis (−2.19 to −3.76 %); with nitrite as N it fails on every one (−11.1 to −12.7 %). So the imbalance is consistent with the dropped nitrogen, and the ammonia basis cannot be decided from the analysis (defect 68).

**What is *not* useful:** suggestions to improve the water saving by better control. That is settled — it is inside the measurement error bar.

---

## 7. Current status

- 295 tests pass and 4 are registered xfails; internal consistency audit passes; defect register **74 found, 64 fixed, 10 open**.
- Branch pushed to `origin`, 26 commits ahead of `main`.
- **Customer interviews: 4 completed against a pre-registered target of 15 by 15 September 2026.** This is the binding constraint on accelerator applications, and no amount of engineering closes it.
- Sanabil (Saudi) applications close **1 October 2026**; a16z SPEEDRUN window **12 October – 1 November 2026**.
