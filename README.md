# Furqan / Mizan — DTV Cohort 2 evidence package

Supervisory controller for Gulf condenser-water loops. Co-optimises tower fan
speed, blowdown and acid dose against ion-specific mineral saturation,
each mineral evaluated where it binds: calcite at the condenser **skin**,
amorphous silica at the cold tower **basin**.

## Reproduce everything (4 commands)

```
pip install -r requirements.txt
python src/fetch_zenodo.py      # downloads + MD5-verifies the public dataset
python src/calibrate.py         # gates V1 (thermal), V2 (water)
python src/run_controller.py    # gates V3 (skin vs bulk), V5/V5b (economics)
python src/make_report.py && python src/make_deck.py && python src/make_pdf.py
```

## Headline results — thresholds fixed before fitting, never moved

Every row is read from `results/calibration.json` and
`results/controller_summary.json`, and `src/audit.py` fails if it stops
matching them.

| Gate | Threshold | Result | |
|---|---|---|---|
| V1 outlet water temperature MAE | <= 1.00 K | 0.600 K | PASS |
| V1 heat rejection MAPE | <= 6.00 % | 6.27 % | **FAIL, reported** |
| V2 evaporation vs *measured* water loss | <= 8.00 % | 10.80 % | **FAIL, reported** |
| V5 total operating cost reduction | >= 3 % | 3.91 % | PASS |
| V5 makeup water reduction | >= 15 % | 4.38 % | **FAIL, reported** |
| V5 saturation violations at skin | 0 | 0 | PASS |

Three pass and three fail. V1 and V2 are scored on 32 held-out points: the
published dataset loads as 165 rows but only 147 are distinct (its Exp3 file
repeats 17 Exp1 rows, and one of those is also a training row). Scored on the
duplicated 50-row holdout, heat rejection had passed at 5.94 % and V2 failed at
9.90 %. The de-duplicated re-score was pre-registered
(`docs/staged/almeria_dedup_preregistration.md`) with thresholds unchanged.

V3: evaluating calcite saturation in the bulk instead of at the condenser skin
overstates the safe cycles limit by **6.9–7.0 %** at a typical +3.8 K skin rise
and **15.1–15.4 %** at +8 K (fouled).
V5b: operating cost falls monotonically to **5 cycles**, the last feasible
point; the **physical** ceiling is **6 cycles**, set by amorphous silica at the
cold basin. A fixed conductivity setpoint locates neither.

Chemistry against PHREEQC 3.9.0 (`tests/test_phreeqc_grid.py`, pre-registered
in `docs/staged/phreeqc_benchmark_preregistration.md`): 95.7 % of 416
saturation indices within tolerance across 4 waters, 1–8 cycles and 25–55 °C.
The registered criterion **fails**: calcite agrees at 89.1 % against a 90 %
bar, worst −0.10 log units at 45–55 °C.

## Layout

```
src/         physics core, controller, gates, document generators
docs/        generated markdown (never hand-edited)
results/     JSON + CSV artefacts; every published number reads from here
submission/  PDFs for the DTV upload
data/        Zenodo dataset (CC BY 4.0), MD5-verified
```

## Attribution

Validation data: Palenzuela, Roca & Serrano Rodríguez, *Steady-state operation
dataset of an experimental Wet Cooling Tower pilot plant located at Plataforma
Solar de Almería*, Zenodo record 10806201, CC BY 4.0.
Equilibrium constants: USGS PHREEQC `phreeqc.dat` (an earlier release than
the one PHREEQC 3.9.0 ships; see the benchmark above).

## Honesty notes

No AI contributes to any result here. Three gates fail and are reported as
failing. A unit defect found in our own first run is documented in the report
rather than quietly fixed. See `docs/poc_report.md` sections 4 and 8.
