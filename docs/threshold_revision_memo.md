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

Pre-registered: **≥ 15 %**. Achieved: **10.83 %**. Failed by 4.17 points.

> **Rewritten twice on 4 September 2026.** First written 30 August against the pre-defect-11 artefacts, when V5 scored 14.83 % and the miss was 0.17 points. Enforcing the chiller capacity limit moved it to 10.02 %, and killed option B. Defects 15 and 16 then moved it again to **10.83 %** — the chiller was given a realistic selection, so all five conditions are feasible once more, and gypsum was given a solubility that can turn over, which pulled the wall in from 8 cycles to **7**. Every number below is recomputed from the current artefacts. **The recommendation has not changed through any of it. It has only got stronger**, because the gap the threshold has to cross is now bounded by a wall one cycle nearer.

### What the number is actually made of

Makeup water is evaporation × C/(C−1), so raising cycles of concentration buys a fixed, computable amount:

| Cycles | Saving from cycles alone |
|---|---|
| 4 → 6 | 10.00 % ← **where the optimiser actually lands**, and the last chemistry-feasible count |
| 4 → 7 | 12.50 % ← **the gypsum wall itself**, infeasible |
| 4 → 8 | 14.29 % |
| 4 → 8.5 | 15.00 % ← **what the criterion required** |

Gypsum saturation is not pH-sensitive, so acid — the lever that buys cycles against calcite — cannot move that wall. The remainder of the achieved saving comes from lowering evaporation by backing the fan off, which is bounded by the chiller's 35 °C entering-condenser ceiling.

### The result nobody had looked at per-condition

| Condition | Water saving |
|---|---|
| Dhahran summer peak | 12.71 % |
| Dhahran summer humid | 12.23 % |
| Dhahran shoulder | 7.27 % |
| Doha summer humid | 12.64 % |
| Gulf winter | 9.29 % |
| **unweighted mean** | **10.83 %** |

**All five conditions are feasible again.** Defect 16 restored the two the chiller could not
previously serve — it had been sized at its rating point rather than at a Gulf design condition —
so the mean is once more taken over the full set rather than over three survivors. **Not one of
the five clears 15 %**, and the best reaches 12.71 %. In the 30 August version four of five
cleared it and the gate failed only on the mean; that margin was bought in a region where the
machine could not make its duty, and it has not come back.

The optimiser lands on 6 cycles in all five conditions, and almost all of the water saving is the
cycles term.

**An earlier version of this memo claimed 14.83 % was “the physical ceiling for this water, this plant and this machine”, a figure since superseded twice. That sentence does not survive, and it should not be reinstated with the new number substituted in.** The gypsum wall permits 7 cycles, worth 12.50 % on cycles alone. The optimiser reaches 6, worth 10.00 %. So 10.83 % is *where the optimiser stops*, not a physical ceiling — though the gap to the chemistry limit is now **1.67 points rather than more than four**, because defect 15 moved the wall in. That is a materially different statement: there is much less unexplained headroom than the previous version of this memo reported.

Cycles alone, 4 → 6, is worth 10.00 %; the mean comes out at 10.83 %, so the air-side lever
contributes 0.83 points net. **Do not quote that as an identity.** Per condition it ranges from
**−2.73 points** at Dhahran shoulder, where the optimiser speeds the fan up, to **+2.71** at
Dhahran summer peak, where it slows the fan down and spends 1.79 % more electrical power to do
it. Averaged, the water benefit looks like pure chemistry headroom. It is not; it is chemistry
headroom plus an air-side trade whose sign changes with the weather.

### Two different walls are being reported as one

The optimiser lands on **6 cycles in all three conditions**, and the run log names the reason:
*“the chemistry constraint boundary”*. The two-ceilings sweep reports the gypsum wall at **8**.
Both are in the same package and they are not the same number, because **they are computed at
different conditions**.

- **V5** runs the three weather conditions that survive the chiller capacity limit. At those, the
  skin is hot enough that saturation binds at **6**.
- **V5b**, the two-ceilings sweep, runs at a single condition — *Dhahran summer humid* — with the
  fan pinned at 90 %. At that condition saturation binds at **8**.

**“Dhahran summer humid” is one of the two conditions V5 discards as having no feasible
solution.** And the sweep's own output says every row of it is out of envelope:

> `CHILLER ENVELOPE: 10 of 10 cycle counts sit outside the machine's validity envelope at this
> condition, at fan 90 %.`

The script adds that this *“does not move the ceilings below”*, and for the **physical** ceiling
that is right: gypsum saturation depends on water composition and temperature, not on whether the
chiller can make its duty. **It does not obviously hold for the economic ceiling.** “Cost falls
monotonically to 7 cycles” is a statement about cost, cost is dominated by chiller power, and
chiller power is the quantity that is not valid out of envelope — which is exactly what defect 11
was.

**This has now been measured.** `src/ceiling_condition_audit.py` re-runs the same sweep at five
conditions:

| condition | fan | economic | gypsum | envelope |
|---|---|---|---|---|
| Dhahran summer humid — **the published one** | 90 % | 7 | 8 | **0 of 10 rows inside** |
| Dhahran summer humid | 100 % | 7 | 8 | **0 of 10 rows inside** |
| Dhahran summer peak | 70 % | **6** | **7** | all rows inside |
| Dhahran shoulder | 50 % | **6** | **7** | all rows inside |
| Gulf winter | 90 % | **6** | **7** | all rows inside |

**The published pair reproduces only at the condition the machine cannot operate at.** At all three
conditions V5 finds feasible, both ceilings are one cycle lower.

The gypsum wall is not corrupted by the chiller clamp — skin saturation comes from the thermal
solve, not the chiller curve. It moves because **gypsum is prograde in this model**: a hotter skin
makes it look safer, so the hottest condition yields the most permissive wall. The published
condition is simultaneously the hottest and the one the York YT cannot serve, which buys an extra
cycle on both ceilings at once.

And it closes the question this section originally opened. V5 lands on 6 and its log calls that
*“the chemistry constraint boundary”*. At an operable condition, **6 is** the last chemistry-feasible
cycle count. The controller was never leaving water on the table; a different gate was reporting a
wall one cycle further out than the plant can reach.

Recorded as **defect 14, open** — open because the fix is a reporting judgement, not a patch.

### Three options

| | Revision | Result | Argument for | Argument against |
|---|---|---|---|---|
| **A** | Leave it failed | FAIL | Nothing to defend. The evidence record is clean and a reviewer sees a team that reports its own misses. | A headline number reads as a failure when the product is at its physical limit. |
| **B** | Re-register to **≥ 12.4 %**, anchored to the last feasible cycle count | **DEAD.** 10.83 % → still **FAIL** | — | This was the fallback in the 30 August version, where it converted 14.83 % into a pass. It no longer converts anything: 10.83 % misses 12.4 % as well. **The option that existed only because the result was close to the threshold disappeared when the result moved.** Worth noticing on its own — a revision argued for on principle turned out to be worth proposing only while it happened to work. Note that re-anchoring it to the *current* wall would make it stricter still: 7 cycles is 12.50 %. |
| **C** | Re-register the metric as an **hours-weighted** annual average | **8.42 % → still FAIL, and still worse** | An unweighted mean over five arbitrary conditions is not a physical quantity; a Gulf plant spends far more hours in summer than winter. | **Computed. It makes the number worse by 2.41 points** — wider than the 1.10 points it cost after defect 11, and wider again than the 3.32-point gap in the first version is narrow. Still not a route to a pass, and now further from one. |

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

3. **It is consistent with how everything else here was done.** Thirty-four defects were found and reported, including five that were caught only because a first-principles model refused a bad input. Revising two thresholds at the end, after seeing the results, would be the one place the discipline slipped — and it would be the first place a sceptical reviewer looked.

**If you disagree**, option B on V5 is the stronger of the two revisions, because 12.4 % is a physical quantity rather than a round number. If you take it, it must appear in the PoC report as a **declared revision** with the original 15 % threshold, the date, and the reason on the record. I will implement it that way and not otherwise.

### Option C was computed, and it goes the other way

Option C — re-registering the metric as an hours-weighted annual average — was the only one that was genuinely new work rather than re-labelling, and it has now been done. A TMYx hourly file for Dhahran (station 404160, 2011–2025) arrived, the year was binned by wet-bulb into eight equal-hour bins, and the controller was run at each bin's centroid.

**It makes the number worse, not better.**

| | Water saving |
|---|---|
| Five-condition unweighted mean — what the V5 gate scores | 10.83 % |
| **Hours-weighted annual, real Dhahran year** | **8.42 %** |
| Difference | **−2.41 points** |

The reason is visible in the bins. The saving is largest in the hottest bin and smallest in the
middle of the year:

| Half of the year | Water saving by bin | Same bins, 30 August |
|---|---|---|
| Cooler half (wet-bulb 9.7–19.3 °C) | 8.2, 8.6, 6.6, 6.0 % | 8.2, 8.7, 6.4, 6.0 % — **essentially unchanged** |
| Hotter half (wet-bulb 21.4–28.5 °C) | 5.6, 8.3, 10.0, 14.0 % | 14.1, 13.8, 16.4, 18.4 % — **superseded** |

The third column is the most useful thing in this memo. Two successive fixes left the cool half of
the year almost exactly where it was and rewrote the hot half — first defect 11 cut it by four to
eight points, then defects 15 and 16 redistributed what remained. That is exactly the signature
both diagnoses predict: a chiller capacity limit and a chiller selection can only bind when the
condenser is hot. The corrections were not spread across the model, they were concentrated in the
half of the year the product is sold for.

The five hand-picked conditions were four summer and one winter. A real Dhahran year is not weighted that way, so **the gate's metric was flattering the product by more than three points.** Weighting it honestly removes that.

**This kills option C as a route to a passing gate**, and it does something more useful instead: it says the number to quote to a customer is the annual one, **not** the 10.83 % the gate scores. Two annual figures exist and they are not interchangeable — the hours-weighted mean of ratios is 8.42 %, and the ratio of hour-weighted totals is **8.81 %**. `annual_dhahran.json` says in its own `weighting_note` that the ratio of totals is the one to quote outside this repository, so **8.81 % is the commercial figure**. The 10.83 % should not be used outside the specific five-condition comparison it was computed for.

It also carries its own caveat, from the same file: only **62.5 %** of the weighted year lies inside the wet-bulb envelope the model was validated in. The remaining 37.5 % rests on extrapolation, which no weighting scheme can fix.


---

*Numbers in this memo are generated from `results/threshold_revision_options.json` and `results/v2_diagnosis.json`. Nothing in the shipped package depends on any option being taken.*
