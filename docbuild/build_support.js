// Two documents that stand in for uploads we do not have: the patent/IP
// slot (we hold none) and the letters-of-intent slot (we hold none).
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const S = require('./style.js');
const { p, h1, h2, h3, quote, bullet, numbered, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');

function build(file, title, headerText, kids) {
  const doc = new Document({
    numbering: S.NUMBERING,
    title,
    creator: 'Furqan',
    sections: [Object.assign({}, S.sectionProps(title, headerText), { children: kids })],
  });
  return Packer.toBuffer(doc).then((b) => {
    fs.mkdirSync(OUT, { recursive: true });
    fs.writeFileSync(path.join(OUT, file), b);
    console.log('wrote', file, (b.length / 1024).toFixed(0) + ' KB');
  });
}

// ==========================================================================
// 1. IP AND PRIOR ART
// ==========================================================================
const ip = [];
const I = (...x) => ip.push(...x);

I(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Intellectual Property and Prior Art',
  subtitle: 'Submitted in place of patent documentation, which we do not hold',
}));

I(quote('**Position in one line: no patents have been filed, none are pending, and no freedom-to-operate opinion has been commissioned.** This document is submitted in place of patent documentation because we would rather disclose a searched and reasoned position than leave the field blank.'));

I(h1('1. Why this document exists'));

I(p('The application form offers a slot for patent or intellectual-property documentation, marked as applicable only if held. We hold none, and the honest answer is to say so. But leaving the field empty would misrepresent the work in the opposite direction, because a prior-art search *has* been carried out, it *did* find close art, and our architecture was chosen partly in response to what it found. That reasoning is the substance of our position, and it is more useful to a reviewer than a filing receipt would be.'));

I(p('There is a second reason to write it down. A reviewer who discovers the ChemTreat patent themselves, after we have claimed novelty, is a reviewer we have lost. Disclosing it first is not a concession; it is the only way the rest of the claim stays credible.'));

I(h1('2. Ownership of what we have built'));

I(table(
  ['Component', 'Origin', 'Status'],
  [
    ['Psychrometric library', 'Implemented in house from the ASHRAE Handbook of Fundamentals formulation', 'Original work; owned outright'],
    ['Poppe / Rögener heat-and-mass-transfer integrator', 'Implemented in house from Kloppers and Kröger (2005), including the supersaturated air branch', 'Original work; owned outright'],
    ['Ion-association speciation engine', 'Implemented in house; equilibrium constants read from the USGS PHREEQC `phreeqc.dat` database', 'Original code; constants are US Government public-domain reference data'],
    ['Supervisory optimiser and constraint handling', 'Original', 'Owned outright'],
    ['Physics-informed surrogate', 'Original; trained against our own physics core, not against third-party data', 'Owned outright'],
    ['Chiller performance curves', 'EnergyPlus CoolTools curve library (US Department of Energy / NREL)', 'Public-domain reference data, cited'],
    ['Validation dataset', 'Zenodo record 10806201, Palenzuela, Roca and Serrano Rodríguez', 'CC BY 4.0; used under licence and attributed'],
  ],
  widths([1.8, 3, 1.8]), { zebra: true, size: 17 }));

I(spacer(140));
I(p('No model code was copied from any repository. Every formulation was implemented from a published source so that each constant is auditable, and so that the whole core can run on an edge controller with no third-party scientific runtime. That decision was made for engineering reasons, but it also means the ownership position is clean.'));

I(h2('What we have published'));

I(p('We hold no patents and no peer-reviewed papers. We do hold one citable publication, and it is the reason this application can be checked rather than taken on trust.'));

I(table(
  ['', 'Detail'],
  [
    ['Title', '*Mizan: an energy–water supervisory controller for cooling-tower and condenser-water loops*, v1.0.0'],
    ['Authors', 'Shakeel, F., Baig, D. and Ahsan, M.'],
    ['Archive', 'Zenodo, 30 August 2026'],
    ['DOI', '**10.5281/zenodo.22179268**'],
    ['Repository', 'github.com/furqan5/mizan'],
    ['Licence', 'PolyForm Noncommercial 1.0.0 — source available for verification and non-commercial research; commercial rights reserved'],
    ['Contents', 'The physics core, the MATLAB and Simulink re-implementation, every validation result, the figures and the defect register'],
  ],
  widths([1, 3.6]), { zebra: true }));

I(spacer(140));
I(p('It is published deliberately rather than incidentally. Every claim in the Proof-of-Concept report — the 0.542 K holdout error, the two failed criteria, the gypsum wall at eight cycles — regenerates from a public dataset in four commands. A reviewer who wants to check any of it can, without asking us for anything.'));

I(p('The licence choice is also deliberate. PolyForm Noncommercial permits use by any educational institution, public research organisation or government institution regardless of funding source, so evaluation by this programme is expressly covered. It reserves commercial use, which is how the commercial position is protected now that the method itself is public.'));

I(note('The archive excludes three things and says so in its own documentation: the copyrighted journal papers we read, which are cited rather than redistributed; the validation dataset, which is downloaded and MD5-verified at runtime so a stale copy cannot silently drift; and all commercial and personal material.'));

I(h1('3. The prior-art search'));

I(p('We searched before we claimed. The sweep covered granted patents and published applications in the cooling-water treatment and HVAC supervisory-control space, the commercial literature of the water-treatment majors, and the academic literature on cooling-tower control and scale prediction. Three independent literature passes were run, and they returned consistent results.'));

I(h2('What the search established'));

I(table(
  ['Element of our approach', 'Finding'],
  [
    ['Ion-association and Pitzer speciation', '**Not novel.** French Creek Software has shipped WaterCycle since 1990; OLI Systems runs full ionic speciation. In use by the water-treatment majors since the 1970s.'],
    ['Evaluating saturation at heat-exchanger skin temperature', '**Not novel.** ChemTreat, US 11,780,742 B2, granted 10 October 2023.'],
    ['Blowdown control against a saturation index', '**Public domain.** US 4,460,008 and US 4,464,315, both 1984, both expired.'],
    ['Heat-exchanger efficiency driving a fouling classification and a chemical dose', '**Taken.** Ecolab, US 11,668,535 B2.'],
    ['A chemical saturation limit bounding a mechanical thermal-energy optimiser in closed loop', '**No art found.** Three independent sweeps returned no academic paper, patent or commercial product describing this.'],
  ],
  widths([2, 4]), { zebra: true, size: 17 }));

I(spacer(140));
I(p('That last row is the differentiation, and it is a negative result rather than a claim of invention. We state it as such.'));

I(h1('4. The closest art, and our position relative to it'));

I(h2('ChemTreat, US 11,780,742 B2'));
I(p('*Methods for online control of a chemical treatment solution using scale saturation indices*, granted 10 October 2023, inventors Boudreaux, Gonzalez and Killough.'));

I(p('Claim 1 requires, as its final elements, determining a dosage of a chemical treatment solution and controlling the application of that solution. The claimed inventive step runs from skin temperature, through a scale saturation parameter, to a **chemical dose**.'));

I(quote('**Our position.** Mizan’s saturation objective drives **blowdown rate and cooling-tower fan speed** — actuators that claim does not recite. Acid is dosed to a conventional pH setpoint, not to a dose computed from a skin-temperature saturation parameter. The architecture was chosen this way deliberately, and the design-around is not a retreat from our design; it *is* our design.'));

I(p('We note two further distinctions that we regard as real but do not rely on. First, ChemTreat evaluates with Langelier-family indices, which describe calcite; on the Gulf treated-effluent water in our evidence package the binding mineral is gypsum, which those indices cannot represent at all. Second, our controller routes *each mineral* to its own governing temperature — retrograde species to the hot skin and prograde amorphous silica to the cold basin — rather than evaluating everything at one point.'));

I(h2('Jurisdiction, which is the practical point'));
I(p('The published family for US 11,780,742 comprises the US grant and the PCT publication. No Saudi, Qatari or other GCC national-phase member is visible on the public record. The GCC is not a contracting state of the Patent Cooperation Treaty, so Gulf coverage would require separate national filings that do not appear to have been made.'));

I(quote('A US patent has no effect in our beachhead markets. That is the operative fact, and it is why the Gulf is the right place to start rather than merely a convenient one.'));

I(p('We treat this as a monitored risk rather than a settled one. If a Saudi, Qatari or GCC family member appears, the design-around described above is already the architecture and no redesign is required.'));

I(h1('5. Freedom to operate'));

I(p('No freedom-to-operate opinion has been commissioned, and none is claimed. The analysis above is our own reading of a public claim, prepared by engineers rather than by counsel, and it is presented as such. It is not legal advice and should not be relied on as though it were.'));

I(p('An opinion will be obtained before either of two events, whichever comes first: any patent filing of our own, or first commercial sale in a jurisdiction where relevant art is in force. That work is budgeted at SAR 25,000 inside the DTV product-development stream, which covers third-party subject-matter experts, so it is funded as an in-kind line item rather than against founder cash.'));

I(h1('6. Our own filing strategy'));

I(p('We have deliberately not filed yet, for three reasons that we would rather state than have inferred.'));

I(numbered('**The claim is not yet at its strongest.** The distinguishing element is per-mineral temperature routing closing three actuators. Its clearest supporting evidence — measured, not modelled — comes from the TRL 4 programme. Filing before that data exists would produce a narrower claim supported by simulation.'));
I(numbered('**Cost discipline.** With no liquid founder cash, a filing before a freedom-to-operate opinion would be spending in the wrong order.'));
I(numbered('**We chose verifiability over secrecy, and that was a real trade.** Publishing the physics core means we hold no trade secret in the method: the per-mineral evaluation scheme, the fill-law identification and the drift measurement are all readable by anyone, including a competitor. We judged that an unverifiable claim is worth less than a checkable one at this stage, and that the commercial position is better held by the licence — which reserves commercial use — than by secrecy we would have to defend. What is not published, and cannot be until the TRL 4 programme runs, is the calibration data from real Gulf loops. That is the asset that compounds, and it does not exist yet.'));

I(p('The intended sequence is therefore: freedom-to-operate opinion during the programme, provisional filing once laboratory data supports the claim, and national filings in Saudi Arabia and Qatar ahead of any wider strategy, because that is where the market is and where the closest art currently has no coverage.'));

I(note('DTV states that participating startups retain their intellectual property and that standard programme support creates no claim over it. We have read that as written and have structured this section accordingly. The risk we are managing here is overclaiming, not underclaiming.'));

I(spacer(200));
I(rule());
I(note('Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley. 30 August 2026. This document is a factual disclosure of our position and is not legal advice.'));

// ==========================================================================
// 2. CUSTOMER DEVELOPMENT PLAN
// ==========================================================================
const cd = [];
const C = (...x) => cd.push(...x);

C(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Customer Development Plan',
  subtitle: 'Submitted in place of letters of intent, which we do not hold',
}));

C(quote('**Position in one line: we have no letters of intent, no pilot agreements and no completed customer interviews at the date of submission.** This document is submitted in place of them, and sets out the qualified pipeline, the ninety-day plan and the criteria under which we would stop.'));

C(h1('1. Why this slot is empty, and why we did not fill it'));

C(p('A letter of intent is trivially easy to obtain from a friendly contact and trivially easy to write. We have not sought one, and we would rather explain that decision than have a reviewer wonder about it.'));

C(p('DTV screens the technology-maturity gate first and scores traction afterwards. A fabricated or solicited letter of intent is the one unrecoverable error in this ecosystem: it costs nothing to produce, it is worth nothing as evidence, and being caught with one ends the relationship permanently. The honest position — strong evidence, zero traction, and a dated plan to build it — is credible on its own terms. An invented one is not.'));

C(p('The same discipline governs the evidence package attached to this application, which reports two failed validation gates and ten defects we found in our own work, four of them caught because the physics refused a bad input. It would be inconsistent to hold that standard on the technical side and abandon it on the commercial side.'));

C(h1('2. What we have done instead'));

C(p('The commercial work to date is qualification rather than conversation: establishing which accounts are real, which are not, and what would have to be true for the product to be worth buying. That work is finished and is summarised below. What has not started is the talking, and that is stated plainly.'));

C(table(
  ['Completed', 'Not started'],
  [
    ['Named-account qualification across Saudi Arabia and Qatar, with capacities and entry theses', 'Any operator conversation'],
    ['Disqualification of accounts that look addressable and are not — dry-cooled, once-through seawater, regulators and producers', 'Any data-sharing discussion'],
    ['Tariff verification against published schedules rather than assumption', 'Any pilot or paid diagnostic'],
    ['Procurement-route mapping and buyer-persona definition', 'Any letter of intent'],
    ['Pricing structure and route-to-market design through integrators, ESCOs and water-treatment contractors', 'Any revenue'],
  ],
  widths([3, 2]), { zebra: true }));

C(spacer(140));
C(p('The disqualification list is the part we would point a reviewer at first. Ruling out Red Sea Global as dry-cooled, the Saudi Electricity Company fleet as once-through seawater, and Kahramaa as a regulator rather than an operator, costs us apparent market size and buys accuracy. Marafiq prices seawater cooling at SAR 0.069 per cubic metre, and where cooling water is effectively free our value proposition collapses to nearly nothing. We would rather say that than be asked it.'));

C(h1('3. The qualified pipeline'));

C(h2('Priority accounts — Qatar first'));
C(p('Qatar is sequenced ahead of Saudi Arabia, which is not the obvious order. The reason is that Qatari district cooling has moved onto treated sewage effluent further and faster, and treated effluent at high cycles is exactly the regime where the incumbent index fails. The technical argument is sharpest there.'));

C(table(
  ['Account', 'Site and capacity', 'Why this account first'],
  [
    ['**Qatar Cool**', 'West Bay, three plants, 92,500 TR', 'Switched to treated effluent and **publicly documented the resulting condenser-chemistry difficulty**. A self-identified pain point is the warmest possible opening.'],
    ['**Qatar Foundation**', 'Education City, 185,000 TR', 'Plants run entirely on treated effluent for condenser cooling — the highest-scaling-risk makeup in the region, under a single owner.'],
    ['Qatar Cool', 'The Pearl-Qatar, 130,000 TR', 'The largest single addressable loop in Qatar; a natural expansion once West Bay is proven.'],
    ['Marafeq Qatar', 'Lusail City, 500,000 TR connected', 'The largest district-cooling scheme in the Gulf.'],
  ],
  widths([1.4, 1.8, 3.4]), { zebra: true, size: 17 }));

C(spacer(160));
C(h2('Priority accounts — Saudi Arabia'));
C(table(
  ['Account', 'Site and capacity', 'Why this account'],
  [
    ['**Marafiq / Marafiq Cool**', 'Jubail and Yanbu', '**Publishes its own approved water tariff schedule**, so the value case computes entirely from the customer’s own numbers. No argument about the price of water is possible.'],
    ['**Saudi Tabreed**', 'Portfolio, 349,000 TR contracted', 'The largest independent Saudi operator: one relationship, many retrofit units. KAFD alone is 100,000 TR on a ten-year extension.'],
    ['Saudi Tabreed', 'King Faisal Specialist Hospital, Jeddah, 62,000 TR', 'Healthcare has zero tolerance for condenser fouling, which changes the buying criterion from cost to risk.'],
    ['Saudi Aramco', 'Ras Tanura, Abqaiq, Hawiyah', 'Maintains its own engineering standards for open evaporative recirculating cooling water — a technical governance framework to plug into rather than argue with.'],
  ],
  widths([1.4, 1.8, 3.4]), { zebra: true, size: 17 }));

C(spacer(160));
C(h1('4. The ninety-day plan'));

C(p('Thirty structured conversations in ninety days, deliberately weighted away from operators alone, because the route to market runs through the contractors who already hold site access.'));

C(table(
  ['Segment', 'Target', 'What we are testing'],
  [
    ['District-cooling and industrial operators', '10', 'Whether the gap between the economic and physical ceilings is real on their plant'],
    ['Controls and water-treatment integrators', '8', 'Whether they will carry the device, and on what commercial terms'],
    ['Energy-service companies', '6', 'Whether the saving is bankable inside an existing performance contract'],
    ['Consultants and specifiers', '6', 'Whether it can be written into a retrofit specification'],
  ],
  widths([2.4, 0.8, 3.4]), { align: ['L', 'C', 'L'], zebra: true }));

C(spacer(140));
C(h2('The conversation is a demonstration, not a pitch'));
C(p('None of the three founders is a salesperson, and the go-to-market is designed around that rather than in spite of it. We ask a prospect for their makeup-water analysis, run it through the model, and show them two numbers they do not currently have: the cycles of concentration at which their operating cost is minimised, and the cycles at which the first mineral saturates at the condenser tube skin. Then we show them where their present conductivity setpoint sits relative to both.'));

C(p('That is a peer conversation between engineers about the prospect’s own plant, and all three founders can hold it credibly. It also doubles as qualification: a plant that already runs near its physical ceiling is not a customer, and we would rather find that out in the first meeting than the third.'));

C(h1('5. The one question that could end this'));

C(quote('*What is your current cycles setpoint, and what set it?*'));

C(p('The business rests on a specific claim: that real plants run conservatively, leaving margin unused, because their instruments cannot locate either ceiling. Our own modelling supports it — the incumbent four-cycle baseline was found safe at skin temperature in all five conditions tested, meaning it is conservative rather than unsafe. But that is a model result, not a field observation, and we do not claim otherwise.'));

C(p('If it turns out that plants with competent antiscalant programmes already operate near the physical ceiling, then the margin we propose to recover does not exist and the product does not have a market. That is the single most important thing the first fifteen conversations are for, and it is answerable with one question. We have written it down here so that we cannot quietly stop asking it.'));

C(h1('6. The first commercial step'));

C(p('The entry wedge is a **paid diagnostic** at $6,000 to $12,000, credited in full against a later purchase. It is deliberately priced to be signable at an engineering manager’s discretion rather than requiring a capital process, and it converts a conversation into a commercial relationship without asking anyone to commit to hardware.'));

C(p('It also serves us in two other ways. It is the first real test of willingness to pay, which no letter of intent can provide. And, closed before 15 October, it is the most credible route to the bridge funding the Dhahran residency requires.'));

C(quote('The conversion rule we hold ourselves to: no move from diagnostic to purchase unless the independently metered benefit is at least three times the first-year fee.'));

C(h1('7. Kill gates'));

C(p('Written in advance so that they cannot be rationalised away later.'));

C(table(
  ['Date', 'Gate', 'Kill criterion'],
  [
    ['15 Sep 2026', 'Discovery volume', 'Fewer than fifteen conversations and three data-sharing discussions → narrow the segment or stop'],
    ['15 Oct 2026', 'Willingness to pay', 'No paid diagnostic signed → treat the value case as unproven and do not commit founder cash to residency'],
    ['25 Nov 2026', 'Funding', 'No paid diagnostic and no QDB decision → stay Lahore-based and defer incorporation'],
    ['11 Jan 2027', 'DTV Deal Day', 'No TRL 4 evidence and no pilot in negotiation → do not raise; take the next cycle'],
  ],
  widths([1.2, 1.6, 4]), { zebra: true, size: 17 }));

C(spacer(140));
C(h1('8. What we would count as traction by Deal Day'));

C(p('So that the standard is fixed before the result is known.'));

C(bullet('Fifteen or more structured conversations completed, with written notes and named counterparties'));
C(bullet('At least three plants having shared a real makeup-water analysis and a current cycles setpoint'));
C(bullet('One paid diagnostic signed and delivered'));
C(bullet('One integrator or energy-service company willing to carry the device on defined commercial terms'));
C(bullet('One site in written discussion for a shadow-mode installation'));

C(p('Anything less than the first two would tell us the segment is wrong. We would rather report that outcome than a letter of intent obtained to fill a field.'));

C(spacer(200));
C(rule());
C(note('Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley. 30 August 2026. Every account named in this document was verified against public sources; the accounts we could not verify are listed as unverified in the commercialisation plan rather than presented as pipeline.'));

// ---------------------------------------------------------------- build ----
build('Furqan_Mizan_IP_and_Prior_Art.docx', 'Intellectual Property and Prior Art — Furqan / Mizan', 'FURQAN · MIZAN', ip)
  .then(() => build('Furqan_Mizan_Customer_Development_Plan.docx', 'Customer Development Plan — Furqan / Mizan', 'FURQAN · MIZAN', cd));
