# Chemistry & Thermal Evidence Base

Literature support for the Mizan cooling-tower water/energy controller.
Compiled 29 Aug 2026. Every source below was fetched and read; nothing is cited from memory.

**Confidence tags**

| Tag | Meaning |
|---|---|
| `[C]` | Confirmed — source fetched, URL given, numbers quoted from the document |
| `[A]` | Inference/calculation by us from `[C]` inputs; arithmetic shown so it can be re-run |
| `[UNVERIFIED]` | We looked and could not confirm. Do not cite. Stated explicitly so nobody fills the gap by guessing |

**Verdict summary on the three model findings** (detail in §8)

| Model finding | Verdict |
|---|---|
| 1. Skin-temperature saturation lowers safe cycles by ~15.6% | **Supported in mechanism, magnitude likely overstated ~2x, and wrongly applied to silica** |
| 2. Gypsum, not calcite, binds at high cycles; LSI cannot see gypsum | **Strongly supported** |
| 3. Water-activity effect on evaporation is small (0.485% at 15,000 mg/L) | **Number supported to 3 significant figures; but the *evaporation* effect is 1.7–3.4x larger than the vapour-pressure effect — see §6.3** |

---

## 1. Water analyses

### 1.1 Our current analysis — now fully published, no adjustment needed `[C]`

This is the single most useful result of the whole exercise. The Saudi TSE analysis we have been using comes from a **Saudi Aramco pilot study**, and the source publishes **chloride = 528 mg/L**. We do not need to close the balance by adjusting chloride.

Source: *Use of Treated Sewage Effluent as Cooling Tower Makeup Water — A Pilot Study*
https://aclima.eus/en/noticia/use-of-treated-sewage-effluent-as-cooling-tower-makeup-water-a-pilot-study/
(also carried by Water Technology Online, ID 14187302 — that mirror returns HTTP 403 to automated fetch)

**Table 1.1 — Saudi Aramco TSE cooling-tower makeup (mg/L unless noted)**

| Parameter | Value | Status |
|---|---|---|
| TDS | 1500 | `[C]` |
| Ca²⁺ | 106 | `[C]` |
| Mg²⁺ | 41 | `[C]` |
| Na⁺ | 310 | `[C]` |
| HCO₃⁻ | 105 | `[C]` |
| SO₄²⁻ | 300 | `[C]` |
| **Cl⁻** | **528** | **`[C]` — was previously an adjusted value in our model** |
| PO₄³⁻ | 8 | `[C]` |
| TOC | 5 | `[C]` |
| K⁺ | not reported | `[UNVERIFIED]` — assume 15–25 mg/L for TSE |
| SiO₂ | not reported | `[UNVERIFIED]` — our 15 mg/L is an assumption (but see §1.3, which back-calculates ~12 mg/L from an independent plant) |
| NO₃⁻, CO₃²⁻, pH, alkalinity | not reported | `[UNVERIFIED]` |

**Operating context `[C]`:** Saudi Arabia, Saudi Aramco facility. Previously ran on groundwater at **2 cycles** with *"severe scaling"*; on TSE, cycles *"almost doubled (from 2 to 3.5)"* and the system stayed *"clean without mineral deposit formation"*.

**Charge balance as published `[A]`** (equivalent weights; Ca 20.039, Mg 12.153, Na 22.990, HCO₃ 61.016, SO₄ 48.031, Cl 35.453):

```
Σ cations = 106/20.039 + 41/12.153 + 310/22.990          = 22.147 meq/L
Σ anions  = 105/61.016 + 300/48.031 + 528/35.453         = 22.860 meq/L
CBE = (Σ+ − Σ−)/(Σ+ + Σ−) × 100                          = −1.58 %
```

Within the APHA ±5% acceptance band **as published**. Adding the unreported K⁺ (20 mg/L) and treating PO₄ as HPO₄²⁻ at pH 7.5 tightens it to **−0.80%**.

**What our adjustment had been doing `[A]`:** forcing balance on the five published ions alone requires
`Cl = (22.147 − 1.721 − 6.246) × 35.453 = 503 mg/L`, i.e. **4.8% below the published 528**. The method was sound; it under-called chloride only because K⁺ and PO₄ were omitted from the cation/anion sums.

> **Action:** replace the adjusted chloride with 528 mg/L. Keep SiO₂ = 15 mg/L but label it an assumption.

---

### 1.2 Same study — Saudi Aramco groundwater (the water TSE replaced) `[C]`

Same source as §1.1. Partial analysis, but a genuine Gulf brackish cooling makeup and a useful high-hardness stress case.

| Parameter | Value (mg/L) |
|---|---|
| TDS | 3040 |
| Ca²⁺ | 233 |
| Mg²⁺ | 97 |
| SO₄²⁻ | 558 |
| HCO₃⁻ | 226 |
| Na⁺, K⁺, Cl⁻, SiO₂ | not reported `[UNVERIFIED]` |

Charge balance cannot be closed — Na and Cl are missing. Use only as a scaling-stress scenario, not as a validated ionic input. Note the Ca × SO₄ product is 4.4x that of the TSE: this is the water that scaled severely at only 2 cycles.

---

### 1.3 Circulating cooling water, 1000 MW plant on treated municipal wastewater `[C]`

Genuinely useful because it is a **real cooling tower running on wastewater makeup**, with makeup and circulating water measured at the same time — so cycles of concentration are directly observable.

Source: Yousefpour et al. (2026), *Assessment of Water Chemistry in the Hybrid Cooling System of a Thermal Power Plant Using ICP-MS Analysis and Comparison with EPRI Guidelines*, **Eurasian J. Chem. Med. Pet. Res. 6(1), 129–139**. Niroo Research Institute, Iran (Persian Gulf region).
DOI: 10.5281/zenodo.21924824 · https://zenodo.org/records/21924824 · CC-BY-4.0, full PDF downloadable

**Table 1.3a — General analysis (paper's Table 1) `[C]`**

| Sample point | Cond. (µS/cm) | TDS (ppm) | Temp (°C) | pH |
|---|---|---|---|---|
| Demineralised | 1.15 | 0.57 | 22.6 | 8.74 |
| Dry tower (dry cycle) | 6.06 | 3.04 | 31.0 | 7.61 |
| **Make-up, wet tower (wastewater)** | **1600** | **800** | **24.0** | **7.80** |
| **Wet tower (circulating)** | **8400** | **4210** | **29.0** | **7.57** |
| Shell & tube HX entry | 6.24 | 3.12 | 36.0 | — |

**Cycles of concentration `[A]`:** 4210 / 800 = **5.26 cycles** on wastewater makeup. Independent corroboration that 5+ cycles on reuse water is achievable in practice.

**Table 1.3b — Wet tower circulating water, major species (paper text) `[C]`**

| Species | Value |
|---|---|
| Ca | 355.8 ppm |
| Na | 1230 ppm |
| K | 117.2 ppm |
| Si | 29.66 ppm (as Si) |
| Cu | 135.9 ppb |
| Zn | 454.2 ppb |
| Al | 30 ppb |

**Derived `[A]`:**
- Si 29.66 as Si → **SiO₂ = 29.66 × 60.08/28.09 = 63.4 mg/L as SiO₂** in the circulating water.
- Back to makeup at 5.26 cycles → **SiO₂ ≈ 12.1 mg/L** in the wastewater makeup. **This independently corroborates our assumed 15 mg/L SiO₂** to within 20%.
- Ca back-calculated to makeup ≈ 67.6 mg/L (vs 106 in the Aramco TSE).

**Limitation:** cations and metals only — no SO₄, Cl, HCO₃ or alkalinity. Not charge-balanceable. Cite for cycles, silica and Ca; do not use as a complete ionic input.

The paper also notes the wet tower is a *"high-ionic-strength environment"* prone to *"extensive scaling of calcium carbonate, silicates, and complex salts"* — consistent with our modelling emphasis.

---

### 1.4 Al-Ahsa, Saudi Arabia — treated wastewater and drainage water `[C]`, partial

Source: AL-Bander et al. (2026), *Influence of Physicochemical Properties and Ionic Composition on Bacterial Abundance in Treated Wastewater and Post-Irrigation Agricultural Drainage Water: A Case Study from Al-Ahsa, Saudi Arabia*, **Frontiers in Environmental Science 14**. DOI: 10.3389/fenvs.2026.1857130
https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2026.1857130/abstract

| Water | Chloride | Sulfate | Organic matter |
|---|---|---|---|
| Treated wastewater (TWW) | 314–333 mg/kg | 206–218 mg/kg | 0.17–0.19% |
| Agricultural drainage water | 1520–1850 mg/kg | 820–980 mg/kg | 0.65–0.72% |

The abstract states the full study measured pH, T, TDS, EC, turbidity, free chlorine, total hardness, Na, K, Ca, Mg, Cl, CO₃, HCO₃, SO₄, DO, BOD, COD, NH₄, NO₃, PO₄ — but **the full table sits behind the full-text and we could not retrieve it** `[UNVERIFIED]`. King Faisal University, Al-Ahsa.

Note the TWW here is *less* saline than the Aramco TSE (Cl 314–333 vs 528; SO₄ 206–218 vs 300) — useful as a lower bound on the Saudi TSE envelope.

---

### 1.5 Arabian Gulf seawater — salinity envelope `[C]`

Relevant because seawater is a real Gulf cooling makeup and the reference case for §6.

Source: Miyakawa et al. (2021), *Reliable Seawater RO Operation with High Water Recovery and No-Chlorine/No-SBS Dosing in Arabian Gulf, Saudi Arabia*, **Membranes 11(2), 141**. DOI: 10.3390/membranes11020141
https://pmc.ncbi.nlm.nih.gov/articles/PMC7923200/ — Al-Jubail, Arabian Gulf

| Parameter | Max | Min | Average |
|---|---|---|---|
| TDS (mg/L) | 48,034 | 42,559 | **45,484** |
| Temperature (°C) | 39.3 | 16.2 | 27.3 |
| SDI | 3.90 | 1.50 | 2.87 |

Gulf seawater is markedly saltier than ocean average (~35,000 mg/L) and, importantly for gypsum, **sulfate-enriched**: one Half Moon Bay (Saudi) analysis reports **4922 mg/L sulfate vs ~2700 mg/L in global seawater** — reported via search snippet only, primary table not retrieved `[UNVERIFIED as to exact provenance]`.

### 1.6 Honest gap statement

The brief asked for **2–3 more real, fully-specified, charge-balanced Gulf analyses**. We found **one further genuinely useful plant analysis (§1.3)** and **two partial ones (§1.2, §1.4)**. We did **not** find a second fully-specified, publicly accessible, charge-balanced Gulf TSE analysis with the complete anion suite including SiO₂.

Blocked routes (all returned HTTP 403 to automated fetch — a human browser will get them):
- MDPI *Water* **17(5), 709 (2025)**, *Analyzing Riyadh Treated Wastewater Parameters for Irrigation Suitability* — search snippet confirms it tabulates pH, TDS, EC, total alkalinity, residual chlorine, chloride, sodium, potassium, calcium, magnesium, bicarbonate and sulfate, with **TDS 1115.02–1435.39 mg/L**. This is very likely the best remaining candidate and is squarely in our TDS range. **Recommend a manual download.**
- Frontiers full text for §1.4.
- ScienceDirect: *Reuse of Treated Sewage Effluent (TSE) in Qatar*, S2214714416301866.

---

## 2. Where the Langelier index breaks down

### 2.1 The primary citable source `[C]`

Ferguson, R.J. (2011), *Mineral Scale Prediction and Control at Extreme TDS*, **Paper No. IWC-11-77**, International Water Conference. French Creek Software.
https://www.frenchcreeksoftware.com/iwc2011/iwc-11-77final.pdf

This paper is worth reading in full. It enumerates the four assumptions behind the LSI and shows what each costs:

| # | Langelier's assumption | Failure mode |
|---|---|---|
| 1 | Total analytical values = free ion concentrations | Ignores ion pairing (CaSO₄°, CaHCO₃⁺, MgSO₄°…). Two waters of identical ionic strength differing only in sulfate vs chloride get the *same* LSI but very different true saturation |
| 2 | M alkalinity ≈ bicarbonate | Fails when phosphate, silicate, borate, ammonia, sulfide contribute to the titration — i.e. exactly in TSE |
| 3 | Activity coefficients from Debye–Hückel limiting law | Invalid above low ionic strength |
| 4 | pH independent of temperature | *"A 1.0 pH unit error results in up to a ten fold error calcite saturation calculation."* |

The paper's own summary: simple indices *"should only be used for very dilute waters near neutral pH, and then only when more advanced models are not available."* Langelier himself characterised the applicable regime as (a) low ionic strength, (b) near-neutral pH, (c) ambient temperature.

**The operational consequence, quoted:** when indices set operating limits such as *"maximum cycles of concentration in cooling water"*, ignoring ion pairing means *"in the worst case, the use of indices based upon total ions present can result in the establishment of operating limits being too high."*

### 2.2 The quantitative ionic-strength ladder `[C]` + `[A]`

Activity-model validity limits, from IWC-11-77 §"Activity Coefficients" and de Moel et al. (2013):

| Model | Valid to (ionic strength) | Source |
|---|---|---|
| Debye–Hückel limiting law (LSI's basis) | ~0.005 mol/kg | classical `[A]` |
| Extended Debye–Hückel / WATEQ | ~0.1 mol/kg | `[A]` |
| Davies (1962) | ~0.5 mol/kg | `[A]` |
| B-dot (Helgeson 1969) | *"useful to 3 molal ionic strength in NaCl based systems and up to 1 molal in other solutions"* | `[C]` IWC-11-77 |
| Robinson–Stokes + Bromley | *"used successfully in the 3 to 6 molal range for NaCl based"* brines | `[C]` IWC-11-77 |
| Pitzer / virial | required above ~0.5 mol/kg | `[C]` de Moel et al. |

de Moel, P.J., van der Helm, A.W.C., van Rijn, M., van Dijk, J.C., van der Meer, W.G.J. (2013), *Assessment of calculation methods for calcium carbonate saturation in drinking water for DIN 38404-10 compliance*, **Drinking Water Engineering and Science 6, 115–124**. DOI: 10.5194/dwes-6-115-2013 (open access, CC-BY)
https://dwes.copernicus.org/articles/6/115/2013/dwes-6-115-2013.pdf

That paper specifies `pitzer.dat` is for waters of high salt content — **ionic strength > 500 mmol/kgw** — *"calibrated on, for instance, seawater and brine"*, and confirms `phreeqc.dat` and `wateq4f.dat` as the mainstream ion-association databases (its Table 4 lists phreeqc.dat, wateq4f.dat, sit.dat, pitzer.dat, llnl.dat, minteq.dat plus purpose-built stimela.dat / din38404-10_2012.dat). It also notes `phreeqc.dat` includes ion pairs of sodium with sulphate, phosphate, bicarbonate, carbonate and hydroxide that the DIN standard omits.

### 2.3 Applying the ladder to *our* water — the decisive calculation `[A]`

Ionic strength of the Aramco TSE, `I = ½ Σ cᵢzᵢ²` using Table 1.1 plus K = 20 mg/L:

```
I(makeup) = 0.0302 mol/L      →      I(N cycles) ≈ 0.0302 × N
```

| Cycles N | I (mol/L) | Appropriate activity model |
|---|---|---|
| 1 | 0.030 | already past Debye–Hückel limiting law |
| 2 | 0.060 | extended DH marginal |
| **3.5** (Aramco pilot) | **0.106** | **extended DH exhausted** |
| 5 | 0.151 | ion association (phreeqc.dat / wateq4f.dat) |
| 8 | 0.242 | ion association |
| 10 | 0.302 | ion association |
| 15 | 0.453 | ion association, approaching Davies limit |
| **16.5** | **0.499** | **Pitzer threshold crossed** |
| 20 | 0.604 | Pitzer required |

> **This is the cleanest single argument in the evidence base.** The LSI's activity model is out of validity at the *first cycle* of this water and comprehensively so by the 3.5 cycles the Aramco pilot actually ran. An ion-association model (PHREEQC `phreeqc.dat` or `wateq4f.dat`) is the correct tool from 1 to ~16 cycles; Pitzer (`pitzer.dat`) only becomes necessary above ~16.5 cycles. **Our chosen approach is exactly right, and we can now say so with a number rather than an assertion.**

### 2.4 Supporting statements

- LSI becomes unpredictive at very low TDS (<~100 mg/L) or very high TDS (>~10,000 mg/L); Langelier himself noted the desirability of including ion association and common-ion effects in all but low-TDS waters `[C]` (via IWC-11-77 and corroborating search results).
- Above ~10,000 mg/L TDS the Stiff–Davis Stability Index is conventionally preferred over LSI because it carries an ionic-strength term `[A]`, from Stiff & Davis (1952), *A Method for Predicting the Tendency of Oil Field Water to Deposit Calcium Carbonate*, Pet. Trans. AIME 195:213 — cited as ref. 2 of IWC-11-77 `[C]`.
- PHREEQC itself: Parkhurst & Appelo (2013), USGS. https://water.usgs.gov/water-resources/software/PHREEQC/ — *"PHREEQC has all of the capabilities of WATEQ4F and the WATEQ4F data base is included in the distribution."*

---

## 3. Scaling at heat-transfer surfaces vs bulk

### 3.1 The mechanism is well established — but it is sign-dependent `[C]`

Berce, J., Zupančič, M., Može, M., Golobič, I. (2021), *A Review of Crystallization Fouling in Heat Exchangers*, **Processes 9(11), 1356**. MDPI, open access.
https://psecommunity.org/wp-content/plugins/wpor/includes/file/2302/LAPSE-2023.5350-1v1.pdf

The governing sentence, quoted directly:

> *"Depending on the foulant, higher surface temperature (at constant bulk temperature) will cause more fouling with inversely-soluble salts or less fouling with normally-soluble salts."*

Also from the same review:
- Surface and bulk temperature **together** set the concentration gradient that drives diffusive transport to the surface.
- *"The temperature of the surface will also undergo changes as deposition progresses due to the insulating effect of the formed layer"* — the deposit face gets **hotter** than the clean metal wall, so a skin-temperature model becomes *more* correct as the exchanger fouls.
- Determining surface temperature is *"among the biggest contributing factors to measurement uncertainty"* — an honest caveat that our +8 K is itself hard to measure.

Corroborating, Veolia *Water Handbook* Ch. 25 (Deposit and Scale Control — Cooling System),
https://www.watertechnologies.com/handbook/chapter-25-deposit-and-scale-control-cooling-system `[C]`:
scale-forming compounds *"supersaturate in the higher-temperature water adjacent to the heat transfer surface and precipitate on the surface"*, and it names calcium carbonate, calcium phosphate and magnesium silicate as the retrograde-solubility species. Critically, it places **calcium sulfate in a different category** — capable of *"scaling on unheated surfaces when their solubilities are exceeded in the bulk water."*

### 3.2 The sign table — this is a required correction to our model

| Mineral | Solubility vs temperature | Evaluate saturation at | Effect of using skin T |
|---|---|---|---|
| **Calcite (CaCO₃)** | Retrograde (falls as T rises) | **Hot skin** | Correctly **more** conservative ✅ |
| **Gypsum (CaSO₄·2H₂O)** | Rises to a max at ~35–40 °C, then falls | Bulk *and* skin; near-neutral in the 30–45 °C window | Essentially **no benefit**; slightly *anti*-conservative below 40 °C ⚠️ |
| **Amorphous silica (SiO₂)** | **Normal/prograde — rises with T** | **Coldest point** (tower basin / cold return) | **Anti-conservative — under-predicts silica risk** ❌ |
| Magnesium silicate | Inverse | Hot skin | More conservative ✅ |
| Barium sulfate | Least soluble cold | Coldest point | Anti-conservative ❌ |

Sources for the sign column:
- Silica normal solubility, magnesium silicate inverse: Demadis (2003) — §4.2 below, quoted: *"Silica exhibits normal solubility characteristics, which increase proportionally to temperature. In contrast, magnesium silicate exhibits inverse solubility."* `[C]`
- Gypsum maximum near 35–40 °C: §4.1 below `[C]`
- Cold-point species: IWC-11-77 `[C]` — *"The coldest point might be of interest for scales like amorphous silica and barium sulfate which are least soluble at the coldest point in the system."*

> **Action:** the skin-temperature offset must be applied **per mineral with the correct sign**, not as a global +8 K. Applying +8 K to amorphous silica makes the model optimistic about the very species that has no good inhibitor (§5.3).

### 3.3 Is +8 K defensible? `[A]` — a bounded answer

No source states a canonical wall-to-bulk differential for water-cooled condensers; that number is not published as a rule of thumb `[UNVERIFIED]`. It has to be derived. It is a one-line calculation:

```
ΔT_wall−bulk  =  q″ / h_i
```

**Heat flux `[C]`:** Veolia *Water Handbook* Ch. 23 (Cooling Water Systems — Heat Transfer),
https://www.watertechnologies.com/handbook/chapter-23-cooling-water-systems-heat-transfer
*"The heat flux is generally low and in the range of 5,000 to 15,000 Btu/ft²/hr."*
Converting at 3.1546 W/m² per Btu/hr·ft²: **15.8 – 47.3 kW/m²**.

**Water-side film coefficient `[A]`**, Dittus–Boelter `Nu = 0.023 Re^0.8 Pr^0.4` (fluid being heated), water at 30 °C (ρ 995.7 kg/m³, μ 7.97×10⁻⁴ Pa·s, k 0.615 W/m·K, cp 4178 J/kg·K, Pr 5.414), tube ID 17.6 mm:

**Table 3.3 — ΔT_wall−bulk (K)**

| Water velocity | h_i (W/m²K) | q″ = 15.8 kW/m² | q″ = 31.5 kW/m² | q″ = 47.3 kW/m² |
|---|---|---|---|---|
| 1.2 m/s | 5440 | 2.9 | 5.8 | **8.7** |
| 1.5 m/s | 6503 | 2.4 | 4.8 | 7.3 |
| **2.0 m/s** (typical design) | 8186 | 1.9 | **3.8** | 5.8 |
| 2.5 m/s | 9786 | 1.6 | 3.2 | 4.8 |

**Verdict: +8 K is defensible only as a conservative upper bound.** It corresponds to the corner of the envelope — low velocity (~1.2 m/s) *and* top-of-range heat flux (~47 kW/m²). A **typical clean design point (2 m/s, ~31 kW/m²) gives ΔT ≈ 3.8 K**, roughly half our assumption.

Two things push the real number back up toward 8 K, so the assumption is not unreasonable as a design margin:
1. **Fouling.** Per Berce et al., the deposit face runs hotter than clean metal, and this grows with deposit thickness. +8 K is a plausible *fouled* condition.
2. **Enhanced tubes** raise h (lowering ΔT), but high-flux designs raise q″ faster.

> **Recommendation:** stop treating +8 K as a constant. Compute `ΔT = q″/h_i` from the duty, tube geometry and velocity the controller already knows, and report the cycles limit as a band across ΔT = 3–9 K rather than a point estimate. Retain +8 K as the conservative design case. Because the calcite effect is roughly linear in ΔT over this range, a typical 3.8 K would cut the claimed 15.6% cycles penalty to **roughly 7–8%** — smaller, but still far too large to ignore, so the finding survives in substance.

### 3.4 Related empirical work `[C]` (references verified to exist; full texts paywalled)

- Berce et al. 2021, Processes 9(11) 1356 — open access, above.
- *Fouling Characteristics of Water−CaSO₄ Solution under Surface Crystallization and Bulk Precipitation*, Int. J. Heat Mass Transfer — https://www.sciencedirect.com/science/article/abs/pii/S0017931021009170. Distinguishes surface-crystallisation (bulk kept **unsaturated**) from bulk-precipitation regimes — directly the distinction our model makes.
- *Parametric study of calcium sulfate crystallization fouling in cross-flow heat exchanger using RSM*, Heat and Mass Transfer — https://link.springer.com/article/10.1007/s00231-023-03368-6. Reported conditions include Re 23,000 (0.6 m/s), bulk CaSO₄ 3.0 kg/m³, bulk inlet 40 °C, with wall temperature controlled to ±1%.
- *Crystallization Fouling of CaCO₃ — Effect of Bulk Precipitation on* … https://heatexchanger-fouling.com/wp-content/uploads/2021/09/30_Paeaekkoenen_F.pdf — open access.

---

## 4. Gypsum and amorphous silica limits

### 4.1 Gypsum `[C]`

**Solubility and its temperature dependence**
- Gypsum solubility ≈ **2.1 g/L at 20 °C** in pure water.
- **Solubility rises with temperature to a maximum at ~35–40 °C, then falls.** This is why gypsum sits awkwardly between "normal" and "inverse" in a cooling tower operating at 30–45 °C.
- Gypsum ⇌ anhydrite transition temperature in pure water is **42 °C**, shifting to lower temperatures as NaCl increases; commonly quoted as ~60 °C in NaCl solutions.
- Calcium sulfate solubility is **~40x that of calcium carbonate** — which is exactly why it only becomes binding at high cycles, once concentration has run far enough.
- Solubility passes through a **maximum at 2–4 molal NaCl** then decreases (common-ion/activity interplay).

Sources: MDPI *Data* 7(10) 140, *Experimental Data on Solubility of the Two Calcium Sulfates Gypsum and Anhydrite in Aqueous Solutions* — https://www.mdpi.com/2306-5729/7/10/140 (open access data compilation, the best single reference for tabulated CaSO₄ solubility); Bock (1961), *On the Solubility of Anhydrous Calcium Sulphate and of Gypsum in Concentrated Solutions of Sodium Chloride at 25, 30, 40 and 50 °C*, Can. J. Chem. — https://cdnsciencepub.com/doi/10.1139/v61-228; Veolia Water Handbook Ch. 25.

**Is gypsum documented as the binding constraint on high-cycle reuse water?** — **Yes, in mechanism and by analogy `[C]`/`[A]`.**
- IWC-11-77 explicitly warns that acid feed to control calcite drives you into sulfate: lowering the pH control point *"increase[s] the sulfate based scale potential of the water due to the higher sulfates in the make-up or feedwater, and recirculating cooling water or R.O. brine."* `[C]` **This is precisely our finding — suppress calcite and gypsum becomes binding.**
- Agricultural drainage water in the San Joaquin Valley is *"nearly saturated with gypsum"*, making gypsum the reclamation-limiting species `[C]` (Rahardianto et al., *Calcium sulfate (gypsum) scaling in nanofiltration of agricultural drainage water* — https://www.sciencedirect.com/science/article/abs/pii/S037673880200128X).
- Gulf seawater is sulfate-enriched (§1.5), and the Aramco groundwater carries SO₄ 558 mg/L (§1.2) — regionally, sulfate is the abundant anion.
- A **direct** paper naming gypsum as the binding cycles constraint for Gulf TSE cooling makeup: `[UNVERIFIED]` — we did not find one. Our model appears to be making a novel, defensible claim rather than restating a known result. That is a strength for the application, provided it is framed as such.

**LSI cannot represent gypsum — confirmed `[C]`.** IWC-11-77 Table 2 gives separate saturation-level expressions per mineral; the LSI is derived solely from `{Ca}{CO₃}/Ksp_CaCO₃`. Gypsum requires `{Ca}{SO₄}/Ksp_CaSO₄`. There is no sulfate term anywhere in the Langelier formulation. This is definitional, not a matter of accuracy.

### 4.2 Amorphous silica `[C]`

Demadis, K.D. (2003), *Water Treatment's "Gordian Knot"*, **Chemical Processing**, May 2003, p. 29.
https://www.chemistry.uoc.gr/demadis/pdfs/3-Gordian%20knot-Silica.pdf

| Finding | Value |
|---|---|
| Amorphous silica solubility in water | **150–180 ppm**, depending on water chemistry and temperature |
| pH dependence | *"largely independent of pH in the range of 6 to 8"* |
| Temperature dependence | **Normal** — solubility increases with temperature |
| Silica scale favoured at | pH < 8.5 |
| Magnesium silicate scale favoured at | pH > 8.5, and Mg silicate has **inverse** solubility |
| Typical Gulf/arid raw water silica | 50–100 ppm as SiO₂ (from quartz dissolution) |

**Demadis operating guidelines (his figure), directly implementable:**

| Condition | Limit |
|---|---|
| pH < 7.5 | SiO₂ < 200 ppm **and** Mg × SiO₂ < 40,000 |
| pH > 7.5 | SiO₂ < 100 ppm **and** Mg × SiO₂ < 20,000 |

where Mg is expressed as ppm CaCO₃ and SiO₂ as ppm SiO₂.

> Note our circulating-water datapoint from §1.3: **SiO₂ 63.4 mg/L at pH 7.57** — inside the pH>7.5 limit of 100 ppm, but only by a factor of 1.6. At 15 mg/L makeup silica, the 100 ppm limit binds at **6.7 cycles**; at 200 ppm (pH<7.5) it binds at **13.3 cycles** `[A]`. **Silica may well bind before gypsum if the tower runs alkaline** — worth checking against the model.

**Water activity appears in the silica saturation expression `[C]`.** IWC-11-77 Table 2 gives amorphous silica saturation level as `{H₄SiO₄} / ((H₂O)² × Ksp_SiO₂)`. The water-activity term is squared. This is a direct link between our §6 work and our §4 work: **at high cycles, lowering a_w raises the silica saturation ratio.** At 15,000 mg/L, a_w ≈ 0.995, so the effect is `1/0.995² = 1.010` — a 1% increase in silica SI `[A]`. Small, but it is the one place where the water-activity model feeds the scaling model rather than the evaporation model.

---

## 5. Antiscalant performance — the key table

### 5.1 Published limits `[C]`

**IWC-11-77 Table 7 — "Treated Limits Comparison"**, reproduced verbatim, with log₁₀ conversions added by us:

| Scale species | Formula | Typical saturation ratio limit | Stressed treatment limit | ⇒ SI typical `[A]` | ⇒ SI stressed `[A]` |
|---|---|---|---|---|---|
| Calcium carbonate | CaCO₃ (calcite) | **135 – 150** | **200 – 225** | **2.13 – 2.18** | **2.30 – 2.35** |
| Calcium sulfate | CaSO₄·2H₂O (gypsum) | **2.5 – 4.0** | **4.0 +** | **0.40 – 0.60** | **≥ 0.60** |
| Barium sulfate | BaSO₄ (barite) | 80 | 80+ | 1.90 | 1.90 |
| Strontium sulfate | SrSO₄ (celestite) | 12 | 12 | 1.08 | 1.08 |
| **Silica** | **SiO₂ (amorphous)** | **1.2** | **2.5** | **0.08** | **0.40** |
| Tricalcium phosphate | Ca₃(PO₄)₂ | 1500 – 2500 | 125,000 | 3.18 – 3.40 | 5.10 |

The paper's framing: *"Scale inhibitors have upper limits and are not effective above saturation level driving force, regardless of the inhibitor dosage."* Limits are *"generally accepted limits for inhibition of scales by standard commercially available inhibitors"*, with "stressed" meaning formulations designed for extreme conditions.

Separately, for a specific named phosphonate: *"the scale inhibitor HEDP (1-1 hydroxyethylidene diphosphonic acid) has an upper limit of 150 saturation ratio. This equates to LSI limits of 2.5 in a high sulfate cooling water but 2.8 in a high chloride water."* `[C]`

That last sentence is worth dwelling on: **the same physical inhibitor limit maps to two different LSI values depending on the anion mix** (2.5 vs 2.8), while it is a single number — SR 150, SI 2.18 — when computed with an ion-association model. This is the most concrete published demonstration that our modelling choice in §2 is not academic.

### 5.2 Verdict on our assumed limits `[A]`

| Our limit | Equivalent SR | Published typical | Published stressed | Verdict |
|---|---|---|---|---|
| **SI_calcite ≤ 2.0** | SR 100 | SR 135–150 (SI 2.13–2.18) | SR 200–225 (SI 2.30–2.35) | **Reasonable, mildly conservative** — ~0.13–0.18 log units below normal practice. Defensible as a safety margin. Could go to 2.15 on a standard phosphonate programme |
| **SI_gypsum ≤ 0.3** | SR 2.0 | SR 2.5–4.0 (SI 0.40–0.60) | SR 4.0+ (SI ≥0.60) | **Conservative by 0.10–0.30 log units.** Literature supports **0.40–0.60** on a normal programme |

**The gypsum limit is the one to revisit.** Raising SI_gypsum from 0.3 to 0.40 (the bottom of the published typical band) is a 26% increase in the allowable {Ca}{SO₄} product. If gypsum is genuinely the binding constraint at high cycles (finding 2), this is the single change with the largest effect on claimed water savings — and it moves in our favour. We recommend:
- Keep **0.3 as the default/conservative** setting for a first deployment on an unfamiliar site.
- Expose **0.40–0.60** as the "characterised antiscalant programme" setting, cited to IWC-11-77 Table 7.
- Never exceed 0.60 without inhibitor-specific vendor data.

Note also IWC-11-77's four rules for dosing at extreme conditions, of which #4 is directly relevant to a controller: *"include a realistic limit. Assure that the point where an inhibitor will fail regardless of dosage is known."*

### 5.3 Is there an effective inhibitor for amorphous silica? `[C]`

**Short answer: partially, and it is by far the weakest link.** SR limit 1.2 typical / 2.5 stressed — the lowest ratios in the whole table.

From Demadis (2003):
- Two distinct approaches: **inhibition** (preventing silica oligomerisation/polymerisation, so silica stays soluble and reactive) and **dispersion** (preventing agglomeration and adhesion of colloidal particles).
- **Dispersants barely work:** *"Dispersant technologies have shown little activity, being able to stabilize only slight increases of total silica in a tower — for instance, by feeding a dispersant, silica levels may increase from 150-200 to 180-220 ppm, which is often an undetectable increase."*
- **Polymerisation inhibitors are better:** *"silica polymerization inhibitors have shown to be more effective against silica scale deposition."*
- Silica deposits are near-impossible to remove: require hydrofluoric-acid cleaning or mechanical removal.
- Silica fouling is aggravated by Fe²⁺/³⁺ and Al³⁺ and their hydroxides; corroded steel surfaces are *"very prone to silica fouling"*. CaCO₃ precipitates provide *"a crystalline matrix in which silica can be entrapped and grow"* — so controlling calcite indirectly controls silica.
- Non-chemical routes: reverse osmosis, ion exchange, desilicizers (lime softening).

> **Model implication:** cap SI_silica at **0.08 (SR 1.2)** for a standard programme, **0.40 (SR 2.5)** only with a named polymerisation inhibitor. Combined with §3.2 (evaluate silica at the *coldest* point, not skin), this is the most likely place our current model is optimistic.

---

## 6. Water activity and vapour-pressure depression

### 6.1 Primary source `[C]`

Sharqawy, M.H., Lienhard V, J.H., Zubair, S.M. (2010), *Thermophysical properties of seawater: a review of existing correlations and data*, **Desalination and Water Treatment 16, 354–380**.
Open-access PDF: https://web.mit.edu/lienhard/www/Thermophysical_properties_of_seawater-DWT-16-354-2010.pdf
MIT DSpace: https://dspace.mit.edu/handle/1721.1/69157

Notation: `S` = salinity in g/kg (or kg/kg where noted), `Sᴘ` practical salinity, `t` in °C, `T` in K.

### 6.2 The equations, transcribed `[C]`

**Eq. (29) — Raoult's-law approximation** (simplest usable form, `S` in g/kg):

```
p_v,w / p_v,sw  =  1 + 0.57357 × ( S / (1000 − S) )
```

**Eq. (30) — Robinson (1954)**, from measurements on natural and synthetic seawater:

```
(p_v,w − p_v,sw) / p_v,w  =  9.206×10⁻⁴ · Cl  +  2.360×10⁻⁶ · Cl²
```
Validity: p_v,w = 3167.2 Pa at 25 °C; t = 25 °C; 10 < Cl < 22 g/kg chlorinity. Accuracy ±0.2%.

**Eq. (31) — Emerson & Jamieson**:
```
log₁₀( p_v,sw / p_v,w )  =  −2.1609×10⁻⁴ · Sᴘ  −  3.5012×10⁻⁷ · Sᴘ²
```
Validity: 100 < t < 180 °C; 35 < Sᴘ < 170 g/kg. Accuracy ±0.07%.

**Eq. (32) — Weiss & Price** (recommended for 0–40 °C, i.e. **our range**):
```
ln p_v,sw = 24.4543 − 67.4509 (100/T) − 4.8489 ln(T/100) − 5.44×10⁻⁴ · Sᴘ
```
Validity: p_v,sw in atm; 273 < T < 313 K; 0 < Sᴘ < 40 g/kg. **Accuracy ±0.015%** — the tightest available.

**Eq. (33) — Millero**:
```
p_v,sw = p_v,w + A·Sᴘ + B·Sᴘ^1.5
A = −2.3311×10⁻³ − 1.4799×10⁻⁴ t − 7.520×10⁻⁶ t² − 5.5185×10⁻⁸ t³
B = −1.1320×10⁻⁵ − 8.7086×10⁻⁶ t + 7.4936×10⁻⁷ t² − 2.6327×10⁻⁸ t³
```
Validity: mm Hg; 0 < t < 40 °C; 0 < Sᴘ < 40 g/kg. Accuracy ±0.02%.

**Eq. (36) — boiling point elevation, Sharqawy's own best fit** (`S` in kg/kg, BPE in K):
```
BPE = A·S² + B·S
A = −4.584×10⁻⁴ t² + 2.823×10⁻¹ t + 17.95
B =  1.536×10⁻⁴ t² + 5.267×10⁻² t + 6.56
```
Validity: 0 < t < 200 °C; 0 < S < 0.12 kg/kg. Accuracy ±0.018 K. (Max BPE 3.6 K at 200 °C, 120 g/kg.)

**Eq. (49) — osmotic coefficient, Sharqawy's own best fit** (`t` in °C, `S` in kg/kg):
```
φ = a₁ + a₂t + a₃t² + a₄t⁴ + a₅S + a₆St + a₇St³ + a₈S² + a₉S²t + a₁₀S²t²

a₁ =  8.9453×10⁻¹    a₂ =  4.1561×10⁻⁴    a₃ = −4.6262×10⁻⁶    a₄ =  2.2211×10⁻¹¹
a₅ = −1.1445×10⁻¹    a₆ = −1.4783×10⁻³    a₇ = −1.3526×10⁻⁸    a₈ =  7.0132
a₉ =  5.696×10⁻²     a₁₀= −2.8624×10⁻⁴
```
Validity: 0 < t < 200 °C; 10 < S < 120 g/kg. Accuracy ±1.4% vs Bromley et al. Recommended by the authors over IAPWS-2008, whose osmotic coefficient is only valid to 25 °C.

**Eq. (47) — Millero, low-salinity alternative**: `φ = 0.90799 − 0.07221 I + 0.11904 I² − 0.0383 I³ − 0.00092 I⁴`, with `I = 19.915 Sᴘ / (1 − 1.00487 Sᴘ)`. Validity t = 25 °C, 0.016 ≤ Sᴘ ≤ 0.04 kg/kg, accuracy ±0.1%.

**Linking φ to water activity `[A]`** (standard thermodynamics, not from Sharqawy):
```
a_w = exp( − φ · ν · m · M_w )        M_w = 0.018015 kg/mol
```
where `ν·m` is total molality of dissolved species. Then `p_v = a_w · p_sat(T)`.

### 6.3 Does our 0.485% at 15,000 mg/L hold up? `[A]` — yes, remarkably well

Working at t = 30 °C, S = 15 g/kg:

| Route | Result |
|---|---|
| Eq. (29), Raoult, seawater composition | depression **0.866%** |
| Eq. (49) → a_w, seawater composition (φ = 0.9024, m = 0.485 mol/kg) | depression **0.785%** |
| Same, but **TSE composition** (Σ ion molality 0.3806 mol/kg — 21.5% fewer particles per gram than seawater, because SO₄ (96) and Ca (40) are heavier than Cl (35.5) and Na (23)) | depression **0.617%** |
| TSE composition **with ion pairing** (CaSO₄°, MgSO₄°, CaHCO₃⁺ removing ~20% of free particles) | depression **0.494%** |

**Our model's 0.485% falls essentially exactly on the ion-paired TSE calculation.** The apparent discrepancy against the raw seawater correlation (0.785–0.866%) is fully explained by composition — and the fact that our number lands where independent thermodynamics says it should is meaningful validation of the water-activity module.

### 6.4 The one genuine caution — evaporation ≠ vapour pressure `[A]`

**This is the most important caveat in the document.** Evaporation is driven by a **difference** of vapour pressures, so a small fractional reduction in `p_sat` becomes a larger fractional reduction in the driving force:

```
E ∝ ( a_w · p_sat(T_w) − p_v,air )
```

At T_w = 30 °C (p_sat = 4.246 kPa), with a_w depression of 0.485%:

| Ambient air vapour pressure | Driving force, clean → saline | **Reduction in evaporation** |
|---|---|---|
| 1.7 kPa (dry) | 2.546 → 2.525 kPa | **0.81%** |
| 2.5 kPa (moderate) | 1.746 → 1.725 kPa | **1.18%** |
| 3.0 kPa (humid Gulf summer) | 1.246 → 1.225 kPa | **1.65%** |

So the **evaporation** reduction is **1.7x to 3.4x larger** than the 0.485% vapour-pressure depression, and the amplification is worst in exactly the humid Gulf coastal conditions we are targeting.

> **This does not overturn the conclusion** — 0.8–1.7% is still small, and still plausibly at or below plant instrumentation noise for makeup-flow metering. But the model must not report 0.485% as "the effect on evaporation". It should report ~0.5% as the vapour-pressure effect and ~0.8–1.7% as the evaporation effect, humidity-dependent. Claiming the smaller number for the larger quantity is the kind of thing a technical reviewer will find.

### 6.5 Salinity effects on cooling-tower performance `[C]`/`[UNVERIFIED]`

- Sharqawy et al. give the complete property set needed to re-run a Merkel/Poppe tower model at salinity: density, specific heat, thermal conductivity, viscosity, surface tension, vapour pressure, BPE, latent heat, enthalpy, entropy, osmotic coefficient. This is the right foundation for a seawater-tower correction `[C]`.
- Surface tension **increases** with salinity — max 1.5% at 40 °C and 40 g/kg `[C]`. Relevant to droplet/film behaviour and drift, not just thermodynamics.
- For seawater, *"no formulae appear to be available for the change of latent heat with salinity and temperature"* `[C]` — a genuine gap; treat latent heat as the pure-water value and say so.
- A dedicated published study quantifying makeup-water salinity effects on **cooling-tower thermal performance specifically** (as opposed to seawater property data): `[UNVERIFIED]`. We did not find one we could read. The nearest confirmed-to-exist item is *Cooling tower modeling based on machine learning approaches: Application to Zero Liquid Discharge in desalination processes* — https://www.sciencedirect.com/science/article/pii/S135943112400190X (paywalled; not read).

---

## 7. A second cooling-tower dataset for thermal validation

### 7.1 Primary recommendation `[C]`

Jamil, S.R., Shehzad, A., Usman, M., et al. (2026), *Data-driven prediction and thermodynamic performance assessment of industrial cooling towers using advanced machine learning algorithms*, **PLOS ONE**. DOI: 10.1371/journal.pone.0351944
https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0351944 — open access, CC-BY

- **Plant:** Head Baloki Power Plant, Pattoki, Pakistan — **induced-draft wet cooling tower** (industrial scale, not a lab rig).
- **243 operating samples**, Jan–Sep 2023, after filtering startup/shutdown/trip/sensor-fault conditions.
- **Crucially, it carries evaporation, blowdown *and* makeup** — which the brief specifically asked for and which most tower papers omit.

**Table 7.1 — Paper's Table 1, "Actual parameters of the whole year of Head Baloki Cooling Tower"** `[C]` with `[A]` on row alignment:

| Parameter | Symbol | Units | Max | Min | Average |
|---|---|---|---|---|---|
| Ambient air temperature | T_amb | °C | 32 | 14 | 26.44 |
| Relative humidity | φ_in | % | 92 | 35 | 60.62 |
| Pressure | P_amb | kPa | 100.30 | 96.99 | 98.27 |
| Inlet water temperature | T_in,w | °C | 41 | 32 | 36 |
| Outlet water temperature | T_out,w | °C | 37.85 | 24.28 | 31.28 |
| Wet-bulb temperature | T_wb | °C | 30.83 | 7.106 | 20.80 |
| Mass flow rate of water | ṁ_w | kg/s | 4722.22 | 4472.13 | 4597.18 |
| Air flow rate | ṁ_a | kg/s | 2773.04 | 2577.66 | 2675.35 |
| Blowdown loss | BL | kg/s | 18.41 | 0.6375 | — |
| Evaporation loss | EL | kg/s | 73.66 | 2.54 | — |
| Makeup water | ṁ_w | kg/s | 101.53 | 12.63 | — |

> ⚠️ **Alignment caveat `[A]`:** this table was recovered from the PDF by text extraction and the numeric column drifted relative to the row labels in the source layout. The first seven rows are self-consistent and confidently assigned. **The last three rows (blowdown/evaporation/makeup) should be verified against the published PDF before use.** Two independent sanity checks say the assignment is right: (i) an energy balance at ṁ_w = 4597 kg/s and range 4.7 K gives evaporation ≈ 37 kg/s, mid-range of the tabulated 2.54–73.66; (ii) makeup ≈ evaporation + blowdown (101.5 ≈ 73.7 + 18.4), and makeup/blowdown ≈ 5.5 cycles, an entirely plausible operating point.

**Also reported in the paper `[C]`:** best model R² 0.985, RMSE 1.25 kg/s. Raising humidity from 35% to 92% *"decreased the evaporation losses by about 55–70% and makeup water"* requirement. Evaporation losses rose 18.08%, 21.96% and 24.61% as inlet water temperature rose at 32, 35 and 41 °C respectively. Wet-bulb rose 86.18% at 14 °C ambient and 50.24% at 32 °C ambient over that humidity swing.

**Limitation `[C]`:** Data Availability reads *"All relevant data are within the manuscript."* There is **no external repository** — so you get the summary statistics and the parametric trends above, **not the 243 raw rows**. Excellent for validating aggregate behaviour and evaporation/makeup trends against humidity and inlet temperature; not a row-level regression target.

### 7.2 If row-level open data is essential `[C]`

Liu et al. (2026), *Cooling and heating season performance of an open counterflow heat-source tower heat pump system in high-humidity climates: An experimental and numerical study*, **PLOS ONE**. DOI: 10.1371/journal.pone.0337196

- **Data availability:** *"All relevant data are available from the figshare database"* — **https://doi.org/10.6084/m9.figshare.30467054** ✅ genuinely downloadable Excel files.
- S1 File: measured **and** calculated outlet solution temperature, air temperature, air humidity ratio, summer and winter.
- S3 File: typical operating conditions — air temperature, relative humidity, water temperature, capacity, COP.
- Field-tested open counterflow tower, **4200 × 6300 × 5400 mm**; summer 29 Jun 2023 (12:15–14:55) and winter 18 Dec 2023 (11:30–14:30); **20 data points per season**.
- **Caveat:** this is a **heat-source tower heat pump** circulating an antifreeze solution, not plain water, and it has no evaporation/makeup measurement. Use it for heat-and-mass-transfer model structure, not for water-balance validation.

### 7.3 Classical datasets — fully tabulated, universally used for Merkel validation `[C]` (existence confirmed; originals not retrieved)

These are the canonical validation sets, all with water and air mass flowrates, inlet/outlet water temperatures, inlet air dry- and wet-bulb, and mass transfer coefficient **fully reported**:

| Dataset | Description |
|---|---|
| **London, Mason & Boelter (1940)** | Induced-draft counterflow tower, 1.75 m packed height, staggered streamlined redwood decks. **60 experimental runs.** |
| **Hutchison & Spivey (1942)** | Three forced-draft counterflow towers. **34 experimental runs.** |
| **Simpson & Sherwood (1946)** | Mechanical-draft counterflow; the classic Merkel demonstration case. |

Confirmed via Klimanek et al., *Modeling and simulation of counterflow wet-cooling towers and the accurate calculation and correlation of mass transfer coefficients for thermal performance prediction*, Int. J. Refrigeration — https://www.sciencedirect.com/science/article/abs/pii/S0140700716303474, which describes each as *"fully reported"*. `[UNVERIFIED]` as to the actual numeric tables — we did not obtain the original 1940s papers. If you need row-level data with no paywall risk, these are worth a library request; they are out of copyright concern for numerical facts.

### 7.4 Recommendation

Use **§7.1 (Head Baloki)** as the headline independent validation source — it is open access, industrial scale, recent, and uniquely carries evaporation/blowdown/makeup. Pair it with **§7.3 (London 1940)** if a reviewer wants row-level thermal validation. Note explicitly in the submission that Zenodo 10806201 remains the row-level primary and Head Baloki is the independent cross-check.

---

## 8. Verdicts on the three model findings

### Finding 1 — Skin-temperature evaluation lowers the safe cycles limit by ~15.6%
**Mechanism: SUPPORTED. Magnitude: LIKELY OVERSTATED ~2x. Blanket application: REFUTED.**

- ✅ The mechanism is textbook. Berce et al. (2021): higher surface temperature causes *more* fouling with inversely-soluble salts. Veolia Ch. 25: scale-formers *"supersaturate in the higher-temperature water adjacent to the heat transfer surface"*. Evaluating calcite at the skin rather than the bulk is unambiguously the right call.
- ⚠️ **+8 K is the corner of the envelope, not the typical case.** From Veolia's published heat-flux range (15.8–47.3 kW/m²) and Dittus–Boelter, ΔT spans **1.6–8.7 K**; a typical design point (2 m/s, ~31 kW/m²) gives **3.8 K** (§3.3). At 3.8 K the cycles penalty is roughly **7–8%**, not 15.6%. Still material — the finding survives — but the headline number should be presented as a band, not a point.
- ❌ **The offset has the wrong sign for silica.** Amorphous silica has *normal* solubility (Demadis 2003), so it is least soluble at the **coldest** point. Applying +8 K to silica makes the model optimistic about the species with the weakest inhibitor (SR limit 1.2). Gypsum is near-neutral in the 30–45 °C window because its solubility peaks at ~35–40 °C. **Per-mineral signs are required.**
- ⚠️ **Internal consistency check:** findings 1 and 2 are in tension. If gypsum binds at high cycles (finding 2), and the skin correction is near-neutral for gypsum (§3.2), then the skin correction should barely move the limit — unless the 15.6% was computed in a regime where calcite still binds. **Please confirm which mineral is binding in the case that produced 15.6%.** This is the question a technical reviewer is most likely to ask.

### Finding 2 — Gypsum binds at high cycles, and LSI cannot represent it
**STRONGLY SUPPORTED — the most defensible of the three.**

- ✅ **LSI cannot represent gypsum, definitionally.** The LSI is derived solely from `{Ca}{CO₃}/Ksp_CaCO₃` (IWC-11-77 Eq. 1, Table 2). There is no sulfate term. This is not an accuracy limitation; it is a structural one.
- ✅ **The acid-feed trap is documented.** IWC-11-77 states that lowering the pH control point to suppress calcite *"increase[s] the sulfate based scale potential of the water."* That is our finding, in the literature, from 2011.
- ✅ **Ion pairing matters most in exactly this water.** IWC-11-77 shows two waters of identical ionic strength differing only in sulfate vs chloride get the same LSI but materially different true calcite saturation — and our TSE has SO₄ 300 mg/L.
- ✅ **The regional case is strong:** Gulf seawater is sulfate-enriched (~4922 mg/L at Half Moon Bay vs ~2700 global); Aramco groundwater carries SO₄ 558 mg/L; our TSE carries 300 mg/L.
- ✅ **Analogue precedent:** San Joaquin agricultural drainage is gypsum-limited for reuse.
- ⚠️ **But note the competitor:** amorphous silica may bind *before* gypsum. At 15 mg/L makeup silica, Demadis's pH>7.5 limit of 100 ppm SiO₂ binds at **6.7 cycles** (§4.2). If the tower runs alkaline, silica — not gypsum — could be the true constraint. **Worth an explicit check in the model.**
- 📌 No paper was found naming gypsum as the binding constraint for *Gulf TSE cooling makeup specifically*. This makes the claim **novel rather than unsupported** — frame it that way in the application; it is a strength, not a gap, provided the mechanism citations above are attached.

### Finding 3 — Water activity depresses evaporation, but the effect is small (0.485%)
**NUMBER SUPPORTED. CONCLUSION SUPPORTED. LABEL NEEDS CORRECTING.**

- ✅ **0.485% reproduces almost exactly** from Sharqawy Eq. (49) osmotic coefficients plus TSE composition and ion pairing: independent calculation gives **0.494%** (§6.3). Three-significant-figure agreement from a completely independent route is strong validation of the module.
- ✅ **The "small" conclusion holds.** Even the most pessimistic route (seawater-composition Raoult, 0.87%) is below plant instrumentation noise for makeup metering.
- ⚠️ **But 0.485% is the vapour-pressure depression, not the evaporation reduction.** Because evaporation is driven by a *difference*, the effect on evaporation is **0.81–1.65%** depending on ambient humidity — 1.7x to 3.4x larger, and worst in humid Gulf coastal conditions (§6.4). Report both numbers, correctly labelled.
- 📌 **One place it is not negligible:** the amorphous silica saturation expression carries water activity **squared** (IWC-11-77 Table 2), so at 15,000 mg/L silica SI rises ~1% from a_w alone. Small, but it couples the water-activity module to the scaling module.

---

## 9. Recommended model changes (ranked by impact)

1. **Replace the adjusted chloride with the published 528 mg/L** (§1.1). Removes an assumption from the critical path at zero cost. The analysis is charge-balanced as published at −1.58%.
2. **Apply the skin-temperature offset per mineral with the correct sign** (§3.2). Calcite → skin; gypsum → near-neutral; **amorphous silica and barite → coldest point**. Currently the model is optimistic on silica.
3. **Report the cycles limit as a band over ΔT = 3–9 K**, computed as `q″/h_i`, rather than a point estimate at +8 K (§3.3).
4. **Add an explicit silica constraint** using Demadis's limits — SiO₂ < 100 ppm at pH > 7.5, < 200 ppm at pH < 7.5, plus Mg × SiO₂ < 20,000 / 40,000 (§4.2). Silica may bind before gypsum at ~6.7 cycles.
5. **Expose SI_gypsum as configurable, default 0.3, characterised range 0.40–0.60** cited to IWC-11-77 Table 7 (§5.2). Largest single upside to claimed water savings.
6. **Separate "vapour-pressure depression" from "evaporation reduction"** in all outputs, and make the latter humidity-dependent (§6.4).
7. **Document the ionic-strength ladder** (§2.3) in the submission — `I = 0.030 × N` — as the quantitative justification for choosing ion association over LSI, and for *not* needing Pitzer below ~16.5 cycles.
8. Optionally raise SI_calcite from 2.0 to 2.15 (SR 140) to match normal phosphonate practice (§5.2).

---

## 10. Sources

**Read in full and quoted**

1. Ferguson, R.J. (2011). *Mineral Scale Prediction and Control at Extreme TDS.* Paper No. IWC-11-77, International Water Conference. French Creek Software. — https://www.frenchcreeksoftware.com/iwc2011/iwc-11-77final.pdf `[C]` — §2, §4.1, §5.1
2. Sharqawy, M.H., Lienhard V, J.H., Zubair, S.M. (2010). *Thermophysical properties of seawater: a review of existing correlations and data.* Desalination and Water Treatment **16**, 354–380. — https://web.mit.edu/lienhard/www/Thermophysical_properties_of_seawater-DWT-16-354-2010.pdf `[C]` — §6
3. de Moel, P.J., van der Helm, A.W.C., van Rijn, M., van Dijk, J.C., van der Meer, W.G.J. (2013). *Assessment of calculation methods for calcium carbonate saturation in drinking water for DIN 38404-10 compliance.* Drinking Water Engineering and Science **6**, 115–124. doi:10.5194/dwes-6-115-2013 — https://dwes.copernicus.org/articles/6/115/2013/dwes-6-115-2013.pdf `[C]` — §2.2
4. Berce, J., Zupančič, M., Može, M., Golobič, I. (2021). *A Review of Crystallization Fouling in Heat Exchangers.* Processes **9**(11), 1356. — https://psecommunity.org/wp-content/plugins/wpor/includes/file/2302/LAPSE-2023.5350-1v1.pdf `[C]` — §3.1
5. Demadis, K.D. (2003). *Water Treatment's "Gordian Knot".* Chemical Processing, May 2003, p. 29. — https://www.chemistry.uoc.gr/demadis/pdfs/3-Gordian%20knot-Silica.pdf `[C]` — §4.2, §5.3
6. Yousefpour, A., et al. (2026). *Assessment of Water Chemistry in the Hybrid Cooling System of a Thermal Power Plant Using ICP-MS Analysis and Comparison with EPRI Guidelines.* Eurasian J. Chem. Med. Pet. Res. **6**(1), 129–139. doi:10.5281/zenodo.21924824 — https://zenodo.org/records/21924824 `[C]` CC-BY-4.0 — §1.3
7. Jamil, S.R., Shehzad, A., Usman, M., et al. (2026). *Data-driven prediction and thermodynamic performance assessment of industrial cooling towers using advanced machine learning algorithms.* PLOS ONE. doi:10.1371/journal.pone.0351944 — https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0351944 `[C]` — §7.1
8. *Use of Treated Sewage Effluent as Cooling Tower Makeup Water — A Pilot Study.* — https://aclima.eus/en/noticia/use-of-treated-sewage-effluent-as-cooling-tower-makeup-water-a-pilot-study/ `[C]` — §1.1, §1.2
9. Veolia Water Technologies. *Water Handbook, Ch. 25 — Deposit and Scale Control, Cooling System.* — https://www.watertechnologies.com/handbook/chapter-25-deposit-and-scale-control-cooling-system `[C]` — §3.1, §4.1
10. Veolia Water Technologies. *Water Handbook, Ch. 23 — Cooling Water Systems, Heat Transfer.* — https://www.watertechnologies.com/handbook/chapter-23-cooling-water-systems-heat-transfer `[C]` — §3.3 (heat flux 5,000–15,000 Btu/ft²/hr)
11. Veolia Water Technologies. *Water Handbook, Ch. 31 — Open Recirculating Cooling Systems.* — https://www.watertechnologies.com/handbook/chapter-31-open-recirculating-cooling-systems `[C]` — programme calcium ranges 75–1200 ppm as CaCO₃; conductivity >10,000 µmho problematic
12. Miyakawa, H., et al. (2021). *Reliable Seawater RO Operation with High Water Recovery and No-Chlorine/No-SBS Dosing in Arabian Gulf, Saudi Arabia.* Membranes **11**(2), 141. doi:10.3390/membranes11020141 — https://pmc.ncbi.nlm.nih.gov/articles/PMC7923200/ `[C]` — §1.5
13. Liu, et al. (2026). *Cooling and heating season performance of an open counterflow heat-source tower heat pump system in high-humidity climates.* PLOS ONE. doi:10.1371/journal.pone.0337196; data at doi:10.6084/m9.figshare.30467054 `[C]` — §7.2
14. ChemTreat. *Considerations for Complex Industrial Cooling Water Monitoring and Treatment.* — https://www.chemtreat.com/resources/technical-publications/considerations-for-complex-industrial-cooling-water-monitoring-and-treatment/ `[C]` — skin temperature qualitative only

**Confirmed to exist, abstract/metadata read only**

15. AL-Bander, et al. (2026). *Influence of Physicochemical Properties and Ionic Composition on Bacterial Abundance in Treated Wastewater and Post-Irrigation Agricultural Drainage Water: A Case Study from Al-Ahsa, Saudi Arabia.* Frontiers in Environmental Science **14**. doi:10.3389/fenvs.2026.1857130 — §1.4 (full table not retrieved)
16. *Experimental Data on Solubility of the Two Calcium Sulfates Gypsum and Anhydrite in Aqueous Solutions.* Data **7**(10), 140. — https://www.mdpi.com/2306-5729/7/10/140 — §4.1, open-access CaSO₄ solubility compilation
17. Bock, E. (1961). *On the Solubility of Anhydrous Calcium Sulphate and of Gypsum in Concentrated Solutions of Sodium Chloride at 25, 30, 40 and 50 °C.* Can. J. Chem. — https://cdnsciencepub.com/doi/10.1139/v61-228
18. Rahardianto, A., et al. *Calcium sulfate (gypsum) scaling in nanofiltration of agricultural drainage water.* — https://www.sciencedirect.com/science/article/abs/pii/S037673880200128X
19. Klimanek, A., et al. *Modeling and simulation of counterflow wet-cooling towers and the accurate calculation and correlation of mass transfer coefficients for thermal performance prediction.* Int. J. Refrigeration. — https://www.sciencedirect.com/science/article/abs/pii/S0140700716303474 — §7.3
20. *Fouling Characteristics of Water−CaSO₄ Solution under Surface Crystallization and Bulk Precipitation.* Int. J. Heat Mass Transfer. — https://www.sciencedirect.com/science/article/abs/pii/S0017931021009170
21. *Parametric study of calcium sulfate crystallization fouling in cross-flow heat exchanger using response surface methodology.* Heat and Mass Transfer. — https://link.springer.com/article/10.1007/s00231-023-03368-6
22. Parkhurst, D.L., Appelo, C.A.J. (2013). *Description of Input and Examples for PHREEQC Version 3.* USGS. — https://water.usgs.gov/water-resources/software/PHREEQC/

**Cited within IWC-11-77 (secondary; not independently retrieved)**

23. Langelier, W.F. (1936). *The Analytical Control of Anti-Corrosion Water Treatment.* JAWWA **28**(10), 1500–1521.
24. Stiff, H.A. Jr., Davis, L.E. (1952). *A Method for Predicting the Tendency of Oil Field Water to Deposit Calcium Carbonate.* Pet. Trans. AIME **195**, 213.
25. Ferguson, R.J. (1992). *Computerized Ion Association Model Profiles Complete Range of Cooling Water Parameters.* International Water Conference.
26. Tomson, M.B., Fu, G., Watson, M.A., Kan, A.T. (2002). *Mechanisms of Mineral Scale Inhibition.* SPE Oilfield Scale Symposium, Aberdeen.
27. Ferguson, R.J. (2004). *Water Treatment Rules of Thumb: Fact or Myth.* Association of Water Technologies. — source of IWC-11-77 Table 7 "stressed" limits
28. Rossum, J.R., Merrill, D.T. (1983). *An Evaluation of the Calcium Carbonate Saturation Indexes.* JAWWA **75**, 95–100.

**Sought and NOT obtained — do not cite without retrieving**

- MDPI *Water* **17**(5), 709 (2025), *Analyzing Riyadh Treated Wastewater Parameters for Irrigation Suitability Through Multivariate Statistical Analysis and Water Quality Indices* — https://www.mdpi.com/2073-4441/17/5/709 — **HTTP 403 to automated fetch; strongly recommended manual download.** Snippet confirms it tabulates the full major-ion suite with TDS 1115.02–1435.39 mg/L.
- *Reuse of Treated Sewage Effluent (TSE) in Qatar* — https://www.sciencedirect.com/science/article/abs/pii/S2214714416301866 — paywalled
- A primary, citable full ionic analysis of Arabian Gulf seawater including SO₄ 4922 mg/L — traced only to a search snippet
- Any published study quantifying makeup-water **salinity** effects on **cooling-tower thermal performance** specifically
- Original numeric tables of London et al. (1940), Hutchison & Spivey (1942), Simpson & Sherwood (1946)
- A canonical published wall-to-bulk ΔT for water-cooled condensers — **no such rule of thumb appears to exist; it must be derived as in §3.3**
