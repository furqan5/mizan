// One CV per core team member, from docbuild/people.json.
// Any field left empty in the data file is OMITTED from the document rather
// than printed as a placeholder — an empty bracket on a CV reads worse than
// a missing section, and DTV reads the CV to make the technical claims in
// the PoC report credible, not to be comprehensive.
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, BorderStyle, AlignmentType } = require('docx');
const S = require('./style.js');
const { p, h2, h3, bullet, note, spacer, rule, table, widths } = S;

const OUT = path.join(__dirname, '..', '..', 'DTV_Submission');
const DATA = JSON.parse(fs.readFileSync(path.join(__dirname, 'people.json'), 'utf8'));

const has = (v) => v !== undefined && v !== null && (Array.isArray(v) ? v.length > 0
  : (typeof v === 'object' ? Object.keys(v).length > 0 : String(v).trim() !== ''));

function cvFor(person) {
  const k = [];
  const A = (...x) => k.push(...x);

  // --- masthead -----------------------------------------------------------
  A(new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: person.name, font: S.HEAD_FONT, size: 40, bold: true, color: S.INK })],
  }));
  A(new Paragraph({
    spacing: { after: 140 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: S.ACCENT, space: 8 } },
    children: [new TextRun({ text: person.role, font: S.BODY_FONT, size: 23, color: S.ACCENT })],
  }));

  const contact = [];
  if (has(person.email)) contact.push(['Email', person.email]);
  if (has(person.mobile)) contact.push(['Mobile', person.mobile]);
  if (has(person.linkedin)) contact.push(['LinkedIn', person.linkedin]);
  if (has(person.location)) contact.push(['Location', person.location]);
  if (has(person.nationality)) contact.push(['Nationality', person.nationality]);
  if (has(person.commitment)) contact.push(['Commitment', person.commitment]);
  A(table(null, contact, widths([1, 4]), { size: 18 }));

  A(spacer(180));

  // --- summary ------------------------------------------------------------
  if (has(person.summary)) {
    A(h2('Profile'));
    A(p(person.summary, { size: 20 }));
  }

  // --- education ----------------------------------------------------------
  if (has(person.education)) {
    A(h2('Education'));
    A(table(
      ['Qualification', 'Institution', 'Year', 'Notes'],
      person.education.map((e) => [e.degree || '', e.institution || '', e.year || '', e.notes || '']),
      widths([1.6, 1.8, 0.6, 2]), { zebra: true, size: 18 }));
    A(spacer(120));
  }

  // --- experience ---------------------------------------------------------
  if (has(person.experience)) {
    A(h2('Experience'));
    A(table(
      ['Role', 'Organisation', 'Period', 'Contribution'],
      person.experience.map((e) => [e.role || '', e.org || '', e.period || '', e.detail || '']),
      widths([1.6, 1.4, 0.8, 2.4]), { zebra: true, size: 18 }));
    A(spacer(120));
  }

  // --- technical contribution --------------------------------------------
  if (has(person.contribution)) {
    A(h2('Contribution to the Mizan evidence package'));
    A(p('The evidence package is public and reproducible in four commands, so the attribution below can be checked against the work itself.', { size: 18, color: S.MUTED }));
    person.contribution.forEach((c) => A(bullet(c)));
    A(spacer(100));
  }

  // --- skills -------------------------------------------------------------
  if (has(person.skills)) {
    A(h2('Skills'));
    Object.keys(person.skills).forEach((key) => {
      A(p('**' + key + ':**  ' + person.skills[key], { size: 20, after: 90 }));
    });
  }

  // --- extras -------------------------------------------------------------
  if (has(person.extras)) {
    A(h2('Publications, projects and certifications'));
    person.extras.forEach((e) => A(bullet(e)));
  }

  if (has(person.languages)) {
    A(h2('Languages'));
    A(p(person.languages, { size: 20 }));
  }

  A(spacer(200));
  A(rule());
  A(note('Prepared for the Deep-Tech Ventures Program (.dvp) Cohort 2, Dhahran Techno Valley — 30 August 2026.'));

  return k;
}

const jobs = DATA.people.map((person) => {
  const title = person.name.replace(/^Engr\.\s*/, '') + ' — CV';
  const doc = new Document({
    numbering: S.NUMBERING,
    title,
    creator: 'Furqan',
    sections: [Object.assign({}, S.sectionProps(title, 'FURQAN · MIZAN'), { children: cvFor(person) })],
  });
  return Packer.toBuffer(doc).then((b) => {
    fs.mkdirSync(OUT, { recursive: true });
    const f = 'Furqan_Mizan_CV_' + person.file + '.docx';
    fs.writeFileSync(path.join(OUT, f), b);
    const missing = [];
    if (!has(person.education)) missing.push('education');
    if (!has(person.nationality)) missing.push('nationality');
    if (!has(person.location)) missing.push('location');
    if (!has(person.languages)) missing.push('languages');
    if (!has(person.skills)) missing.push('skills');
    if (person.experience && person.experience.length < 2) missing.push('prior employment');
    console.log('wrote', f, (b.length / 1024).toFixed(0) + ' KB' +
      (missing.length ? '   [still to supply: ' + missing.join(', ') + ']' : '   [complete]'));
  });
});

Promise.all(jobs);
