# Pre-registration: the plant-scale studies re-run on the site-pressure fill law

**Written 21 October 2026, BEFORE any plant-scale script is run on the new law.**
This follows defect **79**. Nothing is committed when this is written, so the
order is evidenced by this file's SHA-256. The hash goes into the register and
the session notes, and the joint-policy registration hashes this file among its
inputs. A plan edited after the run would not match.

## 1. What changes, and what does not

Only the fill law changes. Every plant-scale script reads it from
`results/calibration.json` (SHA-256 `5a9faae3…1dc9` when this is written):
**c = 1.1728994129484793, n = −0.595079013563148**, against the sea-level
1.2400648125849212 / −0.5013981003349164 the stored artefacts were built on.

Nothing else changes:

* no physics or solver change, and every Gulf, Dhahran, data-centre and region
  study keeps the pressure it uses now, because those sites are not Almería;
* defect 77's corrected Poppe integrator and defect 78's skin pH are **not**
  adopted (77 needs Furqan's decision first);
* no grid, condition, tariff, water or plant input is touched.

## 2. Thresholds and verdict rules (unchanged)

| Gate | Rule, as registered |
|---|---|
| V5 cost | ≥ 3 % total operating cost reduction, 4.0-cycle baseline |
| V5 water | ≥ 15 % makeup water reduction |
| V5 skin | 0 skin saturation-index violations |
| V7 | the V5 function and the same three thresholds, 3.0-cycle baseline (`docs/v7_preregistration.md`) |

Each sub-study's own registered hypotheses are applied exactly as written:
`annual_datacentre.py` P1–P5, `incumbent_gap.py` H1–H4b, `corrosion_floor_conditions.py`
C1/C2, `cdu_hybrid.py` H1a–H4, `cdu_joint_policy.py` H-B2, and the
decidability rule in `gate_uncertainty`. **A verdict that flips is reported
as flipped, in either direction.** Nothing is re-run to move a verdict.

## 3. Scripts and order (each run once on the new law)

Chain 1, in order:

1. `src/run_controller.py` → `controller_summary.json`, `v3_skin_vs_bulk.csv`,
   `v5_controller.csv`, `v5b_two_ceilings.csv`, `v7_controller.csv`; transcript
   `results/controller_out.txt`.
2. `scripts/v7_baseline_sensitivity.py` → `v7_baseline_sensitivity.json`.
3. `src/annual.py` → `annual_dhahran.json`; transcript `results/annual_rerun.log`.
4. `src/annual_datacentre.py` → `annual_datacentre.json`; `results/annual_datacentre.log`.
5. The one-CDU study, both registered forms, into new directories because the
   17 September runs refuse to be overwritten and should not be:
   R1 `src/cdu_hybrid.py --repo . --output results/cdu_hybrid_rescore_20261021`,
   R2 `src/cdu_hybrid_rescore.py --repo . --output results/cdu_hybrid_rescore_corrected_20261021`.
6. Downstream readers of the files above, so they do not go stale against them:
   `src/chiller_feasibility_audit.py`, `src/fouling_energy.py`.

Chain 2, in order:

1. `scripts/generate_pitch_artifacts.py`, the four-region run → `pitch_artifacts.json`.
2. The joint-policy study through a wrapper, `src/cdu_joint_policy_rescore.py`,
   which runs the registered `src/cdu_joint_policy.py` unedited with **two
   declared deviations**: the output goes to `results/cdu_joint_policy_20261021`,
   and the NLR power file it reads (a path on the old laptop, absent here) is
   replaced by the one scalar it contributes, mean/max = **0.9462442583159482**,
   read from the 17 September run's stored `hours.json` rather than typed.

Chain 3, independent: `src/diurnal.py`, `src/incumbent_gap.py`,
`src/corrosion_floor_audit.py`, `src/corrosion_floor_conditions.py`,
`src/ceiling_condition_audit.py` (it writes no JSON, so the transcript is the
artefact) and `src/skin_sensitivity.py`.

After chain 1: the gate-uncertainty campaign constants (section 5), then
`scripts/gate_uncertainty.py` → `gate_uncertainty.json`. After everything:
the defect-42 check (section 6), `src/make_report.py` (the generated PoC
report), `python src/audit.py` and the test suite. Every transcript goes
beside its artefact in `results/`.

## 4. The before column: the same code at the sea-level law

A scratch copy of `src/`, `scripts/`, `results/`, `data/` and `docs/` is made
with `results/calibration.json` replaced by the committed sea-level one
(HEAD), and runs the same chains. Its outputs are the **before** column, so
before and after differ only in the law. Each sea-level output is also
compared with the stored artefact. Headline percentages should reproduce to
0.01 points, and counts and verdicts exactly. A stored artefact that the
sea-level run does not reproduce is reported as drift between the code and
the artefact (defect 74's shape), with its size. It does not stop the run and
is not attributed to defect 79.

## 5. The gate-uncertainty campaign constants

`CAMPAIGN_FITS` (`src/gate_uncertainty.py`) and `CAMPAIGN_SLOPES` /
`CAMPAIGN_RESID_SD` (`scripts/gate_uncertainty.py`) are typed constants with
no generator: per campaign, the relative evaporation error of the published
law regressed on fan speed, `rel = a + k·fan`, with its residual sd. A
generator is written. Its method is fixed by reproducing the stored
constants at the sea-level law and 101,325 Pa (Exp1 −0.52 %, −0.2002 %/fan%,
6.27 pp; Exp2 +9.06 %, −0.3660 %/fan%, 11.63 pp) at their printed precision.
Only then is it run once at the site-pressure law and 95,495 Pa. If it cannot
reproduce them, the constants are not changed and that is reported.

## 6. Defect 42, settled by a rule fixed now

The claim is that fan turndown alone cannot hold the 31.76 °C silica floor in
cold air, so Frankfurt needs a tower bypass for 8 hours a day. On the new
law's four-region run, `scripts/defect42_cold_air.py` asks
`hybrid_supervisor.fan_for_target_fws` again, with the run's own arguments,
for every solved Frankfurt hour flagged `floor_unreachable`, and records
`low_fan_unexplorable` and the slowest fan that solved:

* **SURVIVES** if at least one hour misses with `low_fan_unexplorable` False,
  meaning the tower solved down to its slowest modelled fan (15 %) and still
  over-cooled. The new hours-per-day figure is the count of those hours.
* **SOLVER-LIMITED** if every miss carries `low_fan_unexplorable` True. The
  model then does not support the bypass claim, and documents say it is not
  established.
* **WITHDRAWN** if no solved hour misses. The 8-hour figure and the bypass
  advice are withdrawn on this law.

Unsolved hours (defect 43) count for neither side and are reported apart. The
same check runs on the sea-level copy, so the before is attributed the same way.
The two defect-42 regression tests stay pinned to the sea-level law, because
they test the reporting path. Their prose is updated to the outcome.

## 7. What is reported

The new-law results become the current artefacts. The register gets a
supersession table (before = section 4, after = this run). Every document the
audit flags is updated. Each re-derived item leaves the register's "What the
defect-79 rescore did NOT re-derive" list, and anything not re-run stays on it
with the reason: `pinn.py`, `v2_diagnosis.json`, the MATLAB verification,
`make_deck.py`, `src/weather_sensitivity.py` (its raw ISD-Lite arrays are not
on this laptop), and the CDU diagnostics and dry-cycle studies, which read the
historical 7 September states.
