# Pre-registration: V1 and V2 re-scored at the Almería site pressure

**Written 21 October 2026, BEFORE any site-pressure fit or score is run.**
Register defect **79**. Not committed when written: commits wait for the
owner, so the order is evidenced by this file's SHA-256, which `calibrate.py`
records in `results/calibration.json` at run time, and by the session record.
A plan edited after the run would not match the hash stored beside the result.

## 1. What was found, before anything was run

Established by reading the code. No fit and no gate was run to establish it.

Every call that evaluates the Almería pilot tower or the Almería air uses the
psychrometric default `psychro.P_ATM` = 101,325 Pa, because no caller passes a
pressure:

| Caller | Call made at sea level |
|---|---|
| `calibrate.demanded_merkel` | `humidity_ratio_from_rh`, `tower.integrate_poppe` |
| `calibrate.predict` | `tower.solve_outlet_temperature` |
| `drift.fit_and_score` | both of the above, through `calibrate` |
| `fill_law.features`, `fill_law.holdout_mae` | `wetbulb_from_rh`, `humidity_ratio_from_rh`, `wetbulb`, `integrate_poppe` |
| `uncertainty.propagate` | `tower.solve_outlet_temperature` |
| `pinn.py` | `wetbulb_from_rh`, `solve_outlet_temperature` |

The dataset README states no barometric pressure, and the netCDF files carry
no pressure channel.

## 2. The site pressure (fixed now)

* **Elevation 497 m above sea level.** Source: Solargis s.r.o., *Solar Resource
  Overview*, report SG-01-2016, site "Plataforma Solar de Almeria, Spain",
  37.094416° N, 2.359850° W, issued 22 January 2019 (read 21 October 2026).
  The register row's "about 500 m" is the same figure rounded.
* **Pressure from the standard atmosphere**, ASHRAE Handbook of Fundamentals
  2017 Ch. 1 Eq. (3), the formula `src/weather_sensitivity.py` already uses for
  Dhahran: p = 101,325 × (1 − 2.25577×10⁻⁵ Z)^5.2559 = **95,495 Pa**, 5.75 %
  below sea level. At 500 m the same formula gives 95,461 Pa; the 34 Pa
  difference is 0.04 % and is not chosen by result.
* **One constant pressure for all 147 rows.** Day-to-day weather moves station
  pressure by roughly ±1 kPa and the dataset does not record it. That is stated
  as a limitation of the rescore. **No pressure sweep is run**, so the value
  cannot be tuned to the score.

## 3. Code change

* `calibrate.py` gains `PSA_ELEVATION_M` and `PSA_PRESSURE_PA`, computed as in
  section 2. `demanded_merkel(df, p=...)` and `predict(df, c, n, p=...)` take the
  pressure and pass it to every psychrometric and tower call. Their default is
  the PSA pressure, because both functions exist only for this dataset;
  `drift.py` inherits it through them.
* `fill_law.py` and `uncertainty.py` pass `calibrate.PSA_PRESSURE_PA` to the
  calls listed in section 1.
* **Sea level stays the default everywhere else**: `psychro`, `tower`,
  `controller`, the plant and data-centre models, and every Dhahran or Gulf
  study. Their sites are not Almería.
* `pinn.py` is **not** changed. The surrogate is not a reported result, its P2
  gate is unscored (defect 71) and its checkpoint is not in the repository, so
  an edit there could not be run. It is listed as still at sea level.
* Defects 77 (fogged-air energy closure) and 78 (skin pH) are **not** folded in.
  The solver, the fill-law form and every other input are unchanged.

## 4. Execution check, before the site-pressure result exists

At p = 101,325 Pa the new code must reproduce the stored sea-level result.
This laptop runs numpy 2.5.3, pandas 3.0.6 and scipy 1.18.1, against the
pinned 2.4.6, 2.3.3 and 1.18.0, so the tolerance is fixed now rather than
assumed to be bit-exact:

| Quantity | Stored | Tolerance |
|---|---|---|
| `fill_c` | 1.2400648125849212 | 1e-9 absolute |
| `fill_n` | −0.5013981003349164 | 1e-9 absolute |
| Holdout outlet MAE | 0.5996496645121069 K | 1e-6 K |
| Holdout heat-rejection MAPE | 6.269479706945836 % | 1e-4 percentage points |
| Holdout evaporation MAPE | 10.800079300774595 % | 1e-4 percentage points |

If any line misses its tolerance, **stop**: that is an execution defect and no
site-pressure result is reported. The sea-level reference is written to
`results/calibration_sea_level_reference.json`, deliberately outside
`results/calibration.json`. The audit treats every float in
`calibration.json` as live, so the superseded figures would stop being caught
as stale if they sat there.

## 5. Split, fit and thresholds (unchanged)

* **Train** = the 115 unique Exp2 rows. **Holdout** = the 32 unique Exp1/Exp3
  rows that are in no training campaign (defect 51's split, unchanged).
* Same closed-form OLS of log *Me* on log(*ṁ*w/*ṁ*a), the same two-parameter form
  *Me* = c(*ṁ*w/*ṁ*a)^n, the same 160-step RK4 solver. A training row whose
  demanded-Merkel integration fails is excluded exactly as now, and the count
  is reported.

| Gate | Threshold |
|---|---|
| V1 outlet water temperature MAE | ≤ 1.00 K (target 0.50 K) |
| V1 heat rejection MAPE | ≤ 6.00 % |
| V2 evaporation vs measured water loss MAPE | ≤ 8.00 % |

Nothing about the thresholds is revisited in either direction, whatever the
result. **The rescore is run once.**

## 6. Which result is reported

**The site-pressure rescore becomes the reported V1 and V2 result, and the
sea-level result is superseded**, in either direction, following defects 1, 7,
17, 27 and 51:

* a gate that passed and now fails is reported as **FAIL**;
* a gate that failed and now passes is reported as **PASS**, with the
  before/after beside it;
* the before (sea level, section 4) and the after are produced in the same
  session by the same code, and both go into the register's supersession table.

## 7. Re-derived beside it, which cannot change a verdict

Each is run once, after the verdict is written, with the same pressure:

* leave-one-campaign-out, inside `calibrate.py`, as before;
* `uncertainty.py`: model MAE over the combined measurement uncertainty, and
  the share of holdout points within U (k = 2);
* `drift.py`: within- and across-campaign error and the spread of c between
  campaigns;
* `fill_law.py`: the comparison of fill-law forms and the training wet-bulb
  range. **The form is held at the two-parameter law for this rescore.** If
  `fill_law.py` now prefers another form, that is recorded as a finding and is
  not adopted in this round;
* `export_matlab_cases.py`: the question file the MATLAB twin answers. The audit
  binds it to the fill law to 1e-12.

## 8. Not re-derived in this round, and why

* **Plant-scale artefacts that consume `fill_c` and `fill_n`**:
  `controller_summary.json` (V5), `annual_dhahran.json`, `annual_datacentre.json`,
  the diurnal, CDU, joint-policy, incumbent-gap, corrosion-floor,
  ceiling-condition and skin-sensitivity studies, and the per-campaign
  constants in `gate_uncertainty`. They stay on the sea-level fill law. Re-running
  them is the "re-run every artefact beneath it" job that defect 77 also needs,
  and the register will say which law each one carries.
* **The 21.9 °C wet-bulb edge** (`ALMERIA_WB_MAX_C`) that cuts the annual bins is
  the training wet bulb computed at sea level. Its site-pressure value is
  reported from `fill_law.py`. The constant is not moved here, because moving it
  re-cuts the annual study.
* **`results/v2_diagnosis.json`**: no script writes it (defect 74). It stays as is.
  `drift.py` recomputes the same per-campaign quantities.
* **`pinn.py` and the MATLAB outputs** (`matlab_control_design.json` and the twin
  verification): not re-run.

## 9. What closes defect 79

The run in sections 4 to 6 executes and is recorded in the register with a
supersession table, whatever the outcome. If section 4 fails, 79 stays OPEN.
