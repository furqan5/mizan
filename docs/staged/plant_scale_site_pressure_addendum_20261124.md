# Addendum to the plant-scale site-pressure pre-registration

**Written 24 November 2026, before any plant-scale script is run on the
site-pressure fill law.** It supplements
`docs/staged/plant_scale_site_pressure_preregistration.md` (SHA-256
`5a1dce18ed987aa26a553d29d202b1c2c38154d97d0745a42acbf45158491d54`), which is
unchanged. Both files are committed together with the defect-79 work, before
the run, so the order is now evidenced by the commit as well as by the hash.

## 1. What happened to the 21 October execution

The chains of section 3 were started at 19:11 on 21 October 2026 and stopped
part-way. Only `src/corrosion_floor_audit.py` finished. The partial outputs
(`controller_out.txt`, `v3_skin_vs_bulk.csv`, `corrosion_floor.json`,
`corrosion_floor_conditions.log` and the `_chain_*.status` files) were moved
out of the repository and the committed sea-level artefacts restored before
the defect-79 commit. None of the partial numbers is used anywhere.

## 2. What this pass runs, fixed now

This pass re-derives the artefacts the JWPE manuscript quotes, on the
site-pressure law, once each, in this order:

1. `src/incumbent_gap.py` and `src/skin_sensitivity.py`.
2. `src/run_controller.py`, then `scripts/v7_baseline_sensitivity.py`, then
   `src/annual.py`.
3. The gate-uncertainty campaign constants of section 5, from
   `results/campaign_error_model.json` (written 21 October by
   `scripts/campaign_error_model.py`, which reproduced the stored sea-level
   constants first), at their printed precision; then
   `scripts/gate_uncertainty.py`.
4. `scripts/weather_w1_rescore.py` (section 3 below).
5. `src/paper_jwpe_checks.py`, `src/audit.py` and the full test suite.

The rest of chains 1 to 3 (`annual_datacentre.py`, both CDU forms,
`chiller_feasibility_audit.py`, `fouling_energy.py`,
`generate_pitch_artifacts.py`, the joint-policy wrapper, `diurnal.py`, both
corrosion-floor studies, `ceiling_condition_audit.py` and the defect-42
check) is **not** run in this pass. The subset is chosen by what the paper
quotes, before any new-law output exists, not by outcome. Each of those stays
on the register's "What the defect-79 rescore did NOT re-derive" list, and no
document may quote a site-pressure figure for them.

The before column of section 4 is run for the same subset in a scratch copy
whose `results/calibration.json` is the committed sea-level one. That copy was
started at 22:35 on 24 November, before this file was written; it can only
reproduce stored sea-level figures and says nothing about the new law. Its
incumbent-gap transcript already matches the stored `incumbent_gap.log`
line for line except the output path.

## 3. The W1 weather scenario, rebuilt

`src/weather_sensitivity.py --stage build` needs raw ISD-Lite files that are
not on this laptop, and nothing is downloaded in this pass. W1 needs only the
TMYx array and the dew-point climatology, and the climatology is committed at
four decimals. `scripts/weather_w1_rescore.py` rebuilds W1 from it with the
registered `build_w1` and scores it with the registered `annual.run_annual`.

Rule, fixed now: the rebuild is run first on the sea-level copy. If every
whole-year and per-envelope water, energy and cost figure reproduces the
stored W1 value in `results/annual_weather_sensitivity.json` to **0.01
points**, the site-pressure W1 figures from the same script are used. If not,
they are not used, the stored W1 figures stay labelled as sea-level, and the
paper says so. W2 is weather only (hours above the edge per station year) and
does not depend on the fill law, so it is not re-run.

## 4. Unchanged

Thresholds, verdict rules, inputs, tariffs, waters, conditions and solvers
are exactly those of the original plan. Defect 77's integrator and defect 78's
skin pH are not adopted. A verdict that flips is reported as flipped.
