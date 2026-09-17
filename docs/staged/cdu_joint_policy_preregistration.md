# CDU side: joint cycles/temperature policy, load-shape and plausibility checks. Pre-registration

**Written and committed 17 Sep 2026, before any of the computations below ran.**
Branch `review/cdu-side`, branched from `water-modes-and-cdu` at a0c967d. Each
study runs once. A failure is reported as a failure. No threshold here moves
after a result is known.

Tags: **[C]** checked against a named source this session. **[R]** already cited
in the repository and not re-read this session. **[J]** a judgement with no
source, stated so it can be challenged.

---

## 0. What is being tested, and why

Slide 6 of `docs/deck_2026_09_12.md` comes from `scripts/generate_pitch_artifacts.py`
→ `results/pitch_artifacts.json`, last regenerated at a9dbfa5 (11 Sep 2026).
That run came before defects 44–50. It is **not** the output of
`src/cdu_hybrid.py`, which is a separate chilled-water study registered on 7 Sep.

The deck's bounded policy (`hybrid_supervisor.evaluate(..., cycles=5,
enforce_chemical_floor=True)`) holds cycles at 5 and raises the facility-water
temperature to the silica floor. The cheaper response might be to lower cycles,
which lowers the floor. If so, the "+$107k / +$1.6M / +$9.8M per year" line
overstates what chemistry-awareness costs.

## 1. Common inputs (identical to the deck study, imported and not retyped)

- Regions, IT load, tariffs, currency, weather profiles, `cdu.sized_for(q_it,
  delta_t_k=10)`, `m_w_pri = q_it/20`, `m_a_rated = q_it/22.5`: imported from
  `scripts/generate_pitch_artifacts.py` (`REGIONS`, `diurnal_profile`).
- Makeup water: `run_controller.TSE` (the deck study's water), with the silica floor exactly as
  the product computes it: `chemistry.temperature_floor_for_silica`.
- Fill law: `results/calibration.json`. pH: the `evaluate` default, 8.25.
- Engine: this worktree at the commit that adds this file. The only planned
  source change is a refactor of `hybrid_supervisor.evaluate`, so that a
  caller can price a tower state the caller has chosen. It must leave the
  default path byte-for-byte equivalent in behaviour, and
  `tests/test_cdu_controller.py` must pass before the run.
- `hybrid_supervisor.solve_free_cooling` is memoised in the study process
  only, keyed on its full argument list. A memo cannot change any answer.
- Tolerance for a "material" violation: SI − limit > 1e-3, the same as defect 40.
- Annualisation: the same as the deck. Take the sum over solved hours of the hourly delta, times 365. Unsolved hours are counted and reported (defect 43).
- Output goes to a fresh directory, `results/cdu_joint_policy_20260917/`. The run
  refuses to start if `run.json` already exists.

## 2. Policies

- **B0, blind.** `evaluate(enforce_chemical_floor=False, cycles=5)`: full fan,
  the coldest water the tower makes.
- **B1, the deck policy.** `evaluate(enforce_chemical_floor=True, cycles=5)`.
- **B2, joint.** For each hour, for each cycles value c in {2, 3, …, 10} (the
  integer grid of `src/cdu_hybrid.py`), the candidate set is:
  (a) the bounded state `evaluate(enforce=True, cycles=c)`, and
  (b) every point of the supervisor's own 9-point fan grid (15–100 %) whose
  facility-water temperature is at or above floor(c), priced at cycles c.
  A candidate is **admissible** when all four hold:
  - `evaluate` returned a state;
  - the floor was reached (`floor_unreachable` is False);
  - no mineral in `chemistry.OPERATING_LIMITS` exceeds its limit by more than 1e-3. The limits are silica at the facility water and calcite and gypsum at the plate wall;
  - the cold-plate return is within its limit, which `evaluate` enforces by flow.
  B2 chooses the admissible candidate with the lowest `cost_per_h`. If no
  candidate is admissible, the hour is **B2-infeasible**. It is counted, and B2
  takes B1's state for every metric. That choice works against the hypothesis.
  No equipment limit is added that B1 lacks. The model has no secondary-pump flow cap
  (see §5, P-FLOW), and the maximum flow ratio is reported.
  The admissibility rule is **stricter than B1**, which enforces only silica.
  That asymmetry also works against the hypothesis.
- **B1f, a diagnostic only, not scored.** This is B2 with c fixed at 5. It separates
  the part of B2's advantage that comes from choosing the fan from the part that comes
  from choosing cycles.

## 3. Metrics, per region

- Annual cost delta against B0, in USD/yr, for B1, B2 and B1f. The "cost of bounding" is Δk = cost(Bk) − cost(B0).
- Makeup water, in m³/day and as a % change against B0.
- Silica scaling hours: SI_silica_am > 1e-3. Also any-mineral material hours.
- Floor-unreachable hours, B2-infeasible hours and unsolved hours.
- PUE, both as the mean of hourly ratios (as the deck prints it) and as the ratio of totals. Also the maximum secondary flow ratio.
- A histogram of the cycles B2 chooses, and B2's water cost.
- B0 and B1 are also compared with the values stored in `results/pitch_artifacts.json`, to measure the staleness of the deck table.

## 4. Hypothesis H-B2, and what each outcome means

**H-B2:** in at least **3 of 4** regions, Δ2 ≤ 0.5 × Δ1.
A region where Δ1 ≤ 0 cannot be scored and counts as **not supporting** H-B2.

- **PASS.** The deck's fixed-5-cycles figures overstate the cost of chemistry-awareness
  in most regions. The slide-6 cost line should be replaced by B2's Δ, together with the
  water that B2 spends (lower cycles means more blowdown). The pitch then says:
  "the chemistry costs little if cycles are allowed to move, and choosing that
  is a decision neither an energy-only nor a water-only optimiser can make."
  If Δ2 < 0, the finding is only that B0 (full fan) is not cost-optimal inside this model.
  It is **not** an energy-saving claim, because the model has no trim chiller
  (see P-PUE).
- **FAIL.** Holding cycles at 5 is not what makes bounding expensive. The deck
  line stands, subject to the re-run numbers, and the pitch must not offer
  "lower the cycles" as a cheap escape.
- **Split (2 of 4).** Report per region. Claim nothing in aggregate.

## 5. Plausibility checks against published practice

A computed number that crosses one of these checks gets a root cause before it is quoted.

| Check | Threshold | Basis |
|---|---|---|
| P-PUE | A day-mean PUE above **1.54** for a chiller-less liquid-cooled site contradicts practice | [C] Uptime Institute Global Data Center Survey 2025: global average PUE 1.54, all site types (uptimeinstitute.com survey summary). [R] EnEfG ≤ 1.2 for new German sites, cited in `generate_pitch_artifacts.py` |
| P-T (class) | Facility-water supply below 17 °C (inside W17), or a design that needs a chiller to deliver it, is a chilled-water design and not current DLC practice | [C] ASHRAE TC 9.9, *Emergence and Expansion of Liquid Cooling in Mainstream Data Centers* (2021) p. 4: classes W17/W27/W32/W40/W45/W+, named for their upper supply limit, lower limit 2 °C. p. 14: "Most cold plate solutions today can live easily on W32 water". p. 25: realising the efficiency benefit "largely means eliminating mechanical cooling equipment such as chillers". [C] NVIDIA blog, J. Parker, 21 Jun 2026, *Hotter Than a Hot Tub*: liquid "up to 45 degrees Celsius", and coolant "entering … at 45 degrees Celsius exits at roughly 55 degrees" |
| P-RET | The model's cold-plate return limit (42 °C) is compared with the OEM operating point (≈ 55 °C return at 45 °C inlet) | [C] NVIDIA blog as above. **Sensitivity S-OEM:** B0/B1/B2 re-priced with `return_limit_c = 55.0` and nothing else changed. The tower states are identical and cached |
| P-APP | CDU approach 5 K, compared with the OCP Deschutes 3 °C spec | [R] `src/models/cdu_model.py` `DESCHUTES_SPEC` (OCP, Feb 2026). The spec PDF returned HTTP 403 this session, so it was not re-read |
| P-WUE | Makeup L/kWh(IT) must not exceed the all-latent ceiling (3.6 MJ/kWh ÷ h_fg ≈ 2.4 MJ/kg) × C/(C−1) × (1 + pump heat/IT) by more than 5 % | [J] physics bound. Context: [C] NVIDIA blog as above, "roughly 2.6 million gallons per megawatt per year for conventional cooling-tower-based systems", ≈ 1.12 L/kWh annual mean |
| P-CAP | The model sends 100 % of IT heat to liquid | [C] NVIDIA blog as above: the Rubin generation is "100% liquid cooling". No official capture fraction was found for earlier generations, so the fraction for those is **unverified**, not assumed |
| P-FLOW | A secondary flow ratio above **1.5×** nominal is outside any plausible pump operating range | [J]. No pump run-out source is held |

## 6. Load-shape sensitivity: B0 silica scaling hours only

The deck says: "Blind free cooling runs the loop supersaturated in silica for 12 to 24 hours out of every 24."
The deck study's IT load is **flat at nameplate for all 24 h**.

- **L0**: flat 1.00. This is the deck study, recomputed in the main run.
- **L1, NLR measured**: a flat fraction equal to the job mean divided by the peak 5-min mean of
  `combined_mean_kW`, over the full-coverage bins of `power_5min.csv`
  (Vercellino et al., NLR Data Catalog submission 312, DOI 10.7799/3025227;
  2-node H100 LoRA training). The job lasts about 90 minutes, so it cannot supply a 24-h
  shape. It is used only as evidence of how flat training load is. No data is
  copied into this repository, it is not scaled to a MW claim, and it is not mapped to coolant heat.
- **L2, Google PowerData2019 median**: diurnal peak-to-trough amplitude **0.060** of
  capacity (Startup Astra `byte_level_validation.md`, measured, median over 57 PDUs).
  The load is q(t) = nameplate × [1 − 0.060 × (1 + cos(2π(t − t_cold)/24))/2], where t_cold is the coldest-T_db hour of that
  region's profile. The trough therefore falls on the coldest hour, the worst case for silica [J].
- **L3, PowerData2019 maximum**: the same shape with amplitude **0.155**, the largest across the 57 PDUs.

**Verdict rule.** The "12 to 24 of 24" conclusion **depends on load shape** when either holds:
- under any of L1–L3, any region's B0 silica scaling-hour count moves by ≥ 3 hours from L0 [J];
- the cross-region range leaves [12, 24].
Otherwise it does not depend on load shape within the measured range.

**Weather dependency, flagged and not tested here.** Dhahran uses the highest-mean-wet-bulb
day of `results/tmy_hourly.npy` (TMYx). The weather branch is investigating a TMYx
humidity mismatch in that file. The other three regions use sinusoids at constant RH [A].

## 7. `src/cdu_hybrid.py`: defect-corrected re-score, thresholds untouched

- **R1.** The registered script runs **unchanged** on the current engine:
  `--repo <worktree> --output results/cdu_hybrid_rescore_20260917`. The H1a/H1b/H2/H3/H4
  verdicts are compared with `results/cdu_hybrid_verified/run.json`.
- **R2.** The same run, with the script's three local reproductions of fixed defects
  patched by a wrapper, without editing the registered file:
  - acid charged on blowdown + drift (defect 25);
  - water through `controller._water_cost_per_h` (defect 30);
  - skin rise `controller.SKIN_DELTA_K_DEFAULT` (defect 44) in place of 8.
  Output goes to `results/cdu_hybrid_rescore_corrected_20260917`. Verdict thresholds do not change.
- H1b is a **gypsum** hypothesis. The safety branch's staged defect 54 (acid sulfate
  missing from the gypsum index) applies to `chemistry_at`. It is recorded as a
  dependency and not corrected here.

## 8. Material boundary for defect 46: method fixed in advance

- Wetted surfaces come from sources only. A cycles limit is derived only where a cited chloride
  criterion exists for that alloy, using the `corrosion.py` arithmetic
  (limit ÷ makeup Cl):
  - [R/C] Buecker & Janikowski, Power Engineering, 10 Oct 2019: 304 ≤ 150 mg/L and 316 ≤ 400 mg/L, for neutral pH, 35 °C, flowing water and clean surfaces. No numeric value is given for other alloys.
  - [C] Alfa Laval, *Guideline on water characteristics to avoid corrosion*, fusion-bonded PHE (100 % stainless, SS316), Table 1: at 25 °C, 1000 ppm (pH 7) and 6000 ppm (pH 9); at 50 °C, 300 and 1500 ppm; linear interpolation in pH is permitted.
    Applied at pH 8.25, using the tabulated row at or above the wall temperature, with no temperature interpolation [J].
  - Duplex 2205, titanium and Cu-Ni: **no criterion held, so none is derived.**
- Waters: `ARAMCO_RIYADH_REFINERY_TSE` (defect 46's water) and `run_controller.TSE`.
