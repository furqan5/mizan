# Defect register, and what a failed gate is not

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

There are two different things in this package that can look alike from a distance, and they should not be confused.

A **defect** is a mistake in the work — a wrong unit, an inverted sign, an unconverged solver. Defects are faults. They get found and fixed, and the count of open ones should be zero.

A **failed gate** is a result. A threshold was fixed in advance, the experiment was run, and the answer came out on the wrong side of it. That is not a fault. Suppressing it would be.

This document lists both, separately, so neither can be mistaken for the other.

---

## Part 1 — Defects. Seventy-four found, sixty-four fixed, ten open.

| # | Defect | How it showed up | State |
|---|---|---|---|
| 1 | Fan air-flow correlation read as per cent when it takes hertz | The curve turned over at 62 %, so air flow fell as the fan sped up. All three thermal gates failed with a +1.50 K bias. | **Fixed** — and read with defect 73, which records that the dataset's own README prints the same correlation as a percentage and that nothing in the repository can arbitrate by measurement |
| 2 | Sepiolite used as the magnesium-silicate proxy | Returned indices forbidding operation at every cycle count, against plants demonstrably running 4–5. | **Fixed** — replaced by the empirical Mg × SiO₂ product and the brucite criterion |
| 3 | Carnot-referenced chiller COP | Overstated the value of cooling the condenser by ~60 %. | **Fixed** — replaced by the EnergyPlus bi-quadratic |
| 4 | Chiller coefficients not traced to any machine | Could not be checked by anyone. | **Fixed** — York YT 1758 kW / 6.28 COP, EnergyPlus `Chillers.idf` |
| 5 | Optimiser extrapolating outside the chiller's fitted range | Booked a false 20.41 % water saving that would have flipped a failed gate to passed. | **Fixed** — the entering-condenser window is now a hard constraint; 1,840 of 6,307 candidate points are rejected |
| 6 | Duty fixed point unconverged and seed-dependent | Six substitution steps at 5 mK. Evaporation moved 3.8 % on the choice of seed alone. | **Fixed** — Aitken acceleration with a Brent fallback; 0 of 360 non-converged |
| 7 | Drift eliminator rate 100× too large | `0.0005` used as a fraction — the modern rating of 0.0005 **per cent** with its sign dropped. | **Fixed** — 1×10⁻⁵ in both `tower.py` and `controller.py`, checked by the audit |
| 8 | Simscape temperature sensor read as Celsius when it outputs Kelvin | The chemistry was asked for a saturation pH at 341 °C and the chiller reported itself out of envelope for a whole simulated day. | **Fixed** — explicit conversion block in the diagram |
| 9 | Simscape heat-flow sign inverted | +1000 kW into a 150 t mass for 600 s gave −0.956 K: right magnitude, wrong direction. | **Fixed** — ports swapped, verified against arithmetic |
| 10 | A document existed as two copies | `docs/matlab_model.md` was a manual copy of `matlab/README.md` — identical the day it was made, and guaranteed to go stale the first time either was edited. | **Fixed** — the PDF builds from the original; the audit now rejects duplicated documents |

| 11 | **Chiller capacity constraint logged but never enforced** — the same curve as defect 5, the other of its two limits | Above ~32.5 °C entering condenser water the York YT cannot make the 10 MW duty. `chiller_power_biquad` clamps `plr_raw` to 1.0 and reports the machine as merely full-loaded, so **computed chiller power fell as condenser water got hotter** — backwards. The optimiser's main lever is fan speed, and lowering the fan raises condenser temperature, so it was rewarded in exactly the region where the offsetting cost was under-computed. It moved the plant from **2 of 5** conditions infeasible to **4 of 5**, worst shortfall **1,216 kW of 10,000 kW**. | **Fixed** — `plr_raw > 1.06` is now a hard feasibility constraint alongside the temperature window |
| 12 | **A constant that documents are validated against, hardcoded into four files** | The V5 water figure `14.83` was typed into `annual.py` (×4), `make_report.py` and `audit.py`. When defect 11 moved it to `10.02`, `annual.py` wrote the stale value into the JSON the audit checks other documents against, and `audit.py` began *requiring* the report to quote a superseded number — an audit enforcing staleness. | **Fixed** — all six now read `controller_summary.json`. The audit's `"Open defects: none"` literal was replaced the same way, by a check that the declared count matches the rows marked OPEN |
| 13 | **The audit's memory of superseded numbers was itself hand-maintained, and the artefacts were never scanned** | Defect 12's fix removed hardcoded values from the *checks*, but section 5 still held a typed list of what the numbers used to be. Defect 11 superseded six headline figures and none was added, so the scan passed `linkedin_post_draft.md` while it sourced `12.6 %` to a key holding `9.23 %` — and that draft was published. The glob was `docs/*.md`, so `results/` was never read at all: `calib_out.txt` recorded **V2 as PASS at 7.11 %** while `calibration.json` said **FAIL at 9.90 %**. | **Fixed** — the stale set is now read from the before/after table below; stated provenance (`file.json → key`) is resolved against the artefact and compared; `.txt` is in scope; and a transcript older than the JSON its script writes now fails the audit |
| 15 | **Gypsum's solubility could not have the shape the module's own comment describes** | `log_k_gypsum` was a single-enthalpy van 't Hoff — monotonic by construction — while the comment at `MINERAL_EVAL_POINT` says gypsum has a *"maximum near 35-40 C"*. Measured: strictly decreasing over 10-80 C, moving 0.0105 log units across 25→70 C while activity coefficients moved the full SI ten times that in the **same** direction. Gypsum therefore looked LESS saturated at the hot skin than in the bulk — the opposite of the mechanism this product sells, and the cause of defect 14. | **Fixed** — switched to the `phreeqc.dat` analytic expression, the same treatment calcite already had, from the database already cited. Anchored to the same log_k25 (agrees to 0.0009), interior maximum near 23 C, 10.8× the temperature response. `SI_gypsum` now has a **minimum at 40 C and rises above it** — a solubility maximum at 40 C, matching the literature's ~42 C gypsum–anhydrite transition without being fitted to it. Four pre-registered predictions in `src/gypsum_logk_upgrade.py`, all passed |
| 16 | **The chiller was sized at ARI and asked to run a Gulf summer** | `q_avail = Q_evap_kw * capft_here` asserted the installed machine is exactly the size of the load *at ARI* — 6.67 °C chilled water, **29.44 °C entering condenser water**. No machine is selected that way. Once defect 11 made the capacity limit binding, **two of five design conditions had no feasible operating point at all**, which is a statement about the sizing, not about the Gulf. | **Fixed** — the machine is selected at the top of its own fitted range (35 °C), a **15.0 % margin**, and the same nominal now feeds both the capacity check and the power curve. **All five conditions are feasible again** and the V5b sweep is inside the envelope at every cycle count. `src/chiller_selection_audit.py` |
| 17 | **The modelled makeup water fails charge balance and TDS closure** | `ARAMCO_RECLAIMED` carries **SO₄ = 566 mg/L**; a field write-up of the same Aramco pilot reports **300**. Two objective tests needing no outside authority both fail on the modelled set and both pass on the reported one: charge imbalance **−14.3 %** vs −3.2 %, and the ions sum to **1752 mg/L against a stated TDS of 1500** (+16.8 %) — a water cannot contain more ions than its own TDS. Sulfate is the number the gypsum wall rests on. | **Fixed** — 10 Sep 2026, and NOT by choosing between 566 and 300. Table 1's "Reclaimed Min | Ave | Max" columns are **independent per-ion marginals over a monitoring campaign, not analyses of any sample** — proved by the Max column, whose ions sum to **3557 mg/L against its own stated TDS of 1800**. No sample contains twice its own dissolved solids. The Raw Groundwater column, which IS a sample, closes cleanly (charge +3.9 %, TDS −1.2 %), so the laboratory method is sound and the Ave column is simply not a water. The real defect was that the CONTROLLER ran on it. `ARAMCO_RECLAIMED` is left **unchanged** because the transcription is faithful; the controller now runs on `ARAMCO_FIELD_VALIDATED`, the same pilot reported as one coherent analysis in Water Technology, Jan 2021, which closes at charge −1.2 % and TDS −4.5 % |
| 18 | **Four documents told you to attach a figure that does not exist** | `linkedin_outreach.md`, `linkedin_post_draft.md`, `HANDOFF.md` and `robustness_gaps.md` all said *"Attach: `figs/two_ceilings.png`"*. There is no such file and there never was — the figure is written by `fig_water_ceiling` as `figs/water_ceiling.png`. A document instructing an action that cannot be performed is a defect, and this is the kind nobody finds until they are mid-post. | **Fixed** — all four corrected, and the audit now checks that every `` `figs/*.png` `` a document references actually exists. The check found the fourth one immediately |
| 20 | **The customer-facing value table extrapolated one hour across a whole year** | `commercialisation.md` §2 gave the saving per 10 MW module as **$157,975/yr and 26,711 m³/yr**, obtained by multiplying one condition's hourly saving by 8,760 hours. A Gulf plant does not spend 8,760 hours at a summer design condition. The package had already ruled twice that the hours-weighted figure is the one to quote — for the V5 gate mean, and again for the mean-of-ratios defect — and the value table, the only table a customer is ever shown, had never been brought under the rule. Recomputed against `annual_dhahran.json`: the published figures were **2.07× too high on cost and 2.26× too high on water**, and the 50,000 TR plant value fell from **$2.78M/yr to $1.34M/yr**. | **Fixed** — rebased on the weather-weighted year in `commercialisation.md`, `application_answers.md` and `WHERE-WE-STAND.md`, with the superseded column kept beside it |
| 19 | **A sensitivity study asserted a conclusion its own table had stopped supporting** | `src/skin_sensitivity.py` printed a computed sweep of the gypsum wall against assumed skin ΔT, and then a paragraph of **hardcoded prose** underneath it: that a hotter skin makes gypsum look safer, that the 8 K assumption buys "about one extra cycle", and that the reported zero saturation violations was conditional on a fouled condenser. Defect 15 replaced the gypsum solubility model and the table changed; the paragraph did not. It also still quoted V5 at **14.83 %**, two supersessions out of date. Defects 12 and 13 one more time, in a file nobody thought to re-read. | **Fixed** — every conclusion is now derived from the computed rows, and the artefact records `ceiling_sensitive_to_skin_delta` rather than a remembered direction |
| 14 | **The two headline ceilings are reported from a condition the machine cannot operate at** | `gate_v5b` sweeps cycles at one condition — *Dhahran summer humid*, fan 90 % — and reports **economic 7, physical 8**. That is one of the two conditions V5 discards as having no feasible solution, and its own output says `10 of 10 cycle counts sit outside the machine's validity envelope` (plr 1.097 against a 1.06 limit). `src/ceiling_condition_audit.py` re-runs the same sweep at the three conditions V5 *does* find feasible: both ceilings come back **one cycle lower, 6 and 7**, at all three, with every row inside the envelope. **Fixed** — but not by the reporting judgement this row originally called for. Defects 15 and 16 removed both causes: with gypsum on a temperature function that can turn over, the ceilings come out **6 and 7 at all five conditions**, and with the chiller selected properly the V5b sweep now sits **inside** the envelope at every cycle count. The condition-dependence was an artefact, not a fact about the water. |
| 21 | The staleness guard could not reach the figures declared by hand | The data centre run's annual energy saving is 6.4779 %, which prints as "6.48 %" and collides exactly with the cost saving retired by the chiller capacity fix. The guard that clears live values only ran against tokens derived from the before/after tables, so it never touched the exact figures declared in code, and the audit demanded that a number generated that morning be labelled superseded. | **Fixed** |
| 22 | **The total defect count was maintained by hand in five documents and went stale in all five** | The register's own header said twenty while its table listed twenty-one; its concluding section said eighteen; `threshold_revision_memo.md` said thirteen; `robustness_gaps.md` said fourteen; and `ENGINEERING_IN_PLAIN_ENGLISH.md` — the document the two non-technical co-founders read before speaking to a customer — said **ten found, ten fixed, none open**, while the register declared defect 17 OPEN. `audit.py` checked that the register's declared OPEN count matched its OPEN rows, but nothing checked the TOTAL, which is the number that moves every time a defect is found. Same shape as 12, 13 and 21: a figure maintained by hand, in a file nobody re-reads. | **Fixed** — the count is now DERIVED from the register's own table rows and cross-checked against every document that states one, in `audit.py`; the guard was verified non-vacuous by injecting a wrong count |
| 23 | **The gypsum wall is documented at the condenser skin, and on this water the skin is the LEAST saturated point** | Defect 15 gave `log_k_gypsum` an interior maximum, so `SI_gypsum` has an interior **minimum at 43.4 °C** — a condenser skin at 38–48 °C sits in the trough. On `ARAMCO_RECLAIMED` at 6 cycles, pH 8.0: basin 30 °C **SI 0.2322** against skin 40 °C **0.2254**, the basin worse by 0.0068 log units, and the same ordering at every cycles count tested. `robustness_gaps.md` stated both halves of the contradiction in one paragraph — *"SI_gypsum now has a minimum at 40 °C"* followed by *"Gypsum is therefore most saturated at the hot skin"* — and `HANDOFF.md`'s one-paragraph product description routed gypsum to the skin as the least-soluble point. Found by an external agent's measurement (831 of 909 accepted states had skin SI below basin SI) and confirmed independently here. | **Fixed** — both sentences corrected. The *claim* was the defect and it is gone. `MINERAL_EVAL_POINT['SI_gypsum'] = 'hot'` is deliberately left in place, because changing it is a physics decision rather than a typo; it is carried in Part 3 as an open item. Impact is bounded and no published number moves: max cycles 6.672 at the skin against 6.606 at the basin, so the integer ceilings stay **6 and 7** |
| 24 | **The chemistry engine applies Davies coefficients to TOTAL ions and never solves aqueous complexation** | Benchmarked against PHREEQC 3.9.0-17591 (maintainer's release, SHA256 verified) on the USGS worked example of a solution held **at gypsum saturation**: published SI **0.000**, this engine **0.2046**. Reproduced independently. The example carries 0.01508 mol/kgw total calcium of which only 0.01046 is free — **0.004627 is the neutral CaSO₄⁰ ion pair**, about 31 % invisible to a Davies-on-totals treatment. Matching a mineral's logK is not the same as reproducing its speciation. A known-composition counterexample: it involves no site, no field measurement and none of defect 17's disputed assay. | **Fixed** — 10 Sep 2026. `chemistry.speciate()` now solves aqueous ion association (ten pairs, phreeqc.dat constants transcribed not linked, so the edge controller still ships without a third-party runtime), and `saturation_state` uses FREE-ion molalities and the speciated ionic strength. The benchmark now returns **−0.0163** against a published 0.000, and the solver reproduces the published distribution: free Ca 0.01059 vs 0.01046, CaSO₄ pair 0.004495 vs 0.004627 |
| 25 | **The acid dose is charged against the wrong stream and is overstated by the cycles ratio** | `acid_dose_for_ph` builds its per-kg figure from `water.concentrate(cycles)`, i.e. the **circulating** basis `C·a_makeup − a_target`, and `controller.py:187` and `:494` multiply it by **makeup**. The steady alkalinity balance is `M·a_makeup − L·a_target`, so the multiplier must be **blowdown**. Measured overstatement at 6 cycles: **6.99 kg/h dosed against 1.16 kg/h required, ratio 6.03 = C**; benchmarked at 5–10× across 40 points. Every legacy rate implies **negative outlet alkalinity**, impossible for a bicarbonate-dominated water near pH 8. The docstring said *"per kg of circulating makeup"* — two different streams named as one, which is the defect in one phrase. The docstring is corrected and the defect is declared at the call site; the arithmetic is deliberately NOT changed yet, because it moves the acid cost line and every artefact quoting it. | **Fixed** — 10 Sep 2026. Both call sites now multiply by `blowdown + drift`, which is exactly makeup/C. The dose falls by exactly C at every cycles count: 4.96→1.24, 5.96→1.19, 6.99→1.17, 8.02→1.15 kg/h at 4/5/6/7 cycles |
| 26 | **The Davies validity limit was computed and reported from the first commit and enforced by nothing** | `Water.pitzer_required()` returns `ionic_strength() > 0.5` and appeared only in the output dict of `saturation_state`. Above I = 0.5 mol/kg the Davies equation is outside its range and every activity coefficient in every saturation index is an extrapolation. **The optimiser's entire job is to raise cycles, which raises ionic strength, so it walks directly at this boundary** — the same shape as defect 11, where the chiller's capacity limit was logged for months and read by nothing, and defect 9, where the optimiser collected a false saving from an extrapolated curve. On the validated water Davies fails above ~16 cycles. | **Fixed** — 10 Sep 2026. Both `evaluate_operating_point` and `_cost_at_ph` now record a `davies_range` violation, treated as a MODEL-VALIDITY failure rather than a chemistry one: the water may be fine, but this model is not entitled to an opinion about it |
| 27 | **Nothing validated the water analysis, and silica was carried as an unmeasured zero** | The analysis is the one input every result depends on and the only one nothing checked. `ARAMCO_RECLAIMED` fails TDS closure by **+16.8 %** as transcribed and **+22.7 %** once sodium is balanced — a water cannot contain more ions than its own stated TDS — and carries `SiO2 = 0.0` for a species the source never reports. **Zero is indistinguishable from UNMEASURED**, and amorphous silica binds at the COLD basin and is not pH-sensitive, so acid cannot buy cycles against it. Declaring the measured Salbukh value moved the ceiling from **12.3 to 5.8 cycles** and changed the binding mineral from gypsum to silica. | **Fixed** — 10 Sep 2026. `chemistry.validate_analysis()` runs four objective checks (charge balance, TDS closure, Davies applicability, silica declared) and `require_valid_analysis()` raises at the product boundary. `run_controller` now runs on `ARAMCO_FIELD_VALIDATED`, which passes all four. `ARAMCO_RECLAIMED` is left **unchanged** because the transcription is correct — defect 17 is about the source. Also guarded: `ph_saturation_brucite` takes `(T_c, water)`, reversed from the rest of the module, and a swapped call now raises by name instead of dying inside `_vant_hoff` |
| 28 | **The V5b ceiling explanation was hardcoded for gypsum and printed under whatever mineral the sweep actually found** | `run_controller.py` printed `PHYSICAL ceiling : {phys} cycles -- binding mineral {mineral}. Acid cannot move it: **sulfate** saturation is not pH-sensitive, so the lever that buys cycles against calcite stops working entirely at this wall.` The mineral was interpolated; the explanation was not. Once the validated analysis made **amorphous silica** the binding mineral, the output named silica and then explained the wall in terms of sulfate. Same fault as defect 19 — a paragraph asserting a conclusion its own table had stopped supporting — and the third time prose has outlived the number beneath it. | **Fixed** — the explanation is now derived from the computed mineral, with a branch for each: gypsum (hot skin, pH-insensitive), silica (cold basin, prograde, pH-invariant in this model below ~pH 9), calcite (hot skin, and strongly pH-sensitive — which is precisely how an LSI controller walks into the mineral behind it). Verified: `SI_silica_am` spread across pH 7–9 is exactly **0.0** |
| 29 | **The model has no phosphate species, and calcium phosphate is a named scale-former in exactly this application** | `SPECIES` carries Ca, Mg, Na, K, HCO3, SO4, Cl, NO3, SiO2 — **no PO4**. Yet phosphate is *measured* in both Aramco publications (**8.15 mg/L** in the 2022 table, **8 mg/L** in the 2021 field analysis), the 2022 paper's own prose names *"calcium carbonate, calcium phosphate, magnesium silicates, and calcium sulfates"* as the typical scale formers, `docs/chemistry_evidence.md` already lists calcium phosphate among the three **retrograde** hot-surface species and tabulates tricalcium phosphate solubility, and the definitive DOE study of treated municipal wastewater as cooling makeup (Vidic, Dzombak, DE-NT0006550) reports that *"the major mineral scales formed in recirculating cooling systems using secondary-treated MWW as make-up water are calcium carbonate and to a lesser extent calcium phosphate."* So the second-ranked scale in the published literature for this exact water is the one species the model cannot represent — and unlike silica it is **measured**, not assumed. | **Fixed** — 10 Sep 2026. `SPECIES` gains `PO4`; `speciate()` solves the phosphate sub-system analytically (three acid-base forms and six Ca/Mg pairs, phreeqc.dat constants, verified against the textbook pKa of phosphoric acid); `saturation_state()` reports `SI_tcp` and `SI_hydroxyapatite`; `validate_analysis()` gains a `phosphate_declared` check symmetric with silica; and `ARAMCO_FIELD_VALIDATED` now carries its measured 8 mg/L. **Phosphate is deliberately NOT a binding limit** — see below. Held by `tests/test_doe_benchmark.py` |

| 30 | **The water tariff charged the wastewater-discharge fee on evaporated water** | `run_controller.py` derives USD 3.11/m³ as *"the value of a cubic metre of blowdown avoided — the makeup NOT bought plus the industrial wastewater NOT discharged"*, SAR 8.04 + SAR 3.64 from the same approved Marafiq schedule. Both cost sites, `controller.py:222` and `:542`, then multiplied it by **makeup**. At six cycles makeup is six times blowdown, so the SAR 3.64 discharge half was charged on roughly **six times the water that reaches a sewer** — and on the evaporated fraction in particular, which leaves as vapour and is never discharged at all. Drift was also charged a sewer fee it does not incur. This is the **defect-19/23/28 shape a fourth time**: prose naming one quantity, code computing another. Found by an external agent's review of the tariff derivation. | **Fixed** — 10 Sep 2026. `_water_cost_per_h()` charges `p_makeup·M + p_discharge·B` with the two Marafiq line items carried separately (USD 2.144 and 0.971), asserted at import to reconstruct 3.11. A tariffs dict without the split falls back to the old single figure, so an external caller cannot be silently repriced |

| 44 | **The skin temperature rise was a hardcoded 8 K, and the function written to replace it could not have produced it** | `skin_delta_k=8.0` was a literal in four signatures and in `field_validation.py`. `chemistry.wall_bulk_delta_t` existed to compute it and was **never called** — and could not have produced 8 K anyway, because it returns only the **clean film** rise, 2.4–3.7 K on the corrected heat-flux band. The missing term was the **fouling layer**, and the surface a saturation index belongs on is the **deposit face**, not the metal: scale forms where water touches solid, and once a deposit exists that face runs hotter than clean metal by `q'' × R_f` | **Fixed** — 11 Sep 2026. `skin_temperature_rise()` computes `q'' × (1/h_i + R_f)` against a table of **published** fouling allowances. At 25 kW/m², 2 m/s and the TEMA treated-cooling-tower allowance it returns **7.45 K** — the 8 K was a condenser at its design fouling allowance all along, and nobody had written down which allowance, so it read as a guess. `controller.SKIN_DELTA_K_DEFAULT` is now the single place it is set. **AHRI Guideline E-1997 §5.1 verified from the source** (0.00025 hr·ft²·°F/Btu, the allowance ARI standards rate chillers at); the TEMA value is tagged UNVERIFIED because TEMA is paywalled and we have not read it |

| 46 | **No aggressive-anion corrosion term at all, and chloride binds below the scaling ceiling** | The whole corrosion model was `CORROSION_FLOOR_SI` — one mechanism, a calcium-carbonate film protecting mild steel. Nothing represented the aggressive side, while the optimiser raises cycles and doses acid. Working it out **inverted the received framing**: Larson–Skold is a *ratio*, and concentrating a water multiplies every ion equally, so **cycles move it by exactly zero**; acid moves it from **4.60 to 55.0** as alkalinity goes from untouched to 90 % acidified. Chloride pitting is the mirror — an absolute concentration limit that cycles move and acid does not. And the number that matters: on the measured Riyadh water a **316 stainless** condenser pits at **1.85 cycles** against a **4.52-cycle scaling ceiling** and a **3.0-cycle recommended baseline**. Where the tubing is austenitic stainless, chloride binds first, at less than half the limit this package computes. It bites hardest on the **CDU**, where plate exchangers are routinely 316 | **Fixed** — 12 Sep 2026. `src/corrosion.py`: Larson–Skold with its calibration envelope attached (pH 6.8–8.3, room temperature, mild steel only — a Gulf tower is outside it on two axes, and the module says so rather than returning a number quietly), Ryznar, Puckorius with the correct `2·pHs − pH_eq` sign, UFC 3-230-13 Table 5-9 coupon acceptance bands, and `chloride_pitting_check`. Enforced in `_evaluate_point` **only when the caller declares the tubing alloy**, because the limit is a property of the metal; an undeclared alloy leaves it **inactive, which is not the same as satisfied**. Three UFC quotes verified from the document text, including *"it has lost its practical application for cooling water systems"* about LSI — a US defence standard making our argument for us |

| 50 | **The fix for defect 37 reproduced defect 37** | Defect 37 was *"the diurnal silica margin is computed and enforced by nothing"*, and it was already the **fourth** instance of that shape. The fix added `chemistry.limits_with_diurnal_margin()`. A guard written on 12 Sep 2026 specifically to stop the pattern recurring an eighth time found that function **defined in `chemistry.py`, exercised in `test_defect_regressions.py`, and called by nothing that makes a decision.** The physics has not changed and is not optional: amorphous silica is prograde, so the ceiling falls as the basin cools overnight — the limit moves on a twelve-hour period while the concentration can only follow on half a week, so a setpoint at the mean-temperature limit is exceeded every night and no blowdown policy prevents it | **Fixed** — 12 Sep 2026. The Cycle Ceiling Report **applies** the margin to its recommended ceiling and **discloses** its cost, because reporting it as an option would be the same mistake a third time. On the measured Riyadh assay it costs **nothing**, and the report says why: SiO₂ is 8 mg/L as the page prints it (18 until defect 67 corrected a text-layer misread), so **calcite binds before silica does** and a silica-only margin cannot bite. It starts costing at about 30 mg/L makeup silica (0.42 cycles) and is enforced regardless, because whether it binds is a property of the customer's water, not of ours. **The real fix is the guard** — `test_no_constraint_is_computed_without_being_applied` names every constraint and the file that must call it |

| 49 | **The discharge ceiling was computed, covered by its own test file, and called by nothing outside it** | `discharge.binding_ceiling()` returns the lower of the scaling ceiling and the discharge permit — exactly the number a controller may use — and `grep` finds it called only from `tests/test_discharge.py`. **Seventh instance of computed-but-not-enforced** (11, 26, 31, 37, 43, 45), and the one that most directly misleads a customer: the Cycle Ceiling Report answered **4.52 cycles** while a tested discharge ceiling of **3.33** — the nitrate *daily maximum*, which defect 69 later showed is not the operative column — sat unused. You cannot recommend an operating point whose blowdown is illegal. The binding parameter is **nitrate** — not a scaling species, and therefore invisible to every index in the chemistry engine | **Fixed** — 12 Sep 2026. The report computes both bases, prints them, and renders a BINDS FIRST row. **Reported, not imposed**, and that distinction is the whole of the care needed: RCER-2015 binds Jubail and Yanbu, and the water this report defaults to is a **Riyadh** refinery, in neither — so `applies_here` is `None` and the test asserts it stays `None`. Claiming an illegal operating point for a site outside the jurisdiction would be its own defect. The row names the alternative tables (sewer, irrigation) and tells the reader to check their permit |

| 48 | **The annual study reported how much of the year is extrapolated, and never what the extrapolation is worth** *(every figure in this row was superseded by defect 60; it is left as written, because this is the record of what the study said at the time)* | It correctly recorded that **37.5 % of a Dhahran year** is hotter and wetter than the Almeria calibration data, and treated that as the caveat. Splitting the headline figures by envelope shows the caveat was the smaller half of the story: **the water saving is −3.31 % INSIDE the validated envelope and +8.23 % outside it.** The entire positive annual water figure of +2.37 % is carried by the **3,285 hours the model has never been checked at**. Energy is the exact reverse — **+8.84 % inside, −0.39 % outside**. The two halves of the product are validated to opposite degrees, and the water claim is the one this dataset cannot defend | **Fixed** — 12 Sep 2026. `annual.py` splits every headline by envelope, prints the table and the sign reversal in plain words, and writes `by_envelope` plus an `envelope_warning` into `results/annual_dhahran.json` so the split travels to anything that reads the file. The regression test pins the **signs**, not the values, so a re-run that moves the numbers still catches a reversal. **No number was changed** — the annual figures are exactly what they were; what changed is that the deck can no longer quote the water saving without the split |

| 47 | **Every saturation index rested on an assumed composition that nothing ever checked** | Makeup analysis × cycles, and no test of that assumption after the sample date. The package's own documents recorded it as the largest weakness: *"no water has ever been in front of an instrument."* A costed sensor survey shows why it stayed open — measuring silica, calcium, alkalinity and phosphate online is **$120,000–185,000 per tower** against an **$89,000/yr** saving on a 4.2 MW tower. **The instruments cost more than the thing they optimise**, which is structural and is why nobody sells this | **Fixed** — 12 Sep 2026, and for nothing. Specific conductance is a known function of composition (McCleskey et al. 2012, validated 30–70,000 µS/cm, I = 0.0004–0.7 mol/kg — our whole range), and the sensor is **already on the skid** because the cycles calculation needs it. `src/conductivity.py` computes what the assumed composition implies and returns the **USGS specific-conductance imbalance** against what the sensor reads. It does **not** measure ions — one conductivity and one pH are two equations against eight unknowns — but the **direction of the residual is diagnostic**: precipitation removes ions, measured conductance falls below prediction, SCI goes positive. The controller's job becomes *hold the residual near zero*. Implemented as Kohlrausch + an Onsager-type correction, **not** McCleskey's per-species fits, which we did not transcribe and will not invent; `validate_against()` reports the error instead of asserting a tolerance |

| 45 | **The sharpest test the controller has was computed by the report, the figures and the MATLAB export — and by nothing that binds** | `chemistry.ph_saturation_brucite` has existed since gate V6, whose own docstring calls the brucite envelope *"the sharpest test the controller faces, because it requires all three things the architecture provides and that no incumbent combines"* — skin temperature, bulk pH, and acid as the actuator. The **optimiser's feasibility check called neither it nor `si_sepiolite`**, and `si_sepiolite` was called from nowhere at all — though that half is **deliberate and documented**: a note beside it records sepiolite as rejected for a real-time controller, because crystalline silicates are kinetically inhibited over a condenser residence time and the index chronically over-predicts. The defect is the unenforced **brucite** criterion, not the unused sepiolite one. Sixth instance of computed-but-not-enforced (11, 26, 31, 37, 43). The register also carried *"Mg-silicate SI threshold unknown"* as an open gap — **it was never the blocker**: the mechanism is two-step, brucite precipitates first and then reacts with silica in the boundary layer, so the criterion is on **brucite**, and a sepiolite index is a state rather than a criterion | **Fixed** — 11 Sep 2026. Enforced in `_evaluate_point` as `pH_bulk > pH_s(brucite at SKIN)`, with `MG_SILICATE_BRUCITE_MARGIN_PH = 0.0` — the thermodynamic criterion with **no invented safety factor**, injectable so a site with coupon evidence can pass its own. Checked against field observation **before** switching it on, which is the discipline defect 29 cost us: safe on both measured Aramco waters at 3–5 cycles and 40/44.5 °C skin, biting only at 50 °C on the higher-magnesium water. It excludes 6 of 20 points in a cycles × pH grid on the V6 water, so it binds without collapsing the ceiling |

| 43 | **Hours the plant failed to solve were dropped before averaging, and in a cold climate those are the worst hours** | `run_region` averages over `solved` hours and scales to a day with `* 24 / n`. On the Frankfurt profile **four hours of twenty-four fail to solve at all** — and they are hours 2, 3, 7 and 8, the coldest of the night, which are exactly where the silica floor is hardest to hold. So the region with the most trouble reported the least of it: every per-day figure for Europe is computed from the twenty hours that behaved and scaled up as if the other four looked the same. Same family as defect 42 — a failure removed from the record rather than reported | **Fixed** — 11 Sep 2026. The table carries a **solved h** column, prints an explicit SHORT line naming any region below 24, and the JSON carries `hours_unsolved` and `averages_biased_optimistic` so the bias travels with the data to any consumer of the file. The averaging itself is unchanged: scaling from the hours that solved is the right normalisation, it just has to say so |

| 42 | **The "chemically bounded" policy returned points below its own floor, and a solver failure was read as a measurement** | Two faults in `hybrid_supervisor.fan_for_target_fws`. **(i)** The silica floor is a *minimum* temperature — water at or above it is safe — but the bracket kept the **coldest** point at or below target and returned that, i.e. the wrong side of its own constraint, by about 0.02 K in ordinary conditions. **(ii)** When the tower solver failed to converge it did `lo_pct = mid`, reading a **failure** as the datum *"this fan speed is too warm"* and bisecting upward from it. On the Frankfurt profile the solver does not converge below ~30 % fan in cold humid air, so the low-fan region was discarded one failure at a time and the search settled on 32.3 % fan and **27.4 °C against a 31.8 °C floor — 4.4 K below, silently, for ten hours of twenty-four**, reported as compliance. The physics underneath is real and is the finding for cold climates: **fan turndown alone cannot keep a tower's water warm enough in cold air.** A site that needs the floor there needs a tower **bypass**, not a better setpoint | **Fixed** — 11 Sep 2026. The inversion brackets the crossing and returns the **warm** side, landing 0.009–0.065 K above the floor where it is reachable; a solver failure **truncates** the search instead of steering it and sets `low_fan_unexplorable`; and the state carries `target_met` / `target_shortfall_k`, which `evaluate()` turns into `floor_unreachable` and the four-region table into a **no-floor h** column. The unreachable hours are now a reported product requirement rather than a hidden violation |

| 41 | **The cross-document defect-count check disabled itself at defect 31 and skipped silently for ten defects** | `test_every_document_agrees_on_how_many_defects_were_found` spells numbers from a hardcoded `WORDS` table that stopped at **"thirty"**. From defect 31 onward no document's claim parsed, the test found nothing to compare, and it **skipped** — with the message *"no defect-count claims found to compare"*, which reads like an absence of claims rather than a parser out of vocabulary. The guard switched itself off at exactly the moment the number it guards started moving, and the count was hand-synced across five documents unchecked for ten defects. Same shape as defect 12 and as the register's own note on second-order staleness | **Fixed** — 11 Sep 2026. `WORDS` is now generated to one hundred, and the skip path first asserts that `docs/defect_register.md` does **not** state a count it failed to parse — so a parser that runs out of vocabulary fails instead of skipping. Found while syncing the count for defect 40; the suite went from 179 passed / 1 skipped to 180 passed |

| 40 | **The four-region artifact counted the solver's own tolerance as scaling** | The bounded controller drives the silica index **to** its limit, so it lands on whichever side the root-finder stops at — about 10⁻⁵ to 10⁻⁴ log units above zero. Counting violations with a strict `SI > 0` therefore reported **24 violating hours out of 24, identical to the blind case**, when blind was exceeding by 10⁻² to 10⁻¹. The headline table said the controller was no better than no controller. SI is a **log** scale and that is the whole point: SI = 10⁻⁴ is a saturation ratio of **1.0002**; SI = 0.119 is **1.32**, i.e. 32 % supersaturated. One deposits solid, the other is not measurable. The error ran in the **pessimistic** direction, which is the safer one, but the number was still wrong | **Fixed** — 11 Sep 2026. Both counts are reported: every hour strictly over the line, and every hour over it by more than the solver can resolve (`SI_SOLVER_TOL = 1e-3`, SR 1.002, below any field measurement). The headline column is now the peak **saturation ratio**, which is what an operator can check against a coupon, rather than a log index. Control semantics untouched — `chemistry_at()` still treats any exceedance as infeasible, which is the conservative side for a controller and the wrong side only for a report |

| 39 | **The Ceiling Report printed a confident headline while its own analysis check had failed** | The report defaults to the measured Aramco Riyadh assay, and that assay **fails its own charge-balance check at −5.25 % against a ±5 % tolerance**. The console line said `ceiling 4.52 cycles, bound by SI_calcite` and nothing else; the failed check was visible only in the HTML further down. The console line is what gets pasted into a deck, and the deck does not carry the caveat. This is the report's own stated discipline — *"it will not report a ceiling as a single number when the analysis does not support one"* — applied to silica but not to charge balance | **Fixed** — 11 Sep 2026. The console prints `ANALYSIS CHECK FAILED` first, and `sidestream.charge_closure_bracket()` answers the question the caveat raises: the balance is closed **both ways**, once with Na⁺ and once by removing Cl⁻, and the spread is reported. On this assay it is **4.50 to 4.53 cycles, 0.7 % — immaterial**, because the ceiling is set by calcite and neither ion is in the calcite ion product. The deficit of 0.806 meq/kg closes with **11.3 mg/L NH₄⁺ as N**, which is what a *secondary* effluent carries and which this model has no species for — so the assay is most likely **incomplete rather than wrong**. That is an explanation, not a licence: no ion was added to the water |

| 38 | **The silica index has no pH term, and is silently wrong above pH 9** | `SI_silica_am` is `log10(total SiO2) − logK(T)` with no pH dependence at all. That is CORRECT below about pH 9, where dissolved silica is essentially all neutral H₄SiO₄ — and it is the basis of the claim, made throughout this package, that acid cannot buy cycles against silica. Above pH 9 H₄SiO₄ deprotonates to H₃SiO₄⁻ and solubility rises steeply. **A high-pH programme is the standard commercial answer to a silica ceiling** — Aquatech's HERO process runs the loop alkaline and reports silica **above 1,600 ppm in the reject**, where this model puts saturation at 129.5 mg/L on a 30 °C basin -- a factor of 12. The engine returned a number for that regime and said nothing. | **Fixed** — 11 Sep 2026. `silica_index_valid_at_ph()` guards it; `saturation_state` returns `silica_index_valid` and `saturation_state_split` carries it through from the COLD evaluation point, which is where silica is judged. Deliberately kept out of the `SI_` namespace, because `scripts/ceiling_report.py` selects on that prefix and would have formatted a bool as a saturation index. Evidence in `docs/chemistry_evidence.md` S4.3. The index is unchanged inside its range; what changed is that the range is now declared. Found by searching the Wayback PDF index for cooling-tower silica operating experience |

| 37 | **The diurnal silica margin was computed, validated against an independent simulation, and enforced by nothing** | `chemistry.diurnal_silica_margin()` returns the discount the silica ceiling needs against a daily basin temperature swing -- 10.5 % at 30 °C ± 5 K -- and agrees with `modelica/TowerSilicaDynamics.mo` to better than half a percentage point. **No limit set used it.** The optimiser pushed cycles against the undiscounted ceiling, which the simulation shows is supersaturated for 11.8 hours of every 24. Fourth instance of one pattern: a quantity calculated, printed, and never wired into the constraint (defects 11, 26, 31). | **Fixed** -- 11 Sep 2026. `limits_with_diurnal_margin()` applies it, and `test_defect_37_the_diurnal_margin_is_enforced_not_merely_reported` holds it there |

| 36 | **The side-stream break-even was never compared to what treatment actually costs** | `sidestream.py` returned a break-even -- the price per m3 at which a treatment pays for itself on avoided water and chemicals -- and nothing checked it against a real costed system. A costed engineering study (DiFilippo, Sylvan Source, Oct 2023: coal plant, 1 MGD blowdown, budgetary equipment costs with installation factors) gives, for a precipitation softener + media filtration + WAC train: **$25,440,000 installed and $2,793,000/yr in chemicals for 1.38 Mm3/yr**, i.e. **$2.02/m3 in chemicals alone** and $2.94/m3 with capital amortised over twenty years. Against break-evens of $0.24-0.58/m3 on Gulf tariffs, **every technology in the module is 5 to 12 times underwater**. The module was recommending capital that cannot pay back on water value, and the Ceiling Report was printing those recommendations to a customer. | **Fixed** -- 11 Sep 2026. `REAL_COST_BENCHMARK` and `passes_cost_reality_check()` added; the Ceiling Report now prints the shortfall instead of the recommendation. The same study also supplies a measured silica removal of **89.8 %** (176 -> 18 mg/L) to replace an assumed figure |

| 35 | **The ceiling was reported as an operating limit when it is only a scaling limit** | AlMajnouni & Jaffer (Saudi Aramco, NACE Paper 577) conclude of the Riyadh Refinery TSE analysis: *"the cycles of concentration should be limited to 4 at a maximum pH of 8.0."* The engine returns **6.56 cycles** at pH 8.0 on that exact water, binding calcite. Their 4 carries margin the model does not: process leaks of amines and hydrocarbons, a named inhibitor programme, and a corrosion objective alongside the scaling one. But **being more permissive than the plant operator is the direction that scales a condenser**, and the `SI_calcite` limit of 2.0 (saturation ratio 100) is the most likely place the difference sits. | **Fixed** -- 11 Sep 2026, resolved as a CATEGORY DIFFERENCE rather than a numerical error. Working back from Aramco's own figure: at 4 cycles and pH 8.0 the engine puts that water at calcite SR 42.5 (SI 1.63), so their practical tolerance is SI 1.6-1.7 against a PUBLISHED INHIBITED BAND of SR 135-150 (SI 2.13-2.18). They operate three times more conservatively than the inhibitor chemistry requires, and their own paper says why -- *"process leaks consisting of amines and hydrocarbons prevented an increase in cycles of concentration **due to increased turbidity**"*, plus corrosion as a competing objective and no acid by design. **The engine computes a SCALING ceiling; they set an OPERATING ceiling, which is the minimum over six constraints this model does not compute.** Fixed by relabelling the output and adding `CONSTRAINTS_NOT_MODELLED` and `scaling_ceiling_caveat()`, not by moving a thermodynamic limit to match one site's housekeeping |

| 34 | **Every headline number was a point estimate, and the instrument producing them fails its own gate** | Gate V7 cleared a 15.00 % threshold at **15.01 %** and was reported as a pass. A 0.01-point margin means something only if the error is smaller than 0.01 points, and **nothing in the package had ever computed the error on a water result**. Meanwhile gate V2 scores the evaporation model at 9.90 % MAPE against an 8 % threshold and FAILS — 10.80 % since defect 51 de-duplicated the holdout — and makeup water is computed from evaporation, so every water number inherits that. Diagnosed by decomposing the residual per campaign as `rel = a + k·fan`: the **offset** `a` varies −14.6 to +9.1 pp and **cancels** in a ratio, but the **slope** `k` runs −0.366 to +0.187 %/fan% and does **not**, because baseline and optimised run at different fan speeds. Its sign is not even consistent between campaigns, so it cannot be corrected — only propagated. | **Fixed** — 11 Sep 2026. `scripts/gate_uncertainty.py` propagates the measured residual structure. **V7 = 15.01 %, 95 % interval 1.0 to 22.8, P(true ≥ 15 %) = 0.41. V5 = 4.38 %, interval −11.2 to +13.1** — which includes the optimiser using *more* water than the baseline. Held by `tests/test_gate_uncertainty.py`, which recomputes the error model from the raw dataset rather than trusting typed constants |

| 33 | **Every ceiling in the package was a saturation limit, and the operator's real ceiling is often the discharge permit** | The engine computed how far a water could be concentrated before a mineral precipitated, and nothing else. Blowdown has to go somewhere and where it goes has a consent. **The controller could therefore recommend an operating point that breaches the permit, and would have reported it as optimal.** Measured on the validated makeup analysis against RCER-2015 (Royal Commission for Jubail and Yanbu): the scaling ceiling is **5.02 cycles**, the Table 3C discharge ceiling is **1.00 cycles** — the permit binds **five times harder than the chemistry**, and the makeup water breaches total phosphorus *before it is concentrated at all* (8 mg/L PO₄ = **2.61 mg/L as P** against a 2.0 maximum and a 1.0 monthly average). Found while reading RCER-2015 after the acid-ban clause turned up. | **Fixed** — 11 Sep 2026. `src/discharge.py` carries RCER Table 3C and Table 3B (Jubail), and `binding_ceiling()` returns `min(scaling, discharge)` with the binding parameter named. Both ceilings are always reported; neither is discarded. Held by `tests/test_discharge.py` |

| 32 | **The DOE benchmark ran on the wrong recipe table, and it was the easier one** | `DOE_SYN_MWW_NF_COC4` was transcribed from **Table 2.3.2** (p. 2-14), the general chapter 2/3 synthetic recipe. The heated-surface experiment this package benchmarks against — the one that produced the hydroxyapatite XRD result — is in **chapter 4**, and chapter 4 has its own recipe, **Table 4.2.1** (p. 4-13). They differ where it matters most: **HCO₃ 0.40 vs 1.60 mM, four times the alkalinity**, and Na 8.60 vs 9.80 mM. The wrong table understates carbonate saturation on precisely the water the benchmark claims calcite is undersaturated in, so **the benchmark was passing partly for the wrong reason**. Found by an external agent's review of the source, not by us. | **Fixed** — 11 Sep 2026. Corrected to Table 4.2.1; the 2.3.2 recipe is retained as `DOE_SYN_MWW_NF_COC4_TABLE_2_3_2` so the two can be compared and neither can be re-imported by accident. `test_the_two_doe_recipes_are_not_interchangeable` pins the difference. **The claim it cost us is recorded below** |

| 31 | **The thermal solver's cache key omitted the water composition and the fill law** | `_thermal_solve` keyed its memo on `(fan_pct, cycles, cond items)` only — while the body computes the water activity from `makeup_water.concentrate(cycles).tds()` and passes `fill_c`/`fill_n` into the outlet-temperature solve. **Two different waters at the same fan and cycles therefore shared one thermal solution.** It never bit, because `run_controller.py` runs a single water and nothing sweeps composition through this function. It would have bitten on the **very next study planned** — the silica crossover sweep, whose entire method is to vary SiO₂, and hence TDS and water activity, at fixed fan and cycles. Same class as defects 11 and 26: a quantity computed, understood, and enforced by nothing. The comment above the key already worried about the smaller `id(cond)` hole and said *"it has not been observed to bite, which is exactly why it should not be left in"* — and then left the larger hole open. | **Fixed** — 10 Sep 2026. The key now includes TDS, SiO₂, PO₄ and both fill coefficients |

### The 17 September round, in number order

Six branches were worked in parallel on 17 September 2026 and each staged its
rows rather than editing this table, to avoid conflicts. They are integrated
here on 18 September. The state cell of every row below begins with the verdict
token — `**Fixed**` or `**OPEN**` — and whatever follows it qualifies that
verdict rather than replacing it. **Numbers 59 and 62 are not in this table**,
and the reason for each is written out under the table so that neither reads as
a silent gap.

| # | Defect | How it showed up | State |
|---|---|---|---|
| 51 | **The Almería calibration data counted 18 measurements twice, and the holdout contained a training row** | `dataset.load_all()` concatenated `Exp1.nc`, `Exp2.nc` and `Exp3.nc` into **165** rows, of which only **147** are distinct across the seven measured channels. All 17 rows of `Exp3.nc` are exact copies of `Exp1.nc` rows 0–16, in order — the dataset's own README describes Exp3 as a *different* full-factorial campaign, so the file does not contain that campaign — and Exp1 row 16 is also Exp2 row 113. The 50-row V1/V2 holdout was **33 distinct rows**, one of which the fill law had been trained on. V1 heat rejection had "passed" at **5.94 %** against 6.00 % on it. Found by an independent review and confirmed here from the files. The same duplication sits under every per-campaign analysis that treats Exp3 as a campaign | **Fixed** — 17 Sep 2026, re-scored exactly as pre-registered in `docs/staged/almeria_dedup_preregistration.md`, which was committed first. `load_all()` de-duplicates and records campaign membership; `split_holdout()` cannot hold out a training row; training is unchanged (115 Exp2 rows, fill law identical to 1e-12); the holdout falls **50 → 32** rows. No threshold moved: V1 outlet MAE **0.542 → 0.600 K, still PASS**; V1 heat rejection **5.94 % PASS → 6.27 % FAIL**; V2 evaporation **9.90 % → 10.80 %, FAIL either way**. Leave-one-campaign-out is reported as a diagnostic that cannot change a verdict. Held by `tests/test_dataset_dedup.py` |
| 52 | **The README's results table reported a failed gate as passed, and no guard read the README** | `README.md` — the front page of the public repository — said *V2 evaporation vs measured water loss ≤ 8.00 % \| 7.11 % \| PASS* while `results/calibration.json` held **9.90 %, FAIL**; the V5 cost (5.60 %), V5 water (10.04 %), V3 (15.6 %) and V5b rows were stale too. `7.11 %` is on the audit's own list of superseded figures, but `src/audit.py` section 5 scanned only `docs/*.md`, `docs/*.txt` and `HANDOFF.md`, section 6 checked claims only in `poc_report.md`, and `tests/test_artefact_consistency.py` compared no README row with an artefact. The same shape as defect 13: a guard whose glob stopped short of the document with the widest audience. Found in passing: section 6's `"9.90 %"` literal would have **demanded the superseded V2 figure** once defect 51 moved it, which is defect 12 again, and the variable `v2` is rebound to a `Path` in section 4c | **Fixed** — README rows rewritten from `calibrate.py` and `run_controller.py` output. `README.md` is in the section 5 scan; a new section 6b checks every README gate row's number and verdict against the artefacts; the `9.90 %` literal is replaced by the artefact value with a recomputed verdict. Both guards were shown non-vacuous by running them against the old README — the audit raised 8, the new test failed. `CITATION.cff`'s "Four pass and two fail" is now three and three |
| 53 | **"Benchmarked against PHREEQC 3.9.0" rested on one composition, and the registered multi-composition benchmark fails** | The engine's only comparison with PHREEQC was the USGS gypsum-saturation example: one water, 25 °C, one mineral, −0.0163. Pre-registered grid (`docs/staged/phreeqc_benchmark_preregistration.md`, committed before it was run): 4 waters × cycles 1–8 × 25/35/45/55 °C, identical mol/kgw totals, fixed pH, no charge adjustment in either code, calcite/gypsum/SiO₂(a)/hydroxyapatite. **398 of 416** gated indices, 95.7 %, fall within tolerance — but **calcite is 114 of 128, 89.1 %**, against a 90 % per-mineral bar. All 18 failures sit at I ≤ 0.1 and 45–55 °C; worst calcite −0.098. Inputs were checked first: totals round-trip to 1e-7 and ionic strength agrees within 5 %. At the worst point, −0.041 comes from Davies against Truesdell–Jones activity coefficients, −0.033 from a calcite constant transcribed from an **earlier phreeqc.dat** than 3.9.0 ships, −0.006 from complexation. Gypsum at 55 °C passes largely by cancellation. Hydroxyapatite passes at 4× tolerance and only 39.8 % within the unscaled one | **OPEN** as a result; the wording is fixed. The claim is replaced by the measured statement in the deck, the external handoff, the PoC report generator, `brand.py`, `ceiling_report.py`, `chemistry.py`'s module docstring and the README. `tests/test_phreeqc_grid.py` compares the live engine against the stored PHREEQC output: the criterion is `xfail(strict=True)` against this row, and a non-xfail test pins the shares and where the failures sit. **Whether to move the engine's constants and activity model to 3.9.0 is a physics decision and it is left open**, not closed by wording |
| 54 | **The saturation state the optimiser enforces left out the sulfate its own acid dose adds** | `evaluate_operating_point` and `_cost_at_ph` evaluated every index on `makeup_water.concentrate(cycles)`, so the circulating water carried makeup sulfate × C and nothing from the acid. Sulfuric acid leaves one mole of sulfate per mole dosed. `corrosion.acid_driven_index` already modelled this for Larson–Skold and UFC 3-230-13 §5-2.1.2.2 names the mechanism, but the gypsum index never got it. On the field-validated makeup at 30 °C the acid adds **386.5 mg/L at 5 cycles, pH 8.0**, and **469.1 at 6**, so `SI_gypsum` ran too low by **0.0815** at 5 cycles and 30 °C. The error is non-conservative: it runs in the direction that scales a condenser. It also hid sulfate from `src/concrete.py`, where ACI S2 is reached at **3.99** cycles with acid against 5.00 without | **Fixed** — 17 Sep 2026. `controller.acid_sulfate_mg_l` and `controller.circulating_with_acid` put the acid's sulfate into the circulating composition at the steady-state balance, `s = dose × MW_SO4 / MW_H2SO4`, in which the flows cancel because the dose is charged against blowdown + drift (defect 25) and the sulfate leaves in that same stream. `evaluate_operating_point` and `_cost_at_ph` now evaluate **every** index on it: the saturation split, the Davies validity check, the brucite criterion and the calcite corrosion floor. The staged magnitudes were reproduced exactly before the fix. **V5 and V7 are byte-identical afterwards** (V5 4.38 % water FAIL, 3.91 % cost PASS, 0 violations; V7 15.01 % / 8.54 %), because on this water gypsum is nowhere near binding and the extra sulfate slightly relaxes calcite, SI_calcite **1.5428 → 1.5212** at 5 cycles and 30 °C. On the measured Riyadh water the acid adds **645.11 mg/L** at 5 cycles and SI_gypsum moves +0.0970. **Still not modelled, and conservative:** the acid also destroys alkalinity while the circulating water still carries C × makeup alkalinity, which overstates calcite. Held by two tests in `tests/test_defect_regressions.py` |
| 55 | **The engine's pH closure had no lower validity limit and returned a negative pH once alkalinity ran out** | `chemistry.ph_atmospheric_equilibrium` computed `[H+] = K1·KH·pCO2 / [HCO3-]` with bicarbonate clamped at 1e-12, so at zero alkalinity it returned **pH −0.75**. That formula is correct only while bicarbonate carries the alkalinity. It cannot represent excess strong acid, which is exactly the regime an acid-overdose incident enters, and nothing warned the caller. Any safety simulation built on it would have reported nonsense past the equivalence point | **Fixed** — 17 Sep 2026, inside `chemistry.py`. The open-system balance keeps the free proton, `h = 2K/(A + sqrt(A² + 4K))`, reproduces the old expression to within h²/K, and tends to CO₂-saturated water as alkalinity goes to zero: **pH −0.75 → 5.627** on the field water at zero alkalinity, against `safety_sim.ph_from_alkalinity`'s 5.62. Across every `Water` constant, cycles 1–10 and 20–50 °C, the change moves the returned pH by at most **2.1e-06**, so nothing downstream moves. Negative alkalinity now raises `ValueError` naming `safety_sim.ph_from_alkalinity`, because past the equivalence point this closure has no answer. `tests/test_safety.py` pinned `pH < 0` and is updated |
| 56 | **The specified fail-safe, blowdown to 3.0 cycles on any trip, drains the basin faster during the one incident the interlocks exist for** | Moving the cycles setpoint to 3.0 is right for a chemistry trip and wrong when makeup is lost. A conductivity bleed sees the loop above its new setpoint and opens, discarding water that cannot be replaced. In the pre-registered incident the basin reached the low-level pump trip at **90.8 min** with interlocks against **101.1 min** with none: the protection layer shortened the time to losing circulation. It was specified that way before anyone ran it, and the simulation found it | **OPEN**, mitigated behind a flag that is off by default. `InterlockConfig.hold_blowdown_on_makeup_loss` holds the bleed closed while makeup is unproven and low level then comes at **158.6 min**; it was **not** pre-registered, so it is off by default and the fault matrix still tests what was registered. Held by `test_registered_failsafe_empties_the_basin_sooner_on_makeup_loss` and `test_holding_blowdown_on_makeup_loss_keeps_the_inventory_longer`. Whether it becomes the default is an engineering decision for whoever owns the specification, and until that decision is taken the registered fail-safe is the one that ships |
| 57 | **Brucite saturation pH paired a hydroxide-form log K with a proton-form enthalpy** | `ph_saturation_brucite` used `_vant_hoff(-11.18, -27.1, T)`. −11.18 is the log K of `Mg(OH)2 = Mg²⁺ + 2 OH⁻`, but −27.1 kcal is the enthalpy of the proton form, `Mg(OH)2 + 2 H⁺ = Mg²⁺ + 2 H₂O` (wateq4f.dat). The two agree at 25 °C, so only a temperature sweep sees it, and the function then adds Kw's temperature dependence on top, counting the effect almost twice. At the V5 Dhahran summer skin, 44.85 °C, pH_s reads **8.714** where the consistent constant gives **9.337**. The criterion is enforced by `controller._cost_at_ph` (defect 45), so the optimiser was rejecting every pH above 8.714 at a hot skin | **Fixed** — the hydroxide-form enthalpy is −27.1 + 2 × 13.362 = **−0.376 kcal**, with log K(25 °C) unchanged. Supplementary pre-registration in `docs/staged/phreeqc_brucite_supplement_preregistration.md`, committed before the run; phreeqc.dat has no Brucite phase, so PHREEQC ran with wateq4f.dat from the same installer. Before: **0 of 96** temperature shifts within 0.05 pH, median Δ −0.321 / −0.623 / −0.907 pH at 35 / 45 / 55 °C. After: **96 of 96**, medians −0.004 / −0.007 / −0.012. `results/mg_silicate_envelope.json` re-run: skin saturation pH **8.92 → 9.33** at 38 °C, **8.45 → 9.09** at 46 °C, **8.22 → 8.98** at 50 °C, so 38–46 °C move from depositing or straddling to safe across the 8.5–9.0 band. V5/V7 re-run unchanged. Applied to the MATLAB twin `matlab/+mizan/ph_sat_brucite.m`, which returns **9.9520 at 25 °C and 9.3338 at 45 °C** against the Python engine's 9.9503 and 9.3320. **Not regenerated:** `matlab/cases` and `results/matlab_simulink.json`, which still carry the old constant, and the prose quoting the old limits. Absolute pH_sat still sits 0.06–0.19 below PHREEQC because the function uses total Mg and an unspeciated ionic strength; that is reported, not gated. Held by `tests/test_phreeqc_grid.py` |
| 58 | **The repository carries two incompatible magnesium–silica rules, and chose a unit basis by fit** | The rule appears twice. `src/chemistry.py`, above `MG_SILICA_LIMITS`, has a sum rule `Mg + SiO₂ ≤ 17 000` for pH > 7.5 with Mg taken as Mg²⁺. `docs/chemistry_evidence.md` §4.2, transcribing Demadis (2003), has "SiO₂ < 100 ppm **and** Mg × SiO₂ < 20,000", "where Mg is expressed as ppm CaCO₃". A sum of 17,000 and a product of 20,000 plus a silica cap are different rules, and they state the magnesium basis differently. `chemistry.py` states its reason for choosing Mg²⁺: *"Since plants demonstrably operate at 3.5-5.0 cycles on this water, the Mg-as-Mg2+ convention is the one consistent with reality"* — a unit convention selected because it agrees with observation, which is fitting. On the rule's stated CaCO₃ basis, P3 caps the Dhahran water at **2.10** cycles, below the 3.5 its pilot ran clean; on the Mg²⁺ basis, variants at 20,000–25,000 land within 0.5 cycles of Mizan's ceiling on that water, while on the Riyadh water it is the CaCO₃ basis that lands within 0.5 | **OPEN**. `max_cycles_mg_silicate` is enforced nowhere, because brucite replaced it at defect 45, so no shipped ceiling is wrong because of this. The defect is in the evidence base any novelty argument against rules of thumb has to cite. What closes it: retrieve the Demadis (2003) figure, record its basis and its pH > 7.5 form once, and carry the other variant only as a labelled sensitivity |
| 60 | **The envelope split classified whole wet-bulb bins by their centroid, so 266 unvalidated hours were booked as validated** | `annual.py` split the year into eight equal-hour bins of 1,095 h and marked a whole bin *inside* when its **centroid** wet bulb was ≤ 21.9 °C. Bin 4 had a centroid of 21.38 °C and **266 of its 1,095 hours were above 21.9 °C**. So defect 48's split reported **3,285 extrapolated hours, 37.5 %** — a bin count — where the weather file holds **3,551, 40.5 %**, hour by hour. Those 266 hours' savings were booked to the validated side. `tmy_dhahran.json` had carried the correct 3,551 all along, so two artefacts disagreed about one quantity and nothing compared them. Found by an independent weather cross-check on 16–17 Sep 2026 | **Fixed** — 17 Sep 2026. `annual.envelope_bins()` bins the inside hours and the extrapolated hours **separately**; the eight bins are shared 5/3 by hours, every bin is pure, and the run asserts purity. The split now equals the weather file's own counts, **5,209 / 3,551 h**. The printed conclusion and `envelope_warning` are derived from the signs instead of typed, and the artefact records the SHA-256 of the hourly array it was computed from. Every annual figure moved — the table below is the supersession record. The whole-year numbers moved too although no weather changed, because moving the bin edges moves the centroids the controller runs at; that bin-resolution error is worth about a point of annual water saving. **The same centroid rule survives in `src/annual_datacentre.py`** as a per-bin flag no aggregate reads; it was left there because `src/cdu_hybrid.py`'s frozen pre-registered experiment rebuilds those bins by the old rule. Held by `tests/test_weather_envelope.py` |
| 61 | **`tmy.py` read the EPW time-zone field as the station elevation** | The EPW `LOCATION` record is `…,lat,lon,TZ,elevation`. `tmy.py` took field 8 — the time zone, +3.0 — as the elevation, so `tmy_dhahran.json` and the module docstring said **3 m**. Dhahran 404160 is at **25.6 m**. The cross-check noticed it while using "3 m" to bound a sea-level-pressure correction, so the wrong fact had already propagated one step | **Fixed** — 17 Sep 2026. `tmy.parse_location()` reads the record by field name, refuses a record with fewer than ten fields, and records `timezone_h`. **No number changed**: nothing read the elevation and every psychrometric call uses the EPW pressure column. Re-running `tmy.py` left `tmy_hourly.npy` byte-identical (SHA-256 `57efd6ea…4a04c0`) and every other value in `tmy_dhahran.json` unchanged. Held by `tests/test_weather_envelope.py` |
| 63 | **The data-centre PUE and most of the "cost of bounding" come from an uncapped cubic pump law extrapolated far past a 42 °C cold-plate return budget, with no trim cooling** | `hybrid_supervisor.required_secondary_flow` raises secondary flow without limit to hold the TCS return at `COLD_PLATE_RETURN_MAX_C = 42`, and `pump_power_kw` scales it by the cube. At 5 K approach and 10 K design rise the warmest facility water this allows at design flow is **27.0 °C**; Dhahran's design day never gets below **30.34 °C**, so **all 24 blind hours run above 1.5× design flow** and hours 10–11 need **10.9–11.4×**, which is **233–265 MW** of secondary pumping for a 9 MW hall and an hourly PUE of 26.9–30.5. That is the whole cause of the deck's **PUE 3.537**: excluding hours above 3× flow gives **1.148**. In Frankfurt, **$7.55M of the $9.77M/yr** comes from two hours at **4.95×** flow, 48 MW each. The same law sent a primary plate wall to **111.9 °C** in B1 and, in the joint study, let B2 select a Dhahran state at **18.1×** flow with a **325 °C** wall, which the chemistry engine accepted because nothing checks its temperature validity; in the harness's first attempt a candidate's speciation went complex and crashed the run. At the GPU OEM's published operating point, 45 °C in and about 55 °C out, every flow ratio is **1.00** and PUE is **1.035–1.049** in all four regions | **OPEN**. Two remedies are needed and neither is applied: a sourced return limit, and a flow cap that marks hours needing trim cooling as infeasible rather than pricing them. No pump run-out source is held, and the return limit is a modelling decision rather than a typo. `evaluate` should also refuse a plate-wall temperature outside the chemistry engine's validated range |
| 64 | **The deck priced chemistry-awareness at a fixed 5 cycles, and annualised one design day × 365** | The supervisor's own documentation, `docs/water_modes_and_free_cooling_floor.md` §2, says the correct response to the floor is to lower cycles, not to raise flow. `generate_pitch_artifacts.py` holds cycles at 5 anyway and then multiplies a single 24-hour design day by 365 — Dhahran's highest-mean-wet-bulb TMYx day, and sinusoids for the other three regions. That is defect 20's shape in a new place. Under the pre-registered joint policy (B2: cycles 2–10 plus a fan-grid point) the cost of bounding is **≤ 50 % of B1's in 3 of 4 regions, so H-B2 PASSES**: Loudoun **+$1,601,383 → +$30,234**, Frankfurt **+$9,769,622 → −$93,515**, Balloki **+$533,603 → −$21,483**, at **+4.68 / +4.19 / +3.69 %** makeup against blind. Dhahran does **not** support it, **+$106,579 → +$21,705,498**, entirely through defect 63. The fan-only decomposition B1f equals B1 in all four regions, so the whole advantage comes from choosing cycles | **OPEN**. The dollar claim is withdrawn from the deck rather than restated, because the recomputation belongs in `generate_pitch_artifacts.py`, which this round did not touch. The joint-policy run is stored at `results/cdu_joint_policy_20260917/` with its pre-registration and input hashes |
| 65 | **"316 pits at 1.85 cycles; CDU plate packs are routinely 316" conflates two loops, two waters, and a guidance screen with a measured onset** | **Loops.** The CDU heat exchanger separates the facility water from the technology cooling system, and the TCS is a closed loop that never carries tower water; the facility water reaches heat rejection directly or through a tower-isolation exchanger. So tower water wets a CDU plate **only** where the facility loop is open to the tower. `hybrid_supervisor` assumes exactly that — "the tower outlet IS the facility supply" — and never says so. **Waters.** 1.85 = 400 mg/L ÷ **216** mg/L Cl on the **Riyadh refinery** TSE. The deck's data-centre study runs on `run_controller.TSE`, the Dhahran field TSE at **528** mg/L Cl, where the same screen gives **0.76 cycles**: the makeup exceeds it before any concentration. **Screen, not onset.** The 400 mg/L figure is guidance for 316 at neutral pH, 35 °C, clean flowing water; a plate vendor's own SS316 table gives **1050 mg/L at 50 °C, pH 8.25**, which is **4.86 cycles** on the refinery water and **1.99** on the Dhahran TSE, and at pH 7 the same row gives 1.39 / 0.57. **Braze.** The copper-brazed table requires SO₄ < 100 ppm and HCO₃/SO₄ > 1.5; the refinery makeup is 326 mg/L at a ratio of 0.52 and the Dhahran TSE 300 mg/L at 0.35, so both fail before concentration. No criterion is held for duplex 2205, titanium or Cu-Ni, so no cycles limit exists for them | **OPEN** as a claim. `corrosion.py` is unchanged and still enforces the screen only when the caller declares the alloy (defect 46). The deck wording is corrected here. The model should carry an explicit `fws_topology = open \| isolated` and apply the plate chemistry only when the topology is open; that is not written |
| 66 | **The registered one-CDU study was scored before the chemistry corrections, reproduces three fixed defects locally, and models a chilled-water plant** | The `cdu_hybrid.py` run of 7–8 Sep predates defects 24, 25, 27, 29, 30 and 44. Its makeup carried **no silica**, so `SI_silica_am` at every optimum was about **−27.3**, and the script re-implements acid-on-makeup (25), the discharge fee on makeup (30) and an 8 K skin (44). Independently, its facility-water grid is the York chiller's chilled-water range, so all **909** accepted states have facility water **4.44–8.89 °C**, GPU inlet water 9.44–13.89 °C and a running compressor — a chilled-water design that current direct-liquid-cooling practice avoids | **Fixed** as a record, not as a model. Re-scored unchanged (R1) and with defects 25, 30 and 44 corrected (R2), thresholds untouched, and **no verdict changes**: H1a FAIL, H1b PASS (minimum SI increase 0.0885 → **0.0239 / 0.0247**), H2-cycles PASS with the binding minerals now **calcite + silica** where they were calcite + gypsum, H2-temperature FAIL, H3/H4 NOT_IDENTIFIABLE. The annual coupled-versus-baseline figures moved and are in the supersession table below; the optimum moved from **6 cycles in all 8 bins to 4–5**. Both re-scores are stored under `results/cdu_hybrid_rescore_20260917/` and `results/cdu_hybrid_rescore_corrected_20260917/`, and `docs/cdu_hybrid_readme.md` carries the staleness note. **The chilled-water framing needs a founder decision before any number from this study is quoted** |
| 67 | **The one measured Gulf TSE silica was read from the PDF text layer rather than the page: 18 mg/L where the table prints 8** | `chemistry.ARAMCO_RIYADH_REFINERY_TSE` carried `SiO2=18.0  # MEASURED`. NACE CORROSION/96 Paper 577, Table 1, page 577/9 prints **Silica as SiO₂ = 8**. The text layer reads the row as `Silica as SiO, 18 I Aluminum ] 0.12. 1`: the vertical table rule was OCR'd as a leading "1". Iron extracts as `0.21 1` against a printed 0.2 by the same artefact. Found by reading a high-resolution render of the page. The wrong value made this water **silica-bound** in the incumbent-gap study and is quoted as "18.0 mg/L measured" in the external handoff, the evidence document, the Modelica silica model and defect 50's row | **Fixed** — `SiO2=8.0`, and the whole printed table is carried as `chemistry.NACE577_TABLE1_PRINTED` with all 20 rows pinned against values typed from the page. Re-run with thresholds unchanged: **Cycle Ceiling Report 4.5168 → 4.5171 cycles**, still calcite, printed 4.52 unchanged; **$88,976 → $88,984/yr**; 3-yr capex bound $266,928 → $266,953; silica crossover 30.0 mg/L unchanged. **Incumbent gap**, Riyadh at acid pH 7.8: class **silica-bound → calcite-bound**, M median **6.72 → 8.91**, P3 4.95 → 7.43, gap P1 +4.69 → +2.50, P1 break-even median $12,474 → $5,419/yr, and the four P3 variants that landed within 0.5 cycles become none. Extended-panel verdicts are unchanged in direction (H1 HOLDS, H2 HOLDS, H3 FAILS) but H2 now rests on **one** silica-bound water, Dhahran, whose silica is assumed. **`modelica/TowerSilicaDynamics.mo` parameter updated to 8.0 and NOT re-run** — `src/run_modelica.py` reports omc NOT FOUND — so `results/silica_res.csv` is still the 18 mg/L run; by the model's own blowdown equation B + D falls from 0.678 to 0.277 kg/s and V/(B + D) rises from 20.5 h to 50.2 h, so the 168 h spin-up `tests/test_basin_dynamics.py` assumes must be re-checked when it is run. Held by `tests/test_reference_benchmarks.py` |
| 68 | **The Riyadh assay's charge imbalance was explained by crediting the ammonium it prints and ignoring the nitrite printed beside it** | The assay prints ammonia 16 and nitrite 31 mg/L and states no basis for either. `chemistry.py` said ammonium as NH₄⁺ would move the balance "from −5.25 % to roughly −2 %"; `sidestream.charge_closure_bracket`, the Ceiling Report and `docs/chemistry_evidence.md` said 11.3 mg/L as N closes it. Nitrite is an anion from the same table and moves the balance the other way. Computed here, ammonium alone gives **+0.43 %** as NH₄⁺ or **+2.00 %** as N, so the "−2 %" was wrong as a number as well as as an argument | **Fixed** as reasoning, not as data — verdict **UNDETERMINED**. `makeup_analysis_audit.nitrogen_basis_charge_balance`, whose criteria were committed before it ran, scores 12 basis pairs against the unchanged ±5 % charge and +10 % TDS tolerances. **Nitrite as N fails with every ammonia basis** (−11.14 % to −12.71 %, ion sum 11.5–11.9 % over TDS). **Nitrite as NO₂⁻ passes with every ammonia basis**: −2.19 % as N, −3.44 % as NH₃, −3.76 % as NH₄⁺. Nitrite as NO₂⁻ with no ammonia fails at −9.44 %. So the −5.25 % is consistent with the dropped nitrogen if nitrite is reported as the ion, and the ammonia basis cannot be decided from the analysis. No species was added to the engine and `validate_analysis` still fails the assay on charge balance. Output in `results/nace577_nitrogen_basis.json` |
| 69 | **The permit headline was the nitrate daily MAXIMUM; on the monthly average no cycle count complies, and the search reported its own lower bound as a ceiling** | RCER-2015 Vol. I Table 3C prints "Nitrate \| mg/l \| 10 \| 1". `discharge.py` carried both columns and its own comment calls the monthly average "the operative one for continuous operation", but the package's headline — HANDOFF, the external handoff, the deck, the application answers and defect 49's row — is **3.33 cycles**, which is 10 ÷ 3 mg/L, the maximum. On the monthly average the Riyadh makeup is already at 3 mg/L against a limit of 1. `max_cycles_for_discharge` then returned its search's lower bound, so the Ceiling Report printed "on the monthly average, at **1.00**", which reads as "complies at one cycle" when nothing complies, and the incumbent-gap study recorded "discharge ceiling of 1.0" on both waters. Found by an independent review | **Fixed** — `max_cycles_for_discharge` returns `(INFEASIBLE, parameter)` when the limit is breached at the lower bound. `INFEASIBLE` is a string, so arithmetic or comparison on it raises rather than propagating a number. `binding_ceiling` returns `cycles: INFEASIBLE`, `discharge_feasible: False`, and report-not-impose is unchanged. Ceiling Report re-run: "on the monthly average, at 1.00" → **"on the monthly average, no cycle count complies"**; daily maximum 3.33 unchanged; scaling ceiling 4.52 unchanged. Incumbent gap re-run: the 20 reported discharge entries 1.0 → **INFEASIBLE**, and no verdict reads them. **Basis caveat, reported not adopted:** the table writes "Ammonia, Total as N" and "Phosphorus, total as P" but plain "Nitrate", so the limit is carried as the ion; read as N it would be 4.43 mg/L as NO₃ and the monthly average would admit up to 1.48 cycles on this assay, whose own nitrate basis is also unstated. On the Dhahran water the makeup breaches both nitrate and phosphorus at one cycle, so it is infeasible on either basis. Held by `tests/test_discharge.py` |
| 70 | **The duplicated Exp3 file was resampled as a third calibration campaign in the gate error model** | `gate_uncertainty.CAMPAIGN_FITS` and `scripts/gate_uncertainty.CAMPAIGN_SLOPES` carried Exp1, Exp2 and Exp3 as three campaigns. Exp3 repeats Exp1 rows 0–16 (defect 51), so one campaign was counted twice, the second time as a 17-row subset with its own fit — offset −14.59 %, slope +0.1873 %/fan%, residual sd 3.18 pp. Recomputing the fits from the de-duplicated loader reproduces Exp1 (−0.52 %, −0.2002, 6.27) and Exp2 (+9.06 %, −0.3660, 11.63) to the last digit, and reproduces the Exp3 row as the subset it is | **Fixed** — Exp3 removed from both modules. **The analytic bar narrows, in the flattering direction:** slope spread sd **0.232 → 0.083 %/fan%**, offset sd 9.71 → 4.79 pp, V5/V7 water bar **±5.6 → ±2.0 pp**. **The Monte Carlo widens**, because Exp3 also carried the smallest residual scatter: V7 sd **5.51 → 5.79 pp**, the 95 % interval 1.05–22.77 → **−0.49–22.38 %**, P(≥ 15 %) **0.406 → 0.325**, P(≥ 20 %) 0.094 → 0.072, V5 median 3.03 → 1.65 %. **Two claims died with the file:** that the fan-slope's sign is inconsistent between campaigns — both real campaigns are negative — and that 20 % sits inside the one-sigma bar on V7, which is now 13.0–17.0 %. Both were stated in prose and are rewritten. The population is now **two** campaigns, which the module itself says is not a population. Verdicts unchanged: V5 FAIL decidably, V7 PASS not decidably. Held by `tests/test_gate_uncertainty.py` |
| 71 | **The surrogate's P2 gate was pre-registered and never scored** | `pinn.GATES` fixes `P2_holdout_Tout_MAE_K_max = 0.60` before training, and `main()` computed P1, P3 and P4 only: `results/pinn.json` has no P2 entry at all, so `tests/test_artefact_consistency.py::test_pinn_gates_all_pass` passed over it vacuously. An independent audit reconstructed the checkpoint without retraining and measured **0.627 K against 0.600 K — FAIL** — on the inherited **50-row** holdout, i.e. the pre-defect-51 split. Not reproduced here: `results/pinn.pt` is gitignored and absent, so the number cannot be re-scored without retraining, and it is quoted as that audit's | **OPEN** as a result, partly fixed as code. `pinn.main()` now computes, prints and writes P2 against the **32-row de-duplicated holdout**, which is the only holdout the package still has, so the 0.627 K figure is not comparable with what it will produce. **It has not been run** — no checkpoint, and retraining is outside this round. `tests/test_defect_regressions.py::test_defect_71_the_pinn_artefact_reports_every_pre_registered_gate` is `xfail(strict=True)` against the current artefact, so re-running `src/pinn.py` turns it green and prompts closing this row. Until then the honest wording is **four of five gates scored, and the fifth was not** |
| 72 | **The surrogate's P3 sampler does not enforce the wet-bulb band the gate is written against** | The gate is "physical admissibility in the EXTRAPOLATION band, 24–31 °C wet-bulb". `gulf_envelope(extrapolation=True)` samples dry bulb 33–48 °C and RH 0.28–0.70 and never filters on wet bulb. Reproduced here from the sampler alone, no checkpoint needed, on the gate's own seed 99 and n = 5000: **2,596 points, 51.9 %, lie outside 24–31 °C** — 437 below and 2,159 above — spanning **19.64 to 41.88 °C**. So the zero-violations result is scored on a wider and hotter band than the text claims, and 437 of the points are inside the measured envelope rather than outside it | **OPEN**, recorded and not changed. Changing the sampler changes what a pre-registered gate measures, so it needs its own pre-registration and a re-run. The numbers are written into `src/pinn.py` beside the gate and pinned by `tests/test_defect_regressions.py::test_defect_72_the_p3_sampler_does_not_enforce_its_own_wet_bulb_band` |
| 73 | **The dataset README and the code disagree on the unit the fan-flow polynomial takes, and the repository cannot settle it from the source** | `data/extracted/wct_pilot_plant_dataset/README.md` defines `w_fan` as "% - Fan feed frequency percentage", range 21–94 %, and prints the correlation as `m_a = -0.0014 f² + 0.1743 f - 0.7251` in that same symbol. `tower.air_mass_flow_from_fan` converts % to Hz **before** the polynomial, which is defect 1's fix. Read literally as the README writes it, the audit reports a holdout MAE of **3.309 K**. The two arguments in the code are physical rather than score-based: as a percentage the quadratic turns over at 62.25 %, inside the stated operating range, so air flow would fall as the fan speeds up; and the design point gives L/G 2.55 as a percentage against 1.54 as hertz. **The dataset carries no measured air-flow channel** — `MEASURED_CHANNELS` is seven channels and none of them is air — so nothing in the repository can arbitrate by measurement, and the primary paper was not accessible | **OPEN**, recorded and explicitly not decided by which unit scores better. What would settle it: the paper's own units for that equation, or the raw anemometer traverse behind it. Until then the hertz reading stands on the two physical arguments and the README's literal reading stands as the discrepancy. Defect 1's row records the hertz reading as fixed and should be read with this one |
| 74 | **A stored result can sit stale indefinitely, and nothing re-derives an artefact from the code that now exists** | Defect 57's fix changed `ph_saturation_brucite`, which `incumbent_gap.mizan_ceiling` enforces, and the study was not re-run. Re-running it at 709a3c5 — before any other change — moved every no-acid figure: Dhahran M **1.19 → 2.03**, Riyadh M **1.30 → 1.56**, and the binding mineral from brucite to calcite at all five conditions on both waters. The audit's superseded-number scan reads documents, and `tests/test_artefact_consistency.py` compares documents with artefacts; **neither re-derives an artefact from the source**, so an artefact can go stale and every document quoting it agrees with it perfectly. This is the second-order form of defects 12, 13 and 21 | **OPEN** as a pattern; fixed for the one artefact. `results/incumbent_gap.json` and its log are re-run and committed. The general hole is not closed. A cheap form of the fix: store each artefact's inputs' SHA-256, as defect 60 now does for the weather array and as `results/cdu_joint_policy_20260917/registration.json` does for its inputs. **A second instance:** `results/v2_diagnosis.json` carried an Exp3 entry and **no script in the repository writes it** — `src/audit.py` requires it to exist and `src/make_report.py` reads it into `docs/poc_report.md`, but nothing can regenerate it. The Exp3 entry is deleted by hand here, because defect 51 proved it is not a campaign, and this row is the record that it was a hand edit to an unreproducible artefact. The two remaining entries are still the pre-de-duplication fits |
| 75 | **Every full controller run overwrote the V5 gate table with V7 rows** | `run_controller.gate_v5()` wrote `results/v5_controller.csv` by a hardcoded name, and V7 is the same function called with `baseline_cycles=3.0`, so after `python src/run_controller.py` the file held the 3-cycle baseline. Regenerating `docs/poc_report.md` then printed V7 rows under the V5 heading — "3 → 5", +19.2 % water. Staged unnumbered by the validation branch, which restored the file rather than committing it | **Fixed** — the filename follows the gate label. A full run now reproduces the committed V5 table except in hourly cost at the fourth decimal (192.9097 → 192.9095 USD/h at Dhahran summer peak); V5 4.38 % water FAIL, 3.91 % cost PASS, 0 violations, and V7 15.01 % / 8.54 % are unchanged |
| 76 | **The audit's open-defect guard could not see an OPEN row that explains itself, and its number vocabulary stopped at nine** | `src/audit.py` counted open rows with `\|\s*\*\*OPEN\*\*\s*\|`, which matches only a state cell containing the bare token. Every row in this table qualifies its verdict, so a register could list `**OPEN** — not fixed, because …` and declare "Open defects: none" and the audit would agree. That is the exact case the check's own comment says it was rewritten to catch: *"a table listing an OPEN row while the summary line still claims none"*. Separately, the declared count was parsed through a `_WORDS` dict running "none" to "nine", so the moment this round took the open count into double figures the audit would have reported "the register does not declare an open-defect count" — defect 41's shape, in the other guard. Fourth time the audit itself has been the defect, after 12, 13 and 21 | **Fixed** — 18 Sep 2026. The open-row pattern accepts a qualified cell, `\|\s*\*\*OPEN\*\*[^\|\n]*\|`, which can only ever find MORE open rows and never fewer, so it cannot be used to turn a failure into a pass. The number vocabulary is **built**, not listed, to a hundred, the way the total-count parser in the same file already is. Shown non-vacuous both ways: with the old pattern this register counts 0 open rows against a declared 10 and the audit passed the mismatch; with the new one it counts 10 |

**59 was never issued.** The branches reserved their number blocks in advance and
one block was short by a row, so 59 was allocated and never used. It is recorded
here rather than left as a hole a later reader has to investigate.

**62 was investigated and is not a defect.** The weather cross-check reported
that EPW hour *h* holds the station observation at local **(h−1):00**, not h:00,
which would shift the diurnal silica margin, the night and day windows and any
join to real observations. Verified independently against ISD-Lite 404160 for
three months whose source year the EPW header names: dry bulb agrees within
0.5 K in **98.6–98.9 %** of hours at (h−1):00, against 28–30 % at h:00. But
`diurnal.py` — `pick_summer_day`, the night window `t < 6 or t ≥ 21` and the day
window `11 ≤ t < 17` — and `scripts/generate_pitch_artifacts.py` both already use
the row index `t = h − 1` within a calendar day as the local clock hour, which is
correct under that convention, and hour 24 belongs to the same day at 23:00. The
Modelica models and the synthetic pitch profiles do not read EPW hours.
**Nothing was shifted.** The convention is now stated in `tmy.py`, exposed as
`epw_hour_to_local_hour()`, written to `tmy_dhahran.json` as `hour_convention`,
used by the weather-source sensitivity to map station climatology onto TMYx
rows, and pinned by `tests/test_weather_envelope.py`. It is written down here
because an investigation that finds nothing is worth as much as one that does,
and because the next person to notice the convention should not have to repeat it.

### Failed gates from this round, which are not defects

The register separates these and so does this round. Two rows of the
pre-registered safety fault matrix **fail as registered**, and the matrix has not
been changed.

| row | registered bound | measured | why |
|---|---|---|---|
| F3, pH probe drift | acid off within 61 s of the disagreement first exceeding 0.3 | **149 s** | the setpoint needs the disagreement held for 60 s, and ±0.005 pH noise on each probe resets the timer while a 0.5 pH/h drift passes through the band |
| F4a, fouled conductivity cell | trip within 601 s of SCI first exceeding 15 % | **768 s** | the same mechanism, on the residual |

Neither fault moved the true basin pH. The inconsistency is between the bound and
the setpoint as written in the pre-registration: the bound counts from the first
crossing and the setpoint from a continuous dwell. A fix — a leaky dwell
integrator, or a hysteresis band — would need its own pre-registration and is not
applied.

### Supersession tables for the 17 September round

`superseded_from_register()` reads three-column percentage rows out of this
document, so these tables are what makes `python src/audit.py` find a document
still quoting the old figures. Rows whose "before" cell is negative are not
tracked by that scan, which reads unsigned percentages only; they are recorded
here for the reader.

**Defect 51 — the de-duplicated calibration holdout.**

| | before | after |
|---|---|---|
| V1 outlet water temperature MAE | 0.542 K | **0.600 K** (PASS either way) |
| V1 heat rejection MAPE | 5.94 % | **6.27 %** (PASS → FAIL) |
| V2 evaporation MAPE | 9.90 % | **10.80 %** (FAIL either way) |
| Holdout rows | 50 | **32** |
| Model MAE against propagated measurement uncertainty | 2.48 | **2.82** |

**Defect 60 — the envelope split.** The hours moved from 5,475 / 3,285 to
**5,209 / 3,551**.

| Annual figure, ratio of totals | before | after |
|---|---|---|
| Water, inside the envelope | −3.31 % | **−3.22 %** |
| Water, extrapolated | 8.23 % | **5.41 %** |
| Energy, inside the envelope | 8.84 % | **8.82 %** |
| Energy, extrapolated | −0.39 % | **+0.95 %** |
| Cost, extrapolated | 2.90 % | **2.75 %** |
| Water, whole year | 2.37 % | **1.31 %** |
| Energy, whole year | 4.52 % | **4.86 %** |
| Water, mean of ratios | 1.25 % | **0.31 %** |
| Energy, mean of ratios | 5.38 % | **5.69 %** |
| Cost, mean of ratios | 4.48 % | **4.34 %** |
| Share of year extrapolated | 37.5 % | **40.5 %** |
| Share of year inside | 62.5 % | **59.5 %** |

Cost inside the envelope is unchanged at +5.32 %. **Annual cost, ratio of
totals, moved 4.17 % → 4.01 %**, and that row is deliberately kept out of the
table above: `4.17 %` is already a "before" cell in the defects 15 and 16 table,
where it was superseded by 2.86 %, and a second row carrying the same "before"
would make the scan's old-to-new mapping ambiguous and break the allowance that
lets this register quote its own history. A document quoting 4.17 % is still
caught, under the older label. The energy–water correlation across the bins was
−0.836 on the pre-fix artefact and is **−0.714** now; documents quoting
r = −0.66 were already stale before this fix.

**One sign reversed.** The extrapolated energy saving is now slightly positive,
+0.95 %, where it was −0.39 %. "The energy saving vanishes outside the envelope"
must now read "falls to about one per cent outside it". The magnitude of the
water asymmetry fell by a third. Every sign that carries the headline is
otherwise unchanged.

**Defect 66 — the one-CDU study, re-scored (R1 unchanged, R2 with defects 25,
30 and 44 corrected).**

| Annual coupled vs baseline | before | after (R1 / R2) |
|---|---|---|
| Energy | 12.40 % | **11.06 % / 11.85 %** |
| Water | 11.13 % | **5.63 % / 4.01 %** |
| Cost | 11.79 % | **9.12 % / 9.79 %** |

**Defect 67 — the printed silica.** No percentage moved, so no row here feeds
the scan; the figures are in the row above. Ceiling Report 4.5168 → 4.5171
cycles, printed 4.52 either way; $88,976 → $88,984/yr; 3-year capex bound
$266,928 → $266,953; incumbent-gap Riyadh M 6.72 → 8.91 cycles.

**Defect 70 — the error model on two campaigns.**

| Gate uncertainty | before | after |
|---|---|---|
| V5/V7 water bar, analytic | ±5.6 pp | **±2.0 pp** |
| V7 Monte Carlo sd | 5.51 pp | **5.79 pp** |
| P(V7 true ≥ 15 %) | 0.406 | **0.325** |
| P(V7 true ≥ 20 %) | 0.094 | **0.072** |

Three further things were caught during development and are recorded in the code where they happened, but were never in a released result: a contradictory collocation sampler in the surrogate (42 % of points demanded two mutually exclusive constraints), an untrained evaporation head from a loss-scaling error, and an evaporation output whose range could not represent 60 % of its own training data.

**Open defects: ten.** Seventy-four found, sixty-four fixed. The ten open are
53 (the registered PHREEQC calcite benchmark fails at 89.1 % against a 90 %
bar), 56 (the registered fail-safe empties the basin sooner during a makeup
loss), 58 (two incompatible magnesium–silica rules, one basis chosen by fit),
63 (an uncapped cubic pump law behind the data-centre PUE), 64 (the withdrawn
dollar cost of bounding), 65 (the 316 chloride claim), 71 (the surrogate's
fifth gate is written and unscored), 72 (its P3 sampler does not enforce its own
band), 73 (the fan-flow unit the repository cannot settle), and 74 (nothing
re-derives a stored artefact from the code that now exists). Seven of the ten
are open because closing them is a physics, specification or sourcing decision
rather than an edit, and each row says which. **That is the largest open count
this register has carried**, and it is the direct consequence of six branches
looking at the package at once rather than of anything new breaking.

### Gate V2 is not passable on this dataset, and that is now measured

Defect 34 sent me to look at why V2 fails, and the answer closes it as a
question. Three candidate causes were tested and all three were **falsified**:

- **Not L/G extrapolation.** Zero of fifty holdout points fall outside the
  training range of the fill law's only independent variable.
- **Not hot-water extrapolation.** Restricting the holdout to the calibrated
  inlet-temperature envelope makes it slightly *worse* (9.99 % against
  9.31 % outside it).
- **Not a misspecified fill law.** Relaxing `Me = c(m_w/m_a)^n` to independent
  water and air exponents improves the training residual by **0.8 %**, and the
  fitted exponents come back at `a + b = −0.12`, i.e. the ratio form was right.

What remains is scatter. The fill law carries a **30 % log-residual spread**
and each campaign has its own offset. The decisive number:

> Fitted on **all 165 points** and scored on the **same** points — an
> in-sample upper bound that no honest protocol can beat — the evaporation
> MAPE is **7.57 %**. The threshold is **8.00 %**. Under the pre-registered
> train-on-Exp2 / test-on-Exp1+Exp3 protocol it is **9.90 %**.
>
> *Both figures are superseded in their inputs by defect 51: the 165 includes 18
> repeated measurements, and the out-of-sample score is **10.80 %** on the 32
> distinct holdout rows.*

**Both figures in that quotation predate defect 51 and are kept as written.**
The 165 includes 18 repeated measurements, and the out-of-sample figure is now
**10.80 %** on the 32 distinct holdout rows. The in-sample bound has not been
recomputed on the 147 distinct rows, so no corrected version of it is quoted
here; what the argument needs is that the bound sits below the threshold and the
honest out-of-sample score sits above it, and de-duplication moved the
out-of-sample score further above. The conclusion is unchanged and is now
reached by a wider margin.

So the threshold sits *between* the best possible in-sample result and the
honest out-of-sample one. **V2 cannot be passed without scoring on training
data.** It was set without checking it against the achievable ceiling — the
same failure as the original V5 water threshold, which required 8.5 cycles on
a water that saturates at 6.

This is not fixable by modelling. It needs a better evaporation dataset, and
until one exists **no water result from this package can be quoted to better
than a few percentage points.**

### Defect 29, and the limit that the model itself refused

Phosphate was added and then deliberately **not** given a binding limit, which
needs saying plainly because it looks like an omission.

It was given one first, at `SI_tcp ≤ 3.0`, chosen the way the other three
limits were chosen — just below the published typical inhibited band. The
model immediately falsified the choice: the ceiling on the field water
collapsed to **1.0 cycle**, meaning the water could not be concentrated at
all. The Aramco pilot ran that same TSE at **3.5 cycles** with, in its own
words, the *"condenser surface clean without mineral deposit formation"*. A
limit that contradicts the one field observation the package has is wrong, and
it was the limit that was wrong.

The physics behind that is standard and is what makes phosphate different.
Calcium phosphate is enormously supersaturated in almost every natural and
treated water and does not deposit, because it is **kinetically** inhibited —
the same reason phosphate persists in seawater and in blood. The published
inhibited limits show it directly: calcite tolerates SR 135–150 before
deposition, tricalcium phosphate tolerates **SR 1500–2500**, an order of
magnitude more, and SR 125,000 under a stressed programme.

On this water `SI_tcp` runs **3.28 at three cycles to 4.40 at seven**, and the
published band runs **3.18 to 5.10**. The entire operating range of interest
lies inside the band where the answer is decided by the treatment programme
rather than by the water. **Phosphate therefore selects a requirement, not a
ceiling**, and `phosphate_screen()` reports it as one. Inventing a threshold
inside that band to make phosphate bind would have been fitting.

The US DOE study brackets it experimentally, which is why the conclusion is
trustworthy rather than merely cautious — same mineral, same saturation range,
opposite outcome, decided by the inhibitor:

| condition | SI_tcp | outcome |
|---|---|---|
| bench heated surface, synthetic MWW_NF at 4 cycles, **no inhibitor** | +3.3 to +4.0 | hydroxyapatite deposited — the **only** crystalline phase found by XRD |
| pilot towers B and C, **5 ppm polymaleic acid** at pH 7.8 | same range | orthophosphate stayed at 2.0–3.5× makeup, i.e. did not precipitate |

### Defect 32, and the claim it took away

This one is worth recording in full, because the correction made the package
weaker and it would have been easy not to notice.

On the wrong recipe the benchmark supported a strong, quotable sentence:
**the industry's index reads NEGATIVE on a water that scaled.** LSI came out
at −0.61 in the bulk and −0.35 at the skin, against a calcium phosphate index
above +3. That is the version that was written into the tests, into a memory
note, and into a report published to the founders on 10 September.

On the correct recipe it is not true. With four times the alkalinity:

| | 40 °C | 55 °C (skin) |
|---|---|---|
| LSI | −0.01 | **+0.25** |
| SI_calcite | −0.08 | +0.10 |
| SI_tcp | +3.26 | +4.01 |
| SI_hydroxyapatite | +7.63 | +8.62 |

**LSI is not silent. It reads a mild positive carbonate number.** An operator
following it would dose for calcium carbonate — and would still be treating
the wrong mineral, because the deposit was hydroxyapatite and the phosphate
index sits four log units higher. So the surviving claim is narrower and, on
reflection, more defensible than the one it replaced: *the carbonate index
carries no information about which species deposits.* "The index is blind" was
never quite the right claim; "the index cannot rank species" is.

Everything else in the benchmark survives untouched. Gypsum is far
undersaturated at −1.0, silica is never measured in the report at all, and
calcium phosphate remains the only strongly supersaturated phase.

One consequence for the product: the controller needs to know the site's
inhibitor programme. That is a site input it does not currently have, and it
is now the second thing a site survey must return after the water analysis.

### Defect 20, and why it was the most expensive one to find late

The physics was never wrong here. The extrapolation was. Every gate in this
package is scored on a weather-weighted year or on held-out data, and the one
table that goes in front of a customer was scored on a single summer hour
repeated 8,760 times.

It is the same error as the mean-of-ratios defect and the V5-gate-mean
correction, and it survived both of them because the fix each time was applied to
the *gate* documents and not to the *commercial* one. The lesson is narrow and
worth writing down: **when a metric convention changes, grep for the metric, not
for the document you were thinking about.**

The headline consequence is that the value pool across the five named Gulf
accounts in `market_dossier.md` goes from roughly **$70M/yr to roughly $34M/yr**.
It is still a venture-scale number and it is now the one the model actually
supports.

### Defect 19, and the open item it closed

Re-running `src/skin_sensitivity.py` against the corrected chemistry did not just
fix the file. It changed the status of the largest remaining assumption in the
package, and in the package's favour.

Under the old van 't Hoff gypsum, the wall moved from 8 cycles to 7 across the
clean-to-fouled skin band, so the hardcoded **+8 K was load-bearing** — every
V3 and V5 result was proportional to a number nobody had measured. Under the
`phreeqc.dat` solubility adopted in defect 15, `SI_gypsum` has an interior
minimum at **44.5 °C** and the condenser skin sits near 40 °C, on the flat
bottom of that curve. Measured across ΔT = **2.4 K to 8.0 K**:

| skin ΔT | gypsum wall | last feasible |
|---|---|---|
| 2.4 K (clean, 20 kW/m²) | 7 | 6 |
| 3.0 K | 7 | 6 |
| 3.7 K (clean, 30 kW/m²) | 7 | 6 |
| 5.0 K (lightly fouled) | 7 | 6 |
| 8.0 K (the value every gate used) | 7 | 6 |

**The ceilings do not move at all.** Two consequences, and both were previously
recorded the other way round: the reported zero saturation violations is **not**
conditional on a fouled condenser, and the 8 K literal is no longer load-bearing
for either ceiling. It should still be replaced by a call to `wall_bulk_delta_t`,
because an assumption that happens not to bind is still an assumption — but it is
no longer the thing to fix first.

### Defect 11, and what it cost

Defect 11 was the second half of defect 5. That fix made the entering-condenser **temperature** window a hard constraint. The bi-quadratic has *two* validity limits and the **capacity** limit was left unenforced: `CHILLER_RANGE_LOG["PLR_out"]` counted the excursions and nothing read it.

Found 3 September 2026 by a pre-registered physics gate in `src/fouling_energy.py` which required chiller power to rise when a condenser fouls. It did not. Quantified in `src/chiller_feasibility_audit.py`.

**Fixing it moved every headline number, all downward:**

| | before | after |
|---|---|---|
| V5 makeup water | 14.83 % | **10.02 %** |
| V5 total cost | 8.55 % | **6.37 %** |
| Electrical power | 4.91 % | **4.17 %** |
| Annual water, ratio of totals | 12.57 % | **9.23 %** |
| Annual cost, ratio of totals | 8.16 % | **5.88 %** |
| Annual electrical power, ratio of totals [†] | 6.0 % | **4.20 %** |
| Conditions with a feasible optimum | 5 | **3** |
| Cycles the optimiser reaches | 7 | **6** |
| *every figure above* | | *superseded again on 4 Sep by defects 15 and 16 — see the next table* |

[†] Every other "before" in this table is read from a committed artefact. This one is not: `annual_dhahran.json` gained its `*_ratio_of_totals` keys after the previous commit and was next committed with the fix already applied, so **the pre-fix value survives only in the documents that quoted it** — at one decimal place. That is a gap in the evidence, and it is recorded rather than rounded over. **Commit the artefact before the fix, not just after it.**

The old figures were bought in a region where the machine could not make its duty. **A saving computed where the plant cannot operate is not a saving** — the same sentence defect 5 was fixed with, one dimension over.

**What did not move:** the gypsum ceiling. Economic ceiling 7 cycles, physical ceiling 8, binding mineral gypsum, cost falling monotonically. None of it goes through the chiller curve, so the two-ceilings result and the figure built on it stand unchanged. *(Written 3 September and true of defect 11. Defects 15 and 16 moved the ceilings the next day, for reasons that do not go through the chiller curve either — see immediately below. The pair is now **6 and 7**.)*

### Defects 15 and 16, and what they moved

Recorded here in the same form as defect 11, because that is what makes the
supersession scan work. `superseded_from_register()` reads this table, so any
document still quoting the 4 September figures is found by
`python src/audit.py` rather than by someone remembering.

**They moved every headline number again, and this time not all in one direction:**

| | before | after |
|---|---|---|
| V5 makeup water | 10.02 % | **10.83 %** |
| V5 total cost | 6.37 % | **5.75 %** |
| Electrical power | 4.17 % | **2.86 %** |
| Annual water, ratio of totals | 9.23 % | **8.81 %** |
| Annual cost, ratio of totals | 5.87 % | **6.44 %** |
| Annual electrical power, ratio of totals | 4.20 % | **5.36 %** |
| Annual water, hours-weighted mean of ratios | 8.92 % | **8.42 %** |
| Annual cost, hours-weighted mean of ratios | 6.53 % | **7.04 %** |
| Annual electrical power, hours-weighted mean of ratios | 5.27 % | **6.41 %** |
| Economic ceiling | 7 | **6** |
| Physical (gypsum) ceiling | 8 | **7** |

The mixed signs are the interesting part and they are not a wash. Defect 16 gave
the machine back the two conditions defect 11 had removed, so the **annual**
figures are once more averaged over a plant that can run a Gulf summer — cost and
energy both rise. Defect 15 made gypsum retrograde at the skin as it should always
have been, which tightens the wall by a cycle and takes the annual water figure
down with it. **The water saving got smaller and the energy saving got larger,
which cuts against the way this product has been pitched** — see
`docs/prior_art_esc.md`, where the energy half is already prior art seven times over.

The V5 water gate still fails, and by more in substance than before: 15 % needs
8.5 cycles and gypsum now saturates at **7**, not 8.

### Defect 17, and why it is open rather than fixed

The consequence is bounded, and that is the useful part. `src/makeup_analysis_audit.py` computes
the gypsum wall under both analyses: **5 cycles at SO₄ 566, 6 cycles at SO₄ 300**. One cycle. The
thesis — that gypsum binds, that acid cannot move it, that LSI cannot represent it — survives
either way, and so does the shape of the two-ceilings result.

It stays **open** because neither analysis can be adopted from here. The primary paper is behind a
publisher wall, the two candidate sets differ on five ions, and picking the one that flatters the
product would be indistinguishable from picking the one that is right. What can be said without
the paper is that **the set currently in the model is not self-consistent**, and that is recorded
rather than smoothed over.

---

### Defect 14, and why the gypsum wall moved

The chemistry is not corrupted by the chiller clamp. Skin saturation is computed from the thermal
solve, not from the chiller curve, so `violations` is clean at every condition. The wall moves for
a physical reason instead, and it is one this package already documented from the other direction:
**gypsum is prograde in this model.** Its saturation index *falls* as the skin gets hotter, so the
hottest condition gives the most permissive wall.

The published V5b condition is the hottest of the five. It is therefore simultaneously the most
flattering for gypsum **and** the one at which the York YT cannot make its duty. Reporting from it
picks up an extra cycle on both ceilings.

This also explains something the run log had been saying plainly and nothing had picked up. V5
raises cycles to exactly 6 in every condition and calls it *“the chemistry constraint boundary”*.
At an operable condition, 6 **is** the last chemistry-feasible cycle count — the controller was
never leaving 2.5 points of water on the table, it was sitting on the real wall while a different
gate reported a wall one cycle further out.

**What is not in doubt:** the two-ceilings *result* — that an economic limit and a physical limit
exist, that they are different numbers, that the binding mineral is gypsum, and that an LSI-based
controller cannot represent it. Every one of those survives at every condition tested. What is in
doubt is the pair of integers attached to it in public.

---

### Defect 12, and why an audit can enforce a lie

Defect 12 is subtler and worth stating for its own sake. `14.83` was typed into six places across three files. When the controller re-ran, `annual.py` wrote the stale value into the very JSON that `audit.py` checks other documents against, and `audit.py` began demanding that the report quote a number the artefacts no longer supported.

An audit that hardcodes expected values does not verify consistency — it **freezes one moment and calls every later truth an error**. The same shape appeared in the `"Open defects: none"` literal, which passed for an honest empty register and failed for an honest non-empty one, quietly rewarding concealment.

Both are now consistency checks against the artefacts rather than string comparisons against remembered values.

`python src/audit.py` runs 63 checks across code, results, run transcripts and documents and gates the packaging. Note the count is not a constant: the document scans call the check function once per problem found, so a tree with faults reports *more* checks than a clean one. Quote it as "the audit passes", not as a number. An inconsistent tree produces no bundle.

---

## Part 2 — Gate outcomes. Three pass, three fail, all diagnosed.

Scored on the de-duplicated 32-row holdout (defect 51) and on the current
controller. The thresholds are the ones fixed before fitting and none has moved.

| Gate | Threshold, fixed before fitting | Result | |
|---|---|---|---|
| V1 outlet water temperature MAE | ≤ 1.00 K | 0.600 K | **PASS** |
| V1 heat rejection MAPE | ≤ 6.00 % | 6.27 % | **FAIL** |
| V2 water consumption MAPE | ≤ 8.00 % | 10.80 % | **FAIL** |
| V5 total cost reduction | ≥ 3 % | 3.91 % | **PASS** |
| V5 makeup water reduction | ≥ 15 % | 4.38 % | **FAIL** |
| V5 skin saturation violations | 0 | 0 | **PASS** |

**V1 heat rejection is the new failure and it is a de-duplication result, not a
model change.** It read 5.94 % against a 6.00 % bar on a holdout that contained
18 repeated measurements and one row the fill law had been trained on. On the 32
distinct rows it reads 6.27 %. A gate that passed by 0.06 points on a
contaminated split did not pass.

### V2 — failed, and the cause is now established

The gate compares predicted water consumption against the measured channel. Two explanations were possible and they make **opposite** predictions, which is what made the question answerable:

- an **unaccounted bleed** in the measured channel, which is total water consumption and would include one;
- the **fill characteristic drifting** between campaigns, already documented in the thermal channel.

Re-identifying the fill law on each campaign separately cannot help if the cause is a bleed, because a bleed is a term the model does not contain. It should close the gap if the cause is drift.

| Campaign | Identified c | Evaporation MAPE with its own fill law |
|---|---|---|
| Exp1 | 1.5320 | 6.55 % |
| Exp2 | 1.2401 | 7.80 % |
| Exp3 | 1.3826 | 4.50 % |

**Every campaign falls inside the 8 % gate.** The bleed hypothesis is rejected. The fill coefficient moves **23.5 %** across campaigns spanning four years — the same drift already measured in the thermal channel, now confirmed independently in the water channel.

So V2 fails as a **single-calibration** gate, for a physical reason rather than a modelling one: the gate holds one fill law fixed while the tower itself changed. The model is not deficient; the assumption that a tower's characteristic is a constant is.

That result points the same way as the commercial argument. **Periodic recalibration against the plant's own telemetry is a functional requirement, not an upsell** — and this gate is the measurement of how fast a fixed characteristic goes stale.

Note also that this gate previously read 7.11 % and passed. That pass rested on defect 7, the drift rate a hundred times too large, which was padding the prediction by about five per cent. Fixing a defect turned a pass into a failure. The pass was not real and has been withdrawn.

### V5 water reduction — failed, and the threshold was unreachable

Makeup water is evaporation × C/(C−1), so the saving available from raising cycles of concentration is fixed arithmetic, not a modelling choice:

| Cycles | Makeup saved vs 4 cycles |
|---|---|
| **7** | **12.50 %** ← the gypsum wall |
| 8 | 14.29 % |
| **8.5** | **15.00 %** ← the criterion |
| 10 | 16.67 % |
| ∞ | 25.00 % (zero blowdown, the absolute ceiling) |

Gypsum saturates at **7 cycles** on this makeup water, and gypsum saturation is not pH-sensitive, so the acid dose that buys cycles against calcite cannot move it. The criterion required 8.5 cycles. It was written on the far side of a wall that had not been located yet — and defect 15 moved that wall in by one more cycle, so the criterion is now further out of reach than when it was set, not closer.

The controller reaches **4.38 %** against a 4-cycle baseline. Against the 3-cycle
baseline of gate V7 it reaches 15.01 %, which is more than cycles alone can
deliver at that baseline because it also lowers evaporation — and which the error
model puts at 13.0–17.0 % analytically and −0.5 to +22.4 % by Monte Carlo
(defect 70), so V7 is a pass that is not decidable. **No control strategy of any
kind reaches 15 % from a 4-cycle baseline on this water.** The earlier 10.83 %
was superseded first by defects 24 and 25 and again by defect 30.

The pre-registration was **mis-specified, not missed**. The lesson is stated in the handoff for the next time: check a threshold against the system's physical ceiling before fixing it.

---

## Part 3 — Open items that are neither defects nor failed gates

These are things not yet known. Each is stated with the direction it cuts.

| Item | Direction | What would close it |
|---|---|---|
| Almería wet-bulb tops at 21.9 °C; **40.5 % of a Dhahran year is above it** (3,551 of 8,760 h, 84 % of September) — on the TMYx file's humidity; **24.3 % with Dhahran station dew point**, and 16.1–36.7 % across complete station years 2011–2024 | **Unknown** — the only two-sided one, and now sized rather than described. The size itself depends on the weather source, which is why both are stated | KFUPM's humidifying wind tunnel. Not closable by argument, and the physics-informed surrogate is a mitigation, not a substitute |
| Model error **2.82×** measurement uncertainty (2.48× before the holdout was de-duplicated, defect 51) | Against us | More campaigns, or a better fill model. Reported as a negative result |
| **Skin temperature rise is a hardcoded +8 K.** The film calculation in the codebase gives 2.4-3.7 K clean; 8 K is a fouled surface | **Neutral, and no longer load-bearing.** Re-measured 4 Sep against the corrected gypsum solubility: `SI_gypsum` has an interior minimum at 44.5 °C and the skin sits near 40 °C, so across the whole band 2.4-8.0 K the wall stays at **7 cycles** and the last feasible count at **6**. The previous entry said this bought about one cycle of apparent headroom; that was true of the van 't Hoff model and is not true of this one | `src/skin_sensitivity.py`, now deriving its own conclusions (defect 19). The heated-coupon rig still measures the real ΔT |
| Magnesium-silicate SI threshold | Unknown | Handled by the empirical Mg × SiO₂ product instead of asserted |
| OpenModelica leg | Neutral | Written, not installed, not run. Makes no claim |
| **Acid dosing at high cycles may make the water corrosive, and the controller has no corrosion term.** EPRI warns that sulphuric acid replaces protective alkalinity with corrosive sulphate as cycles rise. **Two operators and a 1992 training syllabus now say this is the first constraint a practitioner sets, not a refinement** | **Against us**, and more sharply than when this line was written. The optimiser searches pH 7.0–9.0 against saturation only, with no corrosion floor. Field evidence in `docs/discovery_findings.md`: a plant chemist holds LSI at **0.8–1.0** deliberately, because a thin carbonate film **is** the corrosion defence; a textile engineer sets the pH window from **metallurgy** before anything else; and the 1992 course notes list *"calcium carbonate protective scale"* as a corrosion-control method. An optimiser driving toward LSI ≈ 0 strips that film | Potentiostat and coupon work in the KFUPM corrosion laboratory. **And before that, a corrosion floor in the optimiser** — this is now a specification, not an open question. **Partly answered, 7 Sep 2026:** the floor is implemented (`CORROSION_FLOOR_SI`, enforced at bulk temperature where LSI practice sits) and `src/corrosion_floor_conditions.py` now sweeps it across **all five V5 conditions**, not the one in `corrosion_floor.json`. Pre-registered C1 — that the floor binds nowhere — **HELD**: cycles, fan, pH, makeup and cost are identical from a floor of -0.5 to +1.0 at every condition, because every optimum sits at pH 8.00-8.25 where SI_calcite is already well above the top of the band a plant chemist holds. So the EPRI objection does not change the controller's answer anywhere in the envelope. It does **not** retire the laboratory work: the floor is a saturation proxy, not a corrosion rate, and sulfate-driven attack after acid dosing is not a saturation phenomenon |
| **Fouling has no energy consequence in the model.** `chiller_power` carries `approach_cond = 4.0` as a fixed constant, so scale can build to the saturation limit and the chiller draws identical power | **Against us, and it under-sells the product.** The ESCO argument in `outreach_messages_saudi.md` §5 asserts the fouling → approach → efficiency chain, and nothing computed it. `src/fouling_energy.py` now does: at the TEMA treated-water allowance, **+11.6 % chiller power**, worth **$80,757/yr** against **$52,285/yr** of water saving at the same tariffs — a ratio of **1.54**. Energy is the larger lever, and every operator interviewed described fouling as a performance problem, never a water one | Wiring `approach_cond` to a fouling state in the controller. The remaining unknown is **rate** — how fast fouling accumulates at a given supersaturation — which needs the heated-coupon rig |
| No traction, no LOIs, no patents | Neutral | Customer interviews. Cohort 1 winners had none either |

---

| **Gypsum is evaluated at the hot skin, where this water is least saturated in it (defect 23).** Saturation says the basin is the worse point by 0.0068 log units at 6 cycles; EPRI reports gypsum forming in the hot end of exchanger tubes above ~38 °C, which is a kinetic and surface argument the model does not represent | **Ambiguous, and both directions are defensible.** Switching the routing to `'cold'` would tighten the wall by 0.066 cycles and change no integer ceiling, so nothing is bought by guessing. The saturation model and the field literature disagree about *where* the deposit forms, and only one of them is in the code | Bench work: deposit gypsum on a heated coupon at controlled bulk saturation and observe whether it forms preferentially at the hot surface. Until then the routing stays as shipped and is declared |

| **The V5 water pass is hostage to unmeasured silica, and this is now the single highest-value open action.** `ARAMCO_RECLAIMED` carries `SiO2 = 0.0` because the source analysis does not report it -- unmeasured, not silica-free. Amorphous silica binds at the COLD basin and is not pH-sensitive, so acid cannot buy cycles against it. At the optimiser's pH the ceiling collapses the moment any realistic silica is present: **0 mg/L gives 12.3 cycles (gypsum) and an 18.2 % saving; 20 mg/L gives 7.8 cycles (silica) and 14.0 %; 26.8 mg/L -- the Salbukh measured Saudi value in HANDOFF.md -- gives 5.8 cycles and 9.5 %** | **Against us, and it flips a gate.** At measured Saudi silica V5 fails again at 9.5 % against 15 %, and the binding mineral is amorphous silica rather than gypsum, so the product would be about a different mineral. Note the ceiling would land near 5.8 cycles, close to the pre-correction 6 | **Measure the silica in a real makeup water.** One analysis settles whether the 16.84 % headline survives. Held by `test_the_water_gate_result_is_hostage_to_unmeasured_silica` |

## What this register is for

A reviewer should be able to ask two questions and get a clean answer to each.

**"Is the work sound?"** Seventy-four defects were found, sixty-four are fixed, ten are open and every open one says what would close it, and a passing audit gates every release. Six of them were found because a first-principles model, or a check written against it, refused a bad input rather than absorbing it — which is the argument for building it that way, and the reason the parent company is called Furqan. The ten open rows are the honest state after six branches examined the package simultaneously on 17 September 2026; three of them (53, 63, 73) are open because the repository does not hold the source that would decide them, and four (56, 58, 64, 65) because the decision belongs to a person rather than to an edit.

Defects 11 and 12 were found the same way as the rest: a threshold fixed before the run, and a result on the wrong side of it. The gate asked only that chiller power rise when a condenser fouls. It did not. Following that back found a validity limit that had been logged for months and read by nothing — and then a constant hardcoded into an audit, which had begun requiring documents to quote a figure the artefacts had already superseded.

Fixing 11 cost the product 4.8 points of water saving and two of five operating conditions. It is reported that way because the old number was earned where the chiller could not make its duty.

**"Did everything work?"** No. Two gates failed. Both are diagnosed to a specific cause with no open questions, neither threshold was moved, and one of them failed precisely *because* a defect was fixed.


---

## Defect 21, and why the fix is about scope rather than about 6.48

This is the third time the audit itself has been the defect, after 12 and 13, and
the three share a shape. A check that is supposed to detect staleness acquires a
way of asserting it, and then asserts it about something current.

The guard exists because a retired figure and a live one can print identically.
It reads the artefacts, rounds what it finds, and subtracts those forms from the
stale list. It was written when every stale token came from a before/after table
in this register, so it only ever cleared tokens of that kind. Seven figures are
declared by hand instead, because they predate the table convention, and the
guard could not see them at all. `annual_datacentre.json` then produced 6.4779 %
and the audit began requiring a document to disown a number the same repository
had computed an hour earlier.

The fix subtracts the hand-declared figures too, but **against headline values
only**, and that restriction is the whole of it. The first attempt cleared them
against every float in the artefacts, per-bin arrays included, which made the
audit pass and quietly retired two declarations that were earned: `11.5 %` and
`8.3 %` were found live in the file the outreach is sent from, still being
offered to prospects. Bin 0 of the Dhahran year saves 11.52 % energy and bin 5
saves 8.33 % water. Those coincidences would have disabled both checks.

The per-bin arrays stay in scope for the table-derived tokens, because documents
quote bin ranges legitimately, and HANDOFF's *"6.0 to 8.6 % across the cooler
half"* is one. So the two callers get two scopes, and the reason is written into
the code rather than left to be rediscovered.

**One declaration was retired honestly.** `6.7 %`, the pre-defect-11 annual
electrical power on mean of ratios, now collides with the data centre run's
annual energy of 6.6534 %. That is a real current headline, so the token cannot
be enforced any more without flagging live work. It is recorded here rather than
left silent, because a check that stops checking should say so.


---

## Defect 23, and why a bounded number still matters

The arithmetic impact is almost nothing. Evaluating gypsum at the basin instead of the
skin moved the continuous cycles root from **6.672 to 6.606** on the engine of the day.
Both rounded to 6 and no artefact changed. **Re-measured after defect 24** the
interior minimum sits near **53.5 C**, further above the skin band than before, so
the finding is unchanged in direction and stronger in degree.

**The claim it invalidates is the one on the front page.** The product is described as
evaluating each mineral *"at the temperature where that mineral is least soluble"*, and
gypsum — the mineral that actually binds — is routed to the hot skin. On this water the
skin is where gypsum is **most** soluble. The routing is therefore permissive, which is
the direction an evidence-first package must never be wrong in.

`docs/robustness_gaps.md` had already worked this out **before** defect 15 and said so
plainly: *"Evaluating gypsum 'hot' is the permissive choice here, not the conservative
one."* Defect 15 replaced the monotonic van 't Hoff with a function that can turn over,
the four pre-registered predictions passed, and the conclusion paragraph was rewritten to
say the opposite — that gypsum is most saturated at the skin — without re-running the
comparison the original paragraph rested on. **A fix was applied and the caveat it was
supposed to remove was deleted instead of re-tested.** That is the fault.

Three consequences, none of which is a number:

1. **The one-line pitch must change.** Say the model evaluates each mineral at its own
   worst point *and* that gypsum's worst point on this water is the basin, not the wall.
   A reviewer who checks `SI_gypsum(T)` will find the minimum in thirty seconds.
2. **`MINERAL_EVAL_POINT['SI_gypsum']` stays `'hot'` for now, deliberately.** Switching it
   to `'cold'` is a physics decision about where the deposit actually forms — EPRI reports
   gypsum forming in the hot end of exchanger tubes above ~38 °C, which is a *kinetic and
   surface* argument, not a saturation one. Saturation says basin; the field literature
   says hot end. Those can both be true and the model represents only the first.
   Resolving it needs the laboratory work already on the list.
3. **`V3`, the gate that shows bulk understates the limit, is untouched** — it compares
   bulk against skin for the binding mineral set as a whole, and calcite, which *is*
   strongly retrograde, dominates it.

Found by an external agent running an independent CDU study against this repository, which
measured skin SI below basin SI in **831 of 909** accepted thermal states, and confirmed
here by direct evaluation before being registered.


---

## Defects 24 and 25, and what they cost

These are the largest defects in this register, and they were found the only way
they could have been: by comparing the engine to something outside it.

**Nothing already in the repository could have caught them.** `src/audit.py` runs
65 checks and passes. `tests/` runs 60 checks and passes. Both verify *internal*
consistency — documents against artefacts, invariants against themselves,
thresholds against their pre-registration. A model can be perfectly coherent with
itself, its own documents and its own physical laws, and still disagree with a
published standard by 0.2 log units. That gap is now closed by
`tests/test_reference_benchmarks.py`, which scores the engine against values this
repository did not produce.

### What actually happened when both were fixed

The pipeline was re-run on 10 September 2026. **The pre-registered thresholds were
not touched** -- `tests/test_artefact_consistency.py` enforces that -- and three of
them changed verdict because the model changed.

| | before | after | note |
|---|---|---|---|
| **V5 makeup water** | 10.83 % **FAIL** | **16.84 % PASS** | against an unmoved 15.0 % threshold |
| **V5 total cost** | 5.75 % PASS | **8.33 % PASS** | |
| V5 skin SI violations | 0 PASS | 0 PASS | |
| energy (diagnostic) | 2.86 % | 3.21 % | still not a gate |
| economic ceiling | 6 cycles | **12 cycles** | |
| physical ceiling | 7 cycles | **none in range** | no mineral binds inside the sweep |
| **V3 bulk vs skin** | 6.9-7.1 % / 15.2-15.6 % | **6.9-7.1 % / 15.3-15.7 %** | **unchanged** |

**V5 water passing is the mirror image of V2.** V2 failed *precisely because* a
defect was fixed; V5 passes for the same reason. A gate that moves when the model
is corrected is a gate doing its job. A gate that moves when the threshold is
edited is fraud, and the threshold is still 15.0.

**V3 not moving is the most important line in the table.** It carries the central
methodological claim -- evaluate saturation at the condenser skin, not in the bulk
-- and speciation scales the bulk and skin evaluations proportionally, so the ratio
the gate reports is invariant. The correction did not touch the thesis.

**What the correction did cost: the two ceilings.** The 6-and-7 pair is gone, and
with it "the economics point straight at the wall". On the corrected engine the
cost curve runs to the end of the sweep because no mineral binds inside it.

**And what it did NOT cost, contrary to the first reading.** Gypsum still binds --
just not where the optimiser sits. Measured on the corrected engine at 40 C:

| SO4 | pH 7.5 | pH 8.0 | pH 8.5 |
|---|---|---|---|
| 566 mg/L (published) | **12.2 cycles vs 30 calcite-only** | 12.3 vs 12.8 | 6.2 vs 6.2 |
| 300 mg/L (field) | **17.2 vs 22.6** | 11.4 vs 11.4 | 5.5 vs 5.5 |

A calcite-only model -- which is what LSI is -- sees its limit relax as acid is
dosed, so it keeps dosing and keeps raising cycles. At pH 7.5 on the published
sulfate it would authorise **thirty** cycles. The true limit is **twelve**, set by
gypsum, which acid cannot move. **The differentiation is not that the constraint
changes what a well-tuned optimiser does; it is that it stops a badly-tuned one
from destroying the condenser.** That is a safety constraint, not an optimisation
term, and it is the conclusion `prior_art_esc.md` reached from the opposite
direction.

### What is untouched

The prior-art measurement is about what *other people publish*, not about this
engine, and it stands — including the Applied Energy paper (Chen et al., NUS,
`10.1016/j.apenergy.2026.128414`), obtained 9 September 2026 and scored **zero**
on the nine chemistry terms across both extraction engines. The tower work, the
Poppe integrator, the chiller envelope and every V1 result are unaffected.

### Why the arithmetic is not fixed in the same commit

Defect 25 is a one-line change with a large blast radius: it moves the acid cost,
which moves the cost objective, which moves every optimum and every artefact that
quotes one. Defect 24 is not a one-line change at all — it requires an aqueous
complexation solver. Registering both, declaring them at the call site, and
pinning their measured magnitude in a strict-xfail test is the honest interim
state. **The magnitude tests are not xfail**: `test_the_gypsum_benchmark_error_has
_not_drifted` holds the error at +0.2046 and
`test_the_acid_error_factor_is_exactly_the_cycles_ratio` holds the overstatement
at exactly C, so neither can move quietly, and a repair that does not drive both
to their correct values will fail rather than pass silently.

Found by an external agent benchmarking this repository against PHREEQC; both
results reproduced here before registration.


---

## Defect 17, and why the answer was not a number

For weeks this register asked which sulfate figure was right, 566 or 300, and
recorded that neither source reconciles. That framing was wrong, and the proof
was inside the table the whole time.

Table 1 of Badruzzaman et al. (2022) is headed **"Raw Groundwater | Reclaimed
Min | Ave | Max"**. Score all four columns against the two objective tests:

| column | charge balance | ions vs stated TDS |
|---|---|---|
| Raw Groundwater | +3.9 % | **−1.2 %** |
| Reclaimed Min | −42.5 % | −16.5 % |
| Reclaimed Ave *(what this package shipped)* | −14.3 % | +16.8 % |
| **Reclaimed Max** | −20.5 % | **+97.6 %** |

**The Max column's ions sum to 3557 mg/L against its own stated TDS of 1800.**
Nothing can contain twice its own dissolved solids. Those three columns are the
highest sodium ever recorded beside the highest sulfate ever recorded, from
different days — **marginals, not samples.** The groundwater column, which is a
sample, closes cleanly, so the laboratory is not the problem.

So there was never a wrong ion to find. Treating a column of marginals as a
water is a **category error**, and no single-ion correction repairs it — which
is exactly why every attempt to fix sulfate alone left a residual TDS gap.

**What made it findable was not cleverness but a check.** Defect 27 added
`validate_analysis()`, the analysis was scored for the first time, and the Max
column failed loudly enough to explain the Ave column. Six earlier defects were
caught the same way: a first-principles check refused a bad input instead of
absorbing it.

**The resolution keeps both sources intact.** `ARAMCO_RECLAIMED` still
transcribes Table 1 faithfully and still fails validation, which is correct
behaviour for a faithful copy of a set of marginals. The controller runs on
`ARAMCO_FIELD_VALIDATED` — the same Aramco Abqaiq pilot reported as **one
coherent analysis** by the operating engineers in *Water Technology*, January
2021 — which passes every check.

**And that source carries a validation target nothing here was fitted to:**
groundwater at COC 2.0 produced *"severe scaling on the condenser surfaces"*;
TSE at COC 3.5 left the *"condenser surface clean without mineral deposit
formation"*; reported LSI 0 to 0.5.

---

## Correction to the commit record, 11 September 2026

Three commit messages state test counts that were never verified:

| commit | claimed | actual |
|---|---|---|
| `878f166` | 176 tests pass | 171 |
| `8b27ccd` | 178 tests pass | 171 |
| `0df3674` | 179 tests pass | 171 |

The true figure throughout was **171 collected cases from 162 test functions** —
the difference being parametrised tests, which expand. The counts were written
into the messages from arithmetic rather than read from a run, which is
exactly the habit this register exists to catch, and it is recorded here
rather than silently left in the history.

**No tests were lost.** Every file present at `f7e1808` is present now and the
definition count rose. The error is in the prose, not the suite.

Git history is not rewritten for this: the commits are real and their
technical content stands. This note is the correction.

**And it happened again.** `422d7b0` states 179 tests; the verified figure is
**175**. Same cause -- a number written from arithmetic instead of read from a
run -- in the very commit that followed the correction above. The habit is
more persistent than the intention, so the rule is now explicit: **a test
count goes into a commit message only by copy from a `pytest` line in the
same shell session.**

That commit also swept in about thirty OpenModelica build products -- the
generated C, headers, makefile and `.bat` that `omc` leaves in the working
directory. Removed from tracking and added to `.gitignore` in the commit that
follows. The model is `modelica/*.mo`, the result is `results/*_res.csv`, and
everything between them is regenerated by re-running the `.mos` script.
