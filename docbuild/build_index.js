// A one-page map of the submission, so a reviewer knows what is in the folder
// and — for the two slots we cannot fill — what stands in their place.
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const S = require('./style.js');
const { p, h1, h2, quote, bullet, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');
const TITLE = 'Submission Contents — Furqan / Mizan';

const kids = [];
const A = (...x) => kids.push(...x);

A(...S.cover({
  kicker: 'DEEP-TECH VENTURES PROGRAM (.dvp) · COHORT 2 · DHAHRAN TECHNO VALLEY',
  title: 'Submission Contents',
  subtitle: 'Mizan — an energy–water supervisory controller for condenser-water loops',
}));

A(p('Every document in this folder is provided in both Word and PDF. Upload the PDF wherever the form asks for one.'));

A(h1('What the form asks for, and what answers it'));

A(table(
  ['The form asks for', 'File', 'Note'],
  [
    ['Pitch deck (PDF)', 'Furqan_Mizan_Pitch_Deck.pdf', '15 slides, ordered to the scoring sequence: maturity gate first'],
    ['Proof-of-Concept report', 'Furqan_Mizan_PoC_Report.pdf', '29 pages, 13 figures, every number generated from the results files'],
    ['CVs of core team members, with LinkedIn URLs', 'Furqan_Mizan_CV_Furqan_Shakeel.pdf and two others', 'One per founder'],
    ['Patent / IP documentation', 'Furqan_Mizan_IP_and_Prior_Art.pdf', '**We hold no patents.** This is the searched and reasoned position that stands in its place'],
    ['Letters of intent or pilot agreements', 'Furqan_Mizan_Customer_Development_Plan.pdf', '**We hold none.** This is the qualified pipeline and dated plan that stands in its place'],
    ['Commercialisation plan and budget', 'Furqan_Mizan_Commercialisation_and_Budget.pdf', 'Pricing, route to market, named accounts, in-kind and cash budget, kill gates'],
    ['Free-text form fields', 'Furqan_Mizan_Application_Answers.pdf', 'Not an upload. The wording to transcribe into each field'],
    ['Any other supporting documents', 'Furqan_Mizan_Defect_Register.pdf', 'Ten defects found and fixed, and the two failed gates explained. Recommended'],
  ],
  widths([1.8, 2.4, 3]), { zebra: true, size: 17 }));

A(spacer(200));

A(h1('Three things a reviewer should know before reading'));

A(h2('We report two failed gates'));
A(p('Of six pre-registered acceptance criteria, four pass and two fail. Both failures are in the package deliberately, both are diagnosed, and neither threshold has been moved. The water-consumption gate fails because we found and fixed a drift constant a hundred times too large, which withdrew an earlier passing result. The makeup-water gate fails because the threshold was written beyond a physical wall — 15 % requires 8.5 cycles of concentration and gypsum saturates at 8. The accompanying defect register lists ten defects found and fixed, four of them caught because a first-principles model refused a bad input rather than absorbing it.'));

A(h2('The energy result is reported separately from the cost result'));
A(p('Electrical power was always the first term of the controller’s objective function, but until this revision it was monetised into the cost figure and never reported on its own. It now is: 4.91 % mean total power reduction across the gate conditions, and 6.68 % hours-weighted across a real Dhahran year. Doing that revealed that the energy saving and the water saving are anti-correlated across the year, which is the strongest argument in the package for coupling the two models.'));

A(h2('We have no traction, and we did not manufacture any'));
A(p('No letters of intent, no pilots, no completed customer interviews. The commercial work to date is account qualification, which is finished, and the conversations, which have not started. A letter of intent is easy to obtain and worth nothing as evidence, and we would rather be judged on the position we actually hold.'));

A(spacer(160));
A(rule());
A(h2('The technology-readiness claim is deliberately conservative'));
A(p('We claim TRL 3. Assessed against the programme’s own software track we already meet three of the four TRL 4 criteria: components integrated, interoperability validated across two independent implementations that agree to 1.4 × 10⁻⁵ K, and the relevant environment defined. We do not claim TRL 4 because performance in that environment is predicted rather than tested — 40.5 % of a Dhahran year lies outside the wet-bulb envelope our validation data covers.'));

A(spacer(160));
A(rule());
A(note('The whole evidence package is reproducible from a public, MD5-verified dataset in four commands, and a 49-check consistency audit gates every release. The code is published at github.com/furqan5/mizan and archived at DOI 10.5281/zenodo.22179268, so a reviewer can run it. Prepared 30 August 2026.'));

const doc = new Document({
  numbering: S.NUMBERING,
  title: TITLE,
  creator: 'Furqan',
  sections: [Object.assign({}, S.sectionProps(TITLE, 'FURQAN · MIZAN'), { children: kids })],
});

Packer.toBuffer(doc).then((b) => {
  fs.mkdirSync(OUT, { recursive: true });
  const f = path.join(OUT, '00_Submission_Contents.docx');
  fs.writeFileSync(f, b);
  console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB');
});
