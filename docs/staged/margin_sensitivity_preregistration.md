# Pre-registration: plant-scale results with the daily silica margin enforced

**Written 25 November 2026 and committed before `scripts/margin_sensitivity.py`
is first run.** It is a sensitivity analysis, decided after the registered
results were known. An independent review of the JWPE manuscript found that the
registered plant-scale optimiser is not held to the ceiling the paper defines.

## 1. What was found

The paper's scaling ceiling (Section 2.4; `incumbent_gap.mizan_ceiling`) lowers
the amorphous-silica limit by the daily margin for a +-5 K basin swing
(`chem.limits_with_diurnal_margin`). The registered plant-scale runs (V5 and V7
in `run_controller.gate_v5`, `annual.run_annual` for the TMYx year and the W1
scenario) call `controller.optimise` with the default `chem.OPERATING_LIMITS`.
That is the steady-state limit without the margin, searched on a 1-cycle grid. In
three of the five design conditions the optimiser chose 5.0 cycles, above the
4.48-4.72-cycle ceiling of Section 4.1. On 25 November a single-condition check
(Dhahran summer peak) gave 4.5 cycles and 26.23 m3/h makeup with the margin
enforced on a 0.1-cycle grid, against 5.0 cycles and 25.50 m3/h as registered.
That check is the only margin-enforced number known before this file was written.

## 2. What is run

Two variants, three parts each, all on the site-pressure fill law in
`results/calibration.json`:

* **margin**: `optimise(..., saturation_limits_fn=f)` with
  `f(T_basin) = chem.limits_with_diurnal_margin(T_basin, 5.0)`, evaluated at each
  candidate's own basin (cold-water) temperature. This is the same function and
  amplitude as Section 4.1.
* **nomargin** (control): the same grid without the margin, so the effect of the
  finer grid can be separated from the effect of the margin.

Common to both variants: cycles grid 2.0-6.0 in steps of 0.1. Fan grid 30-100 % in
steps of 10, pH grid 7.0-9.0 in steps of 0.25, baselines, tariffs, plant, waters,
bins and weather are exactly as registered. The margin-free silica ceiling is at
most 5.3 cycles at any basin temperature these runs reach, so 6.0 does not truncate
the search. If any chosen point sits at 6.0, that is reported and the part is run
again with the grid extended to 8.0.

Parts:

* **gates**: the five design conditions against the 4.0-cycle (V5) and
  3.0-cycle (V7) baselines through `rc.gate_v5(..., optimise_kwargs=...)`. The
  95 % interval uses `scripts/gate_uncertainty.py`'s `sample_saving` and seed.
* **annual**: `annual.run_annual` on `results/tmy_hourly.npy`.
* **w1**: `annual.run_annual` on W1 rebuilt by `scripts/weather_w1_rescore.py`.

## 3. Status of the results, fixed now

* V5 and V7 keep their registered verdicts. The 15 % water, 3 % cost and
  0-violation thresholds are applied to the sensitivity results only to describe
  them, never to re-score a gate.
* Because the margin-enforced constraint set is the one the paper defines, the
  manuscript's headline plant-scale figures (abstract, conclusions, Fig. 5) will
  be the **margin** variant, whatever its direction. The registered margin-free
  figures stay in Table 2 and Section 4.5, labelled as registered.
* Every outcome is reported, including a change of sign of the in-range energy
  or water result.

## 4. Outputs

`results/margin_sensitivity/{margin,nomargin}_{gates,annual,w1}.json`, the gate
CSVs beside them, and a transcript per part in the same folder.
