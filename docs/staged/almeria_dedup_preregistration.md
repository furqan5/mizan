# Pre-registration: V1 and V2 re-scored on de-duplicated Almería data

**Written and committed 17 September 2026, BEFORE the re-score is run.**
Branch `fix/validation-integrity`. Staged defect **51**.

## 1. What was found, before anything was re-run

Established on 17 September 2026 by reading the published netCDF files with
`src/dataset.py`'s own loader. No fit and no gate was run to establish it.

| | rows |
|---|---|
| `Exp1.nc` | 33 |
| `Exp2.nc` | 115 |
| `Exp3.nc` | 17 |
| concatenated by `dataset.load_all()` | **165** |
| unique across all seven measured channels | **147** |
| `Complete.nc` (the publisher's own combined file) | 165 rows, 147 unique |

* **All 17 rows of `Exp3.nc` are exact copies of rows 0-16 of `Exp1.nc`**, in
  the same order. The dataset's own README describes Exp3 as *"Set of 17 tests
  (different from the ones taken for experimental campaigns 1 and 2)"* -- a
  full-factorial design of experiments. The file does not contain that
  campaign; it contains a copy of the first 17 Exp1 rows. This is an upstream
  publication fault in Zenodo record 10806201, carried into this repository
  unchecked.
* **Row 16 of `Exp1.nc` is also an exact copy of row 113 of `Exp2.nc`** (and
  therefore of row 16 of `Exp3.nc`).
* No campaign contains a duplicate within itself.
* Rounding to 1e-6 does not change the count (147), so the result does not
  depend on float equality at the last bit.

Consequence for the gates as currently scored (`src/calibrate.py`, train
`Exp2`, holdout `Exp1 + Exp3`): the 50-row holdout contains **33 unique rows**,
17 of them counted twice, and **one of those 33 is also in the training set**.

## 2. Definitions (fixed now)

* **Measured channels:** `Tin, Tout, Tamb, HR, q, w_fan, q_w_lost` -- every
  variable in the netCDF files. Nothing derived.
* **Duplicate:** two rows equal in all seven measured channels (exact float32
  equality as stored). A de-duplicated row keeps the campaign it first
  appears in, in load order Exp1, Exp2, Exp3, and records **every** campaign
  it appears in.
* **Campaign membership:** a row belongs to every campaign it appears in.

## 3. The split rule -- identical except for leakage

The registered rule is unchanged: *calibrate on campaign Exp2 only, score on
Exp1 + Exp3.* Applied to de-duplicated rows:

* **train** = every unique row that appears in Exp2. That is all 115 Exp2
  rows, exactly as before, so the identified fill law **must not move**.
  If `fill_c` or `fill_n` changes by more than 1e-12 the re-score is invalid
  and is reported as an execution defect, not a result.
* **holdout** = every unique row that appears in Exp1 or Exp3 **and in no
  training campaign**. Expected size: 33 unique Exp1/Exp3 rows minus the 1
  that appears in Exp2 = **32**.

The leaking row goes to training, not to the holdout, because the training
rule is "all of Exp2" and removing a row from it would change the fit as well
as the score. Keeping the fit fixed isolates the effect of the defect to the
scoring.

## 4. Thresholds -- unchanged

| Gate | Threshold |
|---|---|
| V1 outlet water temperature MAE | <= 1.00 K |
| V1 heat rejection MAPE | <= 6.00 % |
| V2 evaporation vs measured water loss MAPE | <= 8.00 % |

Same metrics, same code (`calibrate.metrics`), same solver, same fill-law
identification. Nothing about the thresholds is revisited in either
direction, whatever the result.

## 5. Which result is reported

**The de-duplicated re-score becomes the reported gate result for V1 and V2,
and the 50-row result is superseded.** This follows the repository's own
precedent: when a data or unit defect is found (register defects 1, 7, 17,
27), the defect is fixed and the gates are re-run with thresholds untouched,
and the defect-corrected result is the one reported -- in either direction.

* If a gate that passed now fails, it is reported as **FAIL**.
* If a gate that failed now passes, it is reported as **PASS**, with the
  before/after beside it so the change is visible and attributable to the
  data defect alone.
* Both the before (165 rows loaded, holdout n = 50) and the after
  (147 unique, holdout n = 32) numbers are produced in the same session by
  the same code, and both are reported.

## 6. Diagnostic that cannot change a verdict: leave-one-campaign-out

For each campaign k in Exp1, Exp2, Exp3:

* fold holdout = unique rows that appear in k;
* fold train = unique rows that do **not** appear in k;
* fit the fill law on the fold train with the same closed-form OLS, score the
  fold holdout with the same `calibrate.metrics`;
* a fold with fewer than 5 converged training points, or an empty holdout, is
  reported as not computable.

Expected fold sizes, from section 1: Exp1 holds out 33 and trains on 114;
Exp2 holds out 115 and trains on 32; Exp3 holds out 17 (all of them Exp1 rows)
and trains on 130.

These folds are reported beside the thresholds for context and are written
to `results/calibration.json` under a key whose name says it is a
diagnostic. **They do not enter any verdict.** A fold that passes does not
rescue a failed gate, and a fold that fails does not fail a passed one.

## 7. Loader fix

`dataset.load_all()` de-duplicates by default and carries the membership
column, and the train/holdout split is made by a single function in
`dataset.py` that refuses to put a row in the holdout if it appears in a
training campaign. A regression test asserts: no duplicate measured rows
after loading; train and holdout share no row; the counts in section 1.
