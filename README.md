# Furqan / Mizan — DTV Cohort 2 evidence package

Supervisory controller for Gulf condenser-water loops. Co-optimises tower fan
speed, blowdown and acid dose against ion-specific mineral saturation
evaluated at condenser **skin** temperature.

## Reproduce everything (4 commands)

```
pip install -r requirements.txt
python src/fetch_zenodo.py      # downloads + MD5-verifies the public dataset
python src/calibrate.py         # gates V1 (thermal), V2 (water)
python src/run_controller.py    # gates V3 (skin vs bulk), V5/V5b (economics)
python src/make_report.py && python src/make_deck.py && python src/make_pdf.py
```

## Headline results — thresholds fixed before fitting, holdout scored once

| Gate | Threshold | Result | |
|---|---|---|---|
| V1 outlet water temperature MAE | <= 1.00 K | 0.542 K | PASS |
| V1 heat rejection MAPE | <= 6.00 % | 5.94 % | PASS |
| V2 evaporation vs *measured* water loss | <= 8.00 % | 7.11 % | PASS |
| V5 total operating cost reduction | >= 3 % | 5.60 % | PASS |
| V5 makeup water reduction | >= 15 % | 10.04 % | **FAIL, reported** |
| V5 saturation violations at skin | 0 | 0 | PASS |

V3: evaluating saturation in the bulk overstates the safe cycles limit by
**15.6 %**.
V5b: the **economic** ceiling (7 cycles) and the **physical** ceiling
(10 cycles, gypsum) are different numbers, and a fixed conductivity setpoint
locates neither.

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
Equilibrium constants: USGS PHREEQC `phreeqc.dat`.

## Honesty notes

No AI contributes to any result here. One gate fails and is reported as
failing. A unit defect found in our own first run is documented in the report
rather than quietly fixed. See `docs/poc_report.md` sections 4 and 8.
