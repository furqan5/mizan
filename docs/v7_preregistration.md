# Gate V7 — pre-registration

**Written 11 September 2026, BEFORE the gate was run.** Nothing in this
document may be edited after the first execution of `gate_v7()`. If the result
is disappointing, the result is what gets reported.

---

## Why a new gate rather than a revision of V5

V5 asked: *against an incumbent holding a fixed 4-cycle conductivity setpoint,
how much makeup water does chemistry-aware supervisory control save?* It
returned **4.38 %** against a **15 %** threshold and **failed**. That stands.
It is not revised, rescored, reweighted or reaggregated here, and V7 does not
replace it.

V7 asks a different question, and the reason is a factual one about the
customer rather than a wish about the number.

**The 4-cycle baseline is better practice than the plants this product is for.**
Evidence, all of it external:

| source | water | cycles actually run |
|---|---|---|
| Qatar Cool, public statement | TSE | **maximum 3** |
| Qatar Cool, same statement | potable / polished | approximately 9 |
| Aramco pilot, Water Technology Jan 2021 | groundwater | **2.0** |
| Aramco pilot, same | TSE | 3.5 |

A plant on treated effluent does not run at four cycles. It runs at two to
three and a half, because the operator cannot compute where the limit is and
therefore uses caution as the setpoint. Scoring against four cycles measures
the product against an incumbent who is already doing better than the
incumbent exists.

## What changes, and what deliberately does not

**Exactly one variable changes: the baseline cycles setpoint, 4.0 → 3.0.**

Everything else is held identical to V5 — the same five design conditions, the
same water, the same tariffs, the same plant, the same fan-modulated
setpoint baseline at 29 °C, the same pH 7.8, the same optimiser, the same
skin-temperature saturation constraints, the same `COST_MINIMIZING` objective.

**The threshold does not move. It stays at 15 % makeup-water reduction**, and
the cost threshold stays at 3 %, and skin-SI violations stay at zero.

Keeping the bar identical is the point. A threshold that moves with the
baseline measures nothing. If V7 passes and V5 failed, the finding is precise
and reportable: *the product clears its bar against the baseline its customers
actually run, and does not clear it against a baseline better than they run.*

## The arithmetic headroom, stated in advance

Makeup water is `M = E·C/(C−1)` at fixed evaporation. Purely from cycles,
ignoring everything the controller does with fan and pH:

| baseline → achieved | arithmetic makeup saving |
|---|---|
| 4 → 5 | 6.25 % |
| 4 → 6 | 10.00 % |
| **3 → 5** | **16.67 %** |
| **3 → 6** | **20.00 %** |
| 3 → 4 | 8.33 % |

The US DOE FEMP Best Management Practice #10 publishes the 3 → 6 figure as
**20 % makeup reduction and 50 % blowdown reduction**, which is the same
arithmetic from an independent authority.

This model's ceilings on this water are **5 cycles economic, 6 physical**,
bound by amorphous silica. So the headroom available to V7 is 16.7 % to 20 %,
and the threshold sits at 15 % inside it.

**This is stated in advance precisely so that it cannot be presented
afterwards as a discovery.** The arithmetic was known before the run. What is
NOT known before the run is how much of that headroom the controller actually
captures, because it must also satisfy the chiller envelope, the corrosion
floor, the Davies validity limit and the skin saturation constraints in all
five conditions — and in V5 it captured roughly 70 % of the equivalent
headroom (4.38 % against 6.25 %).

**If the same capture fraction holds, V7 lands near 11.7 % and FAILS.** That
is the honest prior and it is written here before the run. A pass requires the
controller to reach 5 cycles more consistently at the lower baseline than it
did at the higher one, which is plausible — there is more room below the
ceiling — but is not established.

## What a pass would and would not mean

**Would mean:** against a documented, sourced, real-world TSE baseline, the
controller saves more than 15 % of makeup water at unchanged cost and zero
saturation violations.

**Would not mean:** that V5 was wrong, that the 15 % threshold was ever met on
its own terms, or that the water product is viable. A single gate on five
design conditions is not a year and is not a plant. The hours-weighted annual
figure remains the number for a commercial conversation, and it must be
recomputed on the same baseline before it is quoted.

## The obvious objection, answered in advance

*"You changed the baseline until you passed."*

The answer has to be structural, not rhetorical:

1. **The threshold did not move.** Same 15 %, same 3 %, same zero.
2. **One variable changed**, and its new value is sourced to two named
   operators rather than chosen.
3. **V5 is still reported as a failure** in the register, the PoC report and
   the audit. It is not deleted, superseded or relabelled.
4. **The prior is written down above and says FAIL.** If it passes, it passes
   against a stated expectation that it would not.
5. The baseline is **conservative in the other direction too**: Aramco ran
   groundwater at 2.0 cycles, and a 2-cycle baseline would give 37.5 %
   arithmetic headroom. Three is the higher, harder end of the observed range.

If a reviewer still reads this as gaming, the correct response is to report
both gates side by side and let them judge — which is what
`results/controller_summary.json` will do.

---

*Threshold: 15.0 % makeup water. Baseline: 3.0 cycles. Prior: fail.
Written before execution. — 11 Sep 2026*

---

# OUTCOME — appended 11 September 2026, after execution

**Nothing above this line was edited.** This section is post-hoc and is
labelled as such.

## The result

| gate | baseline | water | verdict | cost | verdict | violations |
|---|---|---|---|---|---|---|
| V5 | 4.0 cycles | 4.38 % | **FAIL** | 3.91 % | PASS | 0 |
| **V7** | **3.0 cycles** | **15.01 %** | **PASS** | 8.54 % | PASS | 0 |

The written prior said V7 would **fail at around 11.7 %**, reasoning that V5
captured roughly 70 % of its arithmetic headroom and 70 % of 16.67 % is
11.7 %. That prior was wrong: the controller captured **90 %** of the
available headroom at the lower baseline, not 70 %. There is more room below
the ceiling at three cycles than at four, and it used it.

## Why this is not a result worth celebrating

**The margin is 0.01 percentage points.** 15.01 against 15.00. That is not a
pass, it is a coin toss wearing a verdict, and it must not be reported as
"V7 passed" without everything below it.

**The instrument that measures water failed its own calibration gate.** Gate
V2 scores the evaporation model at **9.90 % MAPE against a pre-registered
8 % threshold — a FAIL, reported as one**. Makeup water is computed from
evaporation. So the quantity this gate is made of carries a validated error
an order of magnitude larger than the margin by which the gate was cleared.

The partial defence, stated fairly: the saving is a RATIO of two makeup
figures computed by the same model, so a systematic evaporation error largely
cancels. The reason that defence is only partial is that the baseline and the
optimised case run at DIFFERENT FAN SPEEDS, and fan speed is what sets the
latent-to-sensible split — which is precisely where the evaporation model's
error lives. The cancellation is therefore not provable, and the residual is
certainly larger than 0.01 points.

**Conclusion: V7 is a PASS by the pre-registered rule and a COIN FLIP on the
physics.** Both halves of that sentence travel together or neither does.

## The baseline sensitivity, which is the real finding

`scripts/v7_baseline_sensitivity.py` sweeps the single input that changed,
across the band the primary sources actually support:

| baseline | source | arithmetic headroom to 5 cycles |
|---|---|---|
| 2.0 | Aramco: *"The COC with groundwater was limited to 2"* | 37.5 % |
| 3.0 | pre-registered; Qatar Cool's stated maximum on TSE | 16.7 % |
| 3.5 | Aramco: *"could be almost doubled (from 2 to 3.5) with municipal reclaimed water"* | **10.7 %** |
| 4.0 | V5 as originally written | 6.3 % |

**At a 3.5-cycle baseline the gate fails on arithmetic before the controller
does anything at all**, and 3.5 is what Aramco actually achieved on reclaimed
water in the pilot this package's own makeup analysis comes from.

So the verdict is not a property of the product. It is a property of **which
incumbent you are compared against**, and the honest range of incumbents spans
a failing case and a passing case. Anyone quoting V7 must quote the sweep.

## What this changes about the pitch

It removes the "double-digit water saving" claim as a standalone headline and
replaces it with something narrower and more defensible:

> Whether chemistry-aware control saves enough water to matter depends
> entirely on how conservatively the plant is running today — and the
> difference between a plant at 2 cycles and a plant at 3.5 is the difference
> between a 37 % opportunity and none. **Nobody currently measures which one
> they are**, because computing the true ceiling requires speciation that no
> incumbent controller performs.

That is a diagnostic claim, not a savings claim, and it is the same conclusion
the rest of this package keeps arriving at from other directions.

**The action it implies is unchanged and now more urgent: get the site's
actual current cycles count, and get the silica assay.** Badruzzaman et al.
(2022) has now been read in full and confirms that Aramco measured eighteen
parameters including strontium and **did not measure silica at all**.
