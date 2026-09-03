// Commercialisation plan and budget.
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const S = require('./style.js');
const { p, h1, h2, h3, quote, bullet, numbered, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');
const TITLE = 'Commercialisation Plan and Budget — Furqan / Mizan';

const kids = [];
const A = (...x) => kids.push(...x);

A(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Commercialisation Plan and Budget',
  subtitle: 'Mizan — an energy–water supervisory controller for condenser-water loops',
}));

A(note('A note on the figures in this document. Values derived from the validated model in the evidence package are identified as modelled. Values taken from a published external schedule are identified by their source. Values that are our own commercial assumptions are identified as assumptions. Nothing here is presented as measured field performance, because none of it is yet — field measurement is a TRL 4 objective.'));

// ------------------------------------------------------------ 1. product ----
A(h1('1. What is sold'));

A(p('Not software. A retrofit edge controller, priced and sold as equipment.'));

A(table(
  ['Component', 'Detail'],
  [
    ['Sensor skid', 'Conductivity, pH, ORP, temperature, makeup flow and blowdown flow'],
    ['Actuation', 'Motorised blowdown valve; fan variable-speed-drive setpoint through the existing building management system'],
    ['Edge compute', 'Runs the validated physics core; BACnet and Modbus; no cloud dependency'],
    ['Licence', 'Annual model recalibration and water-chemistry update'],
  ],
  widths([1, 3.2]), { zebra: true }));

A(spacer(140));
A(p('The controller ships **read-only in shadow mode**. Blowdown and dosing stay advisory until the site has validated the recommendations on its own data. That is a deliberate commercial choice as well as a safety one: it lets a plant quantify the benefit before granting write access, which is the shortest path through an operational-technology security review.'));

A(p('**Why not software as a service.** The programme excludes it, and more importantly the value is inseparable from instrumentation. The saturation limit cannot be computed from a plant’s existing sensors, because bulk conductivity does not determine ion composition and no existing instrument reads skin temperature. The hardware is not packaging around an algorithm; it is what makes the calculation possible.'));

// -------------------------------------------------------------- 2. value ----
A(h1('2. Value created, from the model'));

A(p('Per 10 MW condenser-water module, weighted across five Gulf ambient conditions, on published tariffs rather than assumptions.'));

A(table(
  ['', 'Baseline', 'Optimised', 'Saving'],
  [
    ['Operating cost', '$228.76 / h', '$210.72 / h', '**$157,975 / yr  (7.88 %)**'],
    ['Makeup water', '23.6 m³/h', '20.6 m³/h', '**26,711 m³ / yr**'],
    ['Electrical power', '1,659 kW', '1,578 kW', '**4.91 % mean reduction**'],
  ],
  widths([1.3, 1.2, 1.2, 2]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('The power line is worth separating out, because it is what makes this an energy product rather than a water product. Electrical power reduction ranges from 1.57 % in the mildest condition to **12.09 % in winter**, where the controller runs the fan *up* and spends fan power to buy compressor power. In that condition electricity is 74 % of the total saving, and the water result is deliberately allowed to get worse.'));

A(h2('Scaling by condenser duty'));
A(table(
  ['Plant size', 'Annual saving (modelled)'],
  [
    ['10 MW  (about 2,840 refrigeration tons)', '$157,975'],
    ['30 MW  (about 8,530 tons)', '$473,927'],
    ['60 MW  (about 17,060 tons)', '$947,855'],
    ['100 MW  (about 28,430 tons)', '$1,579,759'],
    ['176 MW  (a 50,000 ton plant)', '$2,780,376'],
  ],
  widths([2.4, 1.8]), { align: ['L', 'R'], zebra: true }));

A(spacer(140));
A(h2('The tariff inputs, and why they are defensible'));
A(table(
  ['Input', 'Value', 'Source'],
  [
    ['Electricity', '$0.074 / kWh  (SAR 0.277)', 'Saudi business all-in retail, December 2025'],
    ['Water avoided', '**$3.11 / m³**', 'Marafiq / RCJY approved schedule effective 7 December 2025: process water at SAR 8.04/m³ **plus** industrial wastewater at SAR 3.64/m³ not discharged'],
    ['Sulphuric acid', '$0.19 / kg', 'Bulk 98 %, Saudi, mid-range of a $0.148–0.380 four-quarter band'],
  ],
  widths([1, 1.3, 3]), { zebra: true }));

A(spacer(140));
A(p('The water figure is the one that carries the case, and it is stronger than a simple tariff lookup: a cubic metre of blowdown avoided saves both the makeup not purchased and the industrial wastewater not discharged, and both line items come from the same approved schedule. For a Jubail or Yanbu operator, the value case computes entirely from the customer’s own published numbers.'));

A(p('Two constraints came with the verification and are stated rather than buried. **No published time-of-use tariff exists** for Saudi commercial or industrial customers, so the fan leg is valued at a flat energy price and no peak-shifting arbitrage is claimed. And **acid prices roughly doubled between the first and second quarters of 2026**, attributed to Strait of Hormuz disruption constraining sulphur supply; the base case sits mid-range deliberately, and acid-price volatility is an argument for dose optimisation rather than against it.'));

A(note('One further honesty check belongs here. The five-condition mean above is the gate metric. Weighted by the hours a real Dhahran year actually spends at each wet-bulb, the water saving falls to 11.51 %, the power saving to 6.68 % and the cost saving to 8.33 %. The annual figures are the ones to quote in a customer conversation; the five-condition mean should not be used outside the comparison it was computed for.'));

A(h2('Why the saving does not have a season'));

A(p('Run across a real Dhahran year, the energy saving and the water saving move in opposite directions, with a correlation of **r = −0.66**. In the cool half of the year the controller runs the fan hard to buy compressor power and returns **10.4 %** on electricity against 7.3 % on water. In the hot half it slows the fan to bank evaporation and returns **15.7 %** on water against 3.0 % on electricity.'));

A(quote('The commercial consequence is that the total operating-cost saving stays between **5.6 % and 10.9 % in every hour-bin of the year**, even though it is produced by a different physical mechanism in each half. A customer is not buying a summer product or a winter product.'));

A(p('This also frames the competitive position more sharply than any feature comparison. A water-treatment controller collects almost nothing across the cool half of a Dhahran year. An energy optimiser collects almost nothing across the hot half. Both are right for part of the year and neither is right for all of it, and no amount of tuning fixes that, because each is missing the model the other one has.'));

// ------------------------------------------------------------ 3. pricing ----
A(h1('3. Pricing'));

A(table(
  ['Line', 'Price (assumption)', 'Basis'],
  [
    ['Controller and sensor skid, per condenser loop', '$28,000 – 42,000', 'Equipment capital cost'],
    ['Commissioning and integration', '$8,000 – 15,000', 'One-off'],
    ['Annual recalibration licence', '$10,000 – 14,000', 'Per loop per year'],
    ['Paid diagnostic (the entry wedge)', '$6,000 – 12,000', 'Credited against a later purchase'],
  ],
  widths([2.4, 1.4, 1.6]), { zebra: true }));

A(spacer(140));
A(p('At a 30 MW plant saving roughly $474,000 a year, a first-year cost near $50,000 per loop gives payback in well under three months and a first-year return above nine times. That ratio is what makes the sale possible without a salesperson: the arithmetic argues for itself in front of an engineer.'));

A(quote('A conversion rule we hold ourselves to: no move from pilot to purchase unless the independently metered benefit is at least three times the first-year fee.'));

// -------------------------------------------------------------- 4. route ----
A(h1('4. Route to market'));

A(p('**Sell through the contractor, not around them.** Controls integrators, energy-service companies and water-treatment contractors already hold site access, commissioning crews and framework agreements. They convert in weeks where a direct utility sale takes quarters.'));

A(p('There is a structural opening worth stating plainly. The incumbent water-treatment model earns on **chemical volume**. A device whose purpose is to cut both blowdown and dosing is something the incumbent is disincentivised to build — but a contractor competing for a service contract on total cost of ownership has every reason to carry it.'));

A(p('The beachhead is Saudi and Qatari district cooling running treated sewage effluent, plus industrial cooling in Jubail and Yanbu. Treated effluent at high cycles is exactly the regime where the incumbent index fails, so the technical argument is sharpest where the water policy is strongest.'));

A(h2('Verified target accounts — Saudi Arabia'));
A(table(
  ['Account', 'Site', 'Capacity', 'Entry thesis'],
  [
    ['Saudi Tabreed', 'Portfolio', '349,000 TR contracted', 'Largest independent Saudi operator — one relationship, many retrofit units'],
    ['Saudi Tabreed', 'KAFD, Riyadh', '100,000 TR', 'Ten-year contract extension signed — a long horizon to amortise a retrofit'],
    ['Saudi Tabreed', 'King Salman Park', '60,000 TR, 25-year', 'Greenfield with a 25-year operations horizon'],
    ['Saudi Tabreed', 'King Faisal Specialist Hospital, Jeddah', '62,000 TR', 'Healthcare — zero tolerance for condenser fouling'],
    ['Saudi Tabreed', 'Jabal Omar, Makkah', '55,000 TR', 'Makkah water scarcity is acute'],
    ['Saudi Tabreed', 'Saudi Aramco cooling', '32,000 TR', 'Proof that Aramco procures third-party district cooling'],
    ['Saudi Aramco', 'Ras Tanura, Abqaiq, Hawiyah', 'Refinery scale', 'Maintains its own engineering standards for open evaporative recirculating cooling water — a governance framework to plug into'],
    ['Marafiq / Marafiq Cool', 'Jubail and Yanbu', '4.8 GW power', 'Publishes its own approved water tariff schedule — the value case computes from the customer’s own numbers'],
  ],
  widths([1.4, 2, 1.4, 3]), { zebra: true, size: 16 }));

A(spacer(160));
A(h2('Verified target accounts — Qatar'));
A(table(
  ['Account', 'Site', 'Capacity', 'Entry thesis'],
  [
    ['**Qatar Foundation**', 'Education City central plants', '**185,000 TR**', 'Plants run completely on treated effluent for condenser cooling — the highest-scaling-risk makeup in the region, under a single owner'],
    ['**Qatar Cool**', 'West Bay, three plants', '92,500 TR', 'Switched to treated effluent and publicly documented the resulting condenser-chemistry difficulty — a warm, self-identified pain point'],
    ['Qatar Cool', 'The Pearl-Qatar', '130,000 TR', 'Largest single addressable loop in Qatar'],
    ['Marafeq Qatar', 'Lusail City', '500,000 TR connected', 'Largest district-cooling scheme in the Gulf'],
    ['QatarEnergy', 'Ras Laffan common cooling', '937,000 m³/h', 'Confirmed recirculating seawater towers with blowdown — but see the seawater caveat below'],
  ],
  widths([1.4, 2, 1.5, 3]), { zebra: true, size: 16 }));

A(spacer(160));
A(h2('Discarded after checking — this list is a credibility asset'));
A(table(
  ['Candidate', 'Why not'],
  [
    ['Red Sea Global', 'The district-cooling plant is dry-cooled with zero water consumption. No tower, no blowdown.'],
    ['Saudi Electricity Company', 'The coastal thermal fleet is once-through seawater, not evaporative. Relevant only as the electricity-tariff counterparty.'],
    ['ACWA Power', 'No evidence of evaporative condenser-water loops; the fleet appears to be coastal seawater-cooled. This one remains unverified.'],
    ['Saudi Water Authority / SWPC', 'Producer, regulator and procurement entity. Not cooling-tower operators.'],
    ['Kahramaa', 'Qatari regulator and tariff-setter, not an operator. A route to market, not a customer.'],
    ['NEOM / ENOWA', 'The 25,000 TR Oxagon plant is confirmed planned, not operating. Pipeline only.'],
  ],
  widths([1.4, 4]), { zebra: true, size: 17 }));

A(spacer(160));
A(p('**The seawater caveat, stated plainly.** Marafiq’s approved schedule prices seawater cooling at SAR 0.069/m³. Where cooling water is effectively free, blowdown-reduction value collapses to nearly zero. Once-through and seawater-makeup loops are **not our market** — the target is freshwater and treated-effluent evaporative loops. This disqualifies part of the apparent Gulf opportunity, and it should be said before a reviewer says it.'));

A(p('**The Qatar bridge.** Identical physics, equipment and water policy — and Qatar’s adoption of treated effluent in district cooling is further advanced than Saudi Arabia’s, which makes it arguably the stronger beachhead rather than the second market.'));

// ---------------------------------------------------------------- 5. GTM ----
A(h1('5. A go-to-market designed for engineers who do not sell'));

A(p('The pitch is a technical demonstration, not a sales call. We run the prospect’s own makeup-water analysis through the model and show them their two ceilings — the economic optimum and the physical saturation limit — and where their current conductivity setpoint sits relative to both. That is a peer conversation between engineers, which all three founders can hold credibly.'));

A(bullet('**Furqan Shakeel**, Founder and Chief Technology Officer, owns the physics core, the controller and the validation programme, and joins calls for technical qualification.'));
A(bullet('**Damia Baig**, Co-founder and Chief Executive Officer, owns commercial strategy, pricing and the pipeline.'));
A(bullet('**Muhammad Ahsan**, Co-founder and Head of Commercial Development, owns account qualification, market and tariff verification, and procurement-route mapping.'));

A(p('Where the two commercial roles and the technical role disagree, the Chief Executive decides commercial scope and the Chief Technology Officer decides technical architecture. Deadlocks resolve toward whichever position carries more customer evidence.'));

A(p('Two of three founders on the commercial side is deliberate. The technical risk is now largely retired — the evidence package is built and reproducible — and the binding risk from here is traction velocity, which is a headcount problem.'));

A(quote('Target: thirty structured conversations in ninety days — ten operators, eight controls and water integrators, six energy-service companies, six consultants.'));

// ------------------------------------------------------------- 6. budget ----
A(h1('6. Budget'));

A(h2('The DTV in-kind stream (SAR 200,000) — capability, not runway'));
A(table(
  ['Item', 'Indicative SAR', 'What it buys'],
  [
    ['Instrumentation — conductivity, pH, ORP, flow', '45,000', 'Turns gates V2 and V3 into measurement rather than calculation'],
    ['Motorised blowdown valve and edge hardware', '30,000', 'Closed-loop TRL 4 integration'],
    ['Heated-coupon side-stream rig', '35,000', 'Scaling kinetics — the data the learned residual needs'],
    ['ICP-OES water analysis campaign', '25,000', 'Ion-specific validation against real Gulf water'],
    ['Operational-technology security assessment', '40,000', 'Removes the largest procurement blocker'],
    ['Third-party validation report', '25,000', 'Countersignable evidence for the first pilot'],
  ],
  widths([2.6, 1.1, 2.6]), { align: ['L', 'R', 'L'], zebra: true, size: 17 }));

A(spacer(140));
A(p('These six lines total exactly SAR 200,000, which is the stream. They are deliberately cheap experiments — salt, coupons, instrumentation and laboratory time on rigs that already exist at KFUPM.'));

A(note('One item was deliberately moved out of this table. A freedom-to-operate opinion, estimated at SAR 25,000, would have taken the ask to SAR 225,000 — over the stream. It is deferred rather than squeezed in, because our own IP position states that the opinion is needed before a patent filing or first commercial sale, and neither falls inside the twelve weeks. If DTV can cover it as a third-party subject-matter expert we would take it; if not, it is a post-programme cost and nothing in the TRL 4 plan depends on it.'));

A(h2('Cash requirement — the binding constraint'));
A(p('DTV support is in kind. It cannot fund residence in Dhahran from 18 October 2026 to 11 January 2027, and the Qatar Development Bank decision does not land until 25 November at the earliest. DTV covers travel and accommodation for two members at the bootcamp and Demo Day only — not the twelve-week residency, and not a third founder.'));

A(table(
  ['Item', 'USD (assumption)'],
  [
    ['One founder resident in Dhahran, twelve weeks', '5,000 – 8,000'],
    ['Second founder, part-time Dhahran presence', '3,000 – 5,000'],
    ['Doha travel and visa for the QDB in-person phase', '1,000 – 2,000'],
    ['Third founder, bootcamp and Demo Day travel not covered by DTV', '1,000 – 1,500'],
    ['Entity formation and compliance', '4,000 – 10,000'],
    ['Contingency at 20 %', '2,800 – 5,300'],
    ['**Minimum viable bridge**', '**about 17,000**'],
    ['**Prudent target**', '**about 32,000**'],
  ],
  widths([3, 1.4]), { align: ['L', 'R'], zebra: true }));

A(spacer(140));
A(p('A third founder raises the bridge by roughly $5,000. The mitigation is that only one founder needs continuous Dhahran residency; the commercial pair can work the Gulf pipeline remotely between the covered trips.'));

A(quote('**Stated plainly: with zero liquid founder cash, the Dhahran residency period is not fundable from the programme itself.** The honest options are a paid diagnostic closed before 15 October, a disclosed family or third-party bridge, or declining the on-site component. We would rather raise this with DTV directly than discover it in December.'));

// --------------------------------------------------------- 7. milestones ----
A(h1('7. Milestones and kill gates'));

A(p('Each gate below has a kill criterion attached, written in advance so that it cannot be rationalised away later.'));

A(table(
  ['Date', 'Gate', 'Kill criterion'],
  [
    ['31 Aug 2026', 'DTV submission', 'Submit only with the honest TRL 3 claim. No letter of intent is invented.'],
    ['5 Sep 2026', 'QDB submission', 'Only after written confirmation of sector and entity eligibility.'],
    ['15 Sep 2026', 'Discovery', 'Fewer than fifteen conversations and three data-sharing discussions → narrow the segment or stop.'],
    ['15 Oct 2026', 'Bridge', 'No unrestricted bridge cash → do not enter the Dhahran residency.'],
    ['25 Nov 2026', 'QDB decision', 'No paid diagnostic and no QDB → stay Lahore-based and defer incorporation.'],
    ['11 Jan 2027', 'DTV Deal Day', 'No TRL 4 evidence → do not apply to YC Spring; take Fall 2027.'],
  ],
  widths([1.2, 1.4, 4]), { zebra: true, size: 17 }));

// ------------------------------------------------------- 8. falsification ----
A(h1('8. What would falsify the business'));

A(p('Written down in advance, so that it is not rationalised away later.'));

A(numbered('**Tariff sensitivity.** If verified Saudi water and electricity tariffs move the modelled saving below roughly 3 %, payback exceeds a year and the sale becomes much harder.'));
A(numbered('**The gap closes.** If real plants with competent antiscalant programmes already run near the physical ceiling, the margin we claim to recover does not exist. This is the single most important thing to test in customer conversations, and it is testable with one question: *what is your current cycles setpoint, and what set it?*'));
A(numbered('**Chemistry does not survive contact with a real loop.** Gates V3 and V5b are calculations. If measured Gulf loop chemistry disagrees materially with the speciation model, the differentiator weakens to a conventional energy optimiser in a crowded market.'));
A(numbered('**The incumbent bundles it.** Nalco or Veolia adding skin-temperature saturation to an existing controller would compress the window quickly — though their chemical-volume revenue model works against it.'));
A(numbered('**A Gulf patent filing appears.** ChemTreat’s skin-temperature claim currently has no visible Saudi, Qatari or GCC family member, which is why the beachhead is clear. If that changes, the design-around — saturation driving blowdown and fan speed rather than chemical dose — is the fallback, and it is already the architecture rather than a retreat from it.'));

A(spacer(200));
A(rule());
A(note('Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley. 30 August 2026.'));

const doc = new Document({
  numbering: S.NUMBERING,
  title: TITLE,
  creator: 'Furqan',
  description: 'Mizan commercialisation plan and budget',
  sections: [Object.assign({}, S.sectionProps(TITLE, 'FURQAN · MIZAN'), { children: kids })],
});

Packer.toBuffer(doc).then((b) => {
  fs.mkdirSync(OUT, { recursive: true });
  const f = path.join(OUT, 'Furqan_Mizan_Commercialisation_and_Budget.docx');
  fs.writeFileSync(f, b);
  console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB');
});
