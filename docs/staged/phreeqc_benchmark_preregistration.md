# Pre-registration: multi-composition PHREEQC benchmark of the chemistry engine

**Written and committed 17 September 2026, BEFORE PHREEQC is run on this grid.**
Branch `fix/validation-integrity`. Staged defect **53** if the "validated
against PHREEQC" wording turns out to overclaim.

## 0. Why

Until now the engine's comparison with PHREEQC is a single composition: the
USGS worked example of a solution at gypsum saturation (25 °C, Ca = SO4 =
0.01508 mol/kgw), where the engine returns SI_gypsum **-0.0163** against a
published 0.000. One point at one temperature, one mineral, I ≈ 0.04. The
documents describe the engine as checkable against, and in places validated
against, PHREEQC. This benchmark measures that across compositions,
concentration, temperature and minerals.

## 1. Reference

* PHREEQC 3.9.0-17591, Windows x64 console `phreeqc.exe`, SHA-256
  `5147679081f53abd4a40d1ba07b3cf7ee5078df9d3510c6378ff5d45db6437c8`.
* Its unmodified `phreeqc.dat`, SHA-256
  `5745f0be5f5f585e72c647895b9b182388ab1f018db3d654529ce2461de499f1`.
* Run from outside the repository; the deck, the raw selected output, the
  parsed values, both hashes and the exact command are committed under
  `data/reference/phreeqc_benchmark_20260917/`.
* Run **once**. If the run fails for a setup or transport reason (the
  executable does not start, a row is missing, a total does not round-trip),
  that is an execution error, fixed and re-run, and recorded as such. It is
  not a result and cannot be used to change anything below.

## 2. Grid

**Compositions** -- every module-level `Water` in `src/chemistry.py` that
passes `validate_analysis(w)` with its default arguments, plus the DOE
synthetic recipe waters the repo carries. Evaluated before registration
(inputs only, no SI computed):

| composition | why included | pH |
|---|---|---|
| `ARAMCO_FIELD_VALIDATED` | passes all five checks | 7.40 |
| `DOE_SYN_MWW_NF_COC4` | DOE recipe (Table 4.2.1) | 7.20 |
| `DOE_SYN_MWW_NF_COC4_TABLE_2_3_2` | DOE recipe (Table 2.3.2) | 7.20 |
| `DOE_SYN_MWW_COC4` | DOE recipe (Table 2.3.2) | 8.80 |

Every other analysis fails `validate_analysis` and is excluded: the three DOE
field waters (Na and K unmeasured, charge imbalance -91 % to -130 %),
`ARAMCO_RECLAIMED` (four checks), `ARAMCO_GROUNDWATER` and
`ARAMCO_FIELD_NO_SILICA` (silica, and for groundwater phosphate, undeclared),
`ARAMCO_RIYADH_REFINERY_TSE` (charge balance -5.25 % against ±5 %).

**Cycles of concentration** 1, 2, ..., 8, by `Water.concentrate(C)`, which
multiplies every total and keeps pH.

**Temperatures** 25, 35, 45, 55 °C.

4 compositions × 8 cycles × 4 temperatures = **128 solutions**.

## 3. Holding the inputs identical

The most likely source of false disagreement is the two codes being given
different waters. So:

* **Totals.** Each total is passed to PHREEQC in `units mol/kgw`, `-water 1`,
  as exactly the molality the engine uses, `Water.molality()` (mg/L × 1e-3 /
  molar mass, i.e. unit density and no TDS correction -- the engine's
  convention, reproduced rather than "corrected"). Elements: Ca, Mg, Na, K,
  Cl, S(6) (= SO4), N(5) (= NO3), Si (= SiO2), P (= PO4). A zero total is
  omitted.
* **pH.** Fixed at the analysis pH as hydrogen-ion activity in both codes,
  the same at every cycles count and temperature, exactly as
  `saturation_state(w.concentrate(C), T)` does. No `charge` keyword in
  PHREEQC, so PHREEQC does not adjust pH.
* **Charge balance.** Neither code adjusts anything during the calculation.
  The engine does not balance inside `saturation_state`; PHREEQC is given no
  `charge` keyword on any element. The only balancing is what is already in
  the shipped analysis (`ARAMCO_FIELD_VALIDATED` was Na-balanced by
  `balance_sodium` when it was defined), and that is an input identical to
  both. PHREEQC's reported percent charge error is recorded, not acted on.
* **Carbonate.** The engine's `HCO3` input is a mass-balance total over the
  bicarbonate-bearing species (free HCO3- plus CaHCO3+, MgHCO3+, NaHCO3);
  carbonate species are computed from it at the fixed pH and CO2(aq) is not
  represented. Neither `Alkalinity` (which PHREEQC shares with phosphate,
  silicate, carbonate and OH-) nor total C(4) (which includes CO2(aq) and
  carbonate) is that quantity. So PHREEQC is given C(4) at the multipliers
  f = 1.00, 1.10, 1.25, 1.50, 2.00, 3.00 of the engine's HCO3 molality, all
  in the same single run; for each, PHREEQC reports S = the sum of its
  bicarbonate-bearing species (HCO3-, CaHCO3+, MgHCO3+, NaHCO3, KHCO3). The
  reference value of every quantity is linearly interpolated in log10(S)
  between the two adjacent multipliers that bracket S = the engine's HCO3
  molality. A point with no bracket is scored as **out of tolerance**, not
  dropped.
  A seventh block per point with `Alkalinity` = the engine's HCO3 (in eq/kgw)
  is run as a **diagnostic only**, so the effect of this choice is visible.

## 4. Minerals and the quantity compared

| mineral | PHREEQC phase | engine key | scored where |
|---|---|---|---|
| calcite | `Calcite` | `SI_calcite` | every point |
| gypsum | `Gypsum` | `SI_gypsum` | every point |
| amorphous silica | `SiO2(a)` | `SI_silica_am` | SiO2 > 0 only (`ARAMCO_FIELD_VALIDATED`) |
| hydroxyapatite | `Hydroxyapatite` | `SI_hydroxyapatite` | PO4 > 0 (every composition) |

Hydroxyapatite is the only phosphate phase in both: `phreeqc.dat` has no
whitlockite/β-TCP, and the engine flags its TCP constant as a literature
value, not a phreeqc.dat transcription.

**Gated quantity:** ΔSI = SI_engine - SI_PHREEQC, each code with its **own**
equilibrium constants. The claim under test is agreement with PHREEQC, so a
constant transcribed from a different database version is part of what is
being tested, not something to subtract. The same-constant difference
(PHREEQC SI + PHREEQC log K - engine log K) is reported beside it as a
diagnostic, so constants and speciation can be separated.

## 5. Tolerances, justified before running

Two things are known before running, and neither comes from this grid.

**(a) Activity models.** The engine uses Davies for every ion; PHREEQC uses
the WATEQ Debye-Hückel (Truesdell-Jones) form with ion-size and b parameters
from `phreeqc.dat` (Ca+2 5.0/0.165, SO4-2 5.0/-0.04, HCO3- 5.4/0.0078, HPO4-2
5.0/0). The difference log γ(Davies) - log γ(TJ) at 25 °C, from the formulas
alone, is:

| I | Ca+2 | SO4-2 | HCO3- | calcite part | gypsum part | HAP part (5 Ca + 3 HPO4) |
|---|---|---|---|---|---|---|
| 0.05 | -0.017 | -0.007 | -0.004 | -0.021 | -0.023 | -0.109 |
| 0.10 | -0.021 | -0.000 | -0.005 | -0.025 | -0.021 | -0.117 |
| 0.20 | -0.015 | +0.026 | -0.001 | -0.016 | +0.011 | -0.020 |
| 0.30 | +0.001 | +0.062 | +0.005 | +0.005 | +0.062 | +0.152 |
| 0.50 | +0.046 | +0.148 | +0.021 | +0.067 | +0.194 | +0.615 |

So for a two-ion mineral the activity model alone moves SI by about 0.02-0.03
up to I = 0.2, 0.06 by I = 0.3 and 0.2 at I = 0.5 -- which is why the band
widens with I and why nothing above 0.5 is gated (the engine itself flags
Davies invalid there, defect 26). The existing single-point result, -0.0163
at I ≈ 0.04, sits inside the 0.05 band with the complexation fixed by defect
24, which is the evidence that 0.05 is achievable at low I rather than
aspirational.

**(b) Constants.** Read from the two source files, not from a run:
`phreeqc.dat` 3.9.0 carries `Calcite -analytic -67.87 -5.1813e-2 0 30.25746`
and `Gypsum -analytical_expression 72.244 -1.474e-2 -4040 -23.7823` (Appelo
2015), while the engine transcribes an older phreeqc.dat
(`-171.9065 -0.077993 2839.319 71.595` and `68.2401 0 -3221.51 -25.0627`);
SiO2(a) is -2.71 with dH 3.34 kcal in 3.9.0 against 3.59 in the engine;
hydroxyapatite matches. log K(engine) - log K(3.9.0):

| | 25 °C | 35 °C | 45 °C | 55 °C |
|---|---|---|---|---|
| calcite | -0.032 | -0.011 | +0.011 | +0.033 |
| gypsum | -0.032 | +0.008 | +0.054 | +0.106 |
| SiO2(a) | 0.000 | +0.006 | +0.012 | +0.017 |
| hydroxyapatite | 0 | 0 | 0 | 0 |

These enter ΔSI with the opposite sign. **They are NOT absorbed into the
tolerance.** They are declared here as the a priori expectation: gypsum at
45-55 °C is expected to disagree by more than the band on constants alone,
and if it does, that is a finding about the engine, not about the tolerance.

**Registered tolerance τ, by the engine's speciated ionic strength I at that
point:**

| I (mol/kg) | τ, one- and two-ion minerals (calcite, gypsum, SiO2(a)) |
|---|---|
| I ≤ 0.1 | 0.05 |
| 0.1 < I ≤ 0.5 | 0.10 |
| I > 0.5 | reported, not gated |

**Hydroxyapatite: 4τ.** SI of Ca5(PO4)3OH carries 5 Ca and 3 HPO4 activities,
so the same per-ion agreement that gives |ΔSI| ≤ τ for a two-ion mineral gives
8/2 = 4 times that for eight ions (row "HAP part" above is 4-6 times the
two-ion rows for exactly this reason). The share within the **unscaled** τ is
also reported, so the scaling is visible and not hidden in the verdict.

Engine-side ionic strengths on this grid were computed before registration
(inputs only): all 128 points lie between 0.025 and 0.21, 54 at I ≤ 0.1 and
74 in 0.1-0.5, none above 0.5.

## 6. Pass criterion

Gated comparisons: every (point, mineral) pair scored per section 4 with
I ≤ 0.5 -- 128 calcite + 128 gypsum + 32 SiO2(a) + 128 hydroxyapatite = 416.

**PASS** if and only if **both**:

1. at least **95 %** of all gated comparisons are within tolerance, and
2. no single mineral has fewer than **90 %** of its comparisons within
   tolerance.

Otherwise **FAIL**, reported as FAIL, with the test in
`tests/test_phreeqc_grid.py` marked `xfail(strict=True)` against staged defect
53 -- never a changed tolerance, share or grid.

## 7. What is reported whatever the verdict

* shares within tolerance: overall, per mineral, per temperature, per
  composition, per I band;
* the worst ten |ΔSI| with composition, cycles, T, I;
* the same-constant diagnostic and the Alkalinity-mapping diagnostic;
* PHREEQC's percent charge error range.

Where disagreement concentrates, the first suspects are this benchmark's own
inputs -- units, mol/kgw vs mg/L, °C vs K, log10 vs ln, the carbonate and
charge handling above -- and they are checked before the engine or the
reference is blamed.

## 8. Wording

Every "validated against PHREEQC" style claim in the repository is replaced by
the measured statement, whatever the verdict.

---

## Addendum, 17 September 2026 -- execution error in run 1, before any result was read

Run 1 of the committed deck stopped at solution 497 of 896 with PHREEQC's
*"Alkalinity has not converged ... Is non-carbonate alkalinity greater than
total alkalinity?"*. Solution 497 is the **Alkalinity diagnostic block**
(section 3) for `DOE_SYN_MWW_NF_COC4_TABLE_2_3_2` at 2 cycles, 45 °C: that
recipe carries 0.48 mM phosphate against 0.40 mM bicarbonate, so phosphate
alkalinity alone exceeds the alkalinity given. This is the reason section 3
gives for not using Alkalinity as the mapping, arriving as a hard error.

Per section 1 this is an execution error, not a result. What was done:

* the partial `selected.tsv` and `deck.out` of run 1 were **deleted without
  being parsed, scored or opened**; its console log and provenance are kept in
  `data/reference/phreeqc_benchmark_20260917/execution_error_run1/`;
* the Alkalinity diagnostic blocks are removed from the deck. The mapping
  diagnostic becomes the f = 1.00 block already in the deck (C(4) = the
  engine's HCO3 molality, i.e. total inorganic carbon), which cannot fail
  this way;
* **nothing gated changes**: grid, compositions, C(4) bracket, minerals,
  tolerances and pass criterion are exactly as registered above.

Also recorded: the registered executable (SHA-256 as in section 1, installed
by `phreeqc-3.9.0-17591-x64.msi`) prints the banner *PHREEQC_3.8.9, October
13, 2025*. The binary and database are identified by hash; the version label
is reported as both strings.
