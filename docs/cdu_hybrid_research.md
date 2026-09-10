# MIZAN | One-CDU data-centre extension

> **[SUPERSEDED IN PART — 11 Sep 2026]** This document was written when the
> binding mineral on this water was believed to be **gypsum**, and its
> chemistry half reflects that: the H1b hypothesis, the 6.67 / 6.74 / 8.71 /
> 8.73 cycles table and the all-bins-select-6 result are all gypsum-bound.
>
> Correcting the aqueous speciation (defects 24, 27) moved the binding mineral
> to **amorphous silica** at 5 / 6 cycles. Silica is *prograde* — it binds at
> the cold basin rather than the hot skin, and it is pH-invariant below about
> pH 9, so acid cannot buy cycles against it. The gypsum figures here remain
> correct as a **gypsum-only sensitivity** and the 6.67 cross-checks defect
> 23's independent measurement of 6.672, but they are **not the operative
> ceiling**.
>
> The thermal half of this document — H1a, the bin table, the ASHRAE margins,
> the verification counts — is unaffected. See
> `docs/water_modes_and_free_cooling_floor.md` for the current treatment of
> the data-centre boundary.
8 Sep 2026 | Evidence reviewed 7 Sep 2026 | Internal engineering decision report

**Decision [Judgment]: retain the chemistry constraint service; do not pitch an ITD-driven hybrid benefit from this model.** Chemistry limits cycles inside the chiller domain, but the registered study finds no case where it lowers the maximum deliverable facility-water temperature. The original mandatory condenser-to-GPU-water sign assertion fails because the evaporator supply is controlled independently. This is a negative result for the proposed warmer-silicon-versus-colder-condenser thesis, not a reason to remove chemistry from MIZAN.

| Test | Outcome | Meaning |
| --- | --- | --- |
| H1a: condenser -> GPU water | FAIL | 1610 matched pairs; water change 0.000000 K at fixed FWS |
| H1b: cycles -> skin gypsum | PASS | 794 pairs; minimum SI increase 0.0885 |
| H2: cycles constraint | PASS | Witnesses in 8 of 8 weather bins |
| H2: water-temperature constraint | FAIL | Witnesses in 0 of 8 bins; sampled domain only |
| H3: chip-optimum gap | Not identifiable | No measured chip-to-water bridge |
| H4: ITD annual cost | Not identifiable | Independent FWS reset priced separately |

**Scope [Estimate]:** one equivalent CDU extends the existing tower/chiller/chemistry model to GPU inlet water. The 9.0 MW liquid load is fixed; equivalent nominal capacity is 11.505 MW. CDU approach is 5 K, with 3/5/7 K diagnostic sensitivity. The inherited model scales the named chiller fit to plant duty; it does not select a physical machine bank. No junction, DVFS, ITD device or CDU allocation model is built. This is a steady-state grid study, not field validation or a controller release.

**Independent value [Estimate]:** optimising FWS within the existing curve yields USD 50,054.36/year incremental cooling-plant cost reduction against the same controller held at 7 °C. That is not ITD savings. Actual ITD savings and chip-optimum shortfall remain undefined without a measured same-part/workload chip-to-water relation.

**Preservation [Verified, local]:** original V2 and V5-water gates remain failed. The protected files and existing user changes are preserved. The final verification record accompanies the package.

<!-- pagebreak -->
# The thermal boundary changes the thesis

**Verified source boundary:** ASHRAE W classes specify facility supply water, not GPU inlet water after the CDU. The actual GPU/OEM liquid-inlet limit and site W class were not supplied; the following margins are reference-class calculations, not equipment certification. [Thermal Guidelines, Fifth Edition, Revised and Expanded, Table 3.1](https://www.ashrae.org/file%20library/technical%20resources/bookstore/supplemental%20files/therm-gdlns-5th-r-e-refcard.pdf) and [ASHRAE Handbook 2023, Chapter 20: Data Centers and Telecommunication Facilities](https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx).

| FWS class | Upper limit (°C) | Margin at max FWS (K) |
| --- | --- | --- |
| W17 | 17 | 8.11 |
| W27 | 27 | 18.11 |
| W32 | 32 | 23.11 |
| W40 | 40 | 31.11 |
| W45 | 45 | 36.11 |

**Governing closure [Estimate]:** T_GPU,water = T_FWS + A_CDU. With equal stream heat-capacity rates Cdot, both terminal approaches equal A_CDU; Q_CDU = Cdot*(T_return - T_supply). Here Cdot = Q_IT/5 K, so each water loop rises 5 K. The heat exchanger has positive terminal differences and equal heat transfer on both sides. Pump heat, heat leaks, pressure losses, variable UA and unequal flows are excluded assumptions that require CDU selection data.

**Chiller/tower [Verified formulation; estimated inputs]:** Q_cond = Q_IT + P_chiller, and T_CW,return = T_ECWT + Q_cond/(m_CW*c_p). Units: kW / [(kg/s)*(kJ/kg/K)] = K. The solver uses the existing Poppe integration and fill law to find the fan speed satisfying Me_required = Me_fill, then replays the point through the original outlet solver. [EnergyPlus 24.2 Engineering Reference: Electric EIR Chiller](https://bigladdersoftware.com/epx/docs/24-2/engineering-reference/chillers.html).

**Cost boundary [Estimate]:** reported electricity is compressor plus tower-fan power. Pump electricity and IT electricity are outside the cost sum; these percentages are not whole-facility energy reductions.

**Why H1a fails [Judgment from balance]:** at fixed FWS and CDU approach, dT_GPU,water/dT_ECWT=0 while the chiller can meet duty. Condenser warming changes compressor power and capacity. COP alone does not determine the controlled evaporator outlet temperature. An overload/trip is infeasibility, not a licensed extrapolation to warmer GPU water.

**Equipment bound [Verified]:** the source York curve is valid only for FWS 4.44 to 8.89 °C, ECWT 15.56 to 35.00 °C, and PLR 0.20 to 1.06. All three bounds are enforced in the new wrapper, with raw PLR and a fixed nameplate. The legacy normalisation at the reference point is preserved as a model convention, not independently validated manufacturer performance. [EnergyPlus 24.2 Chillers.idf: York YT1758kW/6.28COP/Vanes](https://raw.githubusercontent.com/NREL/EnergyPlus/v24.2.0/datasets/Chillers.idf).

<!-- pagebreak -->
# Coupled sweep and annual economics

**Estimate:** 8,760 weather hours are represented by 8 equal-hour wet-bulb bins from the repository TMY file. Each row is a bin-centroid operating point. The FWS grid contains the two curve endpoints and 7 °C; ECWT has nine equally spaced source-domain values plus 32 °C. Cycles are 2 through 10; pH uses the registered grid. Fan speed is solved continuously within 30-100 %. A grid minimum is not a continuous global optimum.

| Bin | WB mean (°C) | FWS (°C) | CW (°C) | Cycles | Fan (%) | USD/h |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 9.7 | 8.89 | 20.42 | 6 | 79.0 | 126.89 |
| 1 | 14.2 | 8.89 | 22.85 | 6 | 84.2 | 136.52 |
| 2 | 16.9 | 8.89 | 25.28 | 6 | 77.4 | 143.98 |
| 3 | 19.3 | 8.89 | 27.71 | 6 | 68.5 | 151.48 |
| 4 | 21.4 | 8.89 | 27.71 | 6 | 87.0 | 158.28 |
| 5 | 23.6 | 8.89 | 30.14 | 6 | 75.4 | 164.40 |
| 6 | 25.8 | 8.89 | 32.57 | 6 | 64.7 | 170.90 |
| 7 | 28.5 | 8.89 | 35.00 | 6 | 56.8 | 175.44 |

The tower uses each bin's mean dry bulb and relative humidity. The WB column is the mean hourly wet bulb, which can differ from wet bulb recomputed from those two means.

**Baseline definition [Estimate]:** fixed 4 cycles, pH 7.8 and FWS 7 °C, choosing the feasible sampled ECWT nearest 32 °C. The fixed-FWS counterfactual optimises the other variables over the same feasible grid. The coupled optimum also selects FWS. These counterfactuals differ from the legacy fan-grid study; the new totals are new scenario results, not revisions of its published gates.

| Comparison | Energy: totals / mean ratios | Cost: totals / mean ratios | USD/year |
| --- | --- | --- | --- |
| Coupled vs baseline | 12.40 % / 12.58 % | 11.79 % / 12.02 % | 179,763.37 |
| FWS reset increment only | 5.13 % / 5.14 % | 3.59 % / 3.60 % | 50,054.36 |

**Annual water [Estimate]:** coupled-versus-baseline reduction is 11.13 % as ratio of totals and 11.15 % as mean of hourly ratios; the annual difference is 18,657.95 m³. All 8,760 represented hours must have both policies before totals are emitted.

**Aggregation [Derived]:** totals saving =100*sum[h_i*(B_i-O_i)]/sum[h_i*B_i]; mean-of-ratios =sum[h_i*100*(B_i-O_i)/B_i]/sum[h_i]. Absolute costs use the requested repository tariff dictionary, including electricity USD 0.074/kWh and legacy water USD 3.11/m³. Site tariff eligibility is not established.

**Validation boundary [Verified local inputs / judgment]:** 3,551 underlying hours exceed the legacy wet-bulb validation maximum. Binning is an annual approximation and does not prove feasibility at every original hour. No field data validates this CDU extension, its makeup chemistry or its annual savings.

<!-- pagebreak -->
# What the ITD lookup does and does not identify

**Verified source scope:** Crop et al. study production Intel Xeons. Figure 2 is average CPU temperature against power at fixed frequency for a specific Xeon 8480/povray experiment, with derived components. It is not a GPU curve or a coolant curve. Figure 5 uses per-part models and Figure 6 is a simulated facility case; the paper's facility-saving range is not a measured MIZAN result. [Crop, Moore and Pasricha, Revisiting Cooler is Better](https://arxiv.org/abs/2606.11163).

| Chip (°C) | Total (W) | Chip (°C) | Total (W) |
| --- | --- | --- | --- |
| 10.0 | 299.2 | 60.0 | 295.1 |
| 20.0 | 295.6 | 70.0 | 301.5 |
| 30.0 | 293.0 | 80.0 | 313.0 |
| 40.0 | 290.4 | 90.0 | 331.5 |
| 50.0 | 292.1 | 100.0 | 359.8 |

**Plot extraction [Verified method]:** numbers above come from the PDF vector paths, calibrated against the printed grid/tick values. The plotted minimum sample is 40.0 °C and 290.4 W. Display precision is not raw-data measurement precision. Piecewise-linear lookup is limited to the plotted range and refuses extrapolation. The curve is retained for internal research; its CC BY-NC-ND licence does not establish commercial deployment permission.

**H3 [Not identifiable]:** the coupled loop's maximum sampled water temperature is 13.89 °C at the assumed 5 K CDU approach. Subtracting that from the plotted chip minimum gives 26.11 K, but this is only the chip-to-water rise REQUIRED to make that source part reach its plotted minimum. It is not the gap between its actual and optimal chip temperature. Actual chip temperature has not been modelled or measured here.

**H4 [Not identifiable]:** there is no defensible annual cost of reaching the ITD optimum until the required FWS target is identifiable. The companion JSON reports the cycles change and annual cost change caused by the independent allowed FWS reset in every bin. Fixed IT load intentionally prevents booking temperature-dependent CPU energy as a saving.

**Required evidence [Judgment]:** a measured table for the same device/part, workload and performance point, containing chip temperature, inlet water temperature, flow and power; an OEM liquid-inlet envelope; and the actual CDU approach/flow rating. An empirical lookup can then connect the boundaries without introducing a semiconductor device model. A generic thermal resistance or another Xeon part's optimum would not close this gap.

<!-- pagebreak -->
# Chemistry: source resolution is not defect closure

**Verified primary evidence:** the 2022 paper Table 1 reports sulfate 566 mg/L; that number was correctly transcribed. The 2020 engineer-authored pilot account reports 300 mg/L and also differs on calcium, sodium, chloride and bicarbonate. Neither source reconciles the analyses. The primary PDF was already in the repository. [Badruzzaman et al., Municipal reclaimed water as makeup water for cooling systems: Water efficiency, biohazards, and reliability](https://doi.org/10.1016/j.wri.2022.100188) and [Jutail et al., Use of treated sewage effluent as cooling tower makeup water - A pilot study](https://www.watertechonline.com/water-reuse/article/14187302/use-of-treated-sewage-effluent-as-cooling-tower-makeup-water-a-pilot-study-print).

| Scenario | Na (mg/L) | Ion sum (mg/L) | Charge error (%) | Gypsum cycles |
| --- | --- | --- | --- | --- |
| published 2022 | 379.0 | 1752.0 | -14.27 | 6.67 |
| published 2022 + Na balance | 468.0 | 1841.0 | 0.00 | 6.74 |
| field 2020 | 310.0 | 1390.0 | -3.17 | 8.71 |
| field 2020 + Na balance | 326.4 | 1406.4 | 0.00 | 8.73 |

**Derived diagnostics:** charge error above uses the repository denominator (cation+anion)/2; the common sum denominator would halve each percentage. Gypsum cycles are continuous roots of the existing operating-SI limit at 40 °C, a chemistry-only sensitivity, not new field ceilings. The controller's sodium-balanced analysis is an explicit assumption. Missing silica remains unmeasured, not evidence of silica-free water.

**Method issue [Verified / inference]:** Table 2 assigns ASTM D1125 to both conductivity and TDS; D1125 measures conductivity/resistivity. Thus a gravimetric TDS reference is not established. The ion-sum discrepancy is a real consistency concern, but it does not identify which ion is wrong or prove that sulfate must be 300. Paired laboratory data and clarification of TDS methodology are required. [ASTM D1125-14, Electrical Conductivity and Resistivity of Water](https://store.astm.org/d1125-14.html).

**Mathematical correction [Derived]:** charge balance is linear: sum[z_i*mean(c_i)] = mean(sum[z_i*c_i]). Equal-weight averages of matched electroneutral samples remain electroneutral. Different sample sets, missingness, weights or analytical errors could explain the discrepancy; ordinary averaging alone does not. Defect 17 remains open and its strict xfail is preserved.

**Thermal caution [Estimate]:** in 831 of 909 accepted thermal states, skin gypsum SI is lower than basin SI. The inherited gypsum temperature relation is not globally retrograde. The clean 3 K versus inherited 8 K chemistry-only sensitivity changes feasible status for 0 states. The new study preserves legacy skin evaluation and reports this limitation; it does not certify that skin is always the worst point in the entire loop.

**Interpretation of H2 [Judgment]:** a cycles ceiling can bind while the chiller has spare capacity. That supports a chemistry constraint service. It does not establish that chemistry sets the maximum IT-water target or creates an antagonistic ITD trade-off. Those are different directions in the control space.

<!-- pagebreak -->
# Dry versus evaporative: price the valid comparison

**Verified tariff / conditional applicability:** Marafiq's industrial table lists process water at SAR 8.04/m³ and industrial wastewater at SAR 3.64/m³. At 3.75 SAR/USD these are separate makeup and discharge charges. The sum is a conditional value of avoided blowdown; charging wastewater treatment on evaporation overstates evaporative cost. Actual reclaimed-water service, discharge route, VAT and electricity classification still need the site's contracts. [Marafiq Water Tariff](https://www.marafiq.com.sa/en/partnering-with-us/water-tariff/) and [Saudi Central Bank exchange-rate display](https://www.sama.gov.sa/en-US).

**Derived cost equation:** C_water=p_M*M+p_B*B, where M and B are makeup and blowdown in m³/h. For the dry comparison use p_E*(P_dry-P_wet)=p_M*M+p_B*B+C_chem when other terms are equal. This gives a break-even power penalty without inventing dry equipment performance. The JSON provides that budget by weather bin and the in-range makeup-price crossover.

| Same schedules repriced | USD saved/year | Totals (%) | Mean ratios (%) |
| --- | --- | --- | --- |
| legacy requested | 179,763.37 | 11.79 | 12.02 |
| process and industrial discharge | 178,314.82 | 12.71 | 12.93 |
| process and unbilled outfall | 161,739.80 | 11.87 | 12.09 |

**Estimate:** the above table reprices the same saved policies; it does not reoptimise them under a new tariff. Legacy requested prices remain in the main study. A coastal-outfall case with no wastewater bill is conditional and does not imply a discharge permit.

| Dry approach (K) | In-curve hours | Unsupported hours |
| --- | --- | --- |
| 3.0 | 5475 | 3285 |
| 5.0 | 4380 | 4380 |
| 7.0 | 4380 | 4380 |

**Domain failure [Verified bound / estimate]:** dry ECWT is assumed T_drybulb plus 3/5/7 K approach. Any point beyond the named chiller's range is rejected, including the hot Gulf regime needed to establish annual ROI. In-range counterparts assume a dry fan power equal to the reference tower fan nameplate purely for sensitivity. No full-year dry/evaporative verdict, annual ROI or universal 16 K priced penalty is supported by this machine map.

**Cycles sensitivity [Estimate]:** the companion study covers every tested cycles count, with 65 supported combinations. Example below: makeup-price crossover in USD/m³ at dry bulb 27.2 °C, recomputed wet bulb 19.9 °C and fixed FWS 8.89 °C. Discharge is separately priced at USD 0.971/m³. Wet fan/ECWT choice can change with price. Below each crossover a sampled wet policy costs less; above it the assumed dry system costs less.

| Cycles | 3 K dry approach | 5 K dry approach | 7 K dry approach |
| --- | --- | --- | --- |
| 2 | -0.11 | 0.07 | 0.27 |
| 4 | 0.31 | 0.59 | 0.89 |
| 6 | 0.43 | 0.74 | 1.07 |

**Judgment:** compare these conditional crossover budgets with a supplier's dry/adiabatic map and actual water contract before claiming annual ROI.

<!-- pagebreak -->
# Prior art and the decision that remains

**Closest paper [Verified metadata; inaccessible body]:** Chen et al., Applied Energy 424, 128414, DOI 10.1016/j.apenergy.2026.128414, is assigned to the December 2026 issue. Publisher preview and metadata are accessible; full methods/results were not obtained through publisher, Elsevier metadata endpoint, author/repository searches or OpenAlex. Its full-text chemistry count is UNAVAILABLE, not zero. It remains a dependency before a novelty pitch. [Chen et al., Physics-informed machine learning-based adaptive predictive control for energy-efficient hybrid-cooled data centers management](https://doi.org/10.1016/j.apenergy.2026.128414).

**Patent counter-evidence [Verified]:** ChemTreat US11780742B2 already discloses online chemical dosage control based on a saturation parameter calculated using heat-exchanger skin temperature. Claims 1, 3, 19 and 20 are directly relevant. Skin-based chemistry alone is not a surviving novelty claim. The combined species-specific surface constraint and mechanical-energy optimisation is a candidate distinction requiring claim mapping; absence from a sampled corpus does not prove novelty or freedom to operate. [ChemTreat US11780742B2, Methods for online control of a chemical treatment solution using scale saturation indices](https://patents.google.com/patent/US11780742B2/en).

**Corpus scope [Verified local scan]:** all eight supplied PDFs returned zero matches for the original exact CHEM regex under both layout and plain extraction, the latter including rotated text. The regex contains 15 alternatives, described as nine term families in the legacy narrative. The legacy 18-document total includes version repeats and background/device documents. Count it as sampled files/versions, not 18 independent control studies or a census. Text layers, hyphenation and vocabulary limit this result; the closest paper remains unread. Existing prior-art documents are not rewritten.

**Already-covered work [Verified scope]:** CDU allocation and flow/supply co-design appear in the supplied co-design paper. The supplied twin paper distinguishes unconstrained from constrained cooling savings. Neither headline should be recycled as a new MIZAN benefit. [Co-Design Optimization for Data Center Cooling System via Digital Twin](https://arxiv.org/abs/2605.15516) and [Digital Twin-Based Cooling System Optimization for Data Center](https://arxiv.org/abs/2603.01198).

| Option [Judgment] | Quantified basis | Decision / missing evidence |
| --- | --- | --- |
| Existing-MIZAN constraint service | H2 cycles witnesses in 8/8 bins | Preferred near-term hypothesis; needs site chemistry and shadow data |
| One-CDU cool-water extension | FWS increment USD 50,054.36/yr, scenario only | Keep as reproducible research; no ITD product claim |
| Warm-water / dry-adiabatic study | Current hot-hour dry power unavailable | Obtain applicable machine/CDU maps and tariff contracts first |

**Verification handoff [Judgment]:** independently check the full Applied Energy manuscript, same-device temperature bridge, measured makeup analysis, corrosion/inhibitor programme, CDU ratings, site temperature/condensation limits, billing route, and dry equipment selection. Pump deltas, dynamics, redundancy, precipitation kinetics and hardware deployment are outside this model. Hardware demand is a small CPU-only steady-state sweep; no GPU training or simulation exceeding the stated laptop class is required.

**Reproduction [Verified local artifacts]:** the README gives all commands, including the cycles crossover. The first experiment failed the unchanged replay guard; its evidence is retained. The accepted run rejects 16 injected faults. A separate verifier passes 60 checks, including extraction faults and replay of the original bad root. Maximum accepted forward error is 0.000880 K against the registered 0.001 K. Source hashes, all candidates and both aggregation conventions accompany the results. Historical gate files are unchanged.
