# Defect register, and what a failed gate is not

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

There are two different things in this package that can look alike from a distance, and they should not be confused.

A **defect** is a mistake in the work — a wrong unit, an inverted sign, an unconverged solver. Defects are faults. They get found and fixed, and the count of open ones should be zero.

A **failed gate** is a result. A threshold was fixed in advance, the experiment was run, and the answer came out on the wrong side of it. That is not a fault. Suppressing it would be.

This document lists both, separately, so neither can be mistaken for the other.

---

## Part 1 — Defects. Twelve found, twelve fixed, zero open.

| # | Defect | How it showed up | State |
|---|---|---|---|
| 1 | Fan air-flow correlation read as per cent when it takes hertz | The curve turned over at 62 %, so air flow fell as the fan sped up. All three thermal gates failed with a +1.50 K bias. | **Fixed** |
| 2 | Sepiolite used as the magnesium-silicate proxy | Returned indices forbidding operation at every cycle count, against plants demonstrably running 4–5. | **Fixed** — replaced by the empirical Mg × SiO₂ product and the brucite criterion |
| 3 | Carnot-referenced chiller COP | Overstated the value of cooling the condenser by ~60 %. | **Fixed** — replaced by the EnergyPlus bi-quadratic |
| 4 | Chiller coefficients not traced to any machine | Could not be checked by anyone. | **Fixed** — York YT 1758 kW / 6.28 COP, EnergyPlus `Chillers.idf` |
| 5 | Optimiser extrapolating outside the chiller's fitted range | Booked a false 20.41 % water saving that would have flipped a failed gate to passed. | **Fixed** — the entering-condenser window is now a hard constraint; 1,840 of 6,307 candidate points are rejected |
| 6 | Duty fixed point unconverged and seed-dependent | Six substitution steps at 5 mK. Evaporation moved 3.8 % on the choice of seed alone. | **Fixed** — Aitken acceleration with a Brent fallback; 0 of 360 non-converged |
| 7 | Drift eliminator rate 100× too large | `0.0005` used as a fraction — the modern rating of 0.0005 **per cent** with its sign dropped. | **Fixed** — 1×10⁻⁵ in both `tower.py` and `controller.py`, checked by the audit |
| 8 | Simscape temperature sensor read as Celsius when it outputs Kelvin | The chemistry was asked for a saturation pH at 341 °C and the chiller reported itself out of envelope for a whole simulated day. | **Fixed** — explicit conversion block in the diagram |
| 9 | Simscape heat-flow sign inverted | +1000 kW into a 150 t mass for 600 s gave −0.956 K: right magnitude, wrong direction. | **Fixed** — ports swapped, verified against arithmetic |
| 10 | A document existed as two copies | `docs/matlab_model.md` was a manual copy of `matlab/README.md` — identical the day it was made, and guaranteed to go stale the first time either was edited. | **Fixed** — the PDF builds from the original; the audit now rejects duplicated documents |

| 11 | **Chiller capacity constraint logged but never enforced** — the same curve as defect 5, the other of its two limits | Above ~32.5 °C entering condenser water the York YT cannot make the 10 MW duty. `chiller_power_biquad` clamps `plr_raw` to 1.0 and reports the machine as merely full-loaded, so **computed chiller power fell as condenser water got hotter** — backwards. The optimiser's main lever is fan speed, and lowering the fan raises condenser temperature, so it was rewarded in exactly the region where the offsetting cost was under-computed. It moved the plant from **2 of 5** conditions infeasible to **4 of 5**, worst shortfall **1,216 kW of 10,000 kW**. | **Fixed** — `plr_raw > 1.06` is now a hard feasibility constraint alongside the temperature window |
| 12 | **A constant that documents are validated against, hardcoded into four files** | The V5 water figure `14.83` was typed into `annual.py` (×4), `make_report.py` and `audit.py`. When defect 11 moved it to `10.02`, `annual.py` wrote the stale value into the JSON the audit checks other documents against, and `audit.py` began *requiring* the report to quote a superseded number — an audit enforcing staleness. | **Fixed** — all six now read `controller_summary.json`. The audit's `"Open defects: none"` literal was replaced the same way, by a check that the declared count matches the rows marked OPEN |

Three further things were caught during development and are recorded in the code where they happened, but were never in a released result: a contradictory collocation sampler in the surrogate (42 % of points demanded two mutually exclusive constraints), an untrained evaporation head from a loss-scaling error, and an evaporation output whose range could not represent 60 % of its own training data.

**Open defects: none.**

### Defect 11, and what it cost

Defect 11 was the second half of defect 5. That fix made the entering-condenser **temperature** window a hard constraint. The bi-quadratic has *two* validity limits and the **capacity** limit was left unenforced: `CHILLER_RANGE_LOG["PLR_out"]` counted the excursions and nothing read it.

Found 3 September 2026 by a pre-registered physics gate in `src/fouling_energy.py` which required chiller power to rise when a condenser fouls. It did not. Quantified in `src/chiller_feasibility_audit.py`.

**Fixing it moved every headline number, all downward:**

| | before | after |
|---|---|---|
| V5 makeup water | 14.83 % | **10.02 %** |
| V5 total cost | 8.55 % | **6.37 %** |
| Electrical power | 4.91 % | **4.17 %** |
| Annual water, ratio of totals | 12.57 % | **9.23 %** |
| Annual cost, ratio of totals | 8.16 % | **5.88 %** |
| Conditions with a feasible optimum | 5 | **3** |
| Cycles the optimiser reaches | 7 | **6** |

The old figures were bought in a region where the machine could not make its duty. **A saving computed where the plant cannot operate is not a saving** — the same sentence defect 5 was fixed with, one dimension over.

**What did not move:** the gypsum ceiling. Economic ceiling 7 cycles, physical ceiling 8, binding mineral gypsum, cost falling monotonically. None of it goes through the chiller curve, so the two-ceilings result and the figure built on it stand unchanged.

### Defect 12, and why an audit can enforce a lie

Defect 12 is subtler and worth stating for its own sake. `14.83` was typed into six places across three files. When the controller re-ran, `annual.py` wrote the stale value into the very JSON that `audit.py` checks other documents against, and `audit.py` began demanding that the report quote a number the artefacts no longer supported.

An audit that hardcodes expected values does not verify consistency — it **freezes one moment and calls every later truth an error**. The same shape appeared in the `"Open defects: none"` literal, which passed for an honest empty register and failed for an honest non-empty one, quietly rewarding concealment.

Both are now consistency checks against the artefacts rather than string comparisons against remembered values.

`python src/audit.py` runs 50 checks across code, results and documents and gates the packaging. An inconsistent tree produces no bundle.

---

## Part 2 — Gate outcomes. Six pass, two fail, both fully diagnosed.

| Gate | Threshold, fixed before fitting | Result | |
|---|---|---|---|
| V1 outlet water temperature MAE | ≤ 1.00 K | 0.542 K | **PASS** |
| V1 heat rejection MAPE | ≤ 6.00 % | 5.94 % | **PASS** |
| V2 water consumption MAPE | ≤ 8.00 % | 9.90 % | **FAIL** |
| V5 total cost reduction | ≥ 3 % | 6.37 % | **PASS** |
| V5 makeup water reduction | ≥ 15 % | 10.02 % | **FAIL** |
| V5 skin saturation violations | 0 | 0 | **PASS** |

### V2 — failed, and the cause is now established

The gate compares predicted water consumption against the measured channel. Two explanations were possible and they make **opposite** predictions, which is what made the question answerable:

- an **unaccounted bleed** in the measured channel, which is total water consumption and would include one;
- the **fill characteristic drifting** between campaigns, already documented in the thermal channel.

Re-identifying the fill law on each campaign separately cannot help if the cause is a bleed, because a bleed is a term the model does not contain. It should close the gap if the cause is drift.

| Campaign | Identified c | Evaporation MAPE with its own fill law |
|---|---|---|
| Exp1 | 1.5320 | 6.55 % |
| Exp2 | 1.2401 | 7.80 % |
| Exp3 | 1.3826 | 4.50 % |

**Every campaign falls inside the 8 % gate.** The bleed hypothesis is rejected. The fill coefficient moves **23.5 %** across campaigns spanning four years — the same drift already measured in the thermal channel, now confirmed independently in the water channel.

So V2 fails as a **single-calibration** gate, for a physical reason rather than a modelling one: the gate holds one fill law fixed while the tower itself changed. The model is not deficient; the assumption that a tower's characteristic is a constant is.

That result points the same way as the commercial argument. **Periodic recalibration against the plant's own telemetry is a functional requirement, not an upsell** — and this gate is the measurement of how fast a fixed characteristic goes stale.

Note also that this gate previously read 7.11 % and passed. That pass rested on defect 7, the drift rate a hundred times too large, which was padding the prediction by about five per cent. Fixing a defect turned a pass into a failure. The pass was not real and has been withdrawn.

### V5 water reduction — failed, and the threshold was unreachable

Makeup water is evaporation × C/(C−1), so the saving available from raising cycles of concentration is fixed arithmetic, not a modelling choice:

| Cycles | Makeup saved vs 4 cycles |
|---|---|
| 7 | 12.50 % |
| 8 | 14.29 % |
| **8.5** | **15.00 %** ← the criterion |
| 10 | 16.67 % |
| ∞ | 25.00 % (zero blowdown, the absolute ceiling) |

Gypsum saturates at **8 cycles** on this makeup water, and gypsum saturation is not pH-sensitive, so the acid dose that buys cycles against calcite cannot move it. The criterion required 8.5 cycles. It was written on the far side of a wall that had not been located yet.

The controller reaches 10.02 %, which is more than cycles alone can deliver, because it also lowers evaporation. **No control strategy of any kind reaches 15 % on this water.**

The pre-registration was **mis-specified, not missed**. The lesson is stated in the handoff for the next time: check a threshold against the system's physical ceiling before fixing it.

---

## Part 3 — Open items that are neither defects nor failed gates

These are things not yet known. Each is stated with the direction it cuts.

| Item | Direction | What would close it |
|---|---|---|
| Almería wet-bulb tops at 21.9 °C; **40.5 % of a Dhahran year is above it** (3,551 of 8,760 h, 84 % of September) | **Unknown** — the only two-sided one, and now sized rather than described | KFUPM's humidifying wind tunnel. Not closable by argument, and the physics-informed surrogate is a mitigation, not a substitute |
| Model error 2.48× measurement uncertainty | Against us | More campaigns, or a better fill model. Reported as a negative result |
| **Skin temperature rise is a hardcoded +8 K.** The film calculation in the codebase gives 2.4-3.7 K clean; 8 K is a fouled surface | **Against us.** A hotter assumed skin makes gypsum look safer, so the 8 K value buys about one cycle of apparent headroom. At a clean 3 K the wall moves from 8 cycles to 7 | `src/skin_sensitivity.py` puts it on the record; the heated-coupon rig measures it |
| Magnesium-silicate SI threshold | Unknown | Handled by the empirical Mg × SiO₂ product instead of asserted |
| OpenModelica leg | Neutral | Written, not installed, not run. Makes no claim |
| **Acid dosing at high cycles may make the water corrosive, and the controller has no corrosion term.** EPRI warns that sulphuric acid replaces protective alkalinity with corrosive sulphate as cycles rise. **Two operators and a 1992 training syllabus now say this is the first constraint a practitioner sets, not a refinement** | **Against us**, and more sharply than when this line was written. The optimiser searches pH 7.0–9.0 against saturation only, with no corrosion floor. Field evidence in `docs/discovery_findings.md`: a plant chemist holds LSI at **0.8–1.0** deliberately, because a thin carbonate film **is** the corrosion defence; a textile engineer sets the pH window from **metallurgy** before anything else; and the 1992 course notes list *"calcium carbonate protective scale"* as a corrosion-control method. An optimiser driving toward LSI ≈ 0 strips that film | Potentiostat and coupon work in the KFUPM corrosion laboratory. **And before that, a corrosion floor in the optimiser** — this is now a specification, not an open question |
| **Fouling has no energy consequence in the model.** `chiller_power` carries `approach_cond = 4.0` as a fixed constant, so scale can build to the saturation limit and the chiller draws identical power | **Against us, and it under-sells the product.** The ESCO argument in `outreach_messages_saudi.md` §5 asserts the fouling → approach → efficiency chain, and nothing computed it. `src/fouling_energy.py` now does: at the TEMA treated-water allowance, **+11.6 % chiller power**, worth **$80,757/yr** against **$52,285/yr** of water saving at the same tariffs — a ratio of **1.54**. Energy is the larger lever, and every operator interviewed described fouling as a performance problem, never a water one | Wiring `approach_cond` to a fouling state in the controller. The remaining unknown is **rate** — how fast fouling accumulates at a given supersaturation — which needs the heated-coupon rig |
| No traction, no LOIs, no patents | Neutral | Customer interviews. Cohort 1 winners had none either |

---

## What this register is for

A reviewer should be able to ask two questions and get a clean answer to each.

**"Is the work sound?"** Twelve defects were found, all twelve are fixed, none is open, and a 50-check audit gates every release. Five of the twelve were found because a first-principles model refused a bad input rather than absorbing it — which is the argument for building it that way, and the reason the parent company is called Furqan.

Defects 11 and 12 were found the same way as the rest: a threshold fixed before the run, and a result on the wrong side of it. The gate asked only that chiller power rise when a condenser fouls. It did not. Following that back found a validity limit that had been logged for months and read by nothing — and then a constant hardcoded into an audit, which had begun requiring documents to quote a figure the artefacts had already superseded.

Fixing 11 cost the product 4.8 points of water saving and two of five operating conditions. It is reported that way because the old number was earned where the chiller could not make its duty.

**"Did everything work?"** No. Two gates failed. Both are diagnosed to a specific cause with no open questions, neither threshold was moved, and one of them failed precisely *because* a defect was fixed.
