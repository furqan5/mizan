// Defect register — submitted as evidence of engineering rigour.
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const S = require('./style.js');
const { p, h1, h2, quote, bullet, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');
const TITLE = 'Defect Register — Furqan / Mizan';

const kids = [];
const A = (...x) => kids.push(...x);

A(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Defect Register',
  subtitle: 'Ten defects found, ten fixed, none open — and what a failed gate is not',
}));

A(p('Two different things in this package can look alike from a distance, and confusing them would be a serious misreading.'));

A(quote('A **defect** is a mistake in the work — a wrong unit, an inverted sign, an unconverged solver. Defects are faults. They get found and fixed, and the count of open ones should be zero.'));
A(quote('A **failed gate** is a result. A threshold was fixed in advance, the experiment was run, and the answer came out on the wrong side of it. That is not a fault. Suppressing it would be.'));

A(p('This document lists both, separately, so that neither can be mistaken for the other. We submit it deliberately. A venture that shows no defects at this stage has either not looked or is not saying, and a reviewer is entitled to assume the second.'));

// ------------------------------------------------------------- part 1 ----
A(h1('Part 1 — Defects: ten found, ten fixed, none open'));

A(table(
  ['#', 'Defect', 'How it revealed itself', 'State'],
  [
    ['1', 'Fan air-flow correlation read as per cent when it takes hertz', 'The curve turned over at 62 %, so air flow *fell* as the fan sped up. All three thermal gates failed with a systematic +1.50 K bias.', 'Fixed'],
    ['2', 'Sepiolite used as the magnesium-silicate proxy', 'Returned saturation indices forbidding operation at every cycle count, against plants demonstrably running four to five.', 'Fixed — replaced by an empirical Mg × SiO₂ product and the brucite criterion'],
    ['3', 'Carnot-referenced chiller coefficient of performance', 'Overstated the value of cooling the condenser by roughly 60 %.', 'Fixed — replaced by the EnergyPlus bi-quadratic form'],
    ['4', 'Chiller coefficients not traceable to any real machine', 'Could not be checked by anyone, including us.', 'Fixed — York YT 1,758 kW at 6.28 COP, from the EnergyPlus CoolTools library'],
    ['5', 'Optimiser extrapolating outside the chiller’s fitted range', 'Booked a false 20.41 % water saving that would have flipped a failed gate to passed.', 'Fixed — the entering-condenser window is a hard constraint; 1,840 of 6,307 candidate points are now rejected'],
    ['6', 'Duty fixed point unconverged and seed-dependent', 'Six substitution steps at 5 mK tolerance. Evaporation moved 3.8 % on the choice of starting guess alone.', 'Fixed — Aitken acceleration with a Brent fallback; 0 of 360 non-converged'],
    ['7', 'Drift eliminator rate one hundred times too large', 'A rating of 0.0005 **per cent** used as a fraction, with the percent sign dropped.', 'Fixed — and it converted a passing gate into a failing one'],
    ['8', 'Simscape temperature sensor read as Celsius when it outputs Kelvin', 'The chemistry was asked for a saturation pH at 341 °C, and the chiller reported itself out of envelope for a whole simulated day.', 'Fixed — explicit conversion block'],
    ['9', 'Simscape heat-flow sign inverted', '+1,000 kW into a 150 t mass for 600 s gave −0.956 K: right magnitude, wrong direction.', 'Fixed — ports swapped, verified against hand arithmetic'],
    ['10', 'A document existed as two copies', 'A manual copy that was identical the day it was made and guaranteed to go stale the first time either was edited.', 'Fixed — the audit now rejects duplicated documents'],
  ],
  widths([0.4, 2.2, 3.4, 2.2]), { zebra: true, size: 16 }));

A(spacer(140));
A(p('Three further problems were caught during development and are recorded in the code where they occurred, but were never present in a released result: a contradictory collocation sampler in the surrogate, in which 42 % of points demanded two mutually exclusive constraints; an untrained evaporation head caused by a loss-scaling error; and an evaporation output whose range could not represent 60 % of its own training data.'));

A(quote('**Open defects: none.** `python src/audit.py` runs **49 checks** across code, results and documents, and gates the packaging. An inconsistent tree produces no bundle.'));

A(h2('Four of the ten were caught by the physics, not by testing'));

A(p('This is the argument for building a first-principles model rather than fitting a regression, and it is why the parent company is named Furqan — from the Arabic root meaning *to separate*, the criterion that distinguishes true from false.'));

A(p('Defects 1, 3, 5 and 6 were all found because a model with few parameters and real physical constants **could not absorb a bad input**. It failed loudly instead of quietly fitting around the fault. A regression with free exponents would have accommodated the fan-correlation unit error, reported a good score, and carried a corrupted air-flow model into the controller — where it would have surfaced on a customer’s plant instead of on our desk.'));

// ------------------------------------------------------------- part 2 ----
A(h1('Part 2 — Gate outcomes: four pass, two fail, both diagnosed'));

A(table(
  ['Gate', 'Threshold, fixed before fitting', 'Result', 'Verdict'],
  [
    ['V1 outlet water temperature, MAE', '≤ 1.00 K', '0.542 K', 'PASS'],
    ['V1 heat rejection, MAPE', '≤ 6.00 %', '5.94 %', 'PASS'],
    ['V2 water consumption, MAPE', '≤ 8.00 %', '9.90 %', '**FAIL**'],
    ['V5 total cost reduction', '≥ 3 %', '8.55 %', 'PASS'],
    ['V5 makeup water reduction', '≥ 15 %', '14.83 %', '**FAIL**'],
    ['V5 skin saturation violations', '0', '0', 'PASS'],
  ],
  widths([2.6, 1.6, 1.1, 1.0]),
  { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(h2('V2 — failed because a defect was fixed'));

A(p('This gate previously read 7.11 % and passed. That pass rested on defect 7, the drift rate a hundred times too large, which was padding the prediction by about five per cent. **Fixing a defect turned a pass into a failure.** The old result was not real and has been withdrawn.'));

A(p('The cause of the remaining shortfall was then established by a test that could have failed. Two explanations were possible and they make opposite predictions: an unaccounted bleed in the measured channel, or the fill characteristic drifting between campaigns. Re-identifying the fill law per campaign cannot help against a bleed, because a bleed is a term the model does not contain — but it should close the gap almost entirely if the cause is drift.'));

A(table(
  ['Campaign', 'Identified coefficient', 'Evaporation MAPE with its own fill law'],
  [['Exp1', '1.5320', '6.55 %'], ['Exp2', '1.2401', '7.80 %'], ['Exp3', '1.3826', '4.50 %']],
  widths([1.2, 1.6, 2.6]), { align: ['L', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Every campaign falls inside the 8 % gate once its own fill law is used. The bleed hypothesis is rejected. The identified coefficient moves **23.5 %** across campaigns spanning four years — the same drift already measured in the thermal channel, now confirmed independently in the water channel. The model is not deficient; the assumption that a cooling tower’s characteristic is a constant is.'));

A(quote('That result points the same way as the commercial argument. **Periodic recalibration against the plant’s own telemetry is a functional requirement of the product, not an upsell** — and this failed gate is the measurement of how fast a fixed characteristic goes stale.'));

A(h2('V5 water — failed because the threshold was written beyond a physical wall'));

A(p('This is the more interesting of the two failures, because the criterion turned out to be arithmetically unreachable rather than merely missed.'));

A(p('Makeup water is evaporation multiplied by C/(C−1), so the saving available from raising cycles of concentration is fixed arithmetic and not a modelling choice:'));

A(table(
  ['Cycles of concentration', 'Makeup water saved against 4 cycles'],
  [
    ['7', '12.50 %'],
    ['8', '14.29 %'],
    ['**8.5**', '**15.00 % — the pre-registered criterion**'],
    ['10', '16.67 %'],
    ['Infinite (zero blowdown)', '25.00 % — the absolute ceiling'],
  ],
  widths([2, 2.4]), { align: ['C', 'C'], zebra: true }));

A(spacer(140));
A(p('Gypsum saturates at **8 cycles** on this makeup water, and gypsum saturation is **not pH-sensitive** — a fact confirmed independently by EPRI’s state-of-knowledge review, which states plainly that calcium sulphate scale is not pH sensitive as calcium carbonate scale is. So the acid dose that buys cycles against calcite cannot move the gypsum wall. The criterion required 8.5 cycles. It was written on the far side of a wall that had not yet been located.'));

A(quote('**No control strategy of any kind reaches 15 % on this makeup water by raising cycles.** The pre-registration was mis-specified, not missed. The threshold has not been moved and the gate stays failed.'));

A(p('The controller nevertheless reaches 14.83 %, which is more than cycles alone can deliver at its operating point, because it also lowers evaporation by slowing the fan wherever the chiller can absorb warmer condenser water. That second term is exactly the coupling this product exists to price, and it is invisible to both incumbent disciplines.'));

A(h2('What the failure discovered'));

A(p('Read as a score, this gate is a miss by 0.17 percentage points. Read as an experiment, it located a hard physical limit that neither of the two incumbent disciplines can see, and it did so before any customer had to find it on an operating plant.'));

A(bullet('The binding mineral on Gulf treated effluent is **gypsum, not calcium carbonate**. The Langelier index the industry controls on describes calcite only and cannot represent gypsum at all.'));
A(bullet('That limit is **immune to the acid lever**, which is the one control a water-treatment programme actually has for buying cycles.'));
A(bullet('An operator following cost alone walks toward that wall with **no instrument that can see it**, because the cost curve on this water falls monotonically right up to the last feasible point.'));

A(quote('A criterion that is missed teaches nothing. A criterion that is *unreachable* tells you where the physics stops — and that is a more valuable thing to know than whether a number cleared a bar we set ourselves before we understood the system.'));

A(p('The operating lesson has been written into the project record so that it is not repeated: **check a pre-registered threshold against the physical ceiling of the system before fixing it.**'));

// ------------------------------------------------------------- part 3 ----
A(h1('Part 3 — Open items: neither defects nor failed gates'));

A(p('These are things not yet known. Each is stated with the direction it biases our own result.'));

A(table(
  ['Item', 'Direction', 'What would close it'],
  [
    ['Validation data tops out at 21.9 °C wet-bulb; **40.5 % of a Dhahran year is above it** — 3,551 of 8,760 hours, and 84 % of September', '**Unknown** — the only two-sided item, and now sized rather than described', 'KFUPM’s humidifying wind tunnel. Not closable by argument'],
    ['Model error is 2.48× the propagated measurement uncertainty', 'Against us', 'More campaigns, or a better fill model. Reported as a negative result'],
    ['**Skin temperature rise is a hardcoded +8 K.** The film calculation in our own codebase gives 2.4–3.7 K clean; 8 K is a fouled surface', '**Against us.** A hotter assumed skin makes gypsum look safer, so 8 K buys about one cycle of apparent headroom. At a clean 3 K the wall moves from 8 cycles to 7', 'A sensitivity run is on the record; the heated-coupon rig measures it'],
    ['**Acid dosing at high cycles may make the water corrosive, and the controller has no corrosion term.** EPRI warns that sulphuric acid replaces protective alkalinity with corrosive sulphate as cycles rise', '**Against us.** The optimiser does exactly this — seven cycles plus acid to pH 8.0–8.25', 'Potentiostat and mass-loss coupon work in the KFUPM corrosion laboratory'],
    ['OpenModelica leg', 'Neutral', 'Written, never installed, never run. Supports no claim'],
    ['No traction, no letters of intent, no patents', 'Neutral', 'Customer interviews, now scheduled'],
  ],
  widths([3, 2.2, 2.2]), { zebra: true, size: 16 }));

A(spacer(160));
A(h1('What this register is for'));

A(p('A reviewer should be able to ask two questions and get a clean answer to each.'));

A(quote('**"Is the work sound?"** Ten defects were found, all ten are fixed, none is open, and a 49-check audit gates every release. Four of the ten were caught because a first-principles model refused a bad input rather than absorbing it.'));

A(quote('**"Did everything work?"** No. Two gates failed. Both are diagnosed to a specific cause with no open questions, neither threshold was moved, and one of them failed precisely *because* a defect was fixed.'));

A(spacer(160));
A(rule());
A(note('Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley. 30 August 2026.'));

const doc = new Document({
  numbering: S.NUMBERING,
  title: TITLE,
  creator: 'Furqan',
  sections: [Object.assign({}, S.sectionProps(TITLE, 'FURQAN · MIZAN'), { children: kids })],
});

Packer.toBuffer(doc).then((b) => {
  fs.mkdirSync(OUT, { recursive: true });
  const f = path.join(OUT, 'Furqan_Mizan_Defect_Register.docx');
  fs.writeFileSync(f, b);
  console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB');
});
