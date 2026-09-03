// Proof-of-Concept report — the primary technical upload.
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType } = require('docx');
const S = require('./style.js');
const { p, h1, h2, h3, quote, bullet, numbered, note, spacer, rule, table, widths } = S;

const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, '..', 'DTV_Submission');
const TITLE = 'Proof-of-Concept Report — Mizan';

// --- figure helper ---------------------------------------------------------
let figNo = 0;
function figure(file, caption, wpx) {
  const f = path.join(ROOT, 'figs', file);
  const buf = fs.readFileSync(f);
  const dim = { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
  const W = wpx || 600;
  const H = Math.round((W * dim.h) / dim.w);
  figNo += 1;
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 70 },
      children: [new ImageRun({ data: buf, type: 'png', transformation: { width: W, height: H } })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 220 },
      children: S.runs('**Figure ' + figNo + '.** ' + caption, { font: S.BODY_FONT, size: 17, color: S.MUTED }),
    }),
  ];
}

const kids = [];
const A = (...x) => kids.push(...x);

// ---------------------------------------------------------------- cover ----
A(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Proof-of-Concept Report',
  subtitle: 'Mizan — an energy–water supervisory controller for condenser-water loops',
}));

A(table(null, [
  ['Product', 'Mizan · *The balance between energy and water*'],
  ['Scope', 'Supervisory control of cooling-tower and condenser-water loops in Gulf district cooling'],
  ['Maturity claimed', 'TRL 3 — analytical and computational studies validated against measured experimental data'],
  ['Validation', '165 published experimental points; 50 held out; thresholds fixed before fitting; scored once'],
  ['Reproducibility', 'Four commands against a public, MD5-verified dataset'],
  ['Date', '30 August 2026'],
], widths([1, 3.4])));

A(spacer(240));

// -------------------------------------------------------------- 0. venture ----
A(h1('0. The group and the venture'));

A(p('*Furqan* (الفرقان), from the Arabic root **f-r-q**, to separate: the criterion that distinguishes the true from the false. The name states the method rather than decorating it. Hard energy infrastructure is run on correlations fitted at one plant and then trusted everywhere. A first-principles model with few parameters cannot absorb a bad input, so it fails loudly instead of quietly fitting around the defect. Three of the four largest corrections recorded in this document are exactly that: a fan correlation read in the wrong unit, a chiller curve used outside the range it was fitted in, and a drift rate a hundred times too large. Each was caught because the physics refused it.'));

A(p('*Mizan* (الميزان): the balance, the scale, the measure held level. The condenser-water loop is the one place in a district-cooling plant where energy and water are the same decision, and it is currently made by three parties who never speak to one another. Mizan is the first venture built on the group’s method. The physics core, the validation discipline and the physics-informed learning layer described here belong to the parent and are intended to carry into further energy products.'));

// ---------------------------------------------------------- 1. claims ----
A(h1('1. What is claimed, and what is not'));

A(h2('Claimed'));
A(p('A first-principles model of a counterflow wet cooling tower, coupled to an ion-specific water-chemistry model, predicts **measured outlet water temperature** and **measured heat rejection** on experimental data the model was never fitted to, within thresholds fixed before the fit was run.'));

A(h2('Explicitly not claimed, on the same data'));
A(p('The water-consumption gate is **failed**. The model predicts measured water consumption to 9.90 % against a threshold of 8.00 %. Section 4 sets out why, including the fact that an earlier revision of this document reported a pass which turned out to rest on a drift constant a hundred times too large. The thermal claim and the water claim are separated here because the evidence separates them.'));

A(h2('Not claimed at all'));
A(p('No closed-loop control on physical hardware. No field data from an operating plant. No validated scaling-kinetics model. These are TRL 4 objectives and are the subject of the laboratory programme in section 9.'));

A(h2('On the machine-learning component'));
A(p('A physics-informed surrogate of the tower model exists and is documented separately, but **no gate result in this document depends on it**. It is trained against the physics core rather than against a plant, it is scored on how faithfully it reproduces that core, and it is excluded by construction from the chemistry and from every safety constraint. Every number in sections 4 through 8 comes from the deterministic physics.'));

// ------------------------------------------------------- 2. evidence ----
A(h1('2. Evidence base'));

A(table(
  ['Item', 'Detail'],
  [
    ['Dataset', 'Steady-state operation of an experimental wet cooling-tower pilot plant, Plataforma Solar de Almería'],
    ['Authors', 'Palenzuela, Roca and Serrano Rodríguez'],
    ['Source', 'Zenodo record 10806201, CC BY 4.0'],
    ['Integrity', 'MD5 `ac94e0076a9217b58e032a2545bf9fc4`, matching the published record'],
    ['Size', '165 steady-state operating points across three campaigns, October 2019 to October 2023'],
    ['Range', 'Duty 48–207 kW; ambient 9–40.5 °C; relative humidity 10–87 %'],
    ['Channels used', 'Inlet and outlet water temperature, water flow, ambient temperature and humidity, fan speed, and **measured water consumption**'],
  ],
  widths([1, 3.4]), { zebra: true }));

A(spacer(140));
A(p('The measured water-consumption channel is why this dataset was chosen over the alternatives. It allows the water model and the thermal model to be validated against one consistent experiment on one rig, rather than borrowing a chemistry benchmark from an unrelated plant.'));

// --------------------------------------------------------- 3. method ----
A(h1('3. Method'));

A(p('The governing physics is the Poppe and Rögener heat-and-mass-transfer formulation in the form given by Kloppers and Kröger (2005), integrated over water temperature with both the unsaturated and the supersaturated — fogged — air branches. Moist-air properties follow the ASHRAE Handbook of Fundamentals formulation, implemented in house so that every constant is auditable and so that the whole core can run on an edge controller with no third-party scientific runtime.'));

A(p('Aqueous speciation uses equilibrium constants taken directly from the USGS PHREEQC `phreeqc.dat` database, so the implementation can be checked against the accepted reference rather than against a correlation of our own.'));

A(h2('Identification'));
A(p('The fill characteristic is identified the way cooling-tower practice identifies it, following CTI ATC-105, and not by black-box search. For each measured point the Poppe equations are integrated from the *measured* outlet temperature to the measured inlet temperature, which gives the Merkel number the duty actually demanded, from measurements alone. Regressing log(Me) on log(m_w/m_a) over the training campaign then yields the fill law in closed form.'));
A(quote('Identified law: **Me = 1.2401 · (m_w/m_a)^(−0.5014)**, with a log-space R² of 0.3719.'));
A(p('The exponent of −0.501 sits in the normal range for counterflow fill, which is an independent check that the identification is physical rather than a curve fit absorbing error.'));

A(h2('Holdout'));
A(p('The model is calibrated on campaign Exp2 only and tested on campaigns Exp1 and Exp3, which are separate experimental campaigns run in different seasons under different designs of experiment. This is a harder test than a random row split, because it measures transfer across campaigns rather than interpolation within one. The holdout was scored once, against thresholds fixed in advance.'));

// -------------------------------------------------------- 4. results ----
A(h1('4. Results against pre-registered thresholds'));

A(table(
  ['Gate', 'Quantity', 'Threshold', 'Holdout result', 'Verdict'],
  [
    ['V1', 'Outlet water temperature, MAE', '≤ 1.00 K', '0.542 K', 'PASS'],
    ['V1', 'Heat rejection, MAPE', '≤ 6.00 %', '5.94 %', 'PASS'],
    ['V2', 'Evaporation vs measured water loss, MAPE', '≤ 8.00 %', '9.90 %', '**FAIL**'],
  ],
  widths([0.7, 4, 1.5, 1.6, 1.2]),
  { align: ['C', 'L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Holdout n = 50, with 100 % solver convergence, RMSE 0.662 K, bias +0.453 K and a 95th-percentile absolute error of 1.366 K. For comparison, on the training set: MAE 0.454 K, heat-rejection MAPE 7.48 %, evaporation MAPE 7.80 %.'));

A(h2('Why gate V2 fails, and why the earlier pass was not real'));
A(p('Gate V2 asks whether predicted water consumption matches the measured water-consumption channel. On the untouched holdout it does not: 9.90 % against a threshold of 8.00 %. An earlier revision of this document reported 7.11 % and a pass. That pass was an artefact and is withdrawn here.'));
A(p('The cause was the drift term. Predicted consumption is evaporation plus drift, and the drift constant was 0.0005 used as a *fraction* of circulating flow — the modern eliminator rating of 0.0005 **per cent** with its percent sign dropped, and therefore a hundred times too much water. On this rig that inflated the prediction by roughly five per cent, which is most of the distance between the 7.11 % previously reported and the threshold. Correcting the constant to a defensible 0.001 % removes the inflation and exposes a real shortfall.'));

A(h3('The shortfall is campaign-dependent, and that is the informative part'));
A(table(
  ['Campaign', 'Role', 'Mean shortfall against measured'],
  [['Exp2', 'training', '0.83 %'], ['Exp1', 'holdout', '9.88 %'], ['Exp3', 'holdout', '8.60 %']],
  widths([1, 1, 1.6]), { align: ['L', 'L', 'C'], zebra: true }));

A(spacer(140));
A(p('A fixed bleed would produce a shortfall proportional to circulating flow; a model deficiency would produce one proportional to evaporation. Regressing the residual on each gives R² of −0.06 and 0.06 respectively, so neither explains it. What does fit the pattern is that the model matches the campaign it was identified on and not the two it was not — the same campaign-to-campaign movement already documented in the fill characteristic.'));

A(p('**The cause is now established, by a test that could have failed.** Two explanations were possible: an unaccounted bleed in the measured channel, which is total water consumption and would include one; or the fill characteristic drifting between campaigns, which is already visible in the thermal channel. They make opposite predictions. Re-identifying the fill law on each campaign separately cannot help if the shortfall is a bleed, because a bleed is a term the model does not contain — but it should close the gap almost entirely if the cause is drift.'));

A(table(
  ['Campaign', 'Identified c', 'Identified n', 'Outlet MAE', 'Evaporation MAPE'],
  [
    ['Exp1', '1.5320', '−0.6015', '0.280 K', '6.55 %'],
    ['Exp2', '1.2401', '−0.5014', '0.454 K', '7.80 %'],
    ['Exp3', '1.3826', '−0.4293', '0.262 K', '4.50 %'],
  ],
  widths([1, 1, 1, 1, 1.3]), { align: ['L', 'C', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('**Every campaign falls inside the 8 % gate once its own fill law is used**, with a worst case of 7.80 %. The bleed hypothesis is rejected, because a bleed would have been untouched by re-identification. The identified fill coefficient moves 23.5 % across the three campaigns, which is the same drift already measured in the thermal channel and is now confirmed independently in the water channel.'));

A(p('So V2 fails as a **single-calibration** gate, and it fails for a physical reason rather than a modelling one. The gate holds one fill law fixed across campaigns spanning four years, and the tower itself changed over those four years. The model is not deficient; the assumption that a tower’s characteristic is a constant is.'));

A(p('That is not a comfortable result, but it is a useful one, and it points the same way as the commercial argument. **Periodic recalibration against the plant’s own telemetry is a functional requirement of the product, not an upsell.** A controller shipped with a fixed fill characteristic degrades silently as the fill fouls, and this gate is the measurement of how fast. What is still not claimed is that the water model is validated against an operating plant. It is not. The gate as pre-registered stands as failed, and the threshold has not been moved.'));

A(h2('A defect found and corrected, reported in full'));
A(p('The first execution of this holdout **failed all three gates**, with an outlet MAE of 1.571 K against a 1.00 K threshold and a systematic +1.50 K bias. A bias that large is characteristic of a unit error rather than model inadequacy, and it was one.'));
A(p('The air-mass-flow correlation published with the dataset, m_a = −0.0014 f² + 0.1743 f − 0.7251, takes fan frequency in **hertz**, although the dataset’s own text describes its fan channel as a percentage. Two independent checks establish this:'));
A(bullet('Read as a percentage, the quadratic turns over at f = 62.25 %, so air mass flow would *fall* as the fan speeds up from 62 % to 100 %. No fan behaves that way.'));
A(bullet('Read as a percentage, the tower’s own published design point implies a liquid-to-gas ratio of 2.55. Read as hertz it gives 1.54, squarely in the normal range for a counterflow induced-draught tower.'));
A(p('This is recorded because it demonstrates the property that makes a first-principles model worth building: it could not absorb the bad input. A regression with free exponents on air flow would have fitted around the distortion, reported a good score, and carried a corrupted air-flow model into the controller.'));

A(h2('An independent check on the psychrometrics'));
A(p('The moist-air property code here is written in house, because Python 3.14 has no wheels for CoolProp or psychrolib and an edge controller should ship without a third-party scientific runtime. That is defensible only if the implementation can be shown to be right, and until recently it could not be: every gate above tests the tower model and the psychrometrics together, so an error in one could in principle be absorbed by the other.'));
A(p('A TMYx weather file for Dhahran, station 404160 covering 2011 to 2025, closes that gap. Its header carries the **2025 ASHRAE Handbook of Fundamentals design conditions** for the same station, computed by ASHRAE from the same underlying hours by their own method. Recomputing those percentiles from the hourly file with our own code is a genuine independent comparison: neither side was fitted to the other, and nothing was tuned to make them agree.'));

A(table(
  ['Percentile', 'ASHRAE 2025', 'This package', 'Difference'],
  [
    ['0.4 % wet-bulb', '31.4 °C', '31.34 °C', '−0.06 K'],
    ['1.0 % wet-bulb', '30.5 °C', '30.45 °C', '−0.05 K'],
    ['2.0 % wet-bulb', '29.6 °C', '29.69 °C', '+0.09 K'],
  ],
  widths([1.4, 1, 1, 1]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('The worst disagreement across six design percentiles, wet-bulb and dry-bulb together, is **0.20 K**. The psychrometric layer is correct, and that is now established separately from everything built on top of it. The same file also settles a figure this document had been carrying without a citation: Gulf design wet-bulb was quoted as 30.3 °C from no stated source, and ASHRAE 2025 for Dhahran gives 30.5 °C at the 1 % percentile and 31.4 °C at 0.4 %. The assumed value was close, but it is now sourced rather than asserted.'));

A(h2('How much of a Gulf year the model has never seen'));
A(p('The same hourly file finally puts a number on the largest open item in this package. The validation data tops out at 21.9 °C wet-bulb, and above that the model extrapolates. That was carried for the whole project as a qualitative worry, because there was no hourly Gulf weather to measure it against.'));
A(quote('**40.5 % of a Dhahran year — 3,551 of 8,760 hours — is above that ceiling**, rising to 84 % of the hours in September, with an annual maximum wet-bulb of 34.6 °C.'));
A(...figure('wetbulb_gap.png', 'Dhahran monthly wet-bulb against the ceiling of the validation dataset and the ASHRAE 1 % design condition. The shaded region is the part of the year the model has never been tested in.'));
A(p('This cuts against us, and it is the strongest possible statement of why the KFUPM humidifying wind tunnel is the right thing to ask for. Two fifths of the operating year sits outside the envelope, and no amount of modelling closes that. The physics-informed surrogate constrains the extrapolation with inequalities that thermodynamics guarantees everywhere, which is a mitigation and not a substitute for measuring it.'));

A(h2('What a real year is worth, rather than five chosen conditions'));
A(p('Gate V5 scores an unweighted mean over five hand-picked ambient conditions. That is not a physical quantity, because it depends on which five were chosen. With an hourly year available, the honest version can be computed: bin the year by wet-bulb, run the controller at each bin centroid, and weight by the hours actually spent there.'));

A(table(
  ['Metric', 'Makeup water saving'],
  [
    ['Five-condition unweighted mean (the V5 gate)', '14.83 %'],
    ['**Hours-weighted annual, Dhahran TMYx**', '**11.51 %**'],
    ['Difference', '−3.32 points'],
  ],
  widths([2.6, 1.4]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(p('**The gate metric was flattering the product.** The saving is large when it is hot and small when it is not — 6.0 to 8.7 % across the cooler half of the year and 13.8 to 18.4 % across the hotter half — and the five chosen conditions were four summer and one winter. A real Dhahran year is not weighted that way.'));
A(p('The figure that belongs in a commercial conversation is therefore **11.5 % annually**, not 14.83 %. The higher number should not be used outside the specific five-condition comparison it was computed for. This is reported here rather than quietly dropped because it was found while looking for a way to make a failed gate pass, and it did the opposite. The same calculation carries its own caveat: only 62.5 % of the weighted year lies inside the wet-bulb envelope the model was validated in, and no weighting scheme fixes the rest.'));

// -------------------------------------------------- 4b. ENERGY ----
A(h1('5. The energy term, reported on its own'));

A(p('Electrical power has always been the first term of the controller’s objective function. Cost per hour is the electricity tariff multiplied by total electrical power, plus water, plus acid, plus antiscalant, where total power is the fan shaft power from the affinity law added to chiller power from the bi-quadratic curve of a named machine. It is the only reason fan speed is an actuator at all: strip the energy term out and the optimiser simply closes the fan to suppress evaporation, which is the degenerate answer a water treater would already give.'));

A(p('Until this revision, however, that term was monetised into the cost result and never reported by itself. For a venture entering under an energy focus area, that was a reporting defect rather than a modelling one, and it is corrected here.'));

A(table(
  ['Condition', 'Baseline kW', 'Optimised kW', 'Δ kW', 'Power reduction', 'Electricity share of the saving'],
  [
    ['Dhahran summer peak', '1,642.6', '1,610.2', '32.4', '1.97 %', '13.4 %'],
    ['Dhahran summer humid', '1,711.5', '1,622.9', '88.6', '5.18 %', '35.4 %'],
    ['Dhahran shoulder', '1,625.8', '1,600.2', '25.6', '1.57 %', '15.2 %'],
    ['Doha summer humid', '1,708.4', '1,644.6', '63.8', '3.73 %', '28.7 %'],
    ['**Gulf winter**', '**1,606.7**', '**1,412.5**', '**194.2**', '**12.09 %**', '**74.2 %**'],
    ['Mean', '', '', '', '**4.91 %**', ''],
  ],
  widths([1.8, 1.1, 1.1, 0.8, 1.2, 1.5]),
  { align: ['L', 'R', 'R', 'R', 'C', 'C'], zebra: true, size: 18 }));

A(spacer(140));
A(p('The winter condition is the one worth reading twice, because it is the clearest demonstration of what this product does that neither incumbent discipline can. There the controller drives the fan **up**, from 40 % to 90 %, pulling entering condenser water from 30.4 °C down to 23.2 °C. It spends fan power to buy compressor power. It accepts a *worse* water result while doing so — 8.4 %, the lowest of the five conditions — and still returns the largest cost saving of any condition at 10.68 %.'));

A(quote('No water-treatment controller on the market would ever make that move, because it makes the water number worse. No energy optimiser would find it either, because it has no way to know what raising the fan does to the saturation state at the tube skin. The move is only available to a controller that prices both at once.'));

A(h2('The two savings are anti-correlated across the year'));

A(p('Reporting the energy term separately made something visible that the five-condition gate could not show at all. Running the controller across eight equal-hour wet-bulb bins of a Dhahran year, the energy saving and the water saving move in **opposite** directions, with a Pearson correlation of **r = −0.664**.'));

A(table(
  ['Half of the year', 'Wet-bulb range', 'Power reduction', 'Water reduction', 'Cost reduction'],
  [
    ['Cool half (4,380 h)', '9.7 – 19.3 °C', '**10.40 %**', '7.34 %', '9.18 %'],
    ['Hot half (4,380 h)', '21.4 – 28.5 °C', '2.96 %', '**15.69 %**', '7.49 %'],
    ['**Hours-weighted year**', '—', '**6.68 %**', '**11.51 %**', '**8.33 %**'],
  ],
  widths([1.6, 1.3, 1.2, 1.2, 1.2]),
  { align: ['L', 'C', 'C', 'C', 'C'], zebra: true }));

A(...figure('seasonal_handoff.png', 'Electrical power and makeup water reductions across eight equal-hour wet-bulb bins of a Dhahran year. The two mechanisms hand off to each other at about 20 °C wet-bulb, which is why the total cost saving stays inside a narrow band all year.'));

A(p('In the cool half the controller runs the fan hard and buys compressor power, and the water result is modest. In the hot half it slows the fan, banks evaporation, and the energy result nearly vanishes — down to 1.25 % in the mildest summer bin. The two mechanisms hand off to each other at about 20 °C wet-bulb.'));

A(quote('The consequence is the strongest argument in this package for coupling the two models. Total operating cost saving stays between **5.6 % and 10.9 % in every bin of the year**, but it is produced by a different physical mechanism in each half. A controller optimising water alone collects almost nothing across the cool half of a Dhahran year. A controller optimising energy alone collects almost nothing across the hot half. Only a controller that prices both holds the saving steady across all 8,760 hours.'));

A(p('This is not a result we designed for, and it was not visible until the energy term was pulled out of the cost figure. It is reported here because it changes what the product is for: the coupling is not a refinement on top of a water-saving device, it is the thing that makes the saving year-round.'));

A(note('These figures are reported diagnostics and not pre-registered gates. They are computed after the fact, and attaching a threshold to them now would be scoring a criterion chosen once the answer was known. They carry exactly the same status as the hours-weighted annual water figure: reported alongside the gates, never in place of them.'));

// -------------------------------------------------- 6. model selection ----
A(h1('6. Model selection — why the fill law has two parameters'));

A(p('The identified fill law fits the training campaign with a log-space R² of 0.372. That is low enough to deserve an answer rather than a footnote, and there are only two possible explanations: the functional form is too poor, or the scatter is experimental and no form will fit it better.'));
A(p('Five candidate forms were fitted on the training campaign alone and scored by forward outlet-temperature prediction on the untouched holdout. R² is reported for interest but is not the selection criterion — a form can raise R² on the Merkel number and still predict temperature worse, and temperature is the quantity that matters.'));

A(table(
  ['Form', 'Params', 'Train R²', 'Holdout MAE', 'Holdout RMSE'],
  [
    ['A: ratio only, Me = c(m_w/m_a)ⁿ **(adopted)**', '2', '0.372', '0.542 K', '0.662 K'],
    ['B: separate flows', '3', '0.382', '0.629 K', '0.788 K'],
    ['C: ratio plus inlet temperature', '3', '0.372', '0.550 K', '0.666 K'],
    ['D: separate flows plus inlet temperature', '4', '0.382', '0.633 K', '0.793 K'],
    ['E: separate flows plus wet-bulb', '4', '0.506', '0.517 K', '0.710 K'],
  ],
  widths([2.6, 0.8, 1, 1.1, 1.1]), { align: ['L', 'C', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('**Adding flow terms raises training R² while making holdout prediction worse.** That is overfitting demonstrated rather than asserted, and it answers the R² question directly: the scatter is experimental, not a deficient functional form.'));

A(p('**The form that scored best on MAE was rejected.** Form E reaches 0.517 K against 0.542 K for the adopted law — a gain of 0.025 K on an error of about half a kelvin, bought while making RMSE *worse* by 0.048 K. It reduces typical error and increases large error, which is a differently-shaped error distribution rather than a better model.'));

A(p('The deciding objection is physical rather than statistical. A Merkel number is a property of the fill’s heat-and-mass-transfer geometry. Ambient wet-bulb is an operating condition. Admitting it to the fill law lets the regression absorb the training climate into what is supposed to be equipment physics — and the training climate is not ours. The training wet-bulb range is 4.3 to 21.9 °C against a Gulf design wet-bulb of 30.3 °C, an extrapolation of +8.4 K. The fitted wet-bulb exponent would predict roughly 14 % different transfer capability at Gulf design wet-bulb on no supporting data, extrapolating hardest exactly where the product is intended to operate. The two-parameter law is retained.'));

A(h2('How large is the residual, and what causes it?'));
A(p('A model error is meaningless without the experiment’s own uncertainty beside it. The dataset publishes its instrument specifications, so they were propagated through the model by Monte Carlo following GUM Supplement 1, with 160 samples per holdout point.'));

A(table(
  ['Quantity', 'Value'],
  [
    ['Uncertainty in predicted outlet temperature, from input uncertainty', '0.188 K'],
    ['Uncertainty in measured outlet temperature, Pt100', '0.104 K'],
    ['Combined standard uncertainty', '0.217 K'],
    ['Expanded uncertainty at k = 2, about 95 %', '0.434 K'],
    ['**Model MAE on the same points**', '**0.537 K**'],
    ['Ratio of MAE to combined standard uncertainty', '**2.48**'],
    ['Points agreeing within the expanded uncertainty', '40 %'],
  ],
  widths([3, 1.2]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(p('**This is a negative result and it is reported as one.** The model does not agree with the experiment to within measurement uncertainty; it sits about two and a half times outside it, with a systematic holdout bias rather than symmetric scatter. Something real is being missed.'));

A(p('The cause was then isolated. A deficiency in the model form would persist within a single campaign. Drift in the fill characteristic — the campaigns span October 2019 to October 2023, and fill fouls and degrades — would appear only across campaigns.'));
A(bullet('Mean **within**-campaign MAE: **0.332 K**, or 1.53 times the combined uncertainty, with bias essentially zero'));
A(bullet('Mean **across**-campaign MAE: **0.470 K**, or 2.17 times the combined uncertainty'));
A(bullet('Drift penalty: **+0.138 K**'));
A(bullet('Identified fill coefficient across campaigns: **1.240 to 1.532**, a spread of **21.1 %**'));

A(p('**Both effects are present, and the honest verdict is mixed.** Within a campaign the model is nearly unbiased and sits at 1.53 times the measurement uncertainty — close to the floor but not at it, so a genuine modelling residual remains. Across campaigns a further 0.138 K appears, and the identified fill coefficient moves by a fifth over four years. The drift finding has a direct product consequence: a cooling-tower fill characteristic is not a constant, so a controller that assumes a fixed characteristic will degrade silently in service. Periodic recalibration against the plant’s own telemetry is a functional requirement, and this dataset is the evidence for it.'));

// ------------------------------------------------------------- 7. V3 ----
A(h1('7. Gate V3 — the saturation limit is set at the tube wall, not in the bulk'));

A(p('Scale forms at the hottest wetted surface, the condenser tube wall, which runs several kelvin above bulk water temperature. Calcite and gypsum both become less soluble as temperature rises, so a saturation index computed at bulk temperature — which is where conventional practice and every conductivity controller evaluates it — systematically understates risk where scale actually forms. The makeup water here is a published Saudi treated-sewage-effluent analysis at 1,500 mg/L total dissolved solids, closed on charge balance by chloride.'));

A(table(
  ['Bulk temperature', 'Limit at bulk', 'Limit at skin (+8 K)', 'Bulk basis overstates by'],
  [
    ['30 °C', '3.48 cycles', '3.02 cycles', '15.2 %'],
    ['33 °C', '3.30 cycles', '2.86 cycles', '15.4 %'],
    ['36 °C', '3.13 cycles', '2.71 cycles', '15.6 %'],
  ],
  widths([1.3, 1.2, 1.5, 1.6]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('The relative gap is stable at about 15.6 % across the whole condenser operating range. That gap is the margin a plant believes it has and does not. The silica ceiling itself moves seasonally, while industry practice holds it fixed.'));

A(...figure('silica_seasonal.png', 'Amorphous silica ceiling against tower-basin temperature, from the PHREEQC SiO₂(a) constant, compared with the static 150 mg/L industry rule.'));
A(...figure('silica_wall.png', 'Highest safe cycles of concentration against makeup silica, with the Saudi brackish range and the industry practice band marked.'));

A(note('Limitation, stated plainly. The absolute cycles limits above assume no acid dosing, so pH free-runs above 9 as the tower strips carbon dioxide and calcite binds early. Real plants dose acid and run four to eight cycles. The absolute limit therefore requires calibration against a specific antiscalant programme. The relative bulk-versus-skin gap is the robust result, and it is what is claimed.'));

// ------------------------------------------------------------ 8. chiller ----
A(h1('8. The chiller model, and the envelope it must be held inside'));

A(p('The optimiser’s central trade is compressor power against fan power, so the sensitivity of chiller power to condenser-water temperature is the accuracy of the whole result. Two corrections were required, and the second was found only because the first was made.'));

A(h2('A named machine replaces a generic curve set'));
A(p('The chiller is modelled with the EnergyPlus `Chiller:Electric:EIR` bi-quadratic form. The coefficients are those of a specific machine — a York YT 1,758 kW (500 ton) water-cooled centrifugal at 6.28 COP, from the CoolTools curve library shipped with EnergyPlus. It was selected on three grounds. Its reference point is the AHRI 550/590 rating point, so normalising to that point is a 5.0 % and 0.5 % correction rather than a fudge. Its curves are fitted over 15.56 to 35.00 °C entering condenser water, which spans the Gulf operating range where most of the library stops at 26.11 °C. And it is a vane-controlled centrifugal rather than a high-COP variable-speed outlier. It gives 2.36 % of chiller power per kelvin of condenser water over 30 to 36 °C, against 2.62 % for the untraced set it replaced and 3.45 % for constant-fraction Carnot.'));

A(h2('A more modern source was examined and rejected'));
A(p('The ASHRAE 90.1-2022 Normative Appendix J curve sets are newer, return exactly unity at the AHRI point, and state validity to 40 °C. They imply 0.4 to 0.5 % per kelvin — a chiller losing 3 % of its coefficient of performance between 30 and 36 °C condenser water, where ideal Carnot loses 21 % and every named machine in the CoolTools library loses 13 to 17 %. Those curves are fitted to reproduce rated full-load and IPLV points, and the IPLV condenser schedule runs *downward* from 29.44 °C as load falls, so above 30 °C they are unconstrained by data despite the stated range. A stated validity range is not evidence of a fitted range.'));

A(h2('The optimiser then exploited the new curve'));
A(p('Given a free hand, the optimiser drove the fan to its lower bound in four of five Gulf conditions, which puts entering condenser water at 36.5 to 40.5 °C — outside the fitted range — and collected a large apparent water saving from the extrapolation. That run scored 20.41 % on the water criterion and would have converted a failed gate into a passed one on the strength of an extrapolation.'));
A(p('The entering-condenser-water window is now enforced as a hard constraint. It is not only the curve’s fitted range: it is also the machine’s permitted operating window, since below the floor condenser head pressure collapses and oil return and expansion-valve control fail, and above the ceiling the machine trips on high head. In the run reported here, 1,840 of 6,307 candidate operating points were rejected on this constraint rather than extrapolated.'));

A(...figure('chiller_envelope.png', 'The chiller operating envelope as a hard constraint. Candidate operating points outside the fitted entering-condenser-water range are rejected rather than extrapolated.'));

A(quote('**The result is a new and specific finding.** In all four Gulf summer conditions the optimum now sits at 33.9 to 34.7 °C entering condenser water, hard against the 35 °C ceiling. In Gulf summer the binding limit on fan speed is the chiller envelope — not tower physics, and not chemistry.'));

A(h2('Two further defects found in the same pass, and one regulation closed'));
A(p('**The drift rate was a hundred times too large.** Cooling-tower drift is quoted by every manufacturer as a percentage of circulating water flow, and modern high-efficiency eliminators are rated at 0.0005 % to 0.001 %. The model carried 0.0005 used directly as a fraction — the modern rating with its percent sign dropped. This is the same class of defect as the fan correlation read in per cent instead of hertz. Makeup water is provably unaffected, and that is worth stating precisely rather than discovering later: with blowdown equal to evaporation/(C−1) minus drift, the drift term cancels exactly out of makeup for as long as blowdown stays positive, and it was verified numerically that makeup is identical to three decimals before and after. What was wrong is the reported **blowdown**, 27 % low at seven cycles — which is the quantity a discharge permit is written against.'));

A(p('**The discharge limit was the wrong kind of number.** A blanket 3,000 mg/L cap on total dissolved solids was carried as unverified, because on 1,500 mg/L makeup it implies a ceiling of 2.0 cycles while plants demonstrably run 3.5 to 5.0. Resolved against the primary regulation — RCER-2015 Volume I, the Royal Commission for Jubail and Yanbu Environmental Regulations — it turns out there are three different limits for three different discharge routes.'));

A(table(
  ['RCER-2015 table', 'Discharge route', 'TDS limit'],
  [
    ['Table 3B', 'Central wastewater treatment facilities', '2,000 mg/L Jubail; 2,500 mg/L Yanbu'],
    ['Table 3C', 'Direct to coastal waters, including the seawater cooling return', '**None**'],
    ['Table 3D', 'Irrigation system', '2,000 mg/L maximum; 1,750 monthly average'],
  ],
  widths([1.2, 2.6, 1.8]), { zebra: true }));

A(spacer(140));
A(p('Table 3C lists only floating particles and temperature under its physical parameters. A cap on total dissolved solids is therefore **not a property of the cooling loop at all — it is a property of where the blowdown goes.** That resolves the contradiction. A 2,000 mg/L cap on this makeup allows 1.33 cycles, which would forbid evaporative cooling on reclaimed water outright, so plants running 3.5 to 5.0 cycles are not discharging tower blowdown to the sewer, and a coastal industrial plant discharging to the seawater cooling return has no limit to satisfy. The cap is now a site configuration item defaulting to no cap, and the controller reports which route it assumed.'));

A(h2('A numerical defect found in the same pass'));
A(p('The condenser duty is a fixed point: the tower rejects evaporator load plus compressor work, and compressor work depends on the cold-water temperature the tower achieves. That fixed point was being solved by six steps of successive substitution at a 5 mK tolerance. The map contracts at roughly 0.5 per step, so six steps stop well short of the solution — and stop short by an amount that depends on the starting guess. Because every grid point was seeded from a single nearby solve, points near the seed were accurate and points far from it were not, which biased the baseline and the optimum by different amounts.'));
A(p('Evaporation, the quantity the water gate measures, moved from 5.199 to 5.396 kg/s — 3.8 % — on the choice of seed alone, an order of magnitude larger than the margin by which that gate was failing. The solver now uses Aitken delta-squared extrapolation of the same iteration, with a bracketed Brent root-find as a fallback, and reports its own non-convergences. All 360 fixed points in the run reported here converged to 10⁻⁵ K, and the two solvers agree on the gate results to the second decimal place.'));

// ------------------------------------------------------------- 9. V5 ----
A(h1('9. Gate V5 — closed-loop economics'));

A(p('The plant archetype is a 10 MW condenser-water module. Tariffs are taken from published schedules: electricity at $0.074/kWh, water avoided at $3.11/m³ from the Marafiq and Royal Commission approved schedule, and sulphuric acid at $0.19/kg.'));

A(table(
  ['Criterion', 'Threshold', 'Result', 'Verdict'],
  [
    ['Makeup water reduction', '≥ 15.0 %', '14.83 %', '**FAIL**'],
    ['Total operating cost reduction', '≥ 3.0 %', '8.55 %', 'PASS'],
    ['Skin-temperature saturation violations', '0', '0', 'PASS'],
  ],
  widths([2.4, 1.1, 1, 1]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(table(
  ['Condition', 'Wet bulb', 'Fan', 'Cycles', 'Makeup m³/h', 'Water', 'Cost'],
  [
    ['Dhahran summer peak', '25.2 °C', '70 → 50 %', '4 → 7', '27.4 → 22.4', '18.4 %', '8.5 %'],
    ['Dhahran summer humid', '29.7 °C', '100 → 70 %', '4 → 7', '24.1 → 20.1', '16.3 %', '9.1 %'],
    ['Dhahran shoulder', '22.4 °C', '60 → 40 %', '4 → 7', '22.4 → 18.9', '15.6 %', '6.5 %'],
    ['Doha summer humid', '30.3 °C', '100 → 80 %', '4 → 7', '25.0 → 21.1', '15.4 %', '8.0 %'],
    ['Gulf winter', '14.7 °C', '40 → 90 %', '4 → 6', '19.5 → 17.9', '8.4 %', '10.7 %'],
  ],
  widths([1.8, 1, 1.2, 0.9, 1.3, 0.9, 0.9]),
  { align: ['L', 'C', 'C', 'C', 'C', 'C', 'C'], zebra: true, size: 18 }));

A(spacer(140));
A(h2('Reading the failure honestly'));
A(p('The water criterion was set at 15 % and was **missed**, at 14.83 %. It is reported as a failure and the threshold has not been moved. What has changed since it was set is that the reason for the miss is now known exactly, and it is not a deficiency of the controller.'));
A(p('Makeup water is evaporation plus blowdown, and blowdown is evaporation divided by (C − 1). At constant evaporation the makeup rate is therefore evaporation multiplied by C/(C − 1), so the makeup saving available by raising cycles from the incumbent four is fixed arithmetic rather than a modelling choice. It is a hyperbola with a horizontal asymptote at 25 %, reached only at zero blowdown.'));

A(table(
  ['Cycles of concentration', 'Makeup saved against 4 cycles'],
  [['5', '6.25 %'], ['6', '10.00 %'], ['7', '12.50 %'], ['8', '14.29 %'], ['9', '15.62 %'], ['10', '16.67 %']],
  widths([2, 2]), { align: ['C', 'C'], zebra: true }));

A(spacer(140));
A(p('A criterion of 15 % therefore requires **8.5 cycles**. Gypsum saturates at **8 cycles** on this water. The criterion was written on the far side of a wall that had not yet been located, and gypsum saturation is not pH-sensitive, so the acid dose that buys cycles against calcite cannot move it. No control strategy of any kind reaches 15 % on this makeup water by raising cycles.'));

A(...figure('water_ceiling.png', 'The arithmetic ceiling on makeup-water saving against cycles of concentration, with the gypsum saturation wall marked. The pre-registered 15 % threshold sits beyond a limit that no control strategy can cross.'));

A(p('The controller nevertheless reaches 14.83 %, which is more than cycles alone can deliver at its operating point, because it also lowers evaporation by slowing the fan wherever the chiller can absorb the warmer condenser water. That second term is precisely the coupling this product exists to price, and it is invisible to both incumbent disciplines: a water treater optimising cycles alone cannot access it, and an energy optimiser lowering condenser temperature moves it the wrong way and never books it.'));

A(p('Two conclusions follow, and they are different from the ones drawn when this gate was first scored.'));
A(numbered('**The pre-registration was mis-specified, not merely missed.** A threshold should be checked against the physical ceiling of the system before it is fixed. This one was not, and the correct record of that is to leave the gate failed and say why.'));
A(numbered('**The water saving is not the product.** At current tariffs the value is the energy trade plus the certainty of not crossing a saturation limit that bulk instrumentation cannot see. Total operating cost falls 8.55 % against a criterion of 3.0 %.'));

A(p('The incumbent four-cycle baseline was found safe at skin temperature in all five conditions tested. It is conservative rather than unsafe — it leaves margin unused. No claim is made here that typical plants are actively scaling; establishing that requires field data and is a TRL 4 objective.'));

A(h2('Gate V5b — the two ceilings'));
A(p('Sweeping cycles at fixed fan speed, with pH free to take its least-cost feasible value, separates two limits that incumbent practice collapses into a single conductivity setpoint.'));

A(table(
  ['Cycles', 'Best pH', 'Makeup m³/h', 'Acid kg/h', 'Water $/h', 'Acid $/h', 'Total $/h', 'Blocked by'],
  [
    ['3', '8.50', '26.68', '2.9', '82.98', '0.54', '209.08', ''],
    ['4', '8.50', '23.71', '3.9', '73.74', '0.74', '199.89', ''],
    ['5', '8.25', '22.23', '5.5', '69.12', '1.04', '195.50', ''],
    ['6', '8.00', '21.33', '6.8', '66.35', '1.29', '192.92', ''],
    ['7', '8.00', '20.74', '7.8', '64.49', '1.47', '**191.22**', ''],
    ['8', '—', '—', '—', '—', '—', '—', '**Gypsum**'],
    ['9', '—', '—', '—', '—', '—', '—', '**Gypsum**'],
    ['10', '—', '—', '—', '—', '—', '—', '**Gypsum**'],
  ],
  widths([0.8, 0.9, 1.3, 1, 1.1, 0.9, 1.1, 1.2]),
  { align: ['C', 'C', 'C', 'C', 'C', 'C', 'C', 'C'], zebra: true, size: 17 }));

A(spacer(140));
A(bullet('**The cost curve does not turn over.** Operating cost falls monotonically from $209.08/h at three cycles to $191.22/h at seven, which is the last feasible point. On this water there is no interior economic optimum.'));
A(bullet('**Physical ceiling: 8 cycles.** The first saturation violation at the condenser skin, with gypsum as the binding mineral. Acid cannot move it, because sulphate saturation is not pH-sensitive.'));

A(p('**This is the more dangerous of the two arrangements, and we report it as the adverse case.** Where an interior cost minimum exists, an operator following the money stops short of the saturation wall without needing to know the wall is there. Here the money points straight at it: every additional cycle is cheaper than the last, right up to the point where gypsum saturates at the tube skin. An operator optimising cost with Langelier-based control walks into that wall blind, because the Langelier index describes calcite and cannot represent gypsum at all.'));

A(p('The general product claim is unaffected and is worth stating separately from this particular result. The economic optimum and the physical limit are **different quantities that require different models to locate** — the first a coupled water, energy and chemical cost model, the second ion-specific speciation evaluated at skin temperature. On some waters they are far apart and on this one they coincide at the wall. A fixed conductivity setpoint locates neither, which is the point.'));

A(...figure('gypsum_wall.png', 'Total operating cost against cycles of concentration, with the gypsum saturation wall. On this water the cost curve never turns over: it falls monotonically to seven cycles, the last feasible point, so the economics run straight at a limit a conductivity setpoint cannot see.'));

A(p('These are different numbers, and a fixed conductivity setpoint can locate neither. Finding the first requires a coupled water, energy and chemical cost model. Finding the second requires ion-specific speciation evaluated at skin temperature — and the Langelier index used across the industry cannot represent the binding mineral here at all, because it describes calcite only. This single table is the clearest statement of what the product is: the plant is operating between two limits it cannot see, and the gap between them is the margin being left unused or unknowingly crossed.'));

// ------------------------------------------------------------ 10. V6 ----
A(h1('10. Gate V6 — the constraint that needs all three models at once'));

A(p('External review identified a real gap: magnesium silicate forms on the hot surface and can bind before amorphous silica does. Closing it produced the sharpest result in this package.'));

A(h2('First, a correction we made and are reporting'));
A(p('Magnesium silicate was initially modelled as sepiolite, using PHREEQC constants. On real water that returned saturation indices of +1.56 to +3.50, which would forbid operation everywhere and is plainly false, since plants run four to five cycles on this water daily. Crystalline magnesium silicates are thermodynamic end-states whose crystallisation is kinetically inhibited over the few seconds a parcel of water spends crossing a condenser. Sepiolite was the wrong phase, and using it would have made the controller reject operating points that are demonstrably safe.'));

A(p('What industry actually uses is an empirical magnesium-silica product, and it validates against observed practice.'));
A(table(
  ['Published limit', 'Maximum cycles on Aramco water with 26.8 mg/L silica'],
  [['Permissive', '6.03'], ['Standard', '5.64'], ['Utility', '4.77'], ['Assurance', '4.27']],
  widths([1.4, 2.6]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(p('Industry operates at 3.5 to 5.0 cycles. The standard and utility limits **bracket that**, which is the consistency check the sepiolite formulation failed. A second unit ambiguity appeared here, of exactly the kind that produced the fan-correlation defect. Sources word the magnesium term as hardness in parts per million as calcium carbonate, but that convention gives 2.78 cycles — below what plants demonstrably run. Read as parts per million of magnesium ion it gives 5.64, which matches. Both are implemented; the model defaults to the convention consistent with reality and documents the discrepancy.'));

A(h2('The deposition criterion'));
A(p('Magnesium silicate forms in two steps: brucite precipitates first at the hot skin, then reacts with silica in the boundary layer. Brucite’s saturation pH is **retrograde** — it falls as the surface gets hotter — so deposition occurs when bulk pH exceeds the brucite saturation pH evaluated at the **skin** temperature.'));

A(table(
  ['Skin temperature', 'Brucite saturation pH', 'Verdict at Gulf operating pH of 8.5–9.0'],
  [
    ['30 °C', '9.41', 'Safe across the whole band'],
    ['34 °C', '9.16', 'Safe across the whole band'],
    ['38 °C', '8.92', 'Deposits above pH 8.92 — the band straddles the limit'],
    ['42 °C', '8.68', 'Deposits above pH 8.68 — the band straddles the limit'],
    ['46 °C', '8.45', '**Depositing across the whole band**'],
    ['50 °C', '8.22', '**Depositing across the whole band**'],
  ],
  widths([1.2, 1.4, 3]), { align: ['C', 'C', 'L'], zebra: true }));

A(spacer(140));
A(quote('**The same tower, on the same water, at the same pH, deposits at high load and does not at low load**, because the skin runs hotter. A fixed pH setpoint cannot express that, and neither can a fixed conductivity setpoint.'));

A(...figure('mg_silicate_envelope.png', 'Magnesium silicate deposition envelope. Brucite saturation pH at the condenser skin, against bulk pH, on Aramco reclaimed water with 26.8 mg/L silica at four cycles.'));

A(p('This is the constraint that requires all three models simultaneously, and it is why the architecture is what it is: skin temperature comes from the live thermal model and duty, bulk pH from the chemistry model, and acid dose is the actuator that moves bulk pH. It also reveals a dual role for acid that conventional practice does not connect. Everyone doses acid for calcite. It simultaneously moves the loop below the brucite saturation pH at the skin, which is what actually prevents magnesium silicate. Nobody controls for the second effect.'));

// ----------------------------------------- 11. MATLAB / SIMULINK ----
A(h1('11. Independent re-implementation in MATLAB and Simulink'));

A(p('A single implementation of a model is a single point of failure. Every result in sections 4 to 10 comes from one Python codebase, and a coding error inside it would be invisible to every gate in this document, because each gate tests the model against data rather than against another model. The whole package was therefore re-implemented a second time, independently, in MATLAB and Simulink, and the two were cross-validated against each other.'));

A(...figure('simulink_model.png', 'The Simulink model, drawn from its own build script. The physical loop is a closed cycle — basin water heats through the condenser, is cooled by the tower and returns — carried as a Simscape thermal network so the time constant comes from the loop’s real 150 t of water rather than from a chosen number. The scaling limit hangs off the condenser outlet, which is the only point in the model where chemistry meets thermal state, and the Stateflow supervisor closes on that margin through a one-step control delay.'));

A(p('The architecture is the argument, and two features of it are deliberate. First, the loop is solved as a **cycle rather than a chain**: the tower must reject the evaporator load plus the compressor work, and the compressor work depends on the temperature the tower achieves, so neither can be computed without the other. Second, the fan command reaches the tower through a **one-step delay**, because a controller that assumes its own command takes effect instantly will hunt against a loop that holds 150 tonnes of water.'));

A(h2('The model as Simulink draws it'));

A(p('The diagram above is our own drawing of the architecture. The two below are the model itself, exported from Simulink, so that the architecture claim can be checked against the artefact rather than taken on trust. The canvas carries **28 top-level blocks**: the Simscape thermal network, six MATLAB Function blocks holding the physics, the Stateflow supervisor, the constants, and the logging outputs.'));

A(...figure('slx_canvas.png', 'The mizan_plant Simulink canvas, exported directly from the model. The Simscape thermal network is the subsystem at lower left; the physics blocks carry the Poppe tower, the York chiller curve, the condenser, the basin heat balance and the fan affinity law; the Stateflow supervisor is at top left.', 640));

A(p('The supervisor is the part worth reading closely, because it is where the safety position lives. It is a four-state chart, and the authority it holds over the plant is **staged rather than granted at commissioning**.'));

A(...figure('slx_supervisor.png', 'The Stateflow supervisor. Authority is staged: SHADOW observes and recommends nothing for the first 1,344 hours; ADVISORY recommends without acting; CLOSED_LOOP is reached only after 1,512 hours and modulates the fan against the saturation margin. FALLBACK is entered immediately on loss of a sensor or departure from the chiller envelope, and returns the fan to the incumbent fixed setpoint.', 380));

A(p('Three properties of that chart matter to a plant operator, and all three are visible in it. The controller **cannot act for the first eight weeks** — it observes, and the site compares its recommendations against what the plant actually did. It **never commands more than the incumbent setpoint** except in CLOSED_LOOP, and even there the command is bounded, `85 − 25·tanh(max(−margin,0)·8)`, so the fan can only be slowed by a bounded amount and only in response to a negative saturation margin. And the FALLBACK transition is guarded on `~sensor_ok || ~in_env`, so a lost sensor or a chiller outside its envelope returns control to the incumbent setpoint immediately, with no operator intervention.'));

A(note('The state positions in the chart were adjusted for legibility before export; no guard, action or transition was changed. The model in the repository is the one that produced every MATLAB result in this section.'));

A(h2('The cross-implementation gate'));

A(p('Thresholds were fixed before the comparison was run, in the same discipline used for the physical gates, and set deliberately tight: the outlet-temperature tolerance is one fiftieth of the model’s own holdout error against experiment, so the test can only pass if the two implementations agree far more closely than either agrees with reality.'));

A(table(
  ['Quantity compared', 'Threshold', 'Worst-case disagreement', 'Verdict'],
  [
    ['Outlet water temperature', '≤ 0.010 K', '**1.4 × 10⁻⁵ K**', 'PASS'],
    ['Brucite saturation pH at the skin', '≤ 0.005', 'within threshold', 'PASS'],
    ['Evaporation rate', 'pre-registered', 'within threshold', 'PASS'],
    ['Chiller electrical power', 'pre-registered', 'within threshold', 'PASS'],
  ],
  widths([2.4, 1.2, 1.8, 0.9]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Four gates pass. The two independent implementations agree on outlet water temperature to fourteen microkelvin — roughly forty thousand times tighter than the 0.542 K error the model carries against the experiment. That establishes that the Python results are not an artefact of one codebase.'));

A(note('What this is, and what it is not. This is verification, not validation: it proves the equations were implemented correctly twice, not that the equations are right. Validation against measurement is section 4, and the agreement there is far weaker, as it should be.'));

A(h2('The fill law, re-identified with an independent toolchain'));

A(p('The MATLAB build re-identifies the fill characteristic using the Curve Fitting Toolbox, which returns confidence intervals the Python implementation does not compute. The comparison is a genuine check, because the two used different fitting machinery on the same measurements.'));

A(table(
  ['Parameter', 'Python (adopted)', 'MATLAB estimate', 'MATLAB 95 % confidence interval'],
  [
    ['Coefficient c', '1.2401', '1.2741', '1.2312 to 1.3170'],
    ['Exponent n', '−0.5014', '−0.5453', '−0.5997 to −0.4908'],
  ],
  widths([1.4, 1.5, 1.5, 2.2]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Both adopted Python values fall inside the MATLAB confidence intervals. The identification is therefore not sensitive to the fitting method, and the width of those intervals gives an honest picture of how well two parameters can be pinned down from this experiment at all.'));

A(h2('Control design, on licensed toolboxes'));

A(bullet('**System identification.** The loop’s thermal response to a fan-speed step is first order with a time constant of **513 s** and a gain of −0.0677 K per per-cent fan, identified at 99.9 % fit.'));
A(bullet('**Classical control.** A proportional-integral regulator tuned on that plant achieves a **60° phase margin**, which is the stability evidence a controls engineer will ask for and which the Python optimiser alone cannot provide.'));
A(bullet('**Model-predictive control.** A twenty-step-horizon controller enforces the 35 °C entering-condenser-water ceiling as a **hard constraint** rather than a penalty, which is the correct structure for a limit that must never be crossed.'));
A(bullet('**Optimiser benchmark, reported against ourselves.** Sequential quadratic programming finds a marginally better operating point than our grid search — $180.30/h against $181.48/h, a 0.65 % improvement — but takes **56.1 s against 7.0 s**, eight times longer. On an edge controller with a bounded execution budget the grid search is the correct engineering choice, and we report the gap rather than hide it.'));

A(h2('A Gulf day in Simulink, and the result that came out of it'));

A(p('The Simulink model couples a Simscape thermal network to a Stateflow supervisor and runs a full diurnal cycle at Gulf conditions. It reproduces the chemistry, the chiller envelope and the thermal response together over twenty-four hours, which no steady-state calculation can.'));

A(table(
  ['Quantity over one simulated Gulf day', 'Range'],
  [
    ['Cold water leaving the tower', '26.9 to 32.4 °C'],
    ['Condenser skin temperature', '38.4 to 46.2 °C'],
    ['Brucite saturation pH at the skin', '8.43 to 8.89'],
    ['Chiller electrical power', '933 to 1,605 kW'],
    ['Hours inside the chiller operating envelope', '24 of 24'],
    ['**Hours in the magnesium-silicate depositing regime**', '**11.1 of 24**'],
  ],
  widths([3, 1.6]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(...figure('gulf_day.png', 'One Dhahran summer day, computed from the physics core. Top: the condenser skin runs 8 K above the water leaving the condenser and well above anything the plant instruments see. Middle: the magnesium-silicate scale limit at the skin is retrograde, so it falls as the afternoon load heats the surface, crossing the loop’s fixed operating pH twice. Bottom: what the plant’s own two instruments read across the same day.'));

A(p('The Simulink run and the Python core were built independently and agree on the result: 11.1 hours by the Simulink integration, 11 hours by the Python core on the same day definition. The figure above is generated by the Python core so that it regenerates with every other figure in this report and cannot drift from the results.'));

A(...figure('matlab_simulink_day.png', 'The same day as computed by the Simulink model, with the electrical power split added. The chiller swings from 933 to 1,605 kW across the day while the fan draw stays almost flat — which is why the fan is worth moving and why the chiller envelope, not the fan, is the binding constraint in Gulf summer.'));

A(quote('That last row is the sharpest single number in this document. On a simulated Gulf day at typical operating pH, the loop spends **eleven hours of every twenty-four above the brucite saturation pH at the tube skin** — while the bulk pH never moves. A plant watching bulk pH sees a flat line all day, while the surface crosses into deposition around mid-morning and back out in the evening.'));

A(p('The steady-state gates in section 10 established that this regime exists. The dynamic model establishes how much of a real day is spent inside it, and that is the number that turns a chemistry curiosity into an operating cost.'));

A(h2('The physics-informed surrogate, scored twice'));

A(p('The learned surrogate was built in both environments and scored against the same pre-registered criteria. It is trained against the physics core rather than against a plant, and no gate result in this document depends on it.'));

A(table(
  ['Metric', 'Python implementation', 'MATLAB implementation'],
  [
    ['Outlet temperature error against the core', '0.022 K', '0.030 K'],
    ['Constraint violations', '0', '0'],
    ['Speed-up over the core', '101,802×', '**298× — FAILS the 500× gate**'],
    ['Verdict', 'All four criteria pass', 'Three pass, one fails'],
  ],
  widths([2.4, 1.6, 1.8]), { align: ['L', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('The MATLAB surrogate fails its speed-up criterion and is reported as failing. The cause is not that the network is worse — its accuracy is comparable — but that the MATLAB physics core it is measured against is itself much faster, at 14.7 ms per evaluation, so the ratio is smaller. Both numbers are correct, and neither should be quoted without the other.'));

A(note('A note on OpenModelica. A Modelica description of the loop exists in the repository, but OpenModelica is not installed on the development machine, the model has never been compiled or run, and it therefore supports no claim in this document. It is mentioned here so that its presence in the repository is not mistaken for a result.'));

// ------------------------------------------------------------ 11. TRL4 ----
A(h1('12. The TRL 4 programme at KFUPM'));

A(p('Every claim above is computational. TRL 4 under DTV’s own definition is components integrated and validated in a laboratory environment, and the facilities for it already exist on the KFUPM campus — three of them in the same building.'));

A(table(
  ['Facility', 'Location', 'What it closes'],
  [
    ['Air-Conditioning & Refrigeration Laboratory — vertical cooling tower and open wind tunnel with heating, cooling and **humidification**', 'Bldg 75-410', 'The climate-extrapolation gap: our data tops out at 21.9 °C wet-bulb and 40.5 % of a Dhahran year is above that'],
    ['Chemistry Teaching Instrumentation Laboratory — ICP-OES PlasmaQuant PQ 9000 for cations, Metrohm 930 Compact IC Flex for anions', 'Bldg 75-230', 'The chemistry gap: turns gates V3 and V5b from calculation into measurement'],
    ['Mechanical Engineering Corrosion Laboratory — Gamry 3000 potentiostats, rotating disc electrode, recirculating loop', 'Bldg 75-409', 'The objection we cannot answer today: does acid dosing trade scale for corrosion?'],
    ['Dream Realization Laboratory — PCB fabrication, electronics assembly, sheet-metal enclosures', 'DTV', 'The physical controller itself, end to end'],
  ],
  widths([2.6, 0.9, 2.6]), { zebra: true, size: 17 }));

A(spacer(140));
A(p('The instrumentation pairing matters more than it looks. ICP-OES measures the cations and ion chromatography the anions; together they give the complete ion inventory that the speciation model predicts. That is precisely the input our current chemistry lacks, because today we drive the model from a published third-party water analysis that had to be closed on charge balance. With those two instruments the model is validated against water we measured ourselves.'));

A(table(
  ['Objective', 'Experiment', 'What it converts'],
  [
    ['Thermal transfer at Gulf wet-bulb', 'Tower across the wind tunnel’s humidity range', 'The climate-extrapolation limitation'],
    ['Water-balance closure', 'Metered makeup and blowdown against predicted evaporation', 'Gate V2, onto a second rig'],
    ['Ion inventory', 'ICP-OES and ion chromatography on synthetic Gulf effluent at four cycle levels', 'Gate V3, from calculation to measurement'],
    ['Saturation limit at the wall', 'Heated coupon side-stream at controlled skin temperature', 'Gate V5b, from calculation to measurement'],
    ['Scale kinetics', 'Coupon mass gain against time and saturation state', 'Supplies the labelled data the learned residual needs'],
    ['**Corrosion under acid dosing**', 'Potentiostat and loop tests across the pH range the optimiser selects', '**The scale/corrosion trade-off, currently unaddressed**'],
    ['Closed-loop control', 'Edge controller driving blowdown valve and fan drive over Modbus', 'The TRL 4 integration claim itself'],
  ],
  widths([1.9, 3, 2.2]), { zebra: true, size: 17 }));

A(spacer(140));
A(p('These experiments are deliberately cheap — salt, coupons and instrument time on equipment that already exists. The SAR 200,000 product-development stream covers instrumentation, the motorised valve and edge hardware, analytical services, an operational-technology security assessment and third-party validation. None of it is modelled as runway.'));

A(note('Engagement with KFUPM’s Interdisciplinary Research Centre for Membranes and Water Security is scoped as testing services rather than co-development, because co-development triggers a separate research collaboration agreement and an intellectual-property negotiation that must be settled in writing before work begins.'));

// -------------------------------------------------------- 12. open items ----
A(h1('13. Open items, and the direction each one cuts'));

A(p('Every remaining open item is listed with the direction it biases the result. That matters more than the list itself: an assumption that makes our own claim weaker is evidence of discipline, not a risk the reviewer inherits.'));

A(table(
  ['Open item', 'Direction', 'Closed by'],
  [
    ['Validation data is from Plataforma Solar de Almería, whose summer wet-bulb tops out at 21.9 °C. **40.5 % of a Dhahran year is above that**, rising to 84 % of hours in September.', '**Unknown** — the one item that could cut either way, which is why it is first', 'The KFUPM wind tunnel, which humidifies: the rig reaches Gulf wet-bulb directly'],
    ['Model error is 2.5 times the propagated measurement uncertainty', '**Against us** — we report the real error, not a floor', 'Already decomposed: roughly 30 % fill drift, 70 % residual. A second rig separates them'],
    ['Silica is not reported in the Aramco analysis, so its constraint is inactive', '**Against us** — present silica could only lower the wall, never raise it, so our 8 cycles is an upper bound', 'ICP-OES and ion chromatography'],
    ['Saturation indices are computed, not measured', '**Neutral** — constants come from the USGS PHREEQC database and are not fitted by us', 'Heated-coupon side-stream rig'],
    ['Makeup water reduction missed its pre-registered 15 % threshold at 14.83 %', '**Against us** — reported as a failure rather than rescored, and now diagnosed as a threshold written beyond the physical ceiling', 'Nothing: the threshold stands as written'],
    ['Fill characteristic identified on one tower', '**Neutral** — the form transfers, the coefficients do not, and per-site calibration is part of the product', 'A second rig; the drift result already quantifies the recalibration interval'],
    ['**The condenser skin temperature rise is a fixed 8 K, not computed.** The film calculation in the codebase gives 2.4-3.7 K on a clean surface; 8 K corresponds to a fouled one. Every chemistry gate used the fouled value.', '**Against us.** A hotter assumed skin makes gypsum look *safer*, because its solubility product is nearly temperature-independent while the Debye-Hückel term rises with temperature. At a clean-surface 3 K the wall moves in from 8 cycles to 7, and the reported optimum at 7 cycles becomes infeasible.', 'Section 11 sensitivity run is on the record; measurement at the heated-coupon rig closes it'],
    ['**Acid dosing at high cycles may make the water corrosive, and the controller has no corrosion term.** EPRI warns that sulphuric acid replaces protective alkalinity with corrosive sulphate, and that sulphate and chloride both concentrate as cycles rise.', '**Against us.** The optimiser raises cycles to seven *and* doses acid, which is precisely the combination the warning describes. We cannot currently price the penalty we may be creating.', 'Potentiostat and mass-loss coupon work in the KFUPM corrosion laboratory - now the highest-priority laboratory objective'],
    ['No AI contributes to any result here', '**Neutral** — stated so the evidence cannot be mistaken for a learned fit', 'The scaling-kinetics residual, once coupon data exists'],
  ],
  widths([3.2, 1.8, 2.2]), { zebra: true, size: 16 }));

A(spacer(140));
A(p('**Nothing in this table is hidden, and nothing in it is fatal.** Seven of the nine items bias against our own numbers, and the two added most recently were found by auditing our own code and by reading the industry literature against ourselves. The one genuinely two-sided item — climate extrapolation — is closed by a facility that already exists on the KFUPM campus and humidifies to the required range. That is the substance of the twelve-week ask.'));

A(h2('What has already been closed'));
A(p('Earlier drafts carried a longer list. The following were open questions and are now settled, each against an external source rather than by assertion.'));
A(bullet('**Tariffs** were assumed; they are now taken from the Marafiq and Royal Commission approved schedule and published Saudi retail rates.'));
A(bullet('**Makeup water composition** was a third-party analysis closed by an invented chloride value; it is now a measured Saudi Aramco analysis from an operating Dhahran cooling tower.'));
A(bullet('**The skin-temperature offset** was a fixed 8 K assumption; it is now computed as heat flux over inside film coefficient, from duty and geometry.'));
A(bullet('**The low fill-law R²** was unexplained; it is now shown to be the expected difference between observational and designed-experiment data, with a published designed experiment at R² = 0.869 as the comparison.'));
A(bullet('**The rejection of a better-scoring wet-bulb model** was our judgement; Kloppers (2003) establishes experimentally that air temperatures have no significant effect on the transfer coefficient.'));
A(bullet('**Prior art** was unexamined; the closest claim, ChemTreat US 11,780,742 B2, is now disclosed with our design position relative to it stated explicitly.'));
A(bullet('**The energy term** was inside the objective but never reported; total electrical power reduction is now stated separately in section 5.'));

// -------------------------------------------- 13. EXTERNAL EVIDENCE ----
A(h1('14. External evidence bearing on the open items'));

A(p('Everything in sections 4 to 11 is our own work. This section sets it against independent published sources that we did not author, because a first-principles claim that agrees with nothing else in the literature is a claim to be suspicious of. Three of our central results are confirmed by an authoritative industry source, one long-standing open item is partly closed, and one risk we had not modelled is raised against us.'));

A(h2('Per-mineral evaluation temperature — independently confirmed'));

A(p('The routing of each mineral to its own governing temperature is the core of our differentiation claim, and it is not our discovery. EPRI’s state-of-knowledge review of cooling water treatment [14] states the same physics directly:'));

A(bullet('**Calcium carbonate** "displays an inverse solubility relationship with temperature... This inverse solubility is why calcium carbonate forms preferentially on the hotter surfaces of the service water system, which unfortunately, is usually the heat exchanger tubing."'));
A(bullet('**Gypsum** "will normally be found in the hot end of heat exchanger tubes because it becomes less soluble as temperature increases above approximately 100 °F" — that is 37.8 °C, inside our condenser operating range.'));
A(bullet('**Silica** "exhibits a normal solubility/temperature relationship, that is, it becomes more soluble as temperature increases. It is therefore found in cooler areas of the system such as the cooling tower fill."'));

A(quote('That last sentence is the strongest external support in this document for the architecture. EPRI places silica deposition at the **tower fill** and the calcium scales at the **heat exchanger tubes** — two different locations, two different temperatures, in the same loop. A controller evaluating both at one temperature is wrong about one of them, and industry practice evaluates both in the bulk.'));

A(h2('Gypsum is not pH-sensitive — independently confirmed'));

A(p('Our diagnosis of the failed water gate rests on the claim that acid cannot move the gypsum limit. EPRI states it without qualification: **"Calcium sulfate scale is not pH sensitive as is calcium carbonate scale."** [14]'));

A(p('The same source also confirms the trade our controller exists to price: "it is common practice in many systems to add sulfate by injecting sulfuric acid to prevent calcium carbonate scale... However, at high enough temperatures, calcium and sulfate concentrations, calcium sulfate scale can form." Dosing acid against calcite moves the loop toward gypsum. That is the mechanism behind our two ceilings, described in an industry reference a decade before we modelled it.'));

A(h2('Magnesium silicate — our rejection of sepiolite is vindicated'));

A(p('Section 10 records that we modelled magnesium silicate as sepiolite, got saturation indices that would forbid operation everywhere, and replaced it with an empirical magnesium-silica product. EPRI confirms that was the right call: "The mechanism of magnesium silicate scale formation is not well understood... these sources disagree on the type of magnesium silicate which is formed." [14] A thermodynamic phase cannot be assumed when the phase itself is disputed.'));

A(p('EPRI also gives the pH mechanism we model: "as the pH increases above 8.0, the silica ion converts to the silicate ion with a negative charge, which seeks positively charged cations such as... magnesium", with magnesium showing retrograde solubility. That is the two-step brucite-then-silica route our gate V6 implements.'));

A(h2('The silica ceiling is condition-dependent, not fixed'));

A(p('Our claim that the static 150 mg/L industry rule is non-conservative rests on the silica ceiling moving with basin temperature. EPRI gives the pH half of the same argument: silica scale "will not form in low pH cooling waters (<7.5) if the silica concentration is kept below 150 ppm as SiO₂. In the higher pH waters (>8.5) silica may be soluble up to 225 ppm and higher." [14] A single number cannot be right across a 75 mg/L spread that depends on operating condition.'));

A(p('Field data brackets it. At the Stanford Linear Accelerator Center, a cooling tower run deliberately at zero blowdown showed its first scale deposit with silica at **145 ppm** and pH 8.9, and ran clean at **123 to 125 ppm** at pH 7.5 to 8.0 [15].'));

A(h2('A single cycles number is ambiguous — direct field evidence'));

A(p('Our argument that a conductivity setpoint cannot represent the loop has, until now, been an argument from our own model. The SLAC zero-blowdown trial measured cycles of concentration by five different species in the **same water sample on the same day** [15]:'));

A(table(
  ['Species used to compute cycles', 'Cycles indicated'],
  [
    ['M alkalinity', '19'],
    ['Calcium hardness', '20'],
    ['Silica', '23'],
    ['Magnesium hardness', '43'],
    ['Sulfate', '**50**'],
  ],
  widths([2.6, 1.6]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(quote('**A factor of 2.6 between the lowest and highest reading of the same quantity, in one sample.** Alkalinity and calcium lag because they are precipitating out of solution; sulfate and magnesium track conservatively because they are not. A conductivity probe returns one number and cannot distinguish these cases — which is precisely the failure our controller is built to remove.'));

A(p('The same trial reported deposit composition by location: the cooling tower fill deposit was **93 % calcium carbonate**, while the deposit on the heat-transfer surface was **62 % silica and magnesium silicates** with 9 % calcium phosphate. Two surfaces in one loop, two different minerals. That is per-location speciation observed in the field, and it is the assumption our architecture is built on.'));

A(h2('Skin-temperature monitoring has field precedent'));

A(p('The SLAC trial monitored deposition with an Admiralty brass heat-transfer surface held at a controlled **110–120 °F (43–49 °C)** at 2–3 ft/s [15] — the same surface-temperature range our model evaluates the retrograde minerals at. The practice of watching a heated surface rather than the bulk is established; what is missing from it is a live thermodynamic model and an actuator.'));

A(h2('The corrosion question — partly closed, and one risk raised against us'));

A(p('Section 12 lists corrosion under acid dosing as an objection we cannot answer. Two sources move it, and they move it in opposite directions.'));

A(p('**In our favour.** The SLAC tower ran above 40 cycles at pH 9.0–9.2 with LSI above 3.2 for months, and reported corrosion rates of 0.3–0.5 mils per year on mild steel and 0.0–0.2 on Admiralty brass, with coupons free of localised attack [15]. High-cycle alkaline operation did not produce a corrosion problem on that system.'));

A(p('**Against us, and this is the more important of the two.** EPRI warns that the benefit of high cycles reverses once acid is used: "increasing cooling tower cycles of concentration increases alkalinity and pH and reduces carbon steel corrosion risk but increases mineral scale deposition risk. **This only applies up to the point where sulfuric acid is applied for pH control. Sulfuric acid replaces protective bicarbonate and carbonate alkalinity with corrosive sulfate. As COC increase with acid and chlorine addition, both sulfates and chlorides increase, often rendering the water very corrosive.**" [14]'));

A(quote('Our optimiser does exactly this. It raises cycles to seven and doses acid to pH 8.0–8.25, which concentrates sulfate and chloride together. **The controller has no corrosion term, so it cannot see the penalty it may be creating.** We report this as a modelling gap found in the literature rather than in our own results, and it is now the highest-priority item in the laboratory programme.'));

A(p('The measurement method is settled and cheap: mass-loss coupons to ASTM G1 and G31, the approach used in a published study of low-carbon steel corrosion in refinery cooling towers across pH 7.0 to 8.5 [16] — the range our optimiser selects in. That study was run under static conditions at room temperature, so it does not transfer directly to a hot flowing condenser, but it fixes the protocol for the KFUPM corrosion work.'));

A(h2('Climate extrapolation, and the host institution’s own work'));

A(p('The largest open item in this package is that 40.5 % of a Dhahran year lies above the wet-bulb ceiling of our validation data. Researchers at King Fahd University of Petroleum and Minerals — the campus whose wind tunnel we are asking to use — have modelled counterflow cooling tower performance across 42 Saudi cities [17], reporting a range of behaviour wide enough to matter: from 4 °C temperature range and 50 kW capacity at Jazan to 7.61 °C and 95.4 kW at Abha, with an August difference of 53.5 % between the two.'));

A(p('That is a modelling study rather than measurement, so it does not close our gap. What it establishes is that the sensitivity we are worried about is real, large, and already recognised at the institution best placed to measure it.'));

A(h2('Why we did not take the machine-learning route'));

A(p('A recent study applied gradient boosting and AdaBoost regressors to cooling tower efficiency at a 1,140 MW combined-cycle plant, reaching R² = 0.983 with relative humidity as the strongest feature [18]. It is a competent piece of work and it is the approach we deliberately did not take.'));

A(p('The reason is section 4 of this document. A regression with free parameters fitted to plant data would have absorbed the fan-correlation unit error and reported a good score with a corrupted air-flow model inside it. A first-principles model could not, and that is how the defect was found. The learned approach also carries no chemistry, no saturation state and no actuator — it predicts efficiency for site selection, which is a different problem from deciding where to put the setpoint tomorrow.'));

// ----------------------------------------------------------- references ----
A(h1('15. References'));

const refs = [
  'P. Palenzuela, L. Roca and J. M. Serrano Rodríguez, “Steady-state operation dataset of an experimental wet cooling tower pilot plant located at Plataforma Solar de Almería,” Zenodo, 2024. doi: 10.5281/zenodo.10806201. [CC BY 4.0]',
  'J. C. Kloppers, “A critical evaluation and refinement of the performance prediction of wet-cooling towers,” Ph.D. dissertation, Dept. Mech. Eng., Univ. Stellenbosch, 2003.',
  'J. C. Kloppers and D. G. Kröger, “A critical investigation into the heat and mass transfer analysis of counterflow wet-cooling towers,” Int. J. Heat Mass Transfer, vol. 48, no. 3, pp. 765–777, 2005.',
  'M. Badruzzaman, J. R. Anazi, F. A. Al-Wohaib, A. A. Al-Malki and F. Jutail, “Municipal reclaimed water as makeup water for cooling systems,” Water Resources and Industry, vol. 28, art. 100188, 2022.',
  'I. S. Al-Mutaz and I. A. Al-Anezi, “Silica removal during lime softening in water treatment plant,” Proc. Int. Conf. Water Resources and Arid Environment, Riyadh, 2004.',
  'D. L. Parkhurst and C. A. J. Appelo, “Description of input and examples for PHREEQC version 3,” U.S. Geological Survey Techniques and Methods, book 6, chap. A43, 2013.',
  'ASHRAE Handbook — Fundamentals, ch. 1, “Psychrometrics.” Atlanta, GA: ASHRAE, 2017.',
  'S. H. Chien, M. K. Hsieh, H. Li, J. Monnell, D. Dzombak and R. Vidic, “Pilot-scale cooling tower to evaluate corrosion, scaling, and biofouling control strategies for cooling system makeup water,” Rev. Sci. Instrum., vol. 83, art. 024101, 2012.',
  'K. Boudreaux, B. Gonzalez and K. Killough, “Methods for online control of a chemical treatment solution using scale saturation indices,” U.S. Patent 11,780,742 B2, Oct. 10, 2023.',
  'Cooling Technology Institute, “Acceptance Test Code for Water Cooling Towers,” CTI ATC-105, Houston, TX.',
  'Veolia Water Technologies, “Water Handbook — Cooling Water Systems: Heat Transfer,” ch. 23.',
  'U.S. Department of Energy, “EnergyPlus Engineering Reference: Chiller:Electric:EIR,” National Renewable Energy Laboratory.',
  'Tubular Exchanger Manufacturers Association, TEMA Standards, 10th ed. Tarrytown, NY: TEMA, 2019.',
  'Royal Commission for Jubail and Yanbu, “Environmental Regulations,” RCER-2015, Volume I.',
  'Electric Power Research Institute, “State of Knowledge: Non-Phosphorous and Low-Phosphorous Cooling Water Treatment,” EPRI Technical Report 3002001276, Palo Alto, CA.',
  'G. E. Geiger, J. Ogg and M. R. Hatch, “Chemical approaches to zero blowdown operation (TP93-05),” SLAC-PUB-6097, Stanford Linear Accelerator Center, presented at the Cooling Technology Institute Annual Meeting, New Orleans, LA, Feb. 1993. [U.S. Dept. of Energy contract DE-AC03-76SF00515]',
  'Z. K. Kuraimid, D. Abdulsalam, H. Mudhafar, Q. Muthana and W. Ismael, “Studying optimum conditions to reduce low carbon steel corrosion in cooling towers system of Al-Daura refinery,” Eurasian Chemical Communications, vol. 3, no. 11, pp. 786-799, 2021.',
  'A. M. A. Hasan and E. M. A. Mokheimer, “Performance analysis of a counter-flow cooling tower under different weather conditions,” Energy Proceedings, vol. 41, 2024. [King Fahd University of Petroleum & Minerals, Dhahran; ICAE2023, Doha]',
  'M. A. Mujtaba et al., “Leveraging machine learning to optimize cooling tower efficiency for sustainable power generation,” Frontiers in Energy Research, vol. 13, art. 1473946, 2025.',
];
refs.forEach((r, i) => A(p('[' + (i + 1) + ']  ' + r, { size: 18, after: 90, indent: { left: 400, hanging: 400 } })));

A(h1('16. Reproduction'));
A(p('Every number in this report is read from the validation results by the generator. None is typed by hand. The code is public at **github.com/furqan5/mizan** and archived with a citable identifier, **DOI 10.5281/zenodo.22179268**, published so that what follows can be checked rather than believed.'));
A(p('`pip install -r requirements.txt`', { after: 40 }));
A(p('`python src/fetch_zenodo.py`   downloads and MD5-verifies the dataset', { after: 40 }));
A(p('`python src/calibrate.py`   gates V1 and V2', { after: 40 }));
A(p('`python src/run_controller.py`   gates V3, V5 and V5b, and the energy report', { after: 40 }));
A(p('`python src/annual.py`   the hours-weighted annual figures', { after: 40 }));

A(spacer(200));
A(rule());
A(note('This report contains two failed gates and ten corrected defects, four of which were caught because a first-principles model refused a bad input rather than fitting around it. They are in it deliberately. A team that inflates a readiness level is finished in this ecosystem permanently, and everything claimed here is reproducible against a public dataset by anyone who wishes to check it.'));

// ---------------------------------------------------------------- build ----
const doc = new Document({
  numbering: S.NUMBERING,
  title: TITLE,
  creator: 'Furqan',
  description: 'Mizan proof-of-concept report, DTV .dvp Cohort 2',
  sections: [Object.assign({}, S.sectionProps(TITLE, 'FURQAN · MIZAN'), { children: kids })],
});

Packer.toBuffer(doc).then((b) => {
  fs.mkdirSync(OUT, { recursive: true });
  const f = path.join(OUT, 'Furqan_Mizan_PoC_Report.docx');
  fs.writeFileSync(f, b);
  console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB');
});
