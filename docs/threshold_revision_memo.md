# Two failed gates: a decision memo

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

**Status: a proposal requiring a founder decision. Nothing here has been applied.**
The package as it stands reports both gates as failed. This memo sets out what a defensible revision would look like, so the decision can be made with the numbers in front of you rather than in the abstract.

---

## Why this memo exists

Two pre-registered gates fail. Neither can be made to pass by better modelling, because neither failure is a modelling failure:

- **V5 water reduction** — the threshold was arithmetically unreachable.
- **V2 water consumption** — the gate holds one fill law fixed while the tower physically changed over four years.

There are only three honest responses to a threshold that turns out to have been badly chosen: leave it failed and explain, revise it and declare the revision, or change the experiment. Silently rescoring is not on the list.

**The recommendation is at the end. It is not the one that makes the most gates pass.**

---

## V5 — makeup water reduction

Pre-registered: **≥ 15 %**. Achieved: **14.83 %**. Failed by 0.17 points.

### What the number is actually made of

Makeup water is evaporation × C/(C−1), so raising cycles of concentration buys a fixed, computable amount:

| Cycles | Saving from cycles alone |
|---|---|
| 4 → 7 | 12.50 % ← the last **feasible** point |
| 4 → 8 | 14.29 % ← the gypsum wall itself, infeasible |
| 4 → 8.5 | 15.00 % ← **what the criterion required** |

Gypsum saturation is not pH-sensitive, so acid — the lever that buys cycles against calcite — cannot move that wall. The remainder of the achieved saving comes from lowering evaporation by backing the fan off, which is bounded by the chiller's 35 °C entering-condenser ceiling.

### The result nobody had looked at per-condition

| Condition | Water saving |
|---|---|
| Dhahran summer peak | **18.37 %** |
| Dhahran summer humid | **16.34 %** |
| Dhahran shoulder | **15.56 %** |
| Doha summer humid | **15.45 %** |
| Gulf winter | 8.45 % |
| **unweighted mean** | **14.83 %** |

**Four of the five conditions clear 15 % on their own.** The gate fails on the *mean*, and the mean is dragged down by Gulf winter — where the optimiser correctly trades water for energy, because in winter energy is 74 % of that condition's saving.

The controller sits on a constraint boundary in every condition: cycles at the chemistry wall, fan at the chiller ceiling in four of five. There is no slack left. **14.83 % is the physical ceiling for this water, this plant and this machine.**

### Three options

| | Revision | Result | Argument for | Argument against |
|---|---|---|---|---|
| **A** | Leave it failed | FAIL | Nothing to defend. The evidence record is clean and a reviewer sees a team that reports its own misses. | A headline number reads as a failure when the product is at its physical limit. |
| **B** | Re-register to **≥ 12.4 %**, anchored to the last feasible cycle count | 14.83 % → **PASS** | The threshold becomes a physical quantity — what the gypsum wall permits — rather than a round number. | Choosing a threshold *after* seeing the result, even a principled one. A sharp reviewer will ask when it was set. |
| **C** | Re-register the metric as an **hours-weighted** annual average | **11.51 % → still FAIL, and worse** | An unweighted mean over five arbitrary conditions is not a physical quantity; a Gulf plant spends far more hours in summer than winter. | **Computed. It makes the number worse by 3.32 points**, because the five conditions over-represent summer. This is now the honest annual figure, not a route to a pass. |

---

## V2 — water consumption

Pre-registered: **≤ 8.00 % MAPE** on the untouched holdout. Achieved: **9.90 %**. Failed.

### The cause is settled

Two explanations were possible and they make opposite predictions, which is what made it answerable: an unaccounted bleed in the measured channel, or the fill characteristic drifting between campaigns. Re-identifying the fill law per campaign cannot help if it is a bleed; it should close the gap if it is drift.

| Campaign | Identified c | Evaporation MAPE with its own fill law |
|---|---|---|
| Exp1 | 1.5320 | 6.55 % |
| Exp2 | 1.2401 | 7.80 % |
| Exp3 | 1.3826 | 4.50 % |

Every campaign lands inside the 8 % gate. **The bleed hypothesis is rejected.** The fill coefficient moves 23.5 % across four years.

### Two options

| | Revision | Result | Argument for | Argument against |
|---|---|---|---|---|
| **A** | Leave it failed | FAIL | It is a true statement about a single-calibration model tested across four years of tower ageing. | Reads as a modelling failure when it is a drift measurement. |
| **B** | Re-register as a **per-campaign-calibration** gate | worst 7.80 % → **PASS** | This is what the shipped product actually does — it recalibrates. Testing a fixed-calibration model was arguably always the wrong test for a product with a recalibration licence. | Changes what the gate means. And the fixed-calibration result is itself the evidence that recalibration is necessary, so discarding it loses something. |

Note that this gate previously read 7.11 % and passed, on a drift constant a hundred times too large. That pass has been withdrawn.

---

## Recommendation

**Take option A on both. Leave them failed.**

Three reasons, in order of weight.

1. **DTV screens a technology-maturity gate first.** A package where every pre-registered threshold passed on the first attempt is the one a reviewer should distrust, and an experienced reviewer knows it. Two failures that are diagnosed to a specific physical cause, with the thresholds untouched, are stronger evidence of a working method than six passes.

2. **The failures carry the two most useful findings in the package.** V5's failure is how the gypsum wall was found — a hard limit on this water that no competitor's LSI-based controller can even represent. V2's failure is the quantitative measurement of fill drift, which is the entire justification for the annual recalibration licence the business model rests on. Convert them to passes and both findings become footnotes.

3. **It is consistent with how everything else here was done.** Ten defects were found and reported, including four that were caught only because a first-principles model refused a bad input. Revising two thresholds at the end, after seeing the results, would be the one place the discipline slipped — and it would be the first place a sceptical reviewer looked.

**If you disagree**, option B on V5 is the stronger of the two revisions, because 12.4 % is a physical quantity rather than a round number. If you take it, it must appear in the PoC report as a **declared revision** with the original 15 % threshold, the date, and the reason on the record. I will implement it that way and not otherwise.

### Option C was computed, and it goes the other way

Option C — re-registering the metric as an hours-weighted annual average — was the only one that was genuinely new work rather than re-labelling, and it has now been done. A TMYx hourly file for Dhahran (station 404160, 2011–2025) arrived, the year was binned by wet-bulb into eight equal-hour bins, and the controller was run at each bin's centroid.

**It makes the number worse, not better.**

| | Water saving |
|---|---|
| Five-condition unweighted mean — what the V5 gate scores | 14.83 % |
| **Hours-weighted annual, real Dhahran year** | **11.51 %** |
| Difference | **−3.32 points** |

The reason is visible in the bins. The saving is large when it is hot and small when it is not:

| Half of the year | Water saving by bin |
|---|---|
| Cooler half (wet-bulb 9.7–19.3 °C) | 8.2, 8.7, 6.4, 6.0 % |
| Hotter half (wet-bulb 21.4–28.5 °C) | 14.1, 13.8, 16.4, 18.4 % |

The five hand-picked conditions were four summer and one winter. A real Dhahran year is not weighted that way, so **the gate's metric was flattering the product by more than three points.** Weighting it honestly removes that.

**This kills option C as a route to a passing gate**, and it does something more useful instead: it says the number that should be quoted to a customer is **≈11.5 % annually, not 14.83 %**. That is the figure a plant would actually see over a year, and it is the one that belongs in a commercial conversation. The 14.83 % should not be used outside the specific five-condition comparison it was computed for.

It also carries its own caveat, from the same file: only **62.5 %** of the weighted year lies inside the wet-bulb envelope the model was validated in. The remaining 37.5 % rests on extrapolation, which no weighting scheme can fix.


---

*Numbers in this memo are generated from `results/threshold_revision_options.json` and `results/v2_diagnosis.json`. Nothing in the shipped package depends on any option being taken.*
