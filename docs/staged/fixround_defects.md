# Staged defects — branch `fix/source-transcription-and-permit`, 17 September 2026

Staged here, **not** in `docs/defect_register.md`, for the documentation pass to
integrate. Numbers **67–76** were assigned to this branch. No "N found / N fixed"
count anywhere has been changed. Every figure below was produced by code run on
this branch in this session, unless a row attributes it to another source by name.

## Part 1 rows

| # | Defect | How it showed up | State |
|---|---|---|---|
| 67 | **The one measured Gulf TSE silica was read from the PDF text layer, not the page: 18 mg/L where the table prints 8** | `chemistry.ARAMCO_RIYADH_REFINERY_TSE` carried `SiO2=18.0  # MEASURED`. NACE CORROSION/96 Paper 577, Table 1, page 577/9 (source PDF SHA-256 `377486425a7a…c5b7984d`), prints **Silica as SiO₂ = 8**. The text layer reads the row as `Silica as SiO, 18 I Aluminum ] 0.12. 1`: the vertical table rule was OCR'd as a leading "1". Iron extracts as `0.21 1` against a printed 0.2 by the same artefact. Found by the main session reading a high-resolution render of the page; every other row of the table was re-read against the render here and agrees with the code. The wrong value made this water **silica-bound** in the incumbent-gap study and is quoted as "18.0 mg/L measured" in the external handoff, the evidence document, the Modelica silica model and the register (defect 50's row) | **Fixed** — `SiO2=8.0`; the whole printed table is carried as `chemistry.NACE577_TABLE1_PRINTED`, and `tests/test_reference_benchmarks.py::test_defect_67_every_value_is_the_one_printed_in_nace_577_table_1` pins all 20 rows against values typed from the page, every `Water` field against its row, and the printed total hardness against printed Ca and Mg. Re-run, thresholds unchanged: **Cycle Ceiling Report** 4.5168 → 4.5171 cycles, still **calcite**, printed 4.52 unchanged; $88,976 → $88,984/yr; 3-yr capex bound $266,928 → $266,953; silica crossover 30.0 mg/L unchanged. **Incumbent gap**, Riyadh, acid pH 7.8: class **silica-bound → calcite-bound**; M median **6.72 → 8.91** (range 6.57–7.00 → 8.60–9.09), `SI_calcite` at all five conditions; P3 4.95 → 7.43; gap P1 +4.69 → +2.50, P3 −1.77 → −1.48; P3 variants within 0.5: four → none; P1 break-even median $12,474 → $5,419/yr. pH sweep at Dhahran summer peak: M 6.72 (silica) / 6.58 / 4.53 → **14.07 (calcite)** / 6.58 / 4.53. Extended-panel verdicts unchanged in direction (H1 HOLDS, H2 HOLDS, H3 FAILS) but H2 now rests on **one** silica-bound water, Dhahran, whose silica is assumed; its "smallest gap +3.90" for Riyadh no longer exists. Strict panel unchanged. **Modelica `TowerSilicaDynamics.mo`: parameter updated to 8.0, NOT re-run** (`src/run_modelica.py` reports omc NOT FOUND and OMPython not installed); `results/silica_res.csv` is still the 18 mg/L run. By the model's own blowdown equation, B + D falls from 0.678 to 0.277 kg/s at 8 mg/L and V/(B + D) from 20.5 h to 50.2 h, so the 168 h spin-up `tests/test_basin_dynamics.py` assumes must be checked when it is re-run |

## Answer to the question this defect decides

**No measured Gulf TSE analysis in the repository is silica-bound.** The only one
with measured silica is the Riyadh assay, and at 8 mg/L calcite binds first at
every incumbent-gap condition and at every acid pH scored (7.5, 7.8, 8.0, 8.25)
and in the Ceiling Report. The one silica-bound TSE in the package is
`ARAMCO_FIELD_VALIDATED` (M 4.51, `SI_silica_am`), and its 26.8 mg/L is
**assumed**, imported from Salbukh brackish groundwater. `ARAMCO_RECLAIMED` does
not report silica at all. The silica thesis on Gulf TSE therefore rests on an
assumed number, and the one measurement contradicts it.
