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

## Stale before this branch (defect 57's fix, merged at 709a3c5, never re-run into this artefact)

`results/incumbent_gap.json` as committed (8433848) predated the brucite enthalpy fix. Re-running it at 709a3c5, before any change here, moved the no-acid regime only:

- `docs/incumbent_gap.md:84` — Dhahran no-acid "1.19" (M) → "2.03"; gaps "+1.81 / +1.77 / −0.04 / +0.91" → "+0.97 / +0.92 / −0.89 / +0.07"
- `docs/incumbent_gap.md:85` — Riyadh no-acid "1.30" (M) → "1.56"; gaps "+1.70 / +1.00 / −0.30 / +1.00" → "+1.44 / +0.74 / −0.56 / +0.74"
- `docs/incumbent_gap.md:87–94` — "The no-acid M is bound by brucite, and this study stages that as a defect (57)" → defect 57 is fixed; no-acid M is calcite-bound at 2.03 (Dhahran) and 1.56 (Riyadh)
