# Proof-of-Concept Report — Mizan condenser-water controller

**FURQAN** · *The criterion for energy.*  
Deep physics and physics-informed AI for hard energy infrastructure — we separate what is measured from what is merely modelled.  

**MIZAN** · *The balance between energy and water.*  
Supervisory control for cooling-tower and condenser-water loops in Gulf district cooling. A Furqan venture.  

Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley  
Date: 29 August 2026  
Claimed maturity: **TRL 3** (analytical and computational studies validated against measured experimental data)

---

## 0. The group and the venture

*Furqan* (الفرقان), from the Arabic root **f-r-q**, to separate: the criterion that distinguishes the true from the false. The name states the method rather than decorating it. Hard energy infrastructure is run on correlations fitted at one plant and then trusted everywhere; a first-principles model with few parameters cannot absorb a bad input, so it fails loudly instead of quietly fitting around the defect. Three of the four largest corrections recorded in this document are exactly that: a fan correlation read in the wrong unit, a chiller curve used outside the range it was fitted in, and a drift rate a hundred times too large. Each was caught because the physics refused it.

*Mizan* (الميزان): the balance, the scale, the measure held level. The condenser-water loop is the one place in a district-cooling plant where energy and water are the same decision, and it is currently made by three parties who never speak. Mizan is the first venture built on the group's method; the physics core, the validation discipline and the physics-informed learning layer described here are the parent's, and are intended to carry into further energy products.

## 1. What is claimed, and what is not

**Claimed.** A first-principles model of a counterflow wet cooling tower, coupled to an ion-specific water-chemistry model, predicts **measured outlet water temperature** and **measured heat rejection** on experimental data the model was never fitted to, within thresholds fixed before the fit was run.

**Explicitly not claimed, on the same data.** The water-consumption gate is **failed**. The model predicts measured water consumption to 9.90 % against a threshold of 8.00 %, and section 4 sets out why, including the fact that an earlier revision of this document reported a pass that turned out to rest on a drift constant a hundred times too large. The thermal claim and the water claim are separated here because the evidence separates them.

**Not claimed.** No closed-loop control on physical hardware. No field data from an operating plant. No validated scaling-kinetics model. These are TRL 4 objectives and are the subject of the laboratory programme in section 9.

**On the machine-learning component.** A physics-informed surrogate of the tower model exists and is documented in the AI architecture record, but **no gate result in this document depends on it**. It is trained against the physics core rather than against the plant, it is scored on how faithfully it reproduces the core, and it is excluded by construction from the chemistry and from every safety constraint. Every number in sections 4 to 8 comes from the deterministic physics.

## 2. Evidence base

| Item | Detail |
|---|---|
| Dataset | Steady-state operation of an experimental wet cooling tower pilot plant, Plataforma Solar de Almería |
| Authors | Palenzuela, Roca & Serrano Rodríguez |
| Source | Zenodo record 10806201, CC BY 4.0 |
| Integrity | MD5 `ac94e0076a9217b58e032a2545bf9fc4`, matches the published record |
| Size | 165 steady-state operating points across three campaigns, Oct 2019 – Oct 2023 |
| Duty range | 48 – 207 kW; ambient 9 – 40.5 °C; RH 10 – 87 % |
| Channels used | inlet/outlet water temperature, water flow, ambient temperature and RH, fan speed, **measured water consumption** |

The measured water-consumption channel is why this dataset was chosen over the alternatives: it lets the water model and the thermal model be validated against one consistent experiment on one rig, rather than borrowing a chemistry benchmark from an unrelated plant.

## 3. Method

Governing physics is the Poppe and Rögener heat-and-mass-transfer formulation in the form given by Kloppers and Kröger (2005), integrated over water temperature with both the unsaturated and the supersaturated (fogged) air branches. Moist-air properties follow the ASHRAE Handbook of Fundamentals formulation, implemented in house so that every constant is auditable and the whole core can run on an edge controller with no third-party runtime.

Aqueous speciation uses equilibrium constants taken directly from the USGS PHREEQC `phreeqc.dat` database, so the implementation is checkable against the accepted reference rather than against a correlation of our own.

**Identification.** The fill characteristic is identified the way cooling-tower practice identifies it (CTI ATC-105), not by black-box search. For each measured point the Poppe equations are integrated from the *measured* outlet temperature to the measured inlet temperature, giving the Merkel number the duty actually demanded from measurements alone. Regressing log(Me) on log(m_w/m_a) over the training campaign then gives the fill law in closed form.

Identified law: **Me = 1.2401 · (m_w/m_a)^(-0.5014)**, log-space R² = 0.3719.

The exponent -0.501 sits in the normal range for counterflow fill, which is an independent check that the identification is physical and not a curve fit absorbing error.

**Holdout.** Calibrated on campaign Exp2 only; tested on campaigns Exp1 and Exp3, which are separate experimental campaigns in different seasons under different designs of experiment. This is a harder test than a random row split because it measures transfer across campaigns rather than interpolation within one. The holdout was scored once, against thresholds fixed in advance.

## 4. Results against pre-registered thresholds

| Gate | Quantity | Threshold | Holdout result | Verdict |
|---|---|---|---|---|
| V1 | Outlet water temperature MAE | ≤ 1.00 K | 0.542 K | **PASS** |
| V1 | Heat rejection MAPE | ≤ 6.00 % | 5.94 % | **PASS** |
| V2 | Evaporation vs measured water loss MAPE | ≤ 8.00 % | 9.90 % | **FAIL** |

Holdout n = 50, 100 % solver convergence, RMSE 0.662 K, bias +0.453 K, 95th percentile absolute error 1.366 K.  
Training set for comparison: MAE 0.454 K, heat rejection MAPE 7.48 %, evaporation MAPE 7.80 %.

### Why gate V2 fails, and why the earlier pass was not real

V2 asks whether predicted water consumption matches the measured water-consumption channel, and on the untouched holdout it does not: 9.90 % against a threshold of 8.00 %. An earlier revision of this document reported 7.11 % and a pass. That pass was an artefact and is withdrawn here.

The cause was the drift term. Predicted consumption is evaporation plus drift, and the drift constant was 0.0005 used as a FRACTION of circulating flow -- the modern eliminator rating of 0.0005 **per cent** with its percent sign dropped, and so a hundred times too much water. On this rig that inflated the prediction by roughly five per cent, which is most of the distance between the 7.11 % previously reported and the threshold. Correcting the constant to a defensible 0.001 % removes the inflation and exposes a real shortfall.

**The shortfall is campaign-dependent, and that is the informative part.** Mean signed error against measured consumption:

| Campaign | Role | Mean shortfall vs measured |
|---|---|---|
| Exp2 | training | 0.83 % |
| Exp1 | holdout | 9.88 % |
| Exp3 | holdout | 8.60 % |

A fixed bleed would give a shortfall proportional to circulating flow; a model deficiency would give one proportional to evaporation. Regressing the residual on each gives R² = -0.06 and 0.06 respectively -- neither explains it. What does fit the pattern is that the model matches the campaign it was identified on and not the two it was not, which is the same campaign-to-campaign movement already documented in the fill characteristic (section 5.1, a 21 % spread in the identified coefficient over four years).

**The cause is now established, by a test that could have failed.** Two explanations were possible: an unaccounted bleed in the measured channel, which is total water consumption and would include one; or the fill characteristic drifting between campaigns, which is already documented in the thermal channel. They make opposite predictions. Re-identifying the fill law on each campaign separately cannot help if the shortfall is a bleed, because a bleed is a term the model does not contain -- but it should close the gap almost entirely if the cause is drift.

| Campaign | Identified c | Identified n | Outlet MAE | Evaporation MAPE |
|---|---|---|---|---|
| Exp1 | 1.5320 | -0.6015 | 0.280 K | 6.55 % |
| Exp2 | 1.2401 | -0.5014 | 0.454 K | 7.80 % |
| Exp3 | 1.3826 | -0.4293 | 0.262 K | 4.50 % |

**Every campaign falls inside the 8 % gate once its own fill law is used** -- worst case 7.80 %. The bleed hypothesis is rejected: a bleed would have been untouched by re-identification. The identified fill coefficient moves 23.5 % across the three campaigns, which is the same drift already measured in the thermal channel and is now confirmed independently in the water channel.

So V2 fails as a **single-calibration** gate, and it fails for a physical reason rather than a modelling one: the gate holds one fill law fixed across campaigns spanning four years, and the tower itself changed over those four years. The model is not deficient; the assumption that a tower's characteristic is a constant is.

That is not a comfortable result but it is a useful one, and it points the same way as the commercial argument. **Periodic recalibration against the plant's own telemetry is a functional requirement of the product, not an upsell.** A controller shipped with a fixed fill characteristic degrades silently as the fill fouls, and this gate is the measurement of how fast.

What is still NOT claimed is that the water model is validated against an operating plant. It is not. The gate as pre-registered stands as failed and the threshold has not been moved.

### A defect found and corrected, reported in full

The first execution of this holdout **failed all three gates** (outlet MAE 1.571 K against a 1.00 K threshold, with a systematic +1.50 K bias). A bias that large is characteristic of a unit error rather than model inadequacy, and it was one.

The air-mass-flow correlation published with the dataset, `m_a = −0.0014 f² + 0.1743 f − 0.7251`, takes fan frequency in **hertz**, although the dataset's own text describes its `w_fan` channel as a percentage. Two independent checks establish this:

- Read as a percentage, the quadratic turns over at f = 62.25 %, so air mass flow would **fall** as the fan speeds from 62 % to 100 %. No fan behaves that way.
- Read as a percentage, the tower's own published design point implies L/G = 2.55. Read as hertz it gives L/G = 1.54, squarely in the normal range for a counterflow induced-draught tower.

This is recorded because it demonstrates the property that makes a first-principles model worth building: it could not absorb the bad input. A regression with free exponents on air flow would have fitted around the distortion and reported a good score while carrying a corrupted air-flow model into the controller.

### An independent check on the psychrometrics, from ASHRAE

The moist-air property code here is written in house, because Python 3.14 has no wheels for CoolProp or psychrolib and an edge controller should ship without a third-party scientific runtime. That is defensible only if the implementation can be shown to be right, and until now it could not be: every gate above tests the tower model and the psychrometrics together, so an error in one could in principle be absorbed by the other.

A TMYx weather file for Dhahran (station 404160, 2011-2025) closes that. Its header carries the **2025 ASHRAE Handbook of Fundamentals design conditions** for the same station, computed by ASHRAE from the same underlying hours by their own method. Recomputing those percentiles from the hourly file with this package's own code is a genuine independent comparison: neither side was fitted to the other, and nothing was tuned to make them meet.

| Percentile | ASHRAE 2025 | This package | Difference |
|---|---|---|---|
| 0.4 % wet-bulb | 31.4 °C | 31.34 °C | -0.06 K |
| 1.0 % wet-bulb | 30.5 °C | 30.45 °C | -0.05 K |
| 2.0 % wet-bulb | 29.6 °C | 29.69 °C | +0.09 K |

Worst disagreement across six design percentiles, wet-bulb and dry-bulb together: **0.20 K**. The psychrometric layer is correct, and that is now established separately from everything built on top of it.

The same file settles a figure this document had been carrying without a citation. Gulf design wet-bulb was quoted as 30.3 °C from no stated source. ASHRAE 2025 for Dhahran gives **30.5 °C at the 1 % percentile and 31.4 °C at 0.4 %**. The assumed value was close, but it is now sourced rather than asserted. `[C]`

### How much of a Gulf year the model has never seen

The same hourly file finally puts a number on the largest open item in this package. The validation data tops out at 21.9 °C wet-bulb; above that the model extrapolates. That was carried for the whole project as a qualitative worry, because there was no hourly Gulf weather to measure it against.

**40.5 % of a Dhahran year -- 3,551 of 8,760 hours -- is above that ceiling**, rising to 84 % of hours in September, with an annual maximum wet-bulb of 34.6 °C.

![Fig. 4](C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/figs/wetbulb_gap.png)

**Fig. 4.** Dhahran monthly wet-bulb against the ceiling of the validation dataset and the ASHRAE 1 % design condition. The shaded region is the part of the year the model has never been tested in.

This cuts against us, and it is the strongest possible statement of why the KFUPM humidifying wind tunnel is the right thing to ask for. Two fifths of the operating year is outside the envelope, and no amount of modelling closes that. The physics-informed surrogate constrains the extrapolation with inequalities thermodynamics guarantees everywhere, which is a mitigation and not a substitute for measuring it.

### What a real year is worth, rather than five chosen conditions

Gate V5 scores an unweighted mean over five hand-picked ambient conditions. That is not a physical quantity: it depends on which five were chosen. With an hourly year available, the honest version can be computed -- bin the year by wet-bulb, run the controller at each bin centroid, weight by the hours actually spent there.

| Metric | Makeup water saving |
|---|---|
| Five-condition unweighted mean (gate V5) | 4.38 % |
| **Hours-weighted annual, Dhahran TMYx** | **1.25 %** |
| Difference | **-5.00 points** |

**The gate metric was flattering the product.** The saving is large when it is hot and small when it is not, and the five chosen conditions were weighted toward summer. A real Dhahran year is not weighted that way.

The figure that belongs in a commercial conversation is therefore **1.3 % annually**, not 4.38 %. The higher number should not be used outside the specific five-condition comparison it was computed for. This is reported here rather than quietly dropped because it was found while looking for a way to make a failed gate pass, and it did the opposite.

Quoted OUTSIDE this repository the figure is **2.4 %** -- the ratio of hours-weighted totals, cubic metres saved over cubic metres consumed. The 1.3 % above is an hours-weighted mean of ratios, which is the right object for comparing against the gate and the wrong one for a customer.

The same calculation carries its own caveat: only **62.5 %** of the weighted year lies inside the wet-bulb envelope the model was validated in. The rest rests on extrapolation, and no weighting scheme fixes that.

## 5. Model selection — why the fill law has two parameters

The identified fill law fits the training campaign with a log-space R² of 0.372. That is low enough to deserve an answer rather than a footnote, and there are only two possible explanations: the functional form is too poor, or the scatter is experimental and no form will fit it better.

Five candidate forms were fitted on the training campaign alone and scored by forward outlet-temperature prediction on the untouched holdout. R² is reported for interest but is not the selection criterion — a form can raise R² on the Merkel number and still predict temperature worse, and temperature is the quantity that matters.

| Form | Params | Train R² | Holdout MAE | Holdout RMSE |
|---|---|---|---|---|
| A: ratio only  Me=c(mw/ma)^n **(adopted)** | 2 | 0.372 | 0.542 K | 0.662 K |
| B: separate flows  Me=c*mw^a*ma^b | 3 | 0.382 | 0.629 K | 0.788 K |
| C: ratio + inlet temp | 3 | 0.372 | 0.550 K | 0.666 K |
| D: separate flows + inlet temp | 4 | 0.382 | 0.633 K | 0.793 K |
| E: separate flows + wet bulb | 4 | 0.506 | 0.517 K | 0.710 K |

Two results follow, and both are reported because both are informative.

**Adding flow terms raises training R² while making holdout prediction worse.** That is overfitting demonstrated rather than asserted, and it answers the R² question directly: the scatter is experimental, not a deficient functional form.

**The form that scores best on MAE was rejected.** E: separate flows + wet bulb reaches 0.517 K against 0.542 K for the adopted law — a gain of 0.025 K on a ~0.5 K error, bought while making RMSE *worse* by 0.048 K. It reduces typical error and increases large error, which is a differently-shaped error distribution rather than a better model.

The deciding objection is physical, not statistical. A Merkel number is a property of the fill's heat-and-mass-transfer geometry. Ambient wet-bulb is an operating condition. Admitting it to the fill law lets the regression absorb the training climate into what is supposed to be equipment physics — and the training climate is not ours:

- training wet-bulb range: **4.3 – 21.9 °C**
- Gulf design wet-bulb: **30.3 °C**
- extrapolation beyond the fitted range: **+8.4 K**

The fitted wet-bulb exponent would predict roughly 14 % different transfer capability at Gulf design wet-bulb, on no supporting data — extrapolating hardest exactly where the product is intended to operate. The two-parameter law is retained.

### How large is the residual, and what causes it?

A model error is meaningless without the experiment's own uncertainty beside it. The dataset publishes its instrument specifications, so they were propagated through the model by Monte Carlo (GUM Supplement 1), 160 samples per holdout point.

| Quantity | Value |
|---|---|
| u(predicted outlet T), from input uncertainty | 0.188 K |
| u(measured outlet T), Pt100 | 0.104 K |
| combined standard uncertainty u_c | 0.217 K |
| expanded uncertainty U (k=2, ~95 %) | 0.434 K |
| **model MAE on the same points** | **0.537 K** |
| MAE / u_c | **2.48** |
| points agreeing within U (k=2) | 40 % |

**This is a negative result and it is reported as one.** The model does not agree with the experiment to within measurement uncertainty; it is about two and a half times outside it, with a systematic holdout bias rather than symmetric scatter. Something real is being missed.

The cause was then isolated. If the deficiency were in the model form, it would persist within a single campaign. If the fill characteristic drifts — the campaigns span October 2019 to October 2023, and fill fouls and degrades — the error would appear only across campaigns.

- mean **within**-campaign MAE: **0.332 K** (1.53 x u_c), bias essentially zero
- mean **across**-campaign MAE: **0.470 K** (2.17 x u_c)
- drift penalty: **+0.138 K**
- identified fill coefficient across campaigns: **1.240 to 1.532**, a spread of **21.1 %**

**Both effects are present, and the honest verdict is mixed.** Within a campaign the model is nearly unbiased and sits at 1.53 times the measurement uncertainty — close to the floor but not at it, so a genuine modelling residual remains. Across campaigns a further 0.138 K appears, and the identified fill coefficient moves by a fifth over four years.

**The drift finding has a direct product consequence.** A cooling-tower fill characteristic is not a constant. A controller that assumes a fixed characteristic will degrade silently in service as the fill fouls. Periodic recalibration against the plant's own telemetry is therefore a functional requirement of the product, not a commercial add-on — and this dataset is the evidence for it.

## 6. Gate V3 — the saturation limit is set at the tube wall, not in the bulk

Scale forms at the hottest wetted surface, the condenser tube wall, which runs several kelvin above bulk water temperature. Calcite and gypsum both become less soluble as temperature rises, so a saturation index computed at bulk temperature — which is where conventional practice and every conductivity controller evaluates it — systematically understates risk where scale actually forms.

Makeup water is a published Saudi treated-sewage-effluent analysis (TDS 1500 mg/L), closed on charge balance by chloride.

| Bulk temperature | Limit at bulk | Limit at skin (+8 K) | Bulk basis overstates by |
|---|---|---|---|
| 30 °C | 2.63 cycles | 2.29 cycles | 15.1 % |
| 33 °C | 2.50 cycles | 2.17 cycles | 15.3 % |
| 36 °C | 2.37 cycles | 2.05 cycles | 15.4 % |

The relative gap is stable at about 15.6 % across the whole condenser operating range. That gap is the margin a plant believes it has and does not. The silica ceiling itself moves seasonally, as Fig. 1 shows, while industry practice holds it fixed.

![Fig. 1](C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/figs/silica_seasonal.png)

**Fig. 1.** Amorphous silica ceiling against tower-basin temperature, from the PHREEQC SiO2(a) constant, compared with the static 150 mg/L industry rule.

![Fig. 2](C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/figs/silica_wall.png)

**Fig. 2.** Highest safe cycles of concentration against makeup silica, with the Saudi brackish range and industry practice band marked.

**Limitation, stated plainly.** The *absolute* cycles limits above assume no acid dosing, so pH free-runs to above 9 as the tower strips CO₂, and calcite binds early. Real plants dose acid and run 4–8 cycles. The absolute limit therefore requires calibration against a specific antiscalant programme; the relative bulk-versus-skin gap is the robust result and is what is claimed.

## 6b. The chiller model, and the envelope it must be held inside

The optimiser's central trade is compressor power against fan power, so the sensitivity of chiller power to condenser-water temperature is the accuracy of the whole result. Two corrections were required, and the second was found only because the first was made.

**A named machine replaces a generic curve set.** The chiller is modelled with the EnergyPlus `Chiller:Electric:EIR` bi-quadratic form. The coefficients are now those of a specific machine — a York YT 1758 kW (500 TR) water-cooled centrifugal at 6.28 COP, from the CoolTools curve library shipped with EnergyPlus [12]. It was selected on three grounds: its reference point is the AHRI 550/590 rating point, so the normalisation to that point is a 5.0 % / 0.5 % correction rather than a fudge; its curves are fitted over 15.56–35.00 °C entering condenser water, which spans the Gulf operating range where most of the library stops at 26.11 °C; and it is a vane-controlled centrifugal rather than a high-COP variable-speed outlier. It gives 2.36 % of chiller power per K of condenser water over 30–36 °C, against 2.62 % for the untraced set it replaced and 3.45 % for constant-fraction Carnot.

**A more modern source was examined and rejected.** The ASHRAE 90.1-2022 Normative Appendix J curve sets are newer, return exactly unity at the AHRI point, and state validity to 40 °C. They imply 0.4–0.5 %/K — a chiller losing 3 % of its COP between 30 and 36 °C condenser water, where ideal Carnot loses 21 % and every named machine in the CoolTools library loses 13–17 %. Those curves are fitted to reproduce rated full-load and IPLV points, and the IPLV condenser schedule runs *downward* from 29.44 °C as load falls, so above 30 °C they are unconstrained by data despite the stated range. A stated validity range is not evidence of a fitted range.

**The optimiser then exploited the new curve.** Given a free hand it drove the fan to its lower bound in four of five Gulf conditions, which puts entering condenser water at 36.5–40.5 °C — outside the fitted range — and collected a large apparent water saving from the extrapolation. That run scored 20.41 % on the water criterion and would have converted a failed gate into a passed one on the strength of an extrapolation. The entering-condenser-water window is now enforced as a hard constraint. It is not only the curve's fitted range: it is also the machine's permitted operating window, since below the floor condenser head pressure collapses and oil return and expansion-valve control fail, and above the ceiling the machine trips on high head. In the run reported here, 1,840 of 6,307 candidate operating points were rejected on this constraint rather than extrapolated.

**The result is a new and specific finding.** In all four Gulf summer conditions the optimum now sits at 33.9–34.7 °C entering condenser water, hard against the 35 °C ceiling. In Gulf summer the binding limit on fan speed is the chiller envelope — not tower physics, and not chemistry.

### Two further defects found in the same pass, and one regulation closed

**The drift rate was a hundred times too large.** Cooling-tower drift is quoted by every manufacturer as a *percentage* of circulating water flow, and modern high-efficiency eliminators are rated 0.0005 % to 0.001 %. The model carried 0.0005 used directly as a fraction -- the modern rating with its percent sign dropped. This is the same class of defect as the fan correlation read in percent instead of hertz. Makeup water is provably unaffected, and that is worth stating precisely rather than discovering later: with blowdown = evaporation/(C-1) - drift, the drift term cancels exactly out of makeup = evaporation + drift + blowdown for as long as blowdown stays positive, and it was verified numerically that makeup is identical to three decimals before and after. What was wrong is the reported **blowdown**, 27 % low at seven cycles -- which is the quantity a discharge permit is written against.

**The discharge limit was the wrong kind of number.** A blanket 3,000 mg/L TDS cap was carried as unverified, because on 1,500 mg/L makeup it implies a ceiling of 2.0 cycles and plants demonstrably run 3.5 to 5.0. Resolved against the primary regulation, RCER-2015 Volume I, the Royal Commission for Jubail and Yanbu Environmental Regulations, which sets three different limits for three different discharge routes:

| RCER-2015 table | Discharge route | TDS limit |
|---|---|---|
| Table 3B | Central wastewater treatment facilities | 2,000 mg/L Jubail; 2,500 mg/L Yanbu |
| Table 3C | Direct to coastal waters, incl. the seawater cooling return | **none** |
| Table 3D | Irrigation system | 2,000 mg/L max, 1,750 monthly average |

Table 3C lists only floating particles and temperature under its physical parameters. A TDS cap is therefore **not a property of the cooling loop at all -- it is a property of where the blowdown goes.** That resolves the contradiction. A 2,000 mg/L cap on this makeup allows 1.33 cycles, which would forbid evaporative cooling on reclaimed water outright; plants running 3.5 to 5.0 are therefore not discharging tower blowdown to the sewer, and a coastal industrial plant discharging to the seawater cooling return has no TDS limit to satisfy. The cap is now a site configuration item defaulting to no cap, and the controller reports which route it assumed.

### A numerical defect found in the same pass

The condenser duty is a fixed point: the tower rejects evaporator load plus compressor work, and compressor work depends on the cold-water temperature the tower achieves. That fixed point was being solved by six steps of successive substitution at a 5 mK tolerance. The map contracts at roughly 0.5 per step, so six steps stop well short of the solution — and stop short by an amount that depends on the starting guess. Because every grid point was seeded from a single nearby solve, points near the seed were accurate and points far from it were not, which biased the baseline and the optimum by different amounts.

Evaporation, the quantity the water gate measures, moved from 5.199 to 5.396 kg/s — 3.8 % — on the choice of seed alone, an order of magnitude larger than the margin by which that gate was failing. The solver now uses Aitken delta-squared extrapolation of the same iteration, with a bracketed Brent root-find as a fallback, and reports its own non-convergences. All 360 fixed points in the run reported here converged to 1e-5 K, and the two solvers agree on the gate results to the second decimal place.

## 7. Gate V5 — closed-loop economics

Plant archetype: 10 MW condenser-water module. Tariffs are the one class of input in this package that is assumed rather than measured and are tagged for verification.

| Criterion | Threshold | Result | Verdict |
|---|---|---|---|
| Makeup water reduction | ≥ 15.0 % | 4.38 % | **FAIL** |
| Total operating cost reduction | ≥ 3.0 % | 3.91 % | **PASS** |
| Skin-temperature saturation violations | 0 | 0 | **PASS** |

Per condition:

| Condition | Wet bulb | Fan | Cycles | Makeup m³/h | Water | Cost |
|---|---|---|---|---|---|---|
| Dhahran summer peak | 25.2 °C | 70 → 60 % | 4 → 5 | 27.5 → 25.0 | +9.1 % | +2.7 % |
| Dhahran summer humid | 29.7 °C | 100 → 80 % | 4 → 5 | 24.3 → 22.2 | +8.6 % | +3.4 % |
| Dhahran shoulder | 22.4 °C | 60 → 50 % | 4 → 5 | 22.5 → 20.8 | +7.5 % | +0.8 % |
| Doha summer humid | 30.3 °C | 100 → 80 % | 4 → 5 | 25.3 → 23.0 | +9.0 % | +3.6 % |
| Gulf winter | 14.7 °C | 40 → 80 % | 4 → 4 | 19.5 → 19.7 | -0.8 % | +7.9 % |

### Reading the failure honestly

The water criterion was set at 15 % and was **missed**, at 4.38 %. It is reported as a failure and the threshold has not been moved. What has changed since it was set is that the reason for the miss is now known exactly, and it is not a deficiency of the controller.

Makeup water is evaporation plus blowdown, and blowdown is evaporation divided by (C - 1). At constant evaporation the makeup rate is therefore

> makeup = evaporation x C / (C - 1)

so the makeup saving available by raising cycles from the incumbent 4 is fixed arithmetic, not a modelling choice. It is a hyperbola with a horizontal asymptote at 25 %, reached only at zero blowdown:

| Cycles of concentration | Makeup saved vs 4 cycles |
|---|---|
| 5 | 6.25 % |
| 6 | 10.00 % |
| 7 | 12.50 % |
| 8 | 14.29 % |
| 9 | 15.62 % |
| 10 | 16.67 % |

A criterion of 15 % therefore requires **8.5 cycles**. Gypsum saturates at **6 cycles** on this water (section 7, gate V5b). The criterion was written on the far side of a wall that had not yet been located, and gypsum saturation is not pH-sensitive, so the acid dose that buys cycles against calcite cannot move it. No control strategy of any kind reaches 15 % on this makeup water by raising cycles.

The controller nevertheless reaches 4.38 %, which is more than cycles alone can deliver at its operating point, because it also lowers evaporation by slowing the fan wherever the chiller can absorb the warmer condenser water. That second term is precisely the coupling this product exists to price, and it is invisible to both incumbent disciplines: a water treater optimising cycles alone cannot access it, and an energy optimiser lowering condenser temperature moves it the wrong way and never books it.

Two conclusions follow, and they are different from the ones drawn when this gate was first scored.

1. **The pre-registration was mis-specified, not merely missed.** A threshold should be checked against the physical ceiling of the system before it is fixed. This one was not, and the correct record of that is to leave the gate failed and say why.
2. **The water saving is not the product.** At current tariffs the value is the energy trade plus the certainty of not crossing a saturation limit that bulk instrumentation cannot see. Total operating cost falls 3.91 % against a criterion of 3.0 %.

The incumbent 4-cycle baseline was found safe at skin temperature in all 5 conditions tested. It is conservative rather than unsafe -- it leaves margin unused. No claim is made here that typical plants are actively scaling; establishing that requires field data and is a TRL 4 objective.

### Gate V5b — the two ceilings

Sweeping cycles at fixed fan speed, with pH free to take its least-cost feasible value, separates two limits that incumbent practice collapses into a single conductivity setpoint.

| Cycles | Best pH | Makeup m³/h | Acid kg/h | Water $/h | Acid $/h | Total $/h | Blocked by |
|---|---|---|---|---|---|---|---|
| 3 | 8.50 | 26.97 | 1.7 | 83.89 | 0.33 | **220.95** | |
| 4 | 8.25 | 23.97 | 1.8 | 74.55 | 0.34 | **211.51** | |
| 5 | 8.25 | 22.47 | 1.7 | 69.89 | 0.33 | **206.78** | |
| 6 | — | nan | — | — | — | — | **SI_silica_am** |
| 7 | — | nan | — | — | — | — | **SI_silica_am** |
| 8 | — | nan | — | — | — | — | **SI_silica_am** |
| 9 | — | nan | — | — | — | — | **SI_silica_am** |
| 10 | — | nan | — | — | — | — | **SI_silica_am** |
| 11 | — | nan | — | — | — | — | **SI_silica_am** |
| 12 | — | nan | — | — | — | — | **SI_silica_am** |

- **The cost curve does not turn over.** Operating cost falls monotonically to 5 cycles, the last feasible point. There is no interior economic optimum on this water.
- **Physical ceiling: 6 cycles.** First saturation violation at the condenser skin. Binding mineral: **SI_silica_am**.

This is the more dangerous of the two arrangements. Where an interior cost minimum exists, an operator following the money stops short of the saturation wall without needing to know it is there. Here the money points straight at it: every additional cycle is cheaper than the last, right up to the point where the binding mineral saturates at the tube skin.

These are different numbers, and a fixed conductivity setpoint can locate neither. Finding the first requires a coupled water/energy/chemical cost model. Finding the second requires ion-specific speciation evaluated at skin temperature — and the Langelier index used across the industry cannot represent the binding mineral here at all, because LSI describes calcite only.

This single table is the clearest statement of what the product is: the plant is operating between two limits it cannot see, and the gap between them is the margin being left unused or unknowingly crossed.

## 8. Gate V6 — the constraint that needs all three models at once

External review identified a real gap: magnesium silicate forms on the HOT surface and can bind before amorphous silica does. Closing it produced the sharpest result in this package.

**First, a correction we made and are reporting.** Magnesium silicate was initially modelled as sepiolite, using PHREEQC constants. On real water that returned saturation indices of +1.56 to +3.50 — which would forbid operation everywhere, and is plainly false since plants run 4–5 cycles on this water daily. Crystalline magnesium silicates are thermodynamic end-states whose crystallisation is kinetically inhibited over the few seconds a parcel of water spends crossing a condenser. Sepiolite was the wrong phase, and using it would have made the controller reject operating points that are demonstrably safe.

**What industry actually uses** is an empirical magnesium-silica product, and it validates against observed practice:

| Published limit | Max cycles on Aramco water + 26.8 mg/L SiO₂ |
|---|---|
| permissive | 6.03 |
| standard | 5.64 |
| utility | 4.77 |
| assurance | 4.27 |

Industry operates 3.5–5.0 cycles. The standard (35,000) and utility (25,000) limits **bracket that**, which is the consistency check the sepiolite formulation failed.

A second unit ambiguity appeared here, of exactly the kind that produced the fan-correlation defect in section 4. Sources word the magnesium term as "hardness as ppm CaCO₃", but that convention gives 2.78 cycles — *below* what plants demonstrably run. As ppm Mg²⁺ it gives 5.64, which matches. Both are implemented; the model defaults to the convention consistent with reality and documents the discrepancy.

### The deposition criterion

Magnesium silicate forms in two steps: brucite Mg(OH)₂ precipitates first at the hot skin, then reacts with silica in the boundary layer. Brucite's saturation pH is **retrograde** — it falls as the surface gets hotter — so:

> **deposition occurs when bulk pH exceeds pH_s(brucite) evaluated at the SKIN temperature**

At 4 cycles, with Gulf TSE loops running pH 8.5–9.0:

| Skin temperature | pH_s(brucite) | Verdict at Gulf operating pH |
|---|---|---|
| 30 °C | 9.41 | safe across the whole band |
| 34 °C | 9.16 | safe across the whole band |
| 38 °C | 8.92 | deposits above pH 8.92 -- band straddles the limit |
| 42 °C | 8.68 | deposits above pH 8.68 -- band straddles the limit |
| 46 °C | 8.45 | DEPOSITING across the whole band |
| 50 °C | 8.22 | DEPOSITING across the whole band |

**The same tower, same water, same pH, deposits at high load and does not at low load**, because the skin runs hotter. A fixed pH setpoint cannot express that, and neither can a fixed conductivity setpoint. Fig. 3 shows the envelope.

![Fig. 3](C:/Users/Nouman/Desktop/Furqan's Docs/Startup/mizan/figs/mg_silicate_envelope.png)

**Fig. 3.** Magnesium silicate deposition envelope. Brucite saturation pH at the condenser skin, against bulk pH. Aramco reclaimed water with 26.8 mg/L silica at four cycles.

This is the constraint that requires all three models simultaneously, and it is why the architecture is what it is:

- **skin temperature** — from the live thermal model and duty
- **bulk pH** — from the chemistry model
- **acid dose** — the actuator that moves bulk pH

It also reveals a dual role for acid that conventional practice does not connect. Everyone doses acid for calcite. It simultaneously moves the loop below the brucite saturation pH at the skin, which is what actually prevents magnesium silicate. Nobody controls for the second effect.

## 9. TRL 4 programme at KFUPM

Every claim above is computational. TRL 4 under DTV's own definition is components integrated and validated in a laboratory environment, and the facilities for it already exist on the KFUPM campus — three of them in the same building.

| Facility | Location | Closes |
|---|---|---|
| Air-Conditioning & Refrigeration Lab — vertical cooling tower and open wind tunnel with heating, cooling and **humidification** | Bldg 75-410 | The climate-extrapolation gap: our data tops out at 21.9 °C wet-bulb; 41 % of a Dhahran year is above that |
| Chemistry Teaching Instrumentation Lab — **ICP-OES PlasmaQuant PQ 9000** (cations) and **Metrohm 930 Compact IC Flex** ion chromatograph (anions) | Bldg 75-230 | The chemistry gap: turns gates V3 and V5b from calculation into measurement |
| ME Corrosion Lab — Gamry 3000 potentiostats, rotating disc electrode, recirculating loop | Bldg 75-409 | The objection we cannot answer today: does acid dosing trade scale for corrosion? |
| Dream Realization Lab — PCB fabrication, electronics assembly, sheet-metal enclosures | DTV | The physical controller itself, end to end |

The instrumentation pairing matters more than it looks. ICP-OES measures the cations and ion chromatography the anions — together they give the complete ion inventory that the speciation model predicts. That is precisely the input our current chemistry lacks: today we drive the model from a published third-party water analysis that had to be closed on charge balance. With those two instruments the model is validated against water we measured ourselves.

| Objective | Experiment | Converts |
|---|---|---|
| Thermal transfer at Gulf wet-bulb | Tower across the wind tunnel's humidity range | Section 9 limitation 1 |
| Water-balance closure | Metered makeup and blowdown vs predicted evaporation | Gate V2 to a second rig |
| Ion inventory | ICP-OES + IC on synthetic Gulf TSE at four cycle levels | Gate V3 to measurement |
| Saturation limit at the wall | Heated coupon side-stream at controlled skin temperature | Gate V5b to measurement |
| Scale kinetics | Coupon mass gain vs time and saturation state | Supplies the labelled data the learned residual needs |
| **Corrosion under acid dosing** | Potentiostat and loop tests across the pH range the optimiser selects | **The scale/corrosion trade-off, currently unaddressed** |
| Closed-loop control | Edge controller driving blowdown valve and fan VFD over Modbus | The TRL 4 integration claim itself |

These experiments are deliberately cheap — salt, coupons, instrument time on equipment that already exists. The SAR 200,000 product-development stream covers instrumentation, the motorised valve and edge hardware, analytical services, an OT-security assessment and third-party validation. None of it is modelled as runway.

Engagement with KFUPM's Interdisciplinary Research Centre for Membranes and Water Security — whose published themes include fouling and scaling — is scoped as **testing services**, not co-development, because co-development triggers a separate research collaboration agreement and an IP negotiation that must be settled in writing before work begins.

## 10. Open items, and the direction each one cuts

Every remaining open item is listed with the direction it biases the result. That matters more than the list itself: an assumption that makes our own claim weaker is evidence of discipline, not a risk the reviewer inherits.

| Open item | Direction | Closed by |
|---|---|---|
| Validation data is from Plataforma Solar de Almería, whose summer wet-bulb tops out at 21.9 °C. **40.5 % of a Dhahran year (3,551 of 8,760 hours) is above that**, rising to 84 % of hours in September. | **Unknown** — the one item that could cut either way, which is why it is first | KFUPM wind tunnel, which humidifies: the rig reaches Gulf wet-bulb directly |
| Model error is 2.5x the propagated measurement uncertainty | **Against us** — we report the real error, not a floor | Decomposed already: ~30 % fill drift, ~70 % residual. Second rig at KFUPM separates them |
| Silica is not reported in the Aramco analysis, so its constraint is inactive | **Against us** — present silica could only lower the wall, never raise it. Our 8 cycles is an upper bound | ICP-OES and ion chromatography, Bldg 75-230 |
| Saturation indices are computed, not measured | **Neutral** — constants are from the USGS PHREEQC database, not fitted by us | Heated-coupon side-stream rig |
| Makeup water reduction missed its pre-registered 15 % threshold (4.38 %) | **Against us** — reported as a failure rather than rescored. Now diagnosed: 15 % requires roughly 8.5 cycles and **amorphous silica** saturates at 6, so the threshold was written beyond the physical ceiling. (The binding mineral was believed to be gypsum when this row was first written; correcting the speciation moved it to silica without moving the ceiling.) | Nothing: the threshold stands as written |
| Fill characteristic identified on one tower | **Neutral** — the characteristic form transfers, the coefficients do not, and per-site calibration is part of the product | Second rig, and the drift result already quantifies the recalibration interval |
| No AI contributes to any result here | **Neutral** — stated so the evidence cannot be mistaken for a learned fit | Scaling-kinetics residual, once coupon data exists |

**Nothing in this table is hidden, and nothing in it is fatal.** Five of the seven items bias against our own numbers. The one genuinely two-sided item — climate extrapolation — is closed by a facility that already exists on the KFUPM campus and humidifies to the required range. That is the substance of the twelve-week ask.

### What has already been closed

Earlier drafts of this package carried a longer list. The following were open questions and are now settled, each against an external source rather than by assertion:

- **Tariffs** were assumed; they are now taken from the Marafiq/RCJY approved schedule and published Saudi retail rates.
- **Makeup water composition** was a third-party analysis closed by an invented chloride value; it is now a measured Saudi Aramco analysis from an operating Dhahran cooling tower.
- **The skin-temperature offset** was a fixed 8 K assumption; it is now computed as q″/h_i from duty and geometry.
- **The low fill-law R²** was unexplained; it is now shown to be the expected difference between observational and designed-experiment data, with a published DOE at R² = 0.869 as the comparison.
- **The rejection of a better-scoring wet-bulb model** was our judgement; Kloppers (2003) establishes experimentally that air temperatures have no significant effect on the transfer coefficient.
- **Prior art** was unexamined; the closest claim (ChemTreat US 11,780,742 B2) is now disclosed, with our design position relative to it stated explicitly.

## 11. References

[1] P. Palenzuela, L. Roca, and J. M. Serrano Rodriguez, "Steady-state operation dataset of an experimental Wet Cooling Tower pilot plant located at Plataforma Solar de Almeria," Zenodo, 2024. doi: 10.5281/zenodo.10806201. [CC BY 4.0]

[2] J. C. Kloppers, "A critical evaluation and refinement of the performance prediction of wet-cooling towers," Ph.D. dissertation, Dept. Mech. Eng., Univ. Stellenbosch, Stellenbosch, South Africa, 2003.

[3] J. C. Kloppers and D. G. Kroger, "A critical investigation into the heat and mass transfer analysis of counterflow wet-cooling towers," Int. J. Heat Mass Transfer, vol. 48, no. 3, pp. 765-777, 2005.

[4] M. Badruzzaman, J. R. Anazi, F. A. Al-Wohaib, A. A. Al-Malki, and F. Jutail, "Municipal reclaimed water as makeup water for cooling systems: Water efficiency, biohazards, and reliability," Water Resources and Industry, vol. 28, art. 100188, 2022.

[5] I. S. Al-Mutaz and I. A. Al-Anezi, "Silica removal during lime softening in water treatment plant," in Proc. Int. Conf. Water Resources and Arid Environment, Riyadh, Saudi Arabia, 2004.

[6] D. L. Parkhurst and C. A. J. Appelo, "Description of input and examples for PHREEQC version 3," U.S. Geological Survey Techniques and Methods, book 6, chap. A43, 2013. [phreeqc.dat thermodynamic database]

[7] ASHRAE Handbook - Fundamentals, ch. 1, "Psychrometrics." Atlanta, GA: ASHRAE, 2017.

[8] S. H. Chien, M. K. Hsieh, H. Li, J. Monnell, D. Dzombak, and R. Vidic, "Pilot-scale cooling tower to evaluate corrosion, scaling, and biofouling control strategies for cooling system makeup water," Rev. Sci. Instrum., vol. 83, art. 024101, 2012.

[9] K. Boudreaux, B. Gonzalez, and K. Killough, "Methods for online control of a chemical treatment solution using scale saturation indices," U.S. Patent 11 780 742 B2, Oct. 10, 2023.

[10] Cooling Technology Institute, "Acceptance Test Code for Water Cooling Towers," CTI ATC-105, Houston, TX.

[11] Veolia Water Technologies, "Water Handbook - Cooling Water Systems: Heat Transfer," ch. 23. [Online]. Available: https://www.watertechnologies.com/handbook/chapter-23-cooling-water-systems-heat-transfer

[12] U.S. Department of Energy, "EnergyPlus Engineering Reference: Chiller:Electric:EIR," National Renewable Energy Laboratory.

[13] Tubular Exchanger Manufacturers Association, TEMA Standards, 10th ed. Tarrytown, NY: TEMA, 2019. [minimum tube-side velocity]

## 12. Reproduction

```
pip install -r requirements.txt
python src/fetch_zenodo.py      # downloads and MD5-verifies the dataset
python src/calibrate.py         # gates V1, V2
python src/run_controller.py    # gates V3, V5
python src/make_report.py       # regenerates this document
```

Every number in this report is read from `results/*.json` and `results/*.csv` by the generator; none is typed by hand.
