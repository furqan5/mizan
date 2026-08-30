# Mizan

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22179269.svg)](https://doi.org/10.5281/zenodo.22179269)

**An energy–water supervisory controller for cooling-tower and condenser-water loops.**
A [Furqan](#about) venture. *The balance between energy and water.*

This repository exists so that the results reported in our Proof-of-Concept
document can be checked rather than believed. Everything below regenerates from
a public dataset in four commands.

---

## What the model does

A Gulf condenser-water loop is run by three parties setting three handles
independently: the building management system sets fan speed against a fixed
condenser-water setpoint, and the water-treatment contractor sets blowdown
against a fixed conductivity setpoint and acid dose against a fixed pH setpoint.

They are not independent variables. Concentrating the loop to save water raises
scaling risk and changes evaporation; cooling the condenser to save compressor
power costs fan power and evaporates more water.

This code solves them together. A Poppe/Rögener heat-and-mass-transfer model of
a counterflow wet cooling tower is coupled to an ion-association speciation
engine built on USGS PHREEQC constants, with **each mineral evaluated at the
temperature where it is least soluble** — calcite, gypsum and magnesium silicate
at the hot condenser tube skin, amorphous silica at the cold tower basin,
because silica is prograde and a single evaluation point gets it backwards.

## Results, including the two that failed

Six acceptance criteria were fixed and printed **before** the model was fitted.
The holdout is campaign-wise — calibrated on one experimental campaign, tested on
two others run in different seasons under different designs of experiment — and
it was scored once.

| Gate | Quantity | Threshold | Result | Verdict |
|---|---|---|---|---|
| V1 | Outlet water temperature, MAE | ≤ 1.00 K | 0.542 K | **PASS** |
| V1 | Heat rejection, MAPE | ≤ 6.00 % | 5.94 % | **PASS** |
| V2 | Water consumption, MAPE | ≤ 8.00 % | 9.90 % | **FAIL** |
| V5 | Total operating cost reduction | ≥ 3.0 % | 8.55 % | **PASS** |
| V5 | Makeup water reduction | ≥ 15.0 % | 14.83 % | **FAIL** |
| V5 | Saturation violations at the tube skin | 0 | 0 | **PASS** |

**Both failures are reported as failures and neither threshold has been moved.**

- **V2** fails because we found a drift constant in our own code that was a
  hundred times too large — a modern eliminator rating of 0.0005 *per cent* used
  as a fraction. Correcting it withdrew an earlier result that had passed.
  Re-identifying the fill law per campaign brings every campaign inside the gate
  (6.55 / 7.80 / 4.50 %), which establishes fill drift rather than an
  unaccounted bleed.
- **V5** fails because the threshold was written beyond a physical wall. Makeup
  water is evaporation × C/(C−1), so 15 % requires 8.5 cycles of concentration.
  Gypsum saturates at 8 on this water, and gypsum saturation is not pH-sensitive,
  so no acid dose moves it. The criterion was mis-specified, not merely missed.

Reported alongside the gates, and explicitly **not** pre-registered because they
were computed after the fact: mean total electrical power reduction of 4.91 %
across the five gate conditions, and hours-weighted across a real Dhahran year,
6.68 % power, 11.51 % water and 8.33 % operating cost.

`docs/defect_register.md` lists ten defects found in this work and fixed. Four of
them were caught because a first-principles model refused a bad input rather
than fitting around it.

## Reproduce it

```
pip install -r requirements.txt
python src/fetch_zenodo.py      # downloads and MD5-verifies the dataset
python src/calibrate.py         # gates V1 and V2
python src/run_controller.py    # gates V3, V5, V5b, and the energy report
```

Optional, and slower:

```
python src/annual.py            # hours-weighted annual figures from Dhahran TMYx
python src/make_figures.py      # regenerates every figure from results/
python src/audit.py             # 49 consistency checks across the results tree
python src/skin_sensitivity.py  # how much of the gypsum wall is the skin assumption
```

`src/audit.py` is the gate on our own packaging: an inconsistent results tree
produces no submission bundle.

## Data provenance

| Input | Source |
|---|---|
| Validation dataset | Palenzuela, Roca & Serrano Rodríguez, Zenodo record [10806201](https://doi.org/10.5281/zenodo.10806201), CC BY 4.0. 165 steady-state points, three campaigns, 2019–2023. MD5-verified by `fetch_zenodo.py` |
| Equilibrium constants | USGS PHREEQC `phreeqc.dat` — public-domain reference data |
| Chiller curves | EnergyPlus CoolTools library (US DOE / NREL) — York YT 1758 kW centrifugal |
| Psychrometrics | ASHRAE Handbook of Fundamentals formulation, implemented here from published equations |
| Weather | TMYx Dhahran, station 404160, 2011–2025 |

The psychrometric implementation is independently checked against ASHRAE's own
published design conditions for Dhahran and agrees to **0.20 K** across six
design percentiles.

## MATLAB and Simulink

`matlab/` holds an independent re-implementation. A single implementation is a
single point of failure: a coding error would be invisible to every gate here,
because each gate tests the model against data rather than against another
model. The two implementations agree on outlet water temperature to
**1.4 × 10⁻⁵ K**.

`build_mizan_model.m` constructs `mizan_plant.slx` from text, so the Simulink
model is reproducible rather than hand-drawn.

## What is deliberately not in this repository

- **The journal papers we read.** They are copyrighted and are cited in the
  documents rather than redistributed.
- **The validation dataset itself.** `fetch_zenodo.py` downloads it from the
  source and verifies its MD5, which is better than a copy that can silently
  drift.
- **Commercial material** — pricing, named accounts, customer strategy — and all
  personal contact information.

## Known limitations, stated plainly

Everything here is modelled. There is no field data and no installed base.
Model error is about 2.5× the propagated measurement uncertainty, with a
systematic holdout bias. **40.5 % of a Dhahran year is hotter and more humid than
anything in the validation data.** The wall-to-bulk temperature rise is a
hardcoded 8 K, which the code's own film calculation puts at 2.4–3.7 K for a
clean surface — `skin_sensitivity.py` measures what that assumption is worth, and
it moves the gypsum wall by a full cycle. There is no corrosion model, which
matters because the controller selects acid dose.

`docs/poc_report.md` section 12 lists every open item with the direction it
biases the result. Five of seven bias against our own numbers.

## About

**Furqan** — *The criterion for energy.* From the Arabic root ف-ر-ق, to separate:
the criterion that distinguishes the true from the false. A first-principles
model with few parameters cannot absorb a bad input; it fails loudly instead of
quietly fitting around the defect.

**Mizan** (الميزان) — the balance, the scale, the measure held level.

## Citation

Shakeel, F., Baig, D. and Ahsan, M. (2026). *Mizan: an energy-water supervisory
controller for cooling-tower and condenser-water loops* (v1.0.0). Zenodo.
https://doi.org/10.5281/zenodo.22179269

## Licence

Source-available for verification and non-commercial research. See
[LICENSE](LICENSE). Commercial use requires a separate written licence.
