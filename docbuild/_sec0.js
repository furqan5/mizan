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
    ['Trade secret', '**No.** We published the method instead — see the note below'],
    ['Proprietary technology', '**Yes** — the physics core, the speciation engine and the supervisory optimiser, all original and owned outright'],
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
