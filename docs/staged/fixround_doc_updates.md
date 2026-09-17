# Staged document updates — branch `fix/source-transcription-and-permit`

Every document number this branch made stale, as `file:line — old → new`. Line
numbers are at this branch's commits. Nothing here has been applied: these are
for the documentation pass. "New" values come from runs made on this branch
in this session. Where a sentence, not a number, has to change, the new reading
is given in words.

## Defect 67 — Riyadh TSE silica 18 → 8 mg/L

- `docs/chemistry_evidence.md:72` — "SiO₂ 18.0 mg/L, against the 26.8 imported from brackish groundwater" → "SiO₂ 8 mg/L as printed (18.0 until defect 67, a text-layer misread), against the 26.8 imported from brackish groundwater"
- `docs/handoff_external.md:63` — "SiO₂ **18.0 mg/L measured**" → "SiO₂ **8 mg/L measured** (as printed; defect 67)"
- `docs/handoff_external.md:70` — "$88,976/yr" → "$88,984/yr"
- `docs/handoff_external.md:71` — "$266,928 installed" → "$266,953 installed"
- `docs/defect_register.md:57` (defect 50's row) — "SiO2 is 18 mg/L, so **calcite binds before silica does**" → "SiO2 is 8 mg/L (defect 67), so **calcite binds before silica does**". The conclusion survives; the number does not
- `modelica/README.md:52` — "on measured makeup silica of 18 mg/L" → "on makeup silica of 18 mg/L, the value carried before defect 67 (the printed assay says 8; this run has not been redone)". The table under it (0.908 → 1.105, 10.5 %, 11.8 h) is the 18 mg/L run and stays until the model is re-run
- `docs/incumbent_gap.md:22–24` — "H2 holds with a smallest gap of +3.90" → "H2 holds on one silica-bound water, Dhahran (assumed silica), smallest gap +7.66; Riyadh is calcite-bound"
- `docs/incumbent_gap.md:48` — "**measured** 18.0 … silica-bound at all 5 conditions" → "**measured** 8.0 … calcite-bound at all 5 conditions"
- `docs/incumbent_gap.md:51` — "**2 are silica-bound**, **0 are calcite-bound**" → "**1 is silica-bound** (Dhahran, silica assumed), **1 is calcite-bound** (Riyadh, silica measured)"
- `docs/incumbent_gap.md:75` — "3.00 (−3.72) | 11.41 (+4.69) | 1.64 (−5.08) | 4.95 (−1.77) | **6.72**, silica" → "3.00 (−5.91) | 11.41 (+2.50) | 1.64 (−7.27) | 7.43 (−1.48) | **8.91**, calcite"
- `docs/incumbent_gap.md:77` — "6.57–7.00 on Riyadh" → "8.60–9.09 on Riyadh"
- `docs/incumbent_gap.md:103` — Riyadh M column "6.72" → "8.91"
- `docs/incumbent_gap.md:106–108` — "between 2.0 and 2.5 on Riyadh … over-cycles into silica only when pushed to the inhibitor's technical limit" → the Riyadh flip against M = 8.91 now falls between LSI 2.0 (6.22) and 2.5 (11.41) still, but what it over-cycles into on Riyadh is calcite, not silica
- `docs/incumbent_gap.md:118` — "Riyadh: M 6.72 / 6.58 / 4.53 (calcite takes over as pH rises)" → "Riyadh: M 14.07 / 6.58 / 4.53, calcite at all three"
- `docs/incumbent_gap.md` §3.2 and any P3-variant list for Riyadh — "S150/S200 × P35000/P40000, CaCO₃ basis, within 0.5" → "no variant within 0.5 on Riyadh"
- `docs/incumbent_gap.md:180–183` (limitations 1–2) — add that the only measured-silica water is calcite-bound, so no silica-bound result in the study rests on a measurement

## Defect 68 — ammonium credited, nitrite ignored

- `docs/chemistry_evidence.md:76` — "there is one obvious candidate … ammonium … The deficit closes with **11.3 mg/L as N**" → "the table also prints ammonia 16 and nitrite 31 mg/L with no basis. Counting both, the balance passes (−2.19 to −3.76 %) with nitrite as NO₂⁻ on every ammonia basis and fails with nitrite as N on every one; the ammonia basis is undetermined (defect 68)"
- `docs/handoff_external.md:149` — "~11 mg/L as N would close it. Is that the right reading?" → "the assay also prints nitrite 31 mg/L; with nitrite as NO₂⁻ the balance closes within ±5 % on any ammonia basis, with nitrite as N it does not. Which bases did the laboratory report?"
- No document quotes the ion sum; `results/ceiling_report.html` (regenerated) now prints "ions sum to 1053 mg/L … (+0.3 %)" where it printed 1063 (+1.2 %), because defect 67 removed 10 mg/L of silica from the sum

## Defect 69 — nitrate monthly average, and INFEASIBLE instead of 1.00

- `HANDOFF.md:30–32` — "the discharge permit binds at **3.33 cycles on nitrate** before chemistry binds at 4.52" → "on the nitrate monthly average no cycle count complies (makeup 3 mg/L against 1); the daily maximum alone would bind at 3.33"
- `docs/handoff_external.md:72` — "**3.33 cycles** (daily max) on **nitrate**" → "**no cycle count complies** on the nitrate monthly average; 3.33 on the daily maximum alone"
- `docs/handoff_external.md:74` — "**the permit binds before the chemistry does**" → keep, and add that on the monthly average it admits nothing
- `docs/deck_2026_09_12.md:87` and `:172` — "**3.33 cycles** … nitrate" → "monthly average: none; daily max: 3.33" (deck markdown: for the founder)
- `docs/yzi_application_answers.md:52` — "bind at 3.33 cycles on nitrate" → "admit no cycle count on the nitrate monthly average (3.33 on the daily maximum alone)"
- `docs/r3sidency_application_answers.md:65` — "nitrate permit at 3.33" → "nitrate permit infeasible on the monthly average"
- `docs/defect_register.md:59` (defect 49's row) — "a tested discharge ceiling of **3.33**" → add "(the daily maximum; defect 69)"
- `docs/incumbent_gap.md:190–192` — "the makeup alone already breaches it on both waters, giving a discharge ceiling of 1.0" → "… so no cycle count complies (INFEASIBLE)"

## Stale before this branch (defect 57's fix, merged at 709a3c5, never re-run into this artefact)

`results/incumbent_gap.json` as committed (8433848) predated the brucite enthalpy fix. Re-running it at 709a3c5, before any change here, moved the no-acid regime only:

- `docs/incumbent_gap.md:84` — Dhahran no-acid "1.19" (M) → "2.03"; gaps "+1.81 / +1.77 / −0.04 / +0.91" → "+0.97 / +0.92 / −0.89 / +0.07"
- `docs/incumbent_gap.md:85` — Riyadh no-acid "1.30" (M) → "1.56"; gaps "+1.70 / +1.00 / −0.30 / +1.00" → "+1.44 / +0.74 / −0.56 / +0.74"
- `docs/incumbent_gap.md:87–94` — "The no-acid M is bound by brucite, and this study stages that as a defect (57)" → defect 57 is fixed; no-acid M is calcite-bound at 2.03 (Dhahran) and 1.56 (Riyadh)
