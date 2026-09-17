# Incumbent-gap study: pre-registration

**Written and committed on 17 September 2026, before `src/incumbent_gap.py` existed and before any
number in this study was computed.** The harness runs once against this document. A failed
hypothesis stays failed. If a definition here turns out to be wrong, the fix is a declared
revision under "Revisions" with the date and reason. The number above it does not get edited.

## The question

Across the published water analyses the repository holds, how far are the cycles that incumbent
practice permits from Mizan's location-correct, multi-mineral ceiling? In which direction? And
what is that gap worth?

- **Under-cycling:** the incumbent stops below the ceiling, and water is left on the table.
- **Over-cycling:** the incumbent permits cycles beyond a mineral limit it cannot see.

## Prior knowledge, declared

This registration is **not blind**, and it says so here rather than leaving a reader to find out.

1. The repository already reports that the Aramco field water (`ARAMCO_FIELD_VALIDATED`) has a
   silica-bound ceiling of about 5 to 6 cycles (HANDOFF.md, `results/v5b_two_ceilings.csv`). Its
   silica of 26.8 mg/L is **assumed**, carried over from Riyadh brackish groundwater (Al-Mutaz &
   Al-Anezi 2004). It is not a measurement of this water.
2. An independent review in a sibling workspace found the full, calcite-only and bulk-only
   policies chose **identical** actions in all 8 annual bins, so gates C2b and C2c FAILED. Its
   input was the Badruzzaman (2022) Table 1 average, sodium-reconciled, with **silica set to
   zero**. Its full policy chose C = 10, the top of its search grid, in every bin.
3. The rule-of-thumb limits in P3 have closed forms (concentration × cycles), so their values on
   any water are plain arithmetic. What is NOT known in advance is how they compare with M at each
   condition and pH.

What this registration adds is fixed definitions, fixed thresholds and fixed verdict rules. It
does not claim ignorance of the water.

## 1. Water panel

**Registered panel (strict).** Every `chemistry.Water` instance defined in `src/chemistry.py`
(which includes the DOE benchmark waters) that passes **all five** checks of
`chemistry.validate_analysis(water)` at default tolerances, with `silica_declared=False` and
`phosphate_declared=False`. The panel is **enumerated by code**, not by hand. An unmeasured zero
fails, as that function intends.

**Extended panel (secondary, reported, not the verdict of record).** The strict panel plus any
water whose ONLY failed check is `charge_balance`, and by no more than 1 percentage point beyond
tolerance. In practice that admits `ARAMCO_RIYADH_REFINERY_TSE` (−5.25 % against ±5 %). The
repository's closure bracket (`sidestream.charge_closure_bracket`, defect 39) puts its effect on
the ceiling at 0.7 %. H1 to H3 are computed on both panels, and the strict result is the one of
record.

**Rejected candidates for new waters.** Each was checked against the rule "a complete major-ion
analysis with silica, cited by table and page":

| candidate | why rejected |
|---|---|
| Al-Mutaz & Al-Anezi (2004), Salbukh WTP, Table 1 (p. 3), raw water | Na and K not reported; hardness only |
| Biswas et al. (2019), *Chem. Eng. Trans.* 72, 199–204, Table 1 (p. 200), Doha bore water | Na and K not reported; each column is a per-analyte percentile, not a sample (the defect-17 category error) |
| POWER magazine (1 Mar 2017), "Using Reclaimed Water in Power Plant Cooling Applications", Table 1 (source GE) | ranges per ion, not a sample |

No new water is added. **If the panel is one or two waters, that is the headline limitation.**
Percent-of-panel thresholds applied to one water are a single comparison, and the report must say
so in those words.

For each panel water, the report gives: the checks, whether silica and phosphate are measured or
assumed, and the class. The class is **silica-bound**, **calcite-bound**, **gypsum-bound** or
**other**, by M's binding constraint at the acid regime (pH 7.8), taking the mode over the five
conditions. A water is **phosphate-flagged** if `phosphate_screen` at C_M returns "PROGRAMME
REQUIRED" or "UNCONTROLLABLE" at any condition.

## 2. Conditions (the V5 set, not new)

These are the five ambients of `run_controller.AMBIENTS`, with the V5 plant, `rc.TSE` for the
thermal solve, and the fill law from `results/calibration.json`. At each ambient, the temperatures
come from **the incumbent's own operating point**:
`controller.baseline(cond, rc.TSE, rc.TARIFFS, fill_c, fill_n, fixed_cycles=3.0, fixed_ph=7.8,
cw_setpoint_c=32.0, fan_grid=30..100 step 10)`. That is gate V5's call with the V7 baseline cycles.
The seeding is as in `gate_v5`. It gives:

- `T_return` = the baseline's `T_wi`, the hot bulk water leaving the condenser
- `T_basin`  = the baseline's `T_basin` (= `T_wo`), the cold bulk water
- `T_skin`   = the baseline's `T_skin` (= `T_wi` + `controller.SKIN_DELTA_K_DEFAULT`)

The same three temperatures are used for every water and policy at that condition. Temperature is
set by load and weather; the water enters only through water activity. Search range: 1.0 to 30.0
cycles, as `chemistry.max_cycles` uses. A value at 30.0 is reported as "≥ 30 (search bound)".

## 3. pH regimes

- **No acid.** pH is the atmospheric-CO₂ equilibrium pH of the concentrated water
  (`chemistry.ph_atmospheric_equilibrium`) at each policy's own evaluation temperature. For M,
  this is exactly `sidestream.ceiling_with(..., pH=None)`.
- **Acid, primary: pH 7.8.** This is [J]: the incumbent pH setpoint of the V5 baseline
  (`controller.baseline(fixed_ph=7.8)`), not an external citation. It is swept over 7.5, 8.0 and
  8.25. 8.0 is [C] (AlMajnouni & Jaffer, NACE Paper 577, recommended maximum pH). 8.25 is the
  Cycle Ceiling Report's worked example. The pH is held at both evaluation points, as
  `controller._cost_at_ph` does. The free pH at the ceiling is recorded, and any point where
  `ph_free < target` is flagged, because acid cannot raise pH.

## 4. Policies

| id | policy | parameter | source |
|---|---|---|---|
| **P0** | fixed cycles setpoint | 3.0 | [C] `run_controller.V7_BASELINE_CYCLES`; `sidestream.typical_cycles_evidence()` (five operators, 2–4); `tests/test_reference_benchmarks.py::test_the_typical_cycles_baseline_is_now_five_independent_sources` |
| **P1** | `chemistry.langelier_index(conc, T_return, pH) ≤ LSI_max` | LSI_max = **2.5** | [C] Ferguson (2011) IWC-11-77, via `docs/chemistry_evidence.md` §5.1: HEDP's SR-150 limit "equates to LSI limits of 2.5 in a high sulfate cooling water but 2.8 in a high chloride water" |
| **P2** | `corrosion.ryznar_index(conc, T_return, pH) ≥ RSI_min` | RSI_min = **6.0** | [C] UFC 3-230-13 §5-3.4.1 cut at 6, via `src/corrosion.py`. This is an uninhibited criterion. |
| **P3** | P1, AND SiO₂ ≤ S_max in circulating water, AND Mg×SiO₂ ≤ Π_max | at pH > 7.5: S_max = **100 mg/L**, Π_max = **20,000**, Mg as ppm CaCO₃; at pH ≤ 7.5: 200 and 40,000 | [C] Demadis (2003), *Chemical Processing*, guideline figure, via `docs/chemistry_evidence.md` §4.2 |
| **M** | Mizan's ceiling, as below | — | the product |

**M, exactly as the product computes it.**

1. The limits are `chemistry.limits_with_diurnal_margin(T_mean_c=T_basin, T_amplitude_k=5.0,
   programme=None)`. The 5.0 K is the default of `scripts/ceiling_report.analyse`.
2. The scaling ceiling is `sidestream.ceiling_with(water, T_skin, T_basin, limits, pH)`. Calcite,
   gypsum and TCP are evaluated at the skin, and amorphous silica at the basin.
3. Brucite: the largest C with `pH ≤ chemistry.ph_saturation_brucite(T_skin, conc)` and margin 0,
   as enforced in `controller._cost_at_ph`. In the no-acid regime, pH here is the free pH at
   `T_skin`, as `controller.acid_dose_for_ph` computes it.
4. Davies: `sidestream.davies_validity_cycles(water)`. The controller enforces it as a violation,
   so it caps M, and the report flags whenever it binds.
5. **C_M** = the minimum of 2, 3 and 4. The binding constraint is whichever sets the minimum.
6. **Reported, not imposed:** the discharge ceiling (`discharge.binding_ceiling`, monthly
   average), the phosphate screen at C_M, the silica-index validity at the basin pH, and M with
   `programme="standard"` as a phosphate sensitivity.

**Sensitivity sweeps (reported, never verdicts).**

- P1 LSI_max ∈ {0.5 [C Aramco pilot, reported LSI 0–0.5], 1.0 [repo: customer-discovery chemist
  holds 0.8–1.0], 1.4 [C NACE 577 operating LSI], 2.0 [J], 2.5, 2.8 [C IWC-11-77]}.
- P1 evaluated at `T_basin` instead of `T_return`.
- P2 RSI_min ∈ {4.0 [J], 4.5 [J], 5.1 [C NACE 577 operating RSI], 5.5 [J], 6.0}. At a fixed pH,
  RSI = pH − 2·LSI, so P2 is a re-parameterised P1, and the report must say so.
- P3 S_max ∈ {100, 150 [C Demadis 150–180 solubility], 200}, Π_max ∈ {20,000; 25,000; 35,000;
  40,000} [C `chemistry.MG_SILICA_LIMITS`], Mg basis ∈ {CaCO₃ (as the source states), Mg²⁺ (as
  `chemistry.py` adopts)}.
- Acid pH ∈ {7.5, 8.0, 8.25}, for P1, P3 and M.

**If ANY cited P3 variant comes within 0.5 cycles of C_M on a water, the report names it,
whatever the primary H3 verdict.**

## 5. Statistics

- `gap_P(condition) = C_P − C_M`. Positive means the incumbent permits more (over-cycling);
  negative means it permits less (under-cycling).
- A water's **summary gap** is the median of the five condition gaps.
- If either value in a gap sits at the 30-cycle search bound, the gap is flagged as a bound, not a
  measurement.

## 6. Hypotheses, thresholds and what each means

All verdicts use the acid regime at pH 7.8 unless stated. The no-acid regime is reported beside
them and is not scored.

**H1.** On ≥ 50 % of strict-panel waters, |summary gap(P1, M)| ≥ 1.0 cycle.
- *Holds:* an inhibited-LSI incumbent sits a cycle or more from the location-correct ceiling on
  most waters, so the gap is material, in the direction reported.
- *Fails:* on most waters LSI practice lands within a cycle of M, so any gap claim must be
  restricted to the waters where it opens.

**H2.** On every strict-panel water classed silica-bound, gap(P1, M) ≥ +0.5 at **all five**
conditions: acid-dosed LSI control over-cycles into silica.
- *Holds:* the safety claim, that M sees a limit LSI cannot, stands with a number.
- *Fails:* LSI's own bound already stops short of silica, so silica is not a safety differentiator
  on that water.
- *Not testable:* there is no silica-bound water in the panel, and the claim is unsupported by
  this panel. This is recorded as NOT TESTABLE, never as PASS.

**H3 (adversarial).** On ≥ 50 % of strict-panel waters, |summary gap(P3, M)| ≤ 0.5 cycle.
- *Holds:* a free rule of thumb reproduces the ceiling. The claim narrows to "a rule of thumb gets
  you most of the way", and the report says exactly that.
- *Fails:* the cheap rule is not a substitute on most waters. The report states in which
  direction.

**H4 (harness reproduction of the review).** The input is
`chemistry.balance_sodium(chemistry.ARAMCO_RECLAIMED)` (SiO₂ = 0, PO₄ = 0, the review's input).
At all five conditions, on the review's grids (cycles {3, 5, 7, 10} × pH {7.5, 8.0, 8.5}), the
highest grid cycles P1 permits equals the highest grid cycles M permits. The calcite-only policy
(SI_calcite ≤ 2.0 at the skin) and the bulk-only policy (all `OPERATING_LIMITS` at `T_return`)
are computed beside it as C2b/C2c analogues and are not scored.
- *Holds:* this harness agrees with the review's null on the review's input.
- *Fails:* the harness disagrees with a prior result. **Suspect the harness first**, and interpret
  no other verdict until the disagreement is explained.

**H4b.** The same test on `ARAMCO_FIELD_VALIDATED` (declared, assumed silica 26.8 mg/L).
- *Holds:* the review's null survives declared silica, so the value claim on this water is empty.
- *Fails:* the null is conditional on silica = 0, and the input that decides it is unmeasured on
  this water.

**Grid feasibility for H4/H4b.** A grid point is permitted if the policy's constraints hold at
that (cycles, pH). For M, that means the diurnal-margin saturation limits, brucite and Davies.

## 7. Monetising (computed after the verdicts)

- **Tower:** 4.2 MW heat rejection, the Badruzzaman (2022) tower. At each condition, evaporation
  E = `m_evap` × 4200 / `Q_cond_kW` from the same baseline thermal solve, and circulating flow
  m_w = 478 × 4200 / `Q_cond_kW`. That scales the repository's own tower model; no new number is
  introduced.
- **Cost:** `controller._water_cost_per_h(controller.water_balance(E, m_w, C),
  run_controller.TARIFFS)` × 8760 h. This is the Cycle Ceiling Report's annualisation: makeup at
  USD 2.144/m³ plus discharge at USD 0.971/m³ (Marafiq schedule, [C]). It is not hours-weighted,
  because the V5 conditions carry no hour weights, so it reads as an at-condition annual rate. The
  median and the range over conditions are reported. Acid and antiscalant are excluded.
- **Under-cycling** (C_P < C_M): value = cost(C_P) − cost(C_M) per year.
- **Over-cycling** (C_P > C_M): break-even X = cost(C_M) − cost(C_P) per year. "The ceiling pays
  for itself if an avoided scaling event is worth more than X per year." No cleaning or
  replacement cost is cited anywhere in the repository (`docs/gemini_research_prompt_2.md` item 8
  records the search that found none), so only the break-even is presented.

## 8. Harness self-suspicion checklist (tested in `tests/test_incumbent_gap.py`)

- The LSI sign: positive means scale-forming, and LSI rises with cycles.
- Ca is converted to CaCO₃ and HCO₃ to alkalinity as CaCO₃ inside `langelier_index`, and neither
  is double-converted.
- Mg in the Mg×SiO₂ rule is on the stated basis, and SiO₂ is taken as SiO₂, not as Si.
- Silica is evaluated at the basin, calcite at the skin, and the incumbent at bulk.
- The harness reproduces
  `test_acid_dosing_walks_a_calcite_only_controller_into_the_gypsum_wall` through its own ceiling
  function.

## Revisions

None.
