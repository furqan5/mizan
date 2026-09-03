// DTV .dvp Cohort 2 — application answer document.
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const S = require('./style.js');
const { p, h1, h2, h3, quote, bullet, numbered, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');
const TITLE = 'Application Answers — Furqan / Mizan';

const kids = [];
const A = (...x) => kids.push(...x);

// ---------------------------------------------------------------- cover ----
A(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Application Answers',
  subtitle: 'Mizan — an energy–water supervisory controller for condenser-water loops',
}));

A(table(null, [
  ['Venture', 'Furqan (parent) · Mizan (first product)'],
  ['Primary focus area', 'Energy, with a genuine secondary fit to Water & Sustainability'],
  ['Maturity claimed', 'TRL 3 — analytical and computational studies validated against measured experimental data'],
  ['Evidence', 'Five pre-registered validation gates. Four pass, two fail, and both failures are reported as failures'],
  ['Traction', 'None at the date of submission. No letters of intent, no pilots, no completed customer interviews'],
  ['Date', '30 August 2026'],
], widths([1, 3]), { boldRows: [] }));

A(spacer(200));
A(note('This document holds the venture’s answer to every question the application form asks, in the wording we intend to submit. Passages set against a coloured rule are written to be pasted into a form field as they stand. Everything else is context for the person filling in the form.'));

// ============================================================ SECTION 0 ====
// The form's own fields, written to its stated limits and ready to paste.
A(h1('0. The form fields, ready to paste'));

A(note('The form shows a 0/300 counter on five fields and does not say whether it counts words or characters. The guidance under those fields — spell out acronyms, include benchmarking metrics, outline limitations — cannot be satisfied in 300 characters, so these are written to 300 WORDS. A compressed version under 300 CHARACTERS is given beneath each one, so that whichever the counter means, there is an answer that fits. Sections 1 to 11 that follow are the fuller versions, for the interview rather than the form.'));

A(h2('Executive Summary'));
A(note('Form guidance: assume the reviewer has no technical background; simple, clear language; spell out acronyms on first use.'));

A(quote('Large buildings and industrial plants in Saudi Arabia are cooled by machines called chillers. Every chiller must throw away the heat it removes, and does so through a cooling tower, which works by evaporating water. That loop is the biggest single consumer of both electricity and water in a district cooling plant.'));
A(quote('Today three separate parties control that loop and none talks to the others. The building management system sets the tower fan speed. The water-treatment contractor sets how much water is drained and replaced, and how much acid is added. Each follows a fixed target set once, often years ago, and never revisited.'));
A(quote('Those decisions are not independent. Draining less water saves water, but concentrates the dissolved minerals left behind, and those can form a hard crust — scale — on the metal inside the chiller. Scale acts like insulation: once it forms, the chiller burns more electricity for the rest of its life. Running the fan harder saves electricity but evaporates more water.'));
A(quote('Mizan is a retrofit controller — sensors, a motorised valve and a computer — that makes those three decisions together, every few minutes, instead of separately and never. It works because a physics model calculates where scale actually forms: on the hottest metal inside the chiller, not in the bulk water where the plant’s sensors sit. That surface runs several degrees hotter, and nothing on a normal plant measures it.'));
A(quote('Tested against published laboratory measurements it had never seen, the model predicts water temperature to within 0.54 degrees Celsius. Across a full year of real Dhahran weather it cuts make-up water by 11.5 per cent and running cost by 8.3 per cent.'));

A(p('**Under 300 characters, if the counter means characters:**', { after: 60 }));
A(quote('A retrofit controller for the cooling towers that reject heat from building and industrial chillers. It sets fan speed, water bleed and acid dose together, using a physics model of where scale forms on hot metal. Cuts water 11.5 % and running cost 8.3 % across a Dhahran year.'));

A(h2('Problem Statement'));
A(note('Form guidance: the specific problem or need; the current market landscape and the limitations of existing solutions.'));

A(quote('A cooling-tower loop is governed by two limits, and a Gulf plant can see neither of them.'));
A(quote('The first is economic. Concentrating the water saves make-up water and discharge, so the cheapest place to run is as concentrated as possible. The second is physical: past a certain concentration, minerals crystallise onto the hottest metal in the chiller and permanently degrade it. On the treated sewage effluent that Saudi and Qatari plants increasingly run on, our model puts operating cost falling continuously right up to the point where the mineral gypsum saturates. The money points straight at the wall.'));
A(quote('The instruments installed today cannot locate either limit. Plants control on electrical conductivity, a single number that measures how much dissolved material is present but not which minerals, and they measure it in the bulk water rather than at the hot surface where crystals actually form. The industry standard index for scaling risk, the Langelier Saturation Index, describes calcium carbonate only — and on this water the mineral that saturates first is gypsum, which that index cannot represent at all.'));
A(quote('So operators are forced to guess conservatively. They run at roughly four concentration cycles when the physics allows more, wasting water, or they over-dose chemicals to buy a margin they cannot measure. Neither choice is visible to them as a choice.'));
A(quote('Existing products do not close this gap. Water-chemistry software predicts scaling offline, at design conditions, and controls nothing. Building management systems optimise fan energy with no knowledge of chemistry. Chemical suppliers sell dosing programmes whose revenue depends on chemical volume. Nobody sells a controller that prices energy and water against each other in real time, because doing so requires the thermal model and the chemistry model to be one problem rather than two.'));

A(p('**Under 300 characters:**', { after: 60 }));
A(quote('Cooling loops run between an economic limit and a scaling limit, and plant instruments locate neither: conductivity ignores which minerals are present, and is read in bulk water rather than at the hot surface where scale forms. So operators guess, and waste water or chemicals.'));

A(h2('Proposed Solution, competitive advantage, and why it is hard to replicate'));
A(note('Form guidance: unique features and benefits against competitors; quantitative or qualitative benchmarking; performance, scalability and cost advantages; known limitations.'));

A(quote('A retrofit edge controller: a sensor skid, a motorised blowdown valve and an edge computer running a validated physics model over the building-automation protocols already on site. It ships read-only — recommending, not acting — until the site has checked it against its own data.'));
A(quote('The technical difference: each scale-forming mineral is evaluated where it is least soluble, not all at one temperature. Calcium carbonate, gypsum and magnesium silicate grow less soluble as they heat, so they govern at the hot chiller tube wall. Amorphous silica is the opposite, so it governs at the cold tower basin. One evaluation point is wrong for one group or the other.'));
A(quote('Benchmarked against the alternatives: water-chemistry packages such as French Creek WaterCycle run full mineral speciation, but offline, at bulk temperature, and actuate nothing. ChemTreat holds a granted United States patent on surface-temperature dosing, but uses calcium-carbonate indices and drives chemical feed only. Three independent searches found no product or patent where a chemical saturation limit bounds a thermal optimiser in closed loop.'));
A(quote('Performance on a ten-megawatt module across a Dhahran year: 11.5 per cent less make-up water, 8.3 per cent lower operating cost, 6.7 per cent less electrical power. About fifty thousand US dollars first-year cost per loop, against a modelled saving near four hundred and seventy thousand a year at thirty megawatts. It scales linearly and the same hardware fits any evaporative loop.'));
A(quote('Known limitations, stated plainly. Everything is modelled: no field data, no installed base. Two of six pre-registered criteria failed and are reported as failures. Forty per cent of a Dhahran year is hotter and more humid than the validation data. There is no corrosion model yet, which matters because the controller selects acid dose. Seawater-cooled plants are outside the market, because there water is effectively free.'));

A(p('**Under 300 characters:**', { after: 60 }));
A(quote('An edge controller that evaluates each scaling mineral where it is least soluble — hot tube wall or cold basin — and closes fan speed, bleed and acid dose on the result. No competitor actuates on a saturation limit. 11.5 % water, 8.3 % cost. All modelled; no field data yet.'));

A(h2('Does your venture have any of the following?'));

A(table(
  ['Item', 'Answer'],
  [
    ['Granted patents', 'None'],
    ['Patent applications filed or pending', 'None'],
    ['Peer-reviewed publications', 'None'],
    ['Archived, citable software publication', '**Yes** — DOI 10.5281/zenodo.22179268, the v1.0.0 release of the physics core and its evidence'],
    ['Prior-art search conducted and disclosed', '**Yes** — see the attached Intellectual Property and Prior Art document'],
    ['Working prototype', 'Software prototype, reproducible from a public dataset. No hardware built yet'],
    ['Trade secrets and proprietary know-how', '**Yes** — the calibration library and the per-mineral evaluation scheme'],
    ['Third-party or institution-owned IP embedded in the venture', '**None.** See the declaration below'],
  ],
  widths([2.2, 3.4]), { zebra: true }));

A(spacer(140));
A(p('**Intellectual-property ownership declaration.** All model code is original and owned outright by the founders. The psychrometric library, the Poppe heat-and-mass-transfer integrator, the ion-association speciation engine, the supervisory optimiser and the physics-informed surrogate were each implemented from published formulations rather than copied from any repository. No employer, university or third party holds a claim over any of it, and none of it was developed under a funded research agreement.'));
A(p('Third-party material is limited to reference data used under licence, and it is separated here explicitly. The validation dataset is Zenodo record 10806201, used under CC BY 4.0 and attributed. The thermodynamic equilibrium constants come from the United States Geological Survey PHREEQC database, which is public-domain government reference data. The chiller performance curves come from the EnergyPlus CoolTools library published by the United States Department of Energy. None of these is a component we claim to own — each is an input, cited in the report, and any of them could be substituted.'));

A(h2('Current Proof of Concept and validation results'));
A(note('Form guidance: describe the proof of concept and validation results, and upload the report with any related evidence.'));

A(quote('The proof of concept is a complete physics model of a cooling-tower and chiller loop, validated against published experimental measurements and reproducible by anyone in four commands. The code is public at github.com/furqan5/mizan and archived at DOI 10.5281/zenodo.22179268'));
A(quote('The evidence base is a public dataset of 165 measured operating points from an experimental cooling-tower plant in Spain, recorded across three test campaigns between 2019 and 2023. We tuned the model on one campaign only and tested it on the other two — run in different seasons under different experimental designs — which is a harder test than splitting one dataset at random. Six acceptance criteria were fixed and written down before the model was tuned, and the test was scored once.'));
A(quote('Four criteria passed and two failed. Water temperature leaving the tower was predicted to 0.54 degrees Celsius against a one-degree threshold. Heat rejection was predicted to 5.94 per cent against a six per cent threshold. Operating cost reduction reached 8.55 per cent against a three per cent threshold, with zero scaling-limit violations. Water consumption missed at 9.90 per cent against eight, and make-up water reduction missed at 14.83 per cent against fifteen.'));
A(quote('Both failures are reported as failures and neither threshold has been moved. The water-consumption miss was traced to a constant in our own code that was a hundred times too large; correcting it withdrew an earlier result that had passed. The make-up water miss was arithmetic: fifteen per cent needs 8.5 concentration cycles and gypsum saturates at eight, so the target was written beyond a physical wall we had not yet found.'));
A(quote('The model was then independently re-implemented in MATLAB and Simulink. The two agree on water temperature to fourteen microkelvin, which shows the equations were transcribed correctly. Ten defects found during development are documented in an attached register.'));

A(p('**Under 300 characters:**', { after: 60 }));
A(quote('A physics model validated on 165 published measurements: tuned on one test campaign, scored once on two others. Six criteria fixed in advance — four passed, two failed and are reported as failures. Water temperature predicted to 0.54 °C. Reproducible in four commands.'));

A(h2('What to upload against each slot'));
A(table(
  ['Form slot', 'Upload'],
  [
    ['Patents or relevant publications', 'Furqan_Mizan_IP_and_Prior_Art.pdf — we hold no patents; this is the searched prior-art position and the ownership declaration'],
    ['Proof-of-Concept report and related materials', 'Furqan_Mizan_PoC_Report.pdf as the primary document, with Furqan_Mizan_Defect_Register.pdf as supporting evidence'],
  ],
  widths([1.8, 4]), { zebra: true }));

A(spacer(200));

// ------------------------------------------------- 1. technology & TRL ----
A(h1('1. Technology, category and technology-readiness level'));

A(h2('Focus area'));
A(p('Energy is the primary focus area, with a genuine secondary fit to Water & Sustainability. If the form permits only one selection, we choose Energy deliberately: the validated result is dominated by the energy trade, and the water result is the one that missed its threshold. Leading with Water would put our weakest number in front of the reviewer.'));

A(h2('The technology in one sentence'));
A(quote('A retrofit edge controller that co-optimises cooling-tower fan speed, blowdown and acid dose against ion-specific mineral saturation evaluated at condenser tube skin temperature, rather than against a fixed conductivity setpoint measured in the bulk water.'));

A(h2('Technology-readiness level: TRL 3'));
A(p('DTV’s own readiness guide defines TRL 3 for software as *limited functionality to validate critical properties and predictions using non-integrated software components*, with the exit criterion *documented analytical or experimental results validating predictions of key parameters*. The evidence package meets that definition as written.'));
A(p('A first-principles Poppe heat-and-mass-transfer model, coupled to a hydrochemistry engine built on the USGS PHREEQC thermodynamic database, predicts measured outlet water temperature to **0.542 K** mean absolute error and measured heat rejection to **5.94 %** mean absolute percentage error, on fifty experimental points drawn from campaigns the model was never fitted to. Thresholds were fixed and printed before the fit was run, and the holdout was scored once.'));

A(spacer(60));
A(table(
  ['Gate', 'Quantity', 'Threshold', 'Result', 'Verdict'],
  [
    ['V1', 'Outlet water temperature, MAE', '≤ 1.00 K', '0.542 K', 'Pass'],
    ['V1', 'Heat rejection, MAPE', '≤ 6.00 %', '5.94 %', 'Pass'],
    ['V2', 'Water consumption, MAPE', '≤ 8.00 %', '9.90 %', '**Fail**'],
    ['V5', 'Total operating cost reduction', '≥ 3.0 %', '8.55 %', 'Pass'],
    ['V5', 'Makeup water reduction', '≥ 15.0 %', '14.83 %', '**Fail**'],
    ['V5', 'Saturation violations at the tube skin', '0', '0', 'Pass'],
  ],
  widths([0.7, 4, 1.6, 1.4, 1.2]),
  { align: ['C', 'L', 'C', 'C', 'C'], zebra: true }));

A(spacer(120));
A(p('Alongside the gates we report one figure that is **not** a gate. Mean total electrical power reduction across the five conditions is **4.91 %**, reaching **12.09 %** in the winter condition. Electrical power was always the first term of the controller’s objective function — it is the only reason fan speed is an actuator at all — but until now it was monetised into the cost figure and never reported on its own. It is surfaced here because an energy venture should show an energy number. It is explicitly not pre-registered: the threshold would have been chosen after the answer was known, and that is not a test.'));

A(p('Reporting that term separately produced a finding worth putting in front of a reviewer. Across a real Dhahran year the energy saving and the water saving are **anti-correlated**, at r = −0.66. In the cool half the controller returns 10.4 % on electricity and 7.3 % on water; in the hot half it returns 3.0 % on electricity and 15.7 % on water. The total cost saving nonetheless stays between 5.6 % and 10.9 % in every hour-bin of the year, because the two mechanisms hand off to each other. A water-treatment controller collects almost nothing across the cool half; an energy optimiser collects almost nothing across the hot half. That is the clearest statement of why the two models have to be coupled.'));

A(h2('Why not TRL 4 — and what we do meet'));
A(p('Assessed against the programme’s **software** readiness track rather than the hardware one, we already satisfy three of the four TRL 4 criteria. Key components are integrated. Interoperability is validated: the MATLAB and Python implementations agree on outlet water temperature to **1.4 × 10⁻⁵ K** across four pre-registered checks. The relevant environment is defined, as eight equal-hour wet-bulb bins of a Dhahran TMYx year, with performance predicted in it.'));
A(p('We do not claim TRL 4, and the reason is specific: performance in the relevant environment is **predicted rather than tested**. Two implementations of the same equations agreeing to fourteen microkelvin proves the port was correct, not that the physics is right in Gulf summer — and 40.5 % of a Dhahran year lies outside the wet-bulb envelope our validation data covers. We would also be claiming the software track while arguing commercially that this is equipment rather than software, and that inconsistency is not worth a readiness level.'));
A(p('On the hardware track the answer is simpler: nothing has yet been integrated or validated in a laboratory environment. That is precisely what the twelve-week programme is for, and section 9 of the Proof-of-Concept report specifies the experiments, on equipment that already exists on the KFUPM campus: a vertical cooling tower and a humidifying wind tunnel in the Air-Conditioning and Refrigeration Laboratory, ICP-OES and ion chromatography in the Chemistry Teaching Instrumentation Laboratory, and potentiostats in the Mechanical Engineering Corrosion Laboratory.'));

// ---------------------------------------------------------- 2. problem ----
A(h1('2. The problem'));

A(quote('A Gulf condenser-water loop is run by three parties setting three handles independently. The building management system sets fan speed against a fixed condenser-water setpoint. The water-treatment contractor sets blowdown against a fixed conductivity setpoint, and acid dose against a fixed pH setpoint.'));
A(quote('These are not independent variables. Concentrating the loop to save water raises scaling risk and changes evaporation. Cooling the condenser to save compressor power costs fan power and evaporates more water. Nobody solves them together, because doing so requires the thermal model and the water-chemistry model to be one problem rather than two.'));
A(quote('The consequence is measurable. The plant operates against two limits it cannot see. On the Saudi treated-effluent water we modelled, operating cost falls monotonically all the way to seven cycles of concentration, and gypsum saturates at the condenser tube skin at eight. There is no interior economic optimum to stop at: every additional cycle is cheaper than the last, right up to a wall the plant has no instrument to detect.'));

A(p('That is the adverse arrangement, and it is worth being precise about why. Where a cost curve does turn over, an operator following the money stops short of the saturation wall without needing to know the wall is there. Here the money points straight at it. And the Langelier index the industry controls on describes calcite only — it cannot represent gypsum at all, so the instrument that would warn them is measuring the wrong mineral.'));

// --------------------------------------------------------- 3. solution ----
A(h1('3. The solution'));

A(quote('A retrofit edge controller. A sensor skid measuring conductivity, pH, ORP, temperature, makeup flow and blowdown flow; a motorised blowdown valve; and edge compute running a validated physics core, speaking BACnet and Modbus to the equipment already on site. It ships read-only in shadow mode, and blowdown and dosing stay advisory until the site has validated the recommendations on its own data. That is a safety position first and a commercial one second, and it is also the shortest route through an operational-technology security review.'));

A(p('It matters that this is equipment rather than software, and the reason is physical. The saturation limit cannot be computed from the instruments a plant already has: bulk conductivity does not determine ion composition, and nothing installed on a conventional loop reads the tube skin temperature at which scale actually forms. The hardware is not packaging wrapped around an algorithm — it is what makes the calculation possible at all.'));

A(h2('What the controller actually does differently'));
A(p('Every mineral is evaluated at the temperature where it is least soluble, rather than all of them at one temperature. Calcite, gypsum and magnesium silicate are retrograde and govern at the hot condenser skin. Amorphous silica is prograde — more soluble hot — and governs at the cold tower basin. A single evaluation point is wrong for one group or the other, and it is wrong in the optimistic direction for silica, the one species with no effective inhibitor in general service.'));

// --------------------------------------------- 4. competitive advantage ----
A(h1('4. Competitive advantage'));

A(p('We ran a prior-art and competitor sweep before making any novelty claim, and it established that three of the ingredients are already taken. We state that plainly, because a reviewer who finds these patents after we have claimed novelty is a reviewer we have lost.'));

A(spacer(60));
A(table(
  ['Element', 'Status in the prior art'],
  [
    ['Ion-association and Pitzer speciation', 'Not novel. French Creek Software has shipped WaterCycle since 1990 and OLI Systems runs full ionic speciation. The technique has been in use by the water-treatment majors since the 1970s.'],
    ['Skin-temperature saturation', 'Not novel. ChemTreat holds granted US 11,780,742 B2 (October 2023), claiming skin temperature driving chemical dosage.'],
    ['Blowdown control against a saturation index', 'Public domain. US 4,460,008 and US 4,464,315, both 1984 and both long expired.'],
  ],
  widths([1.1, 3]), { zebra: true }));

A(spacer(140));
A(h2('What is open, stated precisely'));
A(quote('Routing each mineral to its own governing temperature, computed live, and closing three actuators on the result.'));

A(p('Three things make that a specific claim rather than a repackaging of the art above.'));

A(numbered('**Per-mineral evaluation temperature.** French Creek works from bulk temperature profiles — a full-text search of its manual returns no occurrence of “skin” or “surface temperature” — and advises checking the lowest and highest anticipated temperatures as a design exercise. ChemTreat evaluates at the skin, but with Langelier-family indices, which describe calcite and cannot represent gypsum at all.'));
A(numbered('**The ceiling is dynamic, and the industry treats it as static.** Commercial practice sets a fixed silica limit, typically “do not exceed 150 mg/L”, regardless of basin temperature. Because silica is prograde and the basin tracks ambient wet-bulb, the true ceiling moves from 95 mg/L at a 15 °C winter basin to 143 mg/L at 35 °C. The static rule is non-conservative at every basin temperature in the Gulf range, and by 37 % in winter. An offline design tool evaluated at design conditions cannot produce a moving setpoint. This is a static-versus-dynamic distinction, not a software-versus-hardware one.'));
A(numbered('**Actuation.** Speciation packages predict; they do not close a loop. We found no incumbent and no startup actuating fan speed, blowdown and acid dose together against a saturation objective.'));

A(h2('The sharpest single demonstration'));
A(p('Magnesium silicate deposits when bulk pH exceeds the brucite saturation pH *at the condenser skin*, and that saturation pH is retrograde — it falls as the surface heats. On Gulf treated sewage effluent running at pH 8.5 to 9.0, a skin below 34 °C is safe across the whole operating band and a skin above 46 °C is depositing across the whole of it.'));
A(quote('The same tower, on the same water, at the same pH, deposits at high load and does not at low load.'));
A(p('A fixed pH setpoint cannot express that. Neither can a fixed conductivity setpoint. Detecting it requires a live thermal model, a chemistry model and an acid actuator operating as one system. Three independent literature sweeps returned the same answer: no academic paper, patent or commercial product describes a closed-loop scheme in which a chemical saturation limit bounds or dynamically alters a mechanical thermal-energy optimiser. That negative result is the differentiation.'));

A(h2('The replication test'));
A(p('A competent generalist team reproduces the tower model in weeks. What it does not reproduce is knowing that the published fan correlation is in hertz and not per cent, that gypsum binds before calcite on Gulf treated sewage effluent, or that the water saving has to be discounted for the evaporation the energy optimum adds back. Each of those came out of the physics, and each one changed the result.'));

// -------------------------------------------------------------- 5. IP ----
A(h1('5. Intellectual-property status'));

A(quote('No patents have been filed and none are pending. The physics core and its evidence are archived as a citable software publication, DOI 10.5281/zenodo.22179268. All third-party components are used under licence and attributed: the validation dataset is CC BY 4.0 (Zenodo record 10806201) and the equilibrium constants come from the USGS PHREEQC phreeqc.dat database. All model code is original — the psychrometric library, the Poppe integrator and the speciation engine were implemented from published formulations rather than copied from any repository.'));

A(p('A prior-art search has been conducted, and we disclose it rather than omit it. The closest art is ChemTreat **US 11,780,742 B2**, granted 10 October 2023, which claims determining heat-exchanger skin temperature and using a scale saturation parameter to set chemical treatment dosage. Also relevant are Ecolab **US 11,668,535 B2**, which runs from heat-exchanger efficiency to a fouling classification to a chemical dose, and the expired **US 4,460,008** and **US 4,464,315**, which set blowdown trip points from the Langelier index.'));

A(h2('Our position relative to that art'));
A(p('The position is architectural and deliberate rather than accidental. Claim 1 of US 11,780,742 requires, as its final elements, determining a dosage of a chemical treatment solution and controlling its application. Mizan’s saturation objective drives **blowdown rate and cooling-tower fan speed** — actuators the claim does not recite. Acid is dosed to a conventional pH setpoint, not to a dose computed from a skin-temperature saturation parameter.'));

A(h2('Jurisdiction'));
A(p('The published family for that patent comprises the US grant and the PCT publication. No Saudi, Qatari or other GCC national-phase member is visible on the public record, and the GCC is not a PCT contracting state, so Gulf coverage would require separate national filings. A US patent has no effect in our beachhead markets.'));

A(p('No freedom-to-operate opinion has been commissioned and none is claimed. One will be obtained before any patent filing, and before first commercial sale in a jurisdiction where relevant art is in force. That work fits DTV’s product-development stream, which covers third-party subject-matter experts, and it is budgeted there rather than against founder cash.'));

A(note('This is our own reading of a public claim and is not legal advice. It is presented as such. DTV states that startups retain their intellectual property and that standard programme support creates no claim over it, so the risk in this section is overclaiming, not underclaiming.'));

// --------------------------------------------------- 6. proof of concept ----
A(h1('6. Proof of concept'));

A(quote('Complete, and reproducible in four commands against a public dataset. Five validation gates, with thresholds fixed and printed before fitting, scored once on a campaign-wise holdout. Four criteria pass and two fail; both failures are reported as failures, and a unit defect found in our own first run is documented in the report rather than quietly corrected.'));

A(p('The evidence base is a published dataset of steady-state operation from an experimental wet cooling-tower pilot plant at Plataforma Solar de Almería — 165 operating points across three campaigns between October 2019 and October 2023, MD5-verified against the published record. It was chosen over the alternatives because it carries a *measured water-consumption channel*, which lets the water model and the thermal model be validated against one consistent experiment on one rig rather than borrowing a chemistry benchmark from an unrelated plant.'));

A(h2('The two failures, and what they mean'));
A(p('**Gate V2 fails because a defect was fixed.** An earlier revision of the report showed 7.11 % and a pass. That pass rested on a drift constant a hundred times too large — a modern eliminator rating of 0.0005 *per cent* with the percent sign dropped, and so used as a fraction. Correcting it removed roughly five per cent of padding and exposed a real shortfall. The old result is withdrawn.'));
A(p('The cause is now established by a test that could have failed. Two explanations were possible: an unaccounted bleed in the measured channel, or the fill characteristic drifting between campaigns. They make opposite predictions, because re-identifying the fill law per campaign cannot help against a bleed. Re-identified per campaign, every campaign falls inside the 8 % gate — 6.55 %, 7.80 % and 4.50 %. The bleed hypothesis is rejected. The identified fill coefficient moves 23.5 % across four years, which is the same drift already measured in the thermal channel.'));
A(p('That result is the justification for the annual recalibration licence. A controller shipped with a fixed fill characteristic degrades silently as the fill fouls, and this gate is the measurement of how fast.'));

A(p('**Gate V5 fails because the threshold was written beyond a physical wall.** Makeup water is evaporation multiplied by C/(C−1), so the saving available from raising cycles is arithmetic rather than a modelling choice: seven cycles gives 12.50 %, eight gives 14.29 %, and 15 % requires 8.5 cycles. Gypsum saturates at eight cycles on this water, and gypsum saturation is not pH-sensitive, so no amount of acid moves it. The criterion was mis-specified rather than merely missed. It stands as written and the gate stays failed.'));

A(note('Both failures are settled and neither is an open question. They are in the package deliberately: they carry the gypsum wall and the fill-drift measurement, which are two of the strongest findings in it.'));

// ------------------------------------------------------- 7. market ----
A(h1('7. Market opportunity'));

A(quote('Per 10 MW condenser-water module, the model gives $157,975 a year in operating cost and 26,711 m³ a year of water, scaling approximately linearly with condenser duty — about $1.58 million a year at 100 MW, or $2.78 million at a 50,000 ton-refrigeration plant. Against a first-year cost near $50,000 per loop, payback is well under three months.'));

A(p('The beachhead is Saudi and Qatari district cooling running treated sewage effluent, together with industrial cooling at Jubail and Yanbu. Treated effluent at high cycles is exactly the regime in which the incumbent index fails, so the technical argument is sharpest where national water-reuse policy is strongest. Qatar needs no rework — same physics, same equipment, same water policy — and its adoption of treated effluent in district cooling is further advanced than Saudi Arabia’s.'));

A(h2('The tariffs underneath these figures'));
A(p('Every tariff is now taken from a published schedule rather than assumed.'));
A(spacer(60));
A(table(
  ['Input', 'Value', 'Source'],
  [
    ['Electricity', '$0.074 / kWh', 'Saudi business all-in retail, December 2025'],
    ['Water avoided', '$3.11 / m³', 'Marafiq / RCJY approved schedule: process water at SAR 8.04 plus industrial wastewater at SAR 3.64 not discharged'],
    ['Sulphuric acid', '$0.19 / kg', 'Bulk 98 %, Saudi, mid-range of a $0.148–0.380 four-quarter band'],
  ],
  widths([1, 1, 3.2]), { zebra: true }));

A(spacer(140));
A(p('The water figure is the one that carries the case, and it is stronger than a simple tariff lookup: a cubic metre of blowdown avoided saves both the makeup not purchased and the industrial wastewater not discharged, and both line items come from the same approved schedule. For a Jubail or Yanbu operator the value case computes from the customer’s own published numbers.'));
A(p('Two constraints came with that verification and are stated rather than glossed. No time-of-use tariff is published for Saudi commercial or industrial customers, so the fan leg is valued at a flat energy price and **no peak-shifting arbitrage is claimed**. And acid prices roughly doubled between the first and second quarters of 2026 on sulphur-supply disruption, so the base case deliberately sits mid-range; acid-price volatility is an argument for dose optimisation, not against it.'));

A(h2('The national-priority argument'));
A(p('Cooling is roughly half of Saudi building electricity and up to 70 to 80 per cent of summer peak demand. The second objective of the National Water Strategy reads, verbatim, *enhance water demand management across all uses*. Mizan is one control action that moves both levers at once, which maps onto the programme’s first two focus areas.'));
A(p('The sharper version of the same point: SEEC’s twenty-six energy-efficiency regulations, and the 2021 switch from EER to SEER, all govern equipment specification. None of them governs the operating point of an already-installed water-cooled plant. The policy intent exists and the lever does not. That gap is the product.'));

A(h2('The obvious counter, pre-empted'));
A(p('Saudi greenfield district cooling is trending toward air-cooled and zero-water designs; Red Sea Global’s plant is dry-cooled with no tower at all. Mizan is explicitly a retrofit for the existing installed base and not a bet on new-build. We say this before a reviewer says it for us. For the same reason, once-through and seawater-makeup loops are outside our market: Marafiq prices seawater cooling at SAR 0.069/m³, and where cooling water is effectively free the blowdown-reduction value collapses to nearly nothing.'));

// ------------------------------------------------------ 8. traction ----
A(h1('8. Early traction'));

A(quote('None. No letters of intent, no pilot agreements, and no completed customer interviews at the time of submission.'));

A(p('We state this plainly. DTV screens the technology-maturity gate first and scores traction afterwards, and a fabricated letter of intent is the one unrecoverable error in this ecosystem. The honest position — strong evidence, zero traction, and a dated plan to build it — is credible. An invented one is not.'));
A(p('The plan itself is specific: thirty structured conversations in ninety days, split as ten operators, eight controls and water integrators, six energy-service companies and six consultants, against a named account list that is already qualified and includes the accounts we have disqualified and why. The customer-development plan attached to this application carries the list, the sequence and the kill criteria.'));

// ------------------------------------------- 9. commercialisation ----
A(h1('9. Commercialisation plan and budget'));

A(p('The full plan is attached as a separate document. In summary, the product is sold as equipment: $28,000 to $42,000 per condenser loop for the controller and sensor skid, $8,000 to $15,000 for commissioning and integration, and an annual model-recalibration licence at $10,000 to $14,000 per loop. The entry wedge is a paid diagnostic at $6,000 to $12,000, credited against a later purchase.'));
A(p('We sell through controls integrators, energy-service companies and water-treatment contractors, who already hold site access, commissioning crews and framework agreements. There is a structural opening worth naming: the incumbent water-treatment model earns on chemical volume, so a device whose purpose is to cut both blowdown and dosing is something the incumbent is disincentivised to build, while a contractor competing on total cost of ownership has every reason to carry it.'));

A(h2('What the in-kind support buys'));
A(p('The SAR 200,000 product-development stream is modelled as physical-validation capability and never as runway. It covers instrumentation, the motorised blowdown valve and edge hardware, a heated-coupon scaling rig, an ICP-OES water-analysis campaign, an operational-technology security assessment, third-party validation, and intellectual-property counsel for the freedom-to-operate opinion.'));

A(h2('The cash constraint, stated honestly'));
A(p('DTV support is in kind and cannot fund residence in Dhahran from 18 October 2026 to 11 January 2027. The programme covers travel and accommodation for two members at the bootcamp and Demo Day only — not the twelve-week residency, and not a third founder. The minimum viable bridge is approximately **$17,000** and the prudent target approximately **$32,000**.'));
A(p('With no liquid founder cash, the residency period is not fundable from the programme itself. The honest options are a paid diagnostic closed before 15 October, a disclosed third-party bridge, or declining the on-site component. We would rather raise this with DTV during selection than discover it in December.'));

// ----------------------------------------------------------- 10. team ----
A(h1('10. Team'));

A(p('Three energy engineers, all full-time on the venture.'));
A(spacer(60));
A(table(
  ['Name', 'Position in the venture', 'Email', 'Mobile', 'LinkedIn'],
  [
    ['Engr. Furqan Shakeel', 'Founder & Chief Technology Officer', 'engr.furqan.shakeel@gmail.com', '+92 302 1044259', 'linkedin.com/in/furqan-shakeel'],
    ['Engr. Damia Baig', 'Co-founder & Chief Executive Officer', 'baigdamia@gmail.com', '+92 331 6491787', 'linkedin.com/in/damia-baig'],
    ['Engr. Muhammad Ahsan', 'Co-founder & Head of Commercial Development', 'muhammadahsan4203@gmail.com', '+92 310 4550698', 'linkedin.com/in/-m-ahsan'],
  ],
  widths([1.5, 2, 2.4, 1.4, 2]), { size: 17, zebra: true }));

A(spacer(140));
A(p('The division of work is real rather than nominal. The Chief Technology Officer owns the physics core, the controller and the validation programme, and joins calls for technical qualification. The Chief Executive Officer and the Head of Commercial Development own discovery and pipeline between them. Where the two disagree, the Chief Executive decides commercial scope and the Chief Technology Officer decides technical architecture, and deadlocks resolve toward whichever position carries more customer evidence.'));

A(p('Two of three founders on the commercial side is deliberate. The technical risk is now largely retired — the evidence package is built, public and reproducible — and the binding risk from here is traction velocity, which is a headcount problem rather than a modelling one.'));

A(h2('On selling'));
A(quote('None of us is a salesperson, which is why the go-to-market is built around a technical demonstration rather than a pitch. We run the prospect’s own makeup-water analysis through the model and show them where their conductivity setpoint sits between their two ceilings — the economic optimum and the physical saturation limit. That is a peer conversation between engineers, and all three founders can hold it credibly.'));

A(note('All three LinkedIn URLs have been confirmed by the founders and resolve to live profiles.'));

// ------------------------------------------------------- 11. uploads ----
A(h1('11. Upload checklist'));

A(table(
  ['Item the form asks for', 'What we attach', 'Status'],
  [
    ['Pitch deck (PDF)', 'Furqan_Mizan_Pitch_Deck.pdf', 'Ready'],
    ['Proof-of-Concept report', 'Furqan_Mizan_PoC_Report.docx / .pdf', 'Ready'],
    ['CVs of core team members, with LinkedIn URLs', 'Three separate CV files, one per founder', 'Ready'],
    ['Patent / IP documentation', 'Furqan_Mizan_IP_and_Prior_Art.docx — no patents held; the prior-art position is disclosed instead', 'Ready, in lieu'],
    ['Letters of intent or pilot agreements', 'None held. Furqan_Mizan_Customer_Development_Plan.docx states the position and the dated plan', 'Ready, in lieu'],
    ['Commercialisation plan and budget', 'Furqan_Mizan_Commercialisation_and_Budget.docx', 'Ready'],
    ['Other supporting documents', 'Defect register; AI architecture note; market dossier', 'Optional'],
  ],
  widths([1.6, 3, 1]), { zebra: true, size: 18 }));

A(spacer(200));
A(rule());
A(note('Every number in this document is read from the validation results in the project repository rather than typed by hand, and the whole evidence package regenerates from a public dataset in four commands. If a gate is re-run and a figure moves, this document is regenerated with it.'));

// ---------------------------------------------------------------- build ----
const doc = new Document({
  numbering: S.NUMBERING,
  title: TITLE,
  creator: 'Furqan',
  description: 'DTV .dvp Cohort 2 application answers',
  sections: [Object.assign({}, S.sectionProps(TITLE, 'FURQAN · MIZAN'), { children: kids })],
});

Packer.toBuffer(doc).then((b) => {
  fs.mkdirSync(OUT, { recursive: true });
  const f = path.join(OUT, 'Furqan_Mizan_Application_Answers.docx');
  fs.writeFileSync(f, b);
  console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB');
});
