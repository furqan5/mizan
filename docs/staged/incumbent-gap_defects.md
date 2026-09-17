# Staged defects from the incumbent-gap study

These are staged here and **not** entered in `docs/defect_register.md`. The numbers 57–58 were
allocated to this study. No count anywhere else has been changed.

---

## 57: the brucite saturation pH pairs a hydroxide-form log K with a proton-form enthalpy

**Where.** `src/chemistry.py::ph_saturation_brucite`. It is enforced by
`controller._cost_at_ph` (defect 45).

**What.** The function writes the reaction as `Mg(OH)2 = Mg+2 + 2 OH-`, with log K −11.18 and ΔH
−27.1 kcal. That log K is the hydroxide form. It is the proton-form value, 16.844, minus 2 × 14.0.
But −27.1 kcal is the enthalpy of the **proton form**, `Mg(OH)2 + 2 H+ = Mg+2 + 2 H2O`.

The thermodynamic cycle sets the hydroxide-form enthalpy at −27.1 + 2 × 13.362 = **−0.376 kcal**,
using the same water-ionisation enthalpy the function already applies to Kw. The function then
adds Kw's temperature dependence on top, so the temperature effect is counted almost twice.

**Size, computed in this session on `ARAMCO_FIELD_VALIDATED` at one cycle:**

| T | pH_s as implemented | pH_s, proton form (consistent) |
|---|---|---|
| 25 °C | 9.940 | 9.952 |
| 44.85 °C (V5 Dhahran summer skin) | **8.714** | **9.337** |

The two forms agree at the reference temperature and diverge by 0.62 pH units at the skin. The
direction is conservative: the criterion bites 0.6 pH units too early at hot skins.

**Consequence, with this caveat: nothing was rerun beyond this study.**

- **In this study.** With no acid, brucite binds M at 1.19 (Dhahran) and 1.30 (Riyadh) cycles.
  With the consistent constant it would bind at 3.435 and 3.742, and calcite would bind first. No
  registered verdict is affected: brucite binds nowhere in the scored acid regime, and
  `tests/test_incumbent_gap.py` asserts that.
- **In the controller.** The optimiser searches pH 7.0–9.0 and enforces the criterion at the skin.
  At a 44.85 °C skin, any pH above 8.714 is currently rejected. The optimum pH values in the V5,
  annual and CDU results should be checked against the corrected limit.
- **In the HANDOFF.** The claim that the criterion "bites only at 50 C" was calibrated on the
  constant as implemented.

**Verify before fixing.** Open the database file and confirm the Brucite entry's reaction form
and delta_h. This session did not read phreeqc.dat. The argument above rests on the thermodynamic
identity alone, and it holds whichever database supplied −27.1.

---

## 58: the repository carries two incompatible magnesium-silica rules, and chose a unit basis by fit

**Where.** The rule appears twice:

- `src/chemistry.py`, the block above `MG_SILICA_LIMITS`: for pH > 7.5 a sum rule
  `Mg + SiO2 <= 17 000`, and a product rule with Mg taken as Mg²⁺.
- `docs/chemistry_evidence.md` §4.2, transcribing Demadis (2003): for pH > 7.5, "SiO₂ < 100 ppm
  **and** Mg × SiO₂ < 20,000", "where Mg is expressed as ppm CaCO₃".

**What.** For pH > 7.5 the two transcriptions give different rules (a sum of 17,000 against a
product of 20,000 plus a silica cap). They also state the magnesium basis differently.
`chemistry.py` states its reason for choosing Mg²⁺: "Since plants demonstrably operate at 3.5-5.0
cycles on this water, the Mg-as-Mg2+ convention is the one consistent with reality". That is a
unit convention selected because it agrees with observation, which is fitting.

**Why it matters, from this study's output.** On the rule's stated basis (CaCO₃, 20,000, SiO₂ ≤
100), P3 caps the Dhahran water at 2.10 cycles, below the 3.5 its pilot ran clean. On the Mg²⁺
basis, variants at 20,000–25,000 land within 0.5 cycles of Mizan's ceiling on that water. On the
Riyadh water, the variants that land within 0.5 cycles use the CaCO₃ basis. Which basis is
"right" decides whether a rule of thumb reproduces the product's ceiling. The repository answers
that question two ways, and on one of them it chose the answer from the data.

`max_cycles_mg_silicate` is enforced nowhere, because brucite replaced it (defect 45). So no
shipped ceiling is wrong because of this. The defect is in the evidence base any novelty argument
against rules of thumb must cite.

**Fix direction.** Retrieve the Demadis (2003) figure. Record its basis and its pH > 7.5 form once.
Carry the other variant only as a labelled sensitivity.
