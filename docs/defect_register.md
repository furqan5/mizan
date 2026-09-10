# Defect register, and what a failed gate is not

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

There are two different things in this package that can look alike from a distance, and they should not be confused.

A **defect** is a mistake in the work — a wrong unit, an inverted sign, an unconverged solver. Defects are faults. They get found and fixed, and the count of open ones should be zero.

A **failed gate** is a result. A threshold was fixed in advance, the experiment was run, and the answer came out on the wrong side of it. That is not a fault. Suppressing it would be.

This document lists both, separately, so neither can be mistaken for the other.

---

## Part 1 — Defects. Thirty-two found, thirty-two fixed, none open.

| # | Defect | How it showed up | State |
|---|---|---|---|
| 1 | Fan air-flow correlation read as per cent when it takes hertz | The curve turned over at 62 %, so air flow fell as the fan sped up. All three thermal gates failed with a +1.50 K bias. | **Fixed** |
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

| 32 | **The DOE benchmark ran on the wrong recipe table, and it was the easier one** | `DOE_SYN_MWW_NF_COC4` was transcribed from **Table 2.3.2** (p. 2-14), the general chapter 2/3 synthetic recipe. The heated-surface experiment this package benchmarks against — the one that produced the hydroxyapatite XRD result — is in **chapter 4**, and chapter 4 has its own recipe, **Table 4.2.1** (p. 4-13). They differ where it matters most: **HCO₃ 0.40 vs 1.60 mM, four times the alkalinity**, and Na 8.60 vs 9.80 mM. The wrong table understates carbonate saturation on precisely the water the benchmark claims calcite is undersaturated in, so **the benchmark was passing partly for the wrong reason**. Found by an external agent's review of the source, not by us. | **Fixed** — 11 Sep 2026. Corrected to Table 4.2.1; the 2.3.2 recipe is retained as `DOE_SYN_MWW_NF_COC4_TABLE_2_3_2` so the two can be compared and neither can be re-imported by accident. `test_the_two_doe_recipes_are_not_interchangeable` pins the difference. **The claim it cost us is recorded below** |

| 31 | **The thermal solver's cache key omitted the water composition and the fill law** | `_thermal_solve` keyed its memo on `(fan_pct, cycles, cond items)` only — while the body computes the water activity from `makeup_water.concentrate(cycles).tds()` and passes `fill_c`/`fill_n` into the outlet-temperature solve. **Two different waters at the same fan and cycles therefore shared one thermal solution.** It never bit, because `run_controller.py` runs a single water and nothing sweeps composition through this function. It would have bitten on the **very next study planned** — the silica crossover sweep, whose entire method is to vary SiO₂, and hence TDS and water activity, at fixed fan and cycles. Same class as defects 11 and 26: a quantity computed, understood, and enforced by nothing. The comment above the key already worried about the smaller `id(cond)` hole and said *"it has not been observed to bite, which is exactly why it should not be left in"* — and then left the larger hole open. | **Fixed** — 10 Sep 2026. The key now includes TDS, SiO₂, PO₄ and both fill coefficients |

Three further things were caught during development and are recorded in the code where they happened, but were never in a released result: a contradictory collocation sampler in the surrogate (42 % of points demanded two mutually exclusive constraints), an untrained evaporation head from a loss-scaling error, and an evaporation output whose range could not represent 60 % of its own training data.

**Open defects: none.** Thirty-two found, thirty-two fixed.

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

## Part 2 — Gate outcomes. Six pass, two fail, both fully diagnosed.

| Gate | Threshold, fixed before fitting | Result | |
|---|---|---|---|
| V1 outlet water temperature MAE | ≤ 1.00 K | 0.542 K | **PASS** |
| V1 heat rejection MAPE | ≤ 6.00 % | 5.94 % | **PASS** |
| V2 water consumption MAPE | ≤ 8.00 % | 9.90 % | **FAIL** |
| V5 total cost reduction | ≥ 3 % | 5.75 % | **PASS** |
| V5 makeup water reduction | ≥ 15 % | 10.83 % | **FAIL** |
| V5 skin saturation violations | 0 | 0 | **PASS** |

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

The controller reaches 10.83 %, which is more than cycles alone can deliver, because it also lowers evaporation. **No control strategy of any kind reaches 15 % on this water.**

The pre-registration was **mis-specified, not missed**. The lesson is stated in the handoff for the next time: check a threshold against the system's physical ceiling before fixing it.

---

## Part 3 — Open items that are neither defects nor failed gates

These are things not yet known. Each is stated with the direction it cuts.

| Item | Direction | What would close it |
|---|---|---|
| Almería wet-bulb tops at 21.9 °C; **40.5 % of a Dhahran year is above it** (3,551 of 8,760 h, 84 % of September) | **Unknown** — the only two-sided one, and now sized rather than described | KFUPM's humidifying wind tunnel. Not closable by argument, and the physics-informed surrogate is a mitigation, not a substitute |
| Model error 2.48× measurement uncertainty | Against us | More campaigns, or a better fill model. Reported as a negative result |
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

**"Is the work sound?"** Thirty-two defects were found, all thirty-two are fixed, and a passing audit gates every release. Six of them were found because a first-principles model, or a check written against it, refused a bad input rather than absorbing it — which is the argument for building it that way, and the reason the parent company is called Furqan.

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
