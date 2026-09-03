// Mizan pitch deck — ordered to DTV's scoring sequence:
// maturity gate first, then problem, evidence, product, market, team.
const fs = require('fs');
const path = require('path');
const PptxGenJS = require('pptxgenjs');

const ROOT = path.join(__dirname, '..');
const SLIDE = path.join(ROOT, 'figs', 'slide');
const OUT = path.join(ROOT, '..', 'DTV_Submission');

const INK = '1A2B33';
const ACCENT = '0E6E6E';
const MUTED = '5B6B73';
const BAND = 'EDF3F4';
const PAPER = 'FFFFFF';
const RED = 'A33227';
const GREEN = '1F6B45';
const FONT = 'Cambria';
const SANS = 'Cambria';

const W = 13.333, H = 7.5;
const M = 0.72;                       // side margin
const CW = W - 2 * M;                 // content width

const pptx = new PptxGenJS();
pptx.defineLayout({ name: 'MIZAN_WIDE', width: W, height: H });
pptx.layout = 'MIZAN_WIDE';
pptx.author = 'Furqan';
pptx.company = 'Furqan';
pptx.title = 'Mizan — an energy–water supervisory controller for condenser-water loops';
pptx.subject = 'DTV .dvp Cohort 2';

let n = 0;

// A standard content slide: eyebrow, headline, thin rule, footer.
function slide(kicker, headline) {
  const s = pptx.addSlide();
  s.background = { color: PAPER };
  n += 1;
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: M, y: 0.30, w: CW, h: 0.28, fontFace: SANS, fontSize: 10.5,
      color: ACCENT, bold: true, charSpacing: 2.2,
    });
  }
  if (headline) {
    s.addText(headline, {
      x: M, y: 0.60, w: CW, h: 0.72, fontFace: FONT, fontSize: 27,
      color: INK, bold: true, valign: 'top',
    });
    s.addShape(pptx.ShapeType.rect, {
      x: M, y: 1.36, w: 1.5, h: 0.035, fill: { color: ACCENT }, line: { width: 0 },
    });
  }
  // footer
  s.addText('FURQAN · MIZAN', {
    x: M, y: H - 0.46, w: 4, h: 0.28, fontFace: SANS, fontSize: 9,
    color: MUTED, charSpacing: 1.4,
  });
  s.addText(String(n), {
    x: W - M - 1, y: H - 0.46, w: 1, h: 0.28, fontFace: SANS, fontSize: 9,
    color: MUTED, align: 'right',
  });
  return s;
}

function body(s, text, o) {
  o = o || {};
  s.addText(text, Object.assign({
    x: M, y: o.y || 1.68, w: o.w || CW, h: o.h || 1.2,
    fontFace: FONT, fontSize: o.size || 15, color: o.color || INK,
    valign: 'top', lineSpacing: (o.size || 15) * 1.55,
  }, o.opts || {}));
}

function bullets(s, items, o) {
  o = o || {};
  s.addText(items.map((t) => ({
    text: typeof t === 'string' ? t : t.text,
    options: Object.assign({ bullet: { code: '2014' }, breakLine: true },
      typeof t === 'string' ? {} : (t.options || {})),
  })), {
    x: o.x || M, y: o.y || 1.68, w: o.w || CW, h: o.h || 3.4,
    fontFace: FONT, fontSize: o.size || 14.5, color: INK,
    valign: 'top', lineSpacing: (o.size || 14.5) * 1.7, indentLevel: 0,
  });
}

// A pulled-out statement in a tinted band.
function pullquote(s, text, o) {
  o = o || {};
  const y = o.y || 5.4;
  const h = o.h || 0.92;
  s.addShape(pptx.ShapeType.rect, {
    x: M, y, w: CW, h, fill: { color: o.fill || BAND }, line: { width: 0 },
  });
  s.addShape(pptx.ShapeType.rect, {
    x: M, y, w: 0.055, h, fill: { color: o.bar || ACCENT }, line: { width: 0 },
  });
  s.addText(text, {
    x: M + 0.26, y, w: CW - 0.5, h, fontFace: FONT, fontSize: o.size || 14.5,
    color: o.color || INK, bold: !!o.bold, valign: 'middle',
    lineSpacing: (o.size || 14.5) * 1.5,
  });
}

function tbl(s, head, rows, colW, o) {
  o = o || {};
  const hdr = head.map((t) => ({
    text: t,
    options: { bold: true, color: INK, fill: { color: BAND }, fontSize: o.size || 12.5, align: o.align || 'left' },
  }));
  const data = rows.map((r) => r.map((c) => {
    const isObj = c && typeof c === 'object';
    return {
      text: isObj ? c.t : c,
      options: Object.assign({ fontSize: o.size || 12.5, color: INK, align: o.align || 'left' },
        isObj ? (c.o || {}) : {}),
    };
  }));
  s.addTable([hdr].concat(data), {
    x: o.x || M, y: o.y || 1.72, w: o.w || CW, colW,
    fontFace: FONT, border: { type: 'solid', pt: 0.5, color: 'C3CCD1' },
    rowH: o.rowH || 0.34, valign: 'middle', margin: [4, 7, 4, 7],
  });
}

// Places a figure at its true aspect ratio inside a (maxW x maxH) box and
// returns the box it actually occupied, so text can be laid out beside it.
// Stretching a plot distorts its axis labels, so the aspect is never forced.
function figure(s, file, o) {
  o = o || {};
  const f = path.join(SLIDE, file);
  const buf = fs.readFileSync(f);
  const ar = buf.readUInt32BE(16) / buf.readUInt32BE(20);
  const maxW = o.maxW === undefined ? CW : o.maxW;
  const maxH = o.maxH === undefined ? 4.0 : o.maxH;
  let h = maxH, w = h * ar;
  if (w > maxW) { w = maxW; h = w / ar; }
  const x = o.x === undefined ? M : o.x;
  const y = o.y === undefined ? 1.62 : o.y;
  s.addImage({ path: f, x, y, w, h });
  return { x, y, w, h, right: x + w, bottom: y + h };
}

// ===========================================================  1. TITLE ====
{
  const s = pptx.addSlide();
  n += 1;
  s.background = { color: INK };
  s.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.16, h: H, fill: { color: ACCENT }, line: { width: 0 } });

  s.addText('FURQAN', {
    x: 1.05, y: 1.35, w: 10, h: 0.62, fontFace: FONT, fontSize: 26,
    color: 'FFFFFF', bold: true, charSpacing: 7,
  });
  s.addText('The criterion for energy.', {
    x: 1.05, y: 1.95, w: 10, h: 0.36, fontFace: FONT, fontSize: 14,
    color: '8FC7C7', italic: true,
  });

  s.addText('MIZAN', {
    x: 1.05, y: 2.85, w: 11, h: 0.95, fontFace: FONT, fontSize: 54,
    color: 'FFFFFF', bold: true, charSpacing: 2,
  });
  s.addText('An energy–water supervisory controller for condenser-water loops', {
    x: 1.05, y: 3.85, w: 11, h: 0.48, fontFace: FONT, fontSize: 19, color: 'C9D6DA',
  });
  s.addShape(pptx.ShapeType.rect, { x: 1.05, y: 4.55, w: 1.7, h: 0.035, fill: { color: ACCENT }, line: { width: 0 } });

  s.addText([
    { text: 'TRL 3', options: { bold: true, color: 'FFFFFF' } },
    { text: '  ·  validated against measured experimental data  ·  thresholds fixed before fitting', options: { color: '9FB2B8' } },
  ], { x: 1.05, y: 4.85, w: 11, h: 0.34, fontFace: FONT, fontSize: 13.5 });

  s.addText('Deep-Tech Ventures Program (.dvp) · Cohort 2 · Dhahran Techno Valley · Energy / Water & Sustainability', {
    x: 1.05, y: 6.45, w: 11.5, h: 0.34, fontFace: SANS, fontSize: 11, color: '7B9095',
  });
}

// =====================================================  2. THE PROBLEM ====
{
  const s = slide('The problem', 'Three parties, three handles, one system');
  bullets(s, [
    'The building management system sets FAN SPEED against a fixed condenser-water setpoint',
    'The water-treatment contractor sets BLOWDOWN against a fixed conductivity setpoint',
    'The same contractor sets ACID DOSE against a fixed pH setpoint',
  ], { y: 1.72, h: 1.7, size: 15 });

  body(s, 'These are not independent variables. Concentrating the loop to save water raises scaling risk and changes evaporation. Cooling the condenser to save compressor power costs fan power and evaporates more water.', { y: 3.55, h: 1.0, size: 15 });

  pullquote(s, 'Nobody solves them together, because doing so requires the thermal model and the chemistry model to be one problem rather than two.', { y: 5.35, h: 0.95, bold: true });
}

// ==============================================  3. THE MATURITY GATE ====
{
  const s = slide('Before the product, because it is scored first', 'The maturity gate');
  body(s, 'Thresholds were fixed and printed before the fit was run. Campaign-wise holdout, n = 50, scored once, 100 % solver convergence. Public dataset, MD5-verified, CC BY 4.0.', { y: 1.62, h: 0.7, size: 14.5 });

  tbl(s, ['Gate', 'Threshold', 'Result', ''], [
    ['Outlet water temperature, MAE', '≤ 1.00 K', { t: '0.542 K', o: { bold: true } }, { t: 'PASS', o: { color: GREEN, bold: true } }],
    ['Heat rejection, MAPE', '≤ 6.00 %', { t: '5.94 %', o: { bold: true } }, { t: 'PASS', o: { color: GREEN, bold: true } }],
    ['Water consumption, MAPE', '≤ 8.00 %', { t: '9.90 %', o: { bold: true } }, { t: 'FAIL', o: { color: RED, bold: true } }],
    ['Total operating cost reduction', '≥ 3.0 %', { t: '8.55 %', o: { bold: true } }, { t: 'PASS', o: { color: GREEN, bold: true } }],
    ['Makeup water reduction', '≥ 15.0 %', { t: '14.83 %', o: { bold: true } }, { t: 'FAIL', o: { color: RED, bold: true } }],
    ['Saturation violations at the tube skin', '0', { t: '0', o: { bold: true } }, { t: 'PASS', o: { color: GREEN, bold: true } }],
  ], [5.6, 2.2, 2.1, 2.0], { y: 2.42, rowH: 0.40, size: 13 });

  pullquote(s, 'Two gates failed. We report them as failures, we know exactly why each one failed, and neither threshold has been moved.', { y: 5.62, h: 0.82, bold: true });
}

// ==================================================  4. TWO CEILINGS ====
{
  const s = slide('The core finding', 'The economics run straight into a limit the plant cannot see');
  const g4 = figure(s, 'gypsum_wall.png', { y: 1.60, maxH: 3.78, maxW: 7.1 });

  s.addText([
    { text: 'The cost curve never turns over.\n', options: { bold: true, color: ACCENT } },
    { text: 'Cost falls monotonically to 7 cycles - the last feasible point. There is no interior optimum on this water.\n\n', options: {} },
    { text: 'Physical ceiling: 8 cycles.\n', options: { bold: true, color: ACCENT } },
    { text: 'First saturation violation at the skin. Binding mineral: gypsum, and acid cannot move it.\n\n', options: {} },
    { text: 'So the economics point straight at the wall, with no margin. An operator following the money on LSI-based control walks into it blind.', options: { bold: true } },
  ], { x: g4.right + 0.34, y: 1.70, w: W - M - g4.right - 0.34, h: 3.7, fontFace: FONT, fontSize: 13.5, color: INK, valign: 'top', lineSpacing: 20 });

  pullquote(s, 'Locating the first limit needs a coupled cost model. Locating the second needs ion-specific speciation at skin temperature. A conductivity setpoint locates neither.', { y: 5.55, h: 0.85, bold: true });
}

// =====================================================  5. PRIOR ART ====
{
  const s = slide('Defensibility', 'Prior art, disclosed before we claim anything');
  body(s, 'We searched before we claimed. Three of the ingredients are already taken, and we say so — a reviewer who finds these themselves after we claim novelty is a reviewer we have lost.', { y: 1.62, h: 0.7, size: 14 });

  tbl(s, ['Element', 'Status in the prior art'], [
    ['Skin-temperature saturation', 'TAKEN — ChemTreat US 11,780,742 B2, granted Oct 2023. But Langelier-family indices, chemical feed only.'],
    ['Ion-association speciation', 'TAKEN — French Creek WaterCycle since 1990. But offline, and at bulk temperature.'],
    ['Blowdown on a saturation index', 'PUBLIC DOMAIN — US 4,460,008 / 4,464,315, 1984, expired.'],
    ['A saturation limit bounding a thermal optimiser, in closed loop', 'NO ART FOUND — three independent sweeps.'],
  ], [3.6, 8.3], { y: 2.42, rowH: 0.46, size: 12.5 });

  pullquote(s, 'What is open, stated precisely: routing each mineral to its own governing temperature, computed live, and closing three actuators on the result.', { y: 5.55, h: 0.88, bold: true });
}

// ============================================  6. PER-MINERAL ROUTING ====
{
  const s = slide('Why one evaluation temperature is wrong', 'Each mineral has its own governing surface');
  tbl(s, ['Mineral', 'Solubility against temperature', 'Governs at'], [
    ['Calcite, magnesium silicate', 'Retrograde — less soluble hot', 'The hot tube skin'],
    ['Gypsum', 'Maximum near 35–40 °C', 'The skin, weakly'],
    [{ t: 'Amorphous silica', o: { bold: true } }, { t: 'PROGRADE — more soluble hot', o: { bold: true } }, { t: 'The cold tower basin', o: { bold: true } }],
  ], [3.4, 4.6, 3.9], { y: 1.72, rowH: 0.46, size: 13.5 });

  body(s, 'Evaluating everything at one temperature is optimistic about silica — the one species with no effective inhibitor in general service. Correcting this moved our predicted silica limit from about 12 cycles to 9.', { y: 3.55, h: 0.85, size: 14.5 });

  body(s, 'And the skin offset is computed, not assumed. Heat flux over the inside film coefficient gives about 3.8 K at typical design and 8.7 K fouled. The bulk basis overstates the safe cycles limit by 7 % typical and 15.4 % fouled — reported as a band, not a point.', { y: 4.45, h: 0.95, size: 14.5 });

  pullquote(s, 'Industry sets a fixed silica ceiling of 150 mg/L. The true ceiling moves from 95 mg/L at a 15 °C winter basin to 143 mg/L at 35 °C — non-conservative at every basin temperature in the Gulf range.', { y: 5.55, h: 0.9 });
}

// ==========================================  7. MAGNESIUM SILICATE ====
{
  const s = slide('The constraint that needs all three models at once', 'The same tower deposits at high load and not at low load');
  const g7 = figure(s, 'mg_silicate_envelope.png', { y: 1.62, maxH: 3.74, maxW: 7.0 });

  s.addText([
    { text: 'Magnesium silicate forms in two steps: brucite precipitates at the hot skin, then reacts with silica.\n\n', options: {} },
    { text: 'Brucite’s saturation pH is retrograde — it FALLS as the surface heats. So deposition occurs when bulk pH exceeds the brucite saturation pH at the SKIN.\n\n', options: {} },
    { text: 'At 4 cycles, Gulf loops running pH 8.5–9.0:\n', options: { bold: true } },
    { text: 'skin 30 °C — safe across the whole band\nskin 38 °C — the band straddles the limit\nskin 46 °C — depositing across the whole band', options: { color: ACCENT } },
  ], { x: g7.right + 0.34, y: 1.70, w: W - M - g7.right - 0.34, h: 3.8, fontFace: FONT, fontSize: 13, color: INK, valign: 'top', lineSpacing: 19 });

  pullquote(s, 'It needs skin temperature (thermal model), bulk pH (chemistry model) and acid (actuator) together. A fixed pH setpoint cannot express it. Neither can a fixed conductivity setpoint.', { y: 5.62, h: 0.85, bold: true });
}

// =============================================  8. THE HONEST FAILURE ====
{
  const s = slide('The result, and the criterion we missed', 'Why 15 % was unreachable, and what that taught us');
  const g8 = figure(s, 'water_ceiling.png', { y: 1.62, maxH: 3.74, maxW: 7.0 });

  s.addText([
    { text: 'Makeup = evaporation × C/(C−1), so the saving from cycles alone is arithmetic, not a modelling choice.\n\n', options: {} },
    { text: '7 cycles → 12.50 %\n8 cycles → 14.29 %\n15 % requires 8.5 cycles\n\n', options: { color: ACCENT, bold: true } },
    { text: 'Gypsum saturates at 8. And gypsum saturation is not pH-sensitive, so no amount of acid moves it.\n\n', options: {} },
    { text: 'The criterion was written on the far side of a wall we had not yet found. It was mis-specified, not merely missed — and it stays failed.', options: {} },
  ], { x: g8.right + 0.34, y: 1.70, w: W - M - g8.right - 0.34, h: 3.8, fontFace: FONT, fontSize: 13, color: INK, valign: 'top', lineSpacing: 19 });

  pullquote(s, 'The controller still reaches 14.83 %, because it also cuts evaporation by slowing the fan wherever the chiller can absorb warmer condenser water. That second term is the coupling this product exists to price.', { y: 5.62, h: 0.85 });
}

// ================================================  9. THE ENERGY CASE ====
{
  const s = slide('The energy case', 'The two savings are anti-correlated across the year');
  const g9 = figure(s, 'seasonal_handoff.png', { y: 1.60, maxH: 3.78, maxW: 7.3 });

  s.addText([
    { text: 'Cool half of the year\n', options: { bold: true, color: ACCENT } },
    { text: '10.4 % power   ·   7.3 % water\nThe fan runs UP, buying compressor power.\n\n', options: {} },
    { text: 'Hot half of the year\n', options: { bold: true, color: ACCENT } },
    { text: '3.0 % power   ·   15.7 % water\nThe fan slows, banking evaporation.\n\n', options: {} },
    { text: 'r = −0.66 across eight equal-hour wet-bulb bins of a real Dhahran year.', options: { bold: true } },
  ], { x: g9.right + 0.34, y: 1.72, w: W - M - g9.right - 0.34, h: 3.7, fontFace: FONT, fontSize: 13, color: INK, valign: 'top', lineSpacing: 19 });

  pullquote(s, 'A water controller collects almost nothing across the cool half. An energy optimiser collects almost nothing across the hot half. Only a controller that prices both holds the saving across all 8,760 hours.', { y: 5.62, h: 0.85, bold: true });
}

// ====================================================  10. PRODUCT ====
{
  const s = slide('Product', 'A retrofit edge controller — equipment, not software');
  bullets(s, [
    'Sensor skid: conductivity, pH, ORP, temperature, makeup and blowdown flow',
    'Motorised blowdown valve, and fan drive setpoint through the existing BMS',
    'Edge compute running the validated physics core over BACnet and Modbus, with no cloud dependency',
    'Sold as capital equipment plus an annual model-recalibration licence',
  ], { y: 1.72, h: 2.3, size: 14.5 });

  body(s, 'It ships read-only in shadow mode. Blowdown and dosing stay advisory until the site has validated the recommendations on its own data — a safety position first, and the shortest route through an OT-security review second. Deterministic fixed-step solver, bounded runtime, and a documented fallback to incumbent setpoints on solver failure or sensor loss.', { y: 4.15, h: 1.2, size: 14.5 });

  pullquote(s, 'Why hardware: the saturation limit cannot be computed from a plant’s existing sensors. Bulk conductivity does not determine ion composition, and nothing installed reads skin temperature.', { y: 5.62, h: 0.85, bold: true });
}

// =================================================  11. MARKET ====
{
  const s = slide('Market', 'Why the Gulf, and why now');
  tbl(s, ['Plant size', 'Modelled annual saving'], [
    ['10 MW  (~2,840 TR)', '$157,975'],
    ['30 MW  (~8,530 TR)', '$473,927'],
    ['100 MW  (~28,430 TR)', '$1,579,759'],
    ['176 MW  (a 50,000 TR plant)', '$2,780,376'],
  ], [3.3, 2.6], { y: 1.75, rowH: 0.40, size: 13, w: 5.9 });

  s.addText([
    { text: 'Saudi and Qatari district cooling is moving onto treated sewage effluent under national reuse policy. Effluent at high cycles is exactly where the incumbent index breaks — high ionic strength, and a binding mineral LSI cannot describe.\n\n', options: {} },
    { text: 'Tariffs are from published schedules, not assumed: electricity $0.074/kWh, water avoided $3.11/m³ from the Marafiq approved schedule.\n\n', options: {} },
    { text: 'Against roughly $50,000 first-year cost per loop, payback is under three months.', options: { bold: true } },
  ], { x: M + 6.3, y: 1.75, w: CW - 6.3, h: 3.6, fontFace: FONT, fontSize: 13.5, color: INK, valign: 'top', lineSpacing: 20 });

  body(s, 'Retrofit for the existing installed base — not a bet on new-build. Saudi greenfield is trending dry-cooled, and once-through seawater loops are explicitly outside our market, because where cooling water is nearly free the value collapses.', { y: 4.35, h: 0.9, size: 13.5, color: MUTED });

  pullquote(s, 'SEEC’s 26 efficiency regulations all govern equipment specification. None governs the operating point of an already-installed water-cooled plant. The policy intent exists; the lever does not.', { y: 5.62, h: 0.85, bold: true });
}

// ==============================================  12. DEFENSIBILITY ====
{
  const s = slide('Defensibility', 'Not data volume, not UI, not AI-applied-to-X');
  bullets(s, [
    'Poppe integration with the water-activity coupling that lets chemistry change tower performance at all',
    'Ion-specific speciation at skin temperature, routed per mineral, rather than at bulk',
    'The separation of the economic ceiling from the physical ceiling, which needs both models at once',
    'The calibration library: which fill laws transfer, how fast a characteristic drifts, which mineral binds first on which water',
  ], { y: 1.68, h: 1.40, size: 13.5 });

  body(s, 'A competent generalist reproduces the tower model in weeks. What they do not reproduce is knowing the published fan correlation is in hertz not per cent, that gypsum binds before calcite on Gulf treated effluent, or that the water saving must be discounted for the evaporation the energy optimum adds back. Each came out of the physics, and each changed the answer.', { y: 3.18, h: 1.05, size: 13.5 });

  s.addText([
    { text: 'And no AI contributes to any result in this package. ', options: { bold: true } },
    { text: 'The surrogate is trained against our own physics core, not a plant, and is excluded by construction from the chemistry and every safety constraint. The only load-bearing learned component is the scaling-kinetics residual, at TRL 4. We rejected reinforcement learning (no hard-constraint guarantee), chemistry soft-sensing (signal an order of magnitude below the noise floor) and a weather LSTM (numerical weather prediction already exists).', options: { color: MUTED } },
  ], { x: M, y: 4.32, w: CW, h: 1.45, fontFace: FONT, fontSize: 12.5, color: INK, valign: 'top', lineSpacing: 18 });

  pullquote(s, 'We would rather be an energy company that uses machine learning exactly where the physics runs out than an AI company looking for a boiler to point at.', { y: 5.95, h: 0.76, bold: true, size: 13.5 });
}

// ==================================================  13. TRL 4 ====
{
  const s = slide('The ask, in engineering terms', 'TRL 4 at KFUPM — the rigs already exist on campus');
  tbl(s, ['Facility', 'What it closes'], [
    ['A/C & Refrigeration Lab — vertical cooling tower and wind tunnel with HUMIDIFICATION', 'The climate gap: our data stops at 21.9 °C wet-bulb, and 40.5 % of a Dhahran year is above it'],
    ['Chemistry Instrumentation Lab — ICP-OES and ion chromatography', 'The chemistry gap: turns gates V3 and V5b from calculation into measurement'],
    ['ME Corrosion Lab — potentiostats and recirculating loop', 'The question we cannot answer today: does acid dosing trade scale for corrosion?'],
    ['Dream Realization Lab — PCB fabrication and enclosures', 'The physical controller itself, end to end'],
  ], [5.4, 6.5], { y: 1.72, rowH: 0.52, size: 12.5 });

  body(s, 'The SAR 200,000 product-development stream buys instrumentation, the blowdown valve and edge hardware, a heated-coupon scaling rig, ICP-OES analysis, an OT-security assessment, IP counsel and third-party validation. It is modelled as physical-validation capability and never as runway.', { y: 4.55, h: 1.0, size: 14 });

  pullquote(s, 'The humidifying wind tunnel closes the one honest gap in this package: our validation data comes from a semi-arid Spanish site whose summer wet-bulb sits well below Dhahran’s.', { y: 5.68, h: 0.8 });
}

// ==================================================  14. TRACTION ====
{
  const s = slide('Traction', 'None. And we did not manufacture any.');
  body(s, 'No letters of intent, no pilot agreements, no completed customer interviews. A letter of intent is easy to obtain from a friendly contact and worth nothing as evidence, and being caught with a solicited one ends the relationship permanently.', { y: 1.62, h: 0.85, size: 14.5 });

  tbl(s, ['Finished', 'Not started'], [
    ['Named-account qualification across Saudi Arabia and Qatar, with capacities and entry theses', 'Any operator conversation'],
    ['Disqualified accounts that look addressable and are not — dry-cooled, seawater, regulators', 'Any data-sharing discussion'],
    ['Tariffs verified against published schedules rather than assumed', 'Any pilot or paid diagnostic'],
    ['Pricing and route to market designed through integrators, ESCOs and contractors', 'Any revenue'],
  ], [7.6, 4.3], { y: 2.52, rowH: 0.50, size: 12.5 });

  s.addText([
    { text: 'The plan: ', options: { bold: true } },
    { text: '30 structured conversations in 90 days — 10 operators, 8 controls and water integrators, 6 ESCOs, 6 consultants. Kill gate: fewer than 15 conversations and 3 data-sharing discussions by 15 September and we narrow the segment or stop.', options: {} },
  ], { x: M, y: 5.18, w: CW, h: 0.72, fontFace: FONT, fontSize: 13.5, color: INK, valign: 'top', lineSpacing: 19 });

  pullquote(s, 'One question decides whether this business exists, and we wrote it down so we cannot quietly stop asking it: what is your current cycles setpoint, and what set it?', { y: 6.02, h: 0.76, bold: true, size: 13.5 });
}

// ==================================================  15. TEAM & ASK ====
{
  const s = slide('Team and ask', 'Three energy engineers, all full-time');
  tbl(s, ['', 'Position', 'Contact'], [
    ['Engr. Furqan Shakeel', 'Founder & CTO', 'engr.furqan.shakeel@gmail.com · linkedin.com/in/furqan-shakeel'],
    ['Engr. Damia Baig', 'Co-founder & CEO', 'baigdamia@gmail.com · linkedin.com/in/damia-baig'],
    ['Engr. Muhammad Ahsan', 'Co-founder & Head of Commercial Development', 'muhammadahsan4203@gmail.com · linkedin.com/in/-m-ahsan'],
  ], [3.1, 3.5, 5.3], { y: 1.75, rowH: 0.44, size: 12 });

  body(s, 'One founder owns the physics core, the controller and the validation programme. Two own customer development. That ratio is deliberate: the technical risk is largely retired — the evidence package is built, public and reproducible — and the binding risk from here is traction velocity.', { y: 3.55, h: 1.0, size: 14.5 });

  s.addText([
    { text: 'The ask:  ', options: { bold: true } },
    { text: 'a Cohort 2 place; lab access for the TRL 4 programme above; and introductions to Saudi and Qatari district-cooling and industrial-cooling operators through the DTV corporate partner network.', options: {} },
  ], { x: M, y: 4.62, w: CW, h: 0.9, fontFace: FONT, fontSize: 15, color: INK, valign: 'top', lineSpacing: 23 });

  pullquote(s, 'Two failed criteria and ten defects we found in our own work. Everything here is reproducible in four commands against a public dataset: github.com/furqan5/mizan', { y: 5.72, h: 0.78, bold: true });
}

// ---------------------------------------------------------------- save ----
fs.mkdirSync(OUT, { recursive: true });
const f = path.join(OUT, 'Furqan_Mizan_Pitch_Deck.pptx');
pptx.writeFile({ fileName: f }).then(() => {
  console.log('wrote', f, (fs.statSync(f).size / 1024).toFixed(0) + ' KB,', n, 'slides');
});
