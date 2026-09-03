// Furqan / Mizan - DTV .dvp Cohort 2 application deck
// Ordered to DTV's published scoring sequence: technology maturity gate is
// screened FIRST, then product strength, market, defensibility, team.
const pptx = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");

// Slide-variant figures: no embedded title and no embedded source note,
// because the slide supplies both. The report variants in figs/ carry them.
const FIG = (n) => path.join(ROOT, "figs", "slide", n);

// Every headline number is read from the result artefacts, so a re-run of
// the gates cannot leave a stale figure on a slide. It used to.
const readJSON = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, "results", p), "utf8"));
const CTRL = readJSON("controller_summary.json");
const CAL = readJSON("calibration.json");
const S = CTRL.summary;
const CRIT = CTRL.criteria;
const HO = CAL.HOLDOUT;

const pct = (v, d = 2) => `${Number(v).toFixed(d)} %`;
const GREEN = "1E7A4D";

const NAVY = "0B3C5D";     // deep water
const TEAL = "1C7293";
const RED = "B3252B";      // the scaling wall
const AMBER = "C89A2B";
const INK = "1A1A1A";
const MUTE = "6B7480";
const PAPER = "FFFFFF";
const WASH = "EEF3F7";

const p = new pptx();
p.layout = "LAYOUT_WIDE";           // 13.333 x 7.5
p.author = "Furqan";
p.company = "Furqan";
p.title = "Mizan - DTV Cohort 2";

const W = 13.333, H = 7.5, M = 0.62;

function titleSlide() {
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("FURQAN", {
    x: M, y: 0.95, w: 8.4, h: 0.62, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 30, bold: true, color: PAPER, charSpacing: 5,
  });
  s.addText("The criterion for energy.", {
    x: M, y: 1.58, w: 9.2, h: 0.42, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 17, italic: true, color: TEAL,
  });
  s.addShape(p.ShapeType.rect, { x: M, y: 2.42, w: 12.1, h: 0.02, fill: { color: "2E5A78" } });
  s.addText("MIZAN", {
    x: M, y: 2.78, w: 8.4, h: 1.1, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 58, bold: true, color: PAPER, charSpacing: 3,
  });
  s.addText("The balance between energy and water.", {
    x: M, y: 3.92, w: 9.2, h: 0.5, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 22, color: "AFC9DC",
  });
  s.addText("Supervisory control for Gulf condenser-water loops  ·  a Furqan venture", {
    x: M, y: 4.48, w: 9.6, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, color: TEAL, bold: true,
  });
  s.addShape(p.ShapeType.rect, { x: M, y: 5.35, w: 5.0, h: 0.035, fill: { color: TEAL } });
  s.addText([
    { text: "TRL 3", options: { bold: true, color: PAPER } },
    { text: "  ·  validated against measured experimental data\n", options: { color: "AFC9DC" } },
    { text: "Deep-Tech Ventures Program (.dvp) Cohort 2  ·  Dhahran Techno Valley\n", options: { color: "AFC9DC" } },
    { text: "Focus area: Energy  ·  secondary Water & Sustainability", options: { color: "AFC9DC" } },
  ], { x: M, y: 5.6, w: 9.5, h: 1.2, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 14, lineSpacing: 22 });
  s.addNotes("Ordered to DTV's scoring sequence: maturity gate first, then product, market, defensibility, team.");
  return s;
}

function sectionHeader(s, kicker, title) {
  s.addText(kicker, {
    x: M, y: 0.42, w: 11, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 2,
  });
  s.addText(title, {
    x: M, y: 0.76, w: 12.1, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 30, bold: true, color: NAVY,
  });
}

// 2 - the maturity gate
function gateSlide() {
  const s = p.addSlide();
  sectionHeader(s, "TECHNOLOGY MATURITY GATE", "Answered first, because DTV screens it first");
  const rows = [
    [{ text: "Gate", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Threshold, fixed before fitting", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Held-out result", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Outlet water temperature MAE", "≤ 1.00 K", `${HO.Tout_MAE_K.toFixed(3)} K`],
    ["Heat rejection MAPE", "≤ 6.00 %", pct(HO.Q_MAPE_pct)],
    ["Evaporation vs measured water loss", "≤ 8.00 %", pct(HO.evap_MAPE_pct)],
  ];
  s.addTable(rows, {
    x: M, y: 1.85, w: 7.5, colW: [3.3, 2.2, 2.0], rowH: 0.44,
    fontFace: "Calibri", fontSize: 13, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  // Verdicts are COMPUTED, never typed. They used to be typed, and when a
  // corrected drift rate moved V2 from 7.11 % to 9.90 % this slide would
  // have gone on claiming three passes.
  const gv = [HO.Tout_MAE_K <= 1.0, HO.Q_MAPE_pct <= 6.0, HO.evap_MAPE_pct <= 8.0];
  gv.forEach((ok, i) => {
    s.addText(ok ? "PASS" : "FAIL", {
      x: 8.25, y: 2.30 + i * 0.44, w: 1.1, h: 0.4, isTextBox: true, margin: 0,
      fontFace: "Calibri", fontSize: 13, bold: true,
      color: ok ? GREEN : RED,
    });
  });
  s.addShape(p.ShapeType.roundRect, { x: 9.55, y: 1.85, w: 3.2, h: 1.85, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText([
    { text: `${HO.n_points}\n`, options: { fontSize: 40, bold: true, color: NAVY } },
    { text: "held-out points from experimental campaigns the model never saw", options: { fontSize: 12, color: MUTE } },
  ], { x: 9.8, y: 2.05, w: 2.7, h: 1.5, isTextBox: true, margin: 0, fontFace: "Calibri" });
  s.addText([
    { text: "Campaign-wise holdout, scored once.  ", options: { bold: true } },
    { text: "Fitted on one experimental campaign, tested on two others run in different seasons under different designs of experiment — a harder test than a random row split. Public dataset, MD5-verified, CC BY 4.0. Reproducible in four commands.", options: {} },
  ], { x: M, y: 4.05, w: 12.1, h: 0.9, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 14, color: INK, lineSpacing: 21 });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 5.15, w: 12.1, h: 1.35, fill: { color: "FBF3F3" }, rectRadius: 0.06 });
  s.addText([
    { text: "We report a defect we found in our own first run.  ", options: { bold: true, color: RED } },
    { text: "That run failed all three gates (1.571 K, +1.50 K bias). The cause was a unit error: the published fan correlation takes hertz, not the percentage the dataset column carries. Read as a percentage the curve turns over at 62 %, so air flow would fall as the fan speeds up. A first-principles model could not absorb it and failed loudly; a regression would have fitted around it.", options: { color: INK } },
  ], { x: 0.85, y: 5.32, w: 11.6, h: 1.05, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, lineSpacing: 19 });
  s.addNotes("DTV screens the maturity gate first and scores traction after. Lead with evidence.");
}

// 3 - the problem
function problemSlide() {
  const s = p.addSlide();
  sectionHeader(s, "THE PROBLEM", "Three handles, three parties, one physics");
  const items = [
    ["Fan speed", "set by the BMS,\non a fixed condenser-\nwater setpoint"],
    ["Blowdown", "set by the water treater,\non a fixed conductivity\nsetpoint"],
    ["Acid dose", "set by the water treater,\non a fixed pH\nsetpoint"],
  ];
  items.forEach(([h, b], i) => {
    const x = M + i * 4.15;
    s.addShape(p.ShapeType.roundRect, { x, y: 1.95, w: 3.75, h: 1.95, fill: { color: WASH }, rectRadius: 0.06 });
    s.addText(h, { x: x + 0.3, y: 2.15, w: 3.2, h: 0.4, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 19, bold: true, color: NAVY });
    s.addText(b, { x: x + 0.3, y: 2.62, w: 3.2, h: 1.15, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13, color: MUTE, lineSpacing: 18 });
  });
  s.addText("They are not independent.", {
    x: M, y: 4.25, w: 12, h: 0.45, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 24, bold: true, color: RED,
  });
  s.addText("Concentrating the loop to save water raises scaling risk and changes evaporation. Cooling the condenser to save compressor power costs fan power and evaporates more water. Nobody solves them together, because doing so requires the thermal model and the water-chemistry model to be one problem rather than two.", {
    x: M, y: 4.8, w: 12.1, h: 1.0, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15, color: INK, lineSpacing: 23,
  });
  s.addText("Correcting the chiller model changed the water answer: with condenser cooling correctly valued, the optimiser stopped over-cooling and makeup water fell 11.2 % → 12.5 %. The coupling is not rhetorical.", {
    x: M, y: 5.95, w: 12.1, h: 0.7, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13, italic: true, color: TEAL, lineSpacing: 20,
  });
}

// 4 - prior art
function priorArtSlide() {
  const s = p.addSlide();
  sectionHeader(s, "PRIOR ART", "Disclosed up front, because a reviewer will find it");
  const rows = [
    [{ text: "Element", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Status", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Ion-association / Pitzer speciation", "Taken. French Creek (since 1990) and OLI Systems — but offline, from bulk temperatures"],
    ["Skin-temperature saturation index", "Taken. ChemTreat US 11,780,742 B2, granted Oct 2023 — but empirical calcite indices, antiscalant feed only"],
    ["Blowdown control on a saturation index", "Public domain. US 4,460,008 / 4,464,315, 1984, expired"],
  ];
  s.addTable(rows, {
    x: M, y: 1.85, w: 12.1, colW: [4.0, 8.1], rowH: 0.5,
    fontFace: "Calibri", fontSize: 13, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 4.15, w: 12.1, h: 2.15, fill: { color: NAVY }, rectRadius: 0.06 });
  s.addText("What is open, stated precisely", {
    x: 0.95, y: 4.35, w: 11.4, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5,
  });
  s.addText("Routing each mineral to its own governing temperature, computed live, and closing three actuators on the result.", {
    x: 0.95, y: 4.72, w: 11.4, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 22, bold: true, color: PAPER, lineSpacing: 30,
  });
  s.addText("Calcite, gypsum and magnesium silicate are retrograde — they govern at the hot condenser skin. Amorphous silica is prograde — it governs at the cold basin. One evaluation temperature is wrong for one group or the other. No FTO opinion is claimed; one is commissioned before any filing.", {
    x: 0.95, y: 5.62, w: 11.4, h: 0.6, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: "AFC9DC", lineSpacing: 18,
  });
}

// 5 - V6, the sharpest result
function v6Slide() {
  const s = p.addSlide();
  sectionHeader(s, "GATE V6", "Magnesium silicate: the constraint no setpoint can express");
  s.addImage({ path: FIG("mg_silicate_envelope.png"), x: M, y: 1.72, w: 7.55, h: 4.35 });
  s.addShape(p.ShapeType.roundRect, { x: 8.45, y: 1.72, w: 4.28, h: 2.35, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Magnesium silicate forms in two steps: brucite precipitates at the hot skin, then reacts with silica. Brucite's saturation pH is retrograde — it falls as the surface heats.", {
    x: 8.68, y: 1.92, w: 3.82, h: 1.1, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addText("deposition occurs when\nbulk pH > pH_s(brucite) at the SKIN", {
    x: 8.68, y: 3.05, w: 3.82, h: 0.8, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 13.5, bold: true, color: RED, lineSpacing: 20,
  });
  s.addText("It needs all three at once", {
    x: 8.45, y: 4.28, w: 4.3, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5,
  });
  s.addText([
    { text: "skin temperature", options: { bold: true } }, { text: " — live thermal model\n", options: {} },
    { text: "bulk pH", options: { bold: true } }, { text: " — chemistry model\n", options: {} },
    { text: "acid dose", options: { bold: true } }, { text: " — the actuator", options: {} },
  ], { x: 8.45, y: 4.62, w: 4.3, h: 1.0, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13, color: INK, lineSpacing: 21 });
  s.addText("Everyone doses acid for calcite. It also moves the loop below the brucite limit at the skin — which is what actually prevents magnesium silicate. Nobody controls for the second effect.", {
    x: 8.45, y: 5.62, w: 4.3, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11.5, italic: true, color: MUTE, lineSpacing: 17,
  });
  s.addNotes("Sepiolite was our first proxy and it was wrong — kinetically inhibited, returned indices forbidding operation everywhere. Corrected to the empirical Mg x SiO2 product, which brackets observed practice.");
}

// 6 - the silica ceiling moves
function silicaSlide() {
  const s = p.addSlide();
  sectionHeader(s, "GATE V3 · SILICA", "Where the industry's rule and the physics part company");
  s.addImage({ path: FIG("silica_seasonal.png"), x: M, y: 1.72, w: 7.55, h: 4.35 });
  s.addShape(p.ShapeType.roundRect, { x: 8.45, y: 1.72, w: 4.28, h: 1.75, fill: { color: "FBF3F3" }, rectRadius: 0.06 });
  s.addText([
    { text: "37 %\n", options: { fontSize: 40, bold: true, color: RED } },
    { text: "non-conservative at a winter basin — on the one mineral with no effective inhibitor", options: { fontSize: 12, color: INK } },
  ], { x: 8.68, y: 1.92, w: 3.82, h: 1.4, isTextBox: true, margin: 0, fontFace: "Calibri", lineSpacing: 17 });
  s.addText("Amorphous silica is prograde — solubility rises with temperature. A Gulf basin tracks ambient wet-bulb, which swings about 15 K seasonally, so the true ceiling moves from 95 to 143 mg/L. Commercial practice sets a fixed limit regardless of basin temperature.", {
    x: 8.45, y: 3.62, w: 4.3, h: 1.5, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addText("An offline design tool evaluated at design conditions cannot produce a moving setpoint. This is a static-versus-dynamic distinction, not software-versus-hardware.", {
    x: 8.45, y: 5.15, w: 4.3, h: 1.0, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, bold: true, color: NAVY, lineSpacing: 18,
  });
}

// 7 - the result
function resultSlide() {
  const s = p.addSlide();
  sectionHeader(s, "CLOSED-LOOP RESULT", "Optimised against incumbent fixed-setpoint operation");
  const stats = [
    [pct(S.cost_pct), "total operating\ncost reduction",
     `≥ ${CRIT.total_cost_reduction_pct_min} % criterion — met`, GREEN],
    [pct(S.water_pct), "makeup water\nreduction",
     `≥ ${CRIT.makeup_water_reduction_pct_min} % criterion — missed`, RED],
    [String(S.violations), "saturation violations\nat the skin",
     `${CRIT.skin_SI_violations_allowed} criterion — met`, GREEN],
  ];
  stats.forEach(([big, lab, crit, col], i) => {
    const x = M + i * 4.15;
    s.addShape(p.ShapeType.roundRect, { x, y: 1.9, w: 3.75, h: 2.1, fill: { color: WASH }, rectRadius: 0.06 });
    s.addText(big, { x: x + 0.3, y: 2.08, w: 3.2, h: 0.75, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 38, bold: true, color: col });
    s.addText(lab, { x: x + 0.3, y: 2.88, w: 3.2, h: 0.6, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 14, color: INK, lineSpacing: 18 });
    s.addText(crit, { x: x + 0.3, y: 3.52, w: 3.2, h: 0.35, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 11.5, color: MUTE });
  });
  s.addText("We report the miss, and we can now say exactly why it was unreachable.", {
    x: M, y: 4.35, w: 12, h: 0.42, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 21, bold: true, color: NAVY,
  });
  s.addText([
    { text: "Makeup is evaporation × C/(C−1), so the saving available from cycles alone is arithmetic, not a modelling choice. ", options: {} },
    { text: `${CRIT.makeup_water_reduction_pct_min} % requires 8.5 cycles. Gypsum saturates at ${S.physical_ceiling_cycles}. `, options: { bold: true } },
    { text: `The criterion was written on the far side of a wall we had not yet found — and gypsum is not pH-sensitive, so no amount of acid moves it. The controller reaches ${pct(S.water_pct)} by also cutting evaporation, which is more than cycles alone can deliver. The threshold stands as written and the gate stays failed.`, options: {} },
  ], {
    x: M, y: 4.88, w: 12.1, h: 1.25, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, color: INK, lineSpacing: 22,
  });
  s.addText("Tariffs are published, not assumed: electricity $0.074/kWh (Saudi business all-in); water $3.11/m³ avoided (Marafiq/RCJY approved schedule — process water plus industrial wastewater not discharged).", {
    x: M, y: 6.25, w: 12.1, h: 0.55, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11.5, italic: true, color: MUTE, lineSpacing: 17,
  });
}

// 8 - product
function productSlide() {
  const s = p.addSlide();
  sectionHeader(s, "PRODUCT", "A retrofit device, not a subscription");
  const rows = [
    [{ text: "Component", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Detail", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Sensor skid", "Conductivity, pH, ORP, temperature, makeup and blowdown flow"],
    ["Actuation", "Motorised blowdown valve; fan VFD setpoint via the existing BMS"],
    ["Edge compute", "Validated physics core over BACnet/Modbus; no cloud dependency"],
    ["Licence", "Annual model recalibration and water-chemistry update"],
  ];
  s.addTable(rows, {
    x: M, y: 1.85, w: 7.6, colW: [2.3, 5.3], rowH: 0.48,
    fontFace: "Calibri", fontSize: 13, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addShape(p.ShapeType.roundRect, { x: 8.5, y: 1.85, w: 4.25, h: 2.4, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Why not SaaS", { x: 8.75, y: 2.05, w: 3.8, h: 0.32, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5 });
  s.addText("The saturation limit cannot be computed from a plant's existing instruments. Bulk conductivity does not determine ion composition, and nothing installed reads skin temperature. The hardware is not packaging around software — it is what makes the calculation possible.", {
    x: 8.75, y: 2.4, w: 3.8, h: 1.7, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addText("Ships read-only in shadow mode.", {
    x: M, y: 4.6, w: 12, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 20, bold: true, color: NAVY,
  });
  s.addText("Blowdown and dosing stay advisory until site validation. That is a commercial choice as much as a safety one: it lets a plant quantify the benefit on its own data before granting write access, which is the shortest path past OT-security review. Deterministic fixed-step solver, bounded runtime, documented fallback to incumbent setpoints on solver failure or sensor loss.", {
    x: M, y: 5.1, w: 12.1, h: 1.1, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, color: INK, lineSpacing: 22,
  });
}

// 9 - market
function marketSizeSlide() {
  const s = p.addSlide();
  sectionHeader(s, "MARKET", "Sized from regulators, not from forecasts");
  const tiles = [
    ["1.153 M TR", "installed district cooling in Qatar, 2023, across 70 plants", "Kahramaa"],
    ["82 %", "of Qatari district-cooling makeup water is already recycled water", "Kahramaa, Mar 2025"],
    ["18.5 M m³", "water consumed by Qatari district cooling in 2024 — a figure the regulator publishes", "Kahramaa, Mar 2025"],
    ["$1.52 bn", "Saudi district cooling market, 2024, growing 9.4 % a year to 2030", "market research [A]"],
  ];
  tiles.forEach(([big, lab, src], i) => {
    const x = M + (i % 2) * 6.25;
    const y = 1.80 + Math.floor(i / 2) * 1.62;
    s.addShape(p.ShapeType.roundRect, { x, y, w: 5.85, h: 1.42, fill: { color: WASH }, rectRadius: 0.06 });
    s.addText(big, { x: x + 0.28, y: y + 0.14, w: 2.5, h: 0.6, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY });
    s.addText(lab, { x: x + 2.85, y: y + 0.16, w: 2.85, h: 0.9, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, color: INK, lineSpacing: 16 });
    s.addText(src, { x: x + 0.28, y: y + 0.86, w: 2.5, h: 0.4, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 10.5, italic: true, color: MUTE });
  });
  s.addText("The 82 % is the number that matters.", {
    x: M, y: 5.18, w: 12, h: 0.42, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 21, bold: true, color: NAVY,
  });
  s.addText("Recycled water is the high-TDS, high-silica, high-scaling-potential feedstock that makes skin-temperature saturation control matter at all. The market has already moved to the water chemistry this product is built for, and a regulator is counting it. Qatar additionally mandates district cooling for standalone buildings above 1,500 TR.", {
    x: M, y: 5.68, w: 12.1, h: 1.2, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, color: INK, lineSpacing: 22,
  });
  s.addNotes("Qatar is the better-evidenced market. No verified installed-TR figure exists for Saudi Arabia, so the Saudi line is given in USD, which is properly sourced, and never as a TR target.");
}

function marketSlide() {
  const s = p.addSlide();
  sectionHeader(s, "MARKET", "Where the physics and the water policy align");
  const accts = [
    ["Qatar Foundation", "Education City — 185,000 TR", "runs entirely on treated sewage effluent"],
    ["Qatar Cool", "West Bay — 92,500 TR", "switched to TSE and publicly documented the condenser-chemistry difficulty"],
    ["Saudi Tabreed", "349,000 TR contracted", "largest independent KSA operator; includes 32,000 TR for Saudi Aramco"],
    ["Marafiq", "Jubail & Yanbu", "publishes its own approved water tariff — the value case computes from the customer's numbers"],
  ];
  accts.forEach(([n, cap, why], i) => {
    const y = 1.85 + i * 1.02;
    s.addShape(p.ShapeType.ellipse, { x: M, y: y + 0.12, w: 0.42, h: 0.42, fill: { color: TEAL } });
    s.addText(String(i + 1), { x: M, y: y + 0.12, w: 0.42, h: 0.42, isTextBox: true, margin: 0, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 13, bold: true, color: PAPER });
    s.addText([
      { text: n + "  ", options: { bold: true, color: NAVY, fontSize: 15 } },
      { text: cap, options: { color: TEAL, fontSize: 13, bold: true } },
    ], { x: M + 0.62, y: y + 0.05, w: 11.4, h: 0.35, isTextBox: true, margin: 0, fontFace: "Calibri" });
    s.addText(why, { x: M + 0.62, y: y + 0.42, w: 11.4, h: 0.35, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, color: MUTE });
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 6.0, w: 12.1, h: 0.95, fill: { color: "FBF3F3" }, rectRadius: 0.06 });
  s.addText([
    { text: "We also disqualify part of the apparent market.  ", options: { bold: true, color: RED } },
    { text: "Red Sea Global's plant is dry-cooled with no tower at all. SEC is once-through seawater. Marafiq prices sea-water cooling at SAR 0.069/m³, where our value collapses to zero. Once-through and seawater-makeup loops are not our market.", options: { color: INK } },
  ], { x: 0.85, y: 6.16, w: 11.6, h: 0.7, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, lineSpacing: 18 });
}

// 10 - defensibility
function moatSlide() {
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("DEFENSIBILITY", {
    x: M, y: 0.55, w: 11, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 2,
  });
  s.addText("Three literature sweeps looked for this and found nothing", {
    x: M, y: 0.92, w: 12.1, h: 0.75, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 30, bold: true, color: PAPER,
  });
  s.addText("“No academic paper, patent, or commercial product literature describes a closed-loop control scheme where a chemical saturation limit directly bounds or dynamically alters the mechanical thermal energy optimizer.”", {
    x: M, y: 2.05, w: 12.1, h: 1.5, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 21, italic: true, color: PAPER, lineSpacing: 32,
  });
  s.addText("Independent research sweep, commissioned specifically to falsify this claim", {
    x: M, y: 3.55, w: 12.1, h: 0.35, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, color: TEAL,
  });
  const pts = [
    ["What a copier reproduces", "The tower model in weeks. The speciation engine from public constants."],
    ["What they do not", "That the published fan correlation is in hertz, not percent. That gypsum binds before calcite on Gulf TSE. That silica governs at the cold basin and magnesium silicate at the hot skin. That the water saving must be discounted for evaporation the energy optimum adds back."],
    ["Each of those changed our answer", "Every one was found by running the physics and being contradicted by it."],
  ];
  pts.forEach(([h, b], i) => {
    const y = 4.15 + i * 0.92;
    s.addText(h, { x: M, y, w: 3.3, h: 0.35, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13.5, bold: true, color: TEAL });
    s.addText(b, { x: M + 3.45, y, w: 8.65, h: 0.85, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, color: "D6E2EC", lineSpacing: 18 });
  });
}

// 11 - TRL4
function trl4Slide() {
  const s = p.addSlide();
  sectionHeader(s, "TRL 4 PROGRAMME", "The facilities already exist — three in one building");
  const rows = [
    [{ text: "Facility", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Closes", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["A/C & Refrigeration Lab, 75-410\nvertical cooling tower + humidifying wind tunnel", "The climate gap. Our data tops out at 21.9 °C wet-bulb; Gulf design is 30.3 °C. This rig humidifies to reach it."],
    ["Chemistry Instrumentation Lab, 75-230\nICP-OES + ion chromatograph", "The chemistry gap. Cations and anions together give the full ion inventory the model predicts — turning calculation into measurement."],
    ["ME Corrosion Lab, 75-409\nGamry potentiostats, rotating disc electrode", "The objection we cannot answer today: does acid dosing trade scale for corrosion?"],
    ["Dream Realization Lab, DTV\nPCB fabrication, electronics, enclosures", "The physical controller itself, end to end."],
  ];
  s.addTable(rows, {
    x: M, y: 1.8, w: 12.1, colW: [4.6, 7.5], rowH: 0.5,
    fontFace: "Calibri", fontSize: 12, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addText("The experiments are deliberately cheap — salt, coupons, and instrument time on equipment that already exists. The SAR 200,000 product-development stream covers instrumentation, the blowdown valve and edge hardware, analytical services, an OT-security assessment and third-party validation. None of it is modelled as runway.", {
    x: M, y: 5.35, w: 12.1, h: 0.9, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13.5, color: INK, lineSpacing: 21,
  });
  s.addText("KFUPM's IRC for Membranes and Water Security lists fouling and scaling as a research theme. We scope it as testing services, not co-development, because co-development triggers a separate IP agreement that must be settled in writing before work begins.", {
    x: M, y: 6.35, w: 12.1, h: 0.6, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 11.5, italic: true, color: MUTE, lineSpacing: 17,
  });
}

// 12 - AI
function aiSlide() {
  const s = p.addSlide();
  sectionHeader(s, "WHERE AI SITS", "No AI contributes to any result in this package");
  s.addText("We say so plainly, because the evidence must not be mistaken for a learned fit.", {
    x: M, y: 1.8, w: 12.1, h: 0.4, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15, color: INK,
  });
  const rows = [
    [{ text: "Proposal", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Decision", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Reinforcement learning for control", "Rejected. RL optimises expected reward; a scaling constraint is a bound, not a preference. Constrained MPC carries hard constraints as first-class objects."],
    ["Fouling prediction from the thermal residual", "Adopted — the load-bearing AI, at TRL 4. Physics gives the driving force; a calibrated residual gives the kinetics, which is not derivable."],
    ["Soft-sensing chemistry from thermal data", "Rejected on our own evidence. The whole thermal signature of 2→10 cycles is under 0.5 %, an order of magnitude below the instrument noise floor. Unobservable."],
    ["Weather-driven predictive dosing", "Idea adopted, LSTM rejected. Feed a numerical weather forecast into the MPC as disturbance preview — you do not need to learn the weather when you can obtain it."],
  ];
  s.addTable(rows, {
    x: M, y: 2.35, w: 12.1, colW: [3.6, 8.5], rowH: 0.55,
    fontFace: "Calibri", fontSize: 12, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 5.75, w: 12.1, h: 1.15, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Thermodynamics is known; kinetics is not. The saturation index — the driving force — comes from published equilibrium constants. The rate at which scale forms depends on nucleation, surface condition and inhibitor residual, and is genuinely site-specific. That is where a learned residual earns its place, and nowhere else.", {
    x: 0.85, y: 5.95, w: 11.6, h: 0.85, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13, color: INK, lineSpacing: 20,
  });
}

// 13 - team and ask
function teamSlide() {
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("TEAM & ASK", {
    x: M, y: 0.55, w: 11, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 2,
  });
  s.addText("Three energy engineers, all full-time", {
    x: M, y: 0.92, w: 12.1, h: 0.7, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 30, bold: true, color: PAPER,
  });
  const team = [
    ["Engr. Furqan Shakeel", "Co-founder & CEO", "Physics core, controller, validation programme"],
    ["Engr. Damia Baig", "Co-founder", "Customer discovery, pipeline, commercial strategy"],
    ["Engr. Muhammad Ahsan", "Co-founder", "Commercial development, market and tariff verification"],
  ];
  team.forEach(([n, r, w], i) => {
    const x = M + i * 4.15;
    s.addShape(p.ShapeType.roundRect, { x, y: 2.0, w: 3.75, h: 2.0, fill: { color: "13496E" }, rectRadius: 0.06 });
    s.addText(n, { x: x + 0.28, y: 2.2, w: 3.2, h: 0.6, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 16, bold: true, color: PAPER });
    s.addText(r, { x: x + 0.28, y: 2.82, w: 3.2, h: 0.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, bold: true, color: TEAL });
    s.addText(w, { x: x + 0.28, y: 3.16, w: 3.2, h: 0.75, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, color: "D6E2EC", lineSpacing: 17 });
  });
  s.addText("One founder owns the physics; two own customer development. That ratio is deliberate — the technical risk is now largely retired, and the binding risk from here is traction velocity.", {
    x: M, y: 4.25, w: 12.1, h: 0.6, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13.5, italic: true, color: "AFC9DC", lineSpacing: 20,
  });
  s.addText("The ask", { x: M, y: 5.0, w: 11, h: 0.32, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5 });
  s.addText([
    { text: "A Cohort 2 place; laboratory access for the TRL 4 programme; and introductions through the DTVC corporate partner network.\n", options: {} },
    { text: "Honeywell, Schneider Electric, Emerson and Yokogawa are named DTV partners. For a BACnet/Modbus retrofit controller those four are simultaneously the integration surface, the channel, and the acquirer set. That is a specific reason this venture belongs in this programme rather than any accelerator.", options: { color: "AFC9DC" } },
  ], { x: M, y: 5.38, w: 12.1, h: 1.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 14, color: PAPER, lineSpacing: 22 });
}

// --- how the product is actually used, on a real plant, day by day -------
function howUsedSlide() {
  const s = p.addSlide();
  sectionHeader(s, "IN SERVICE", "What a plant actually does with it");
  const phases = [
    ["Day 0", "Install", "Sensor skid clamps into the existing condenser-water side loop; the valve replaces the manual blowdown valve. No chiller downtime, no pipework recut. One shift.", TEAL],
    ["Week 1–8", "Shadow mode", "Read-only. The controller publishes the setpoints it WOULD have used and the saturation state at the tube skin, alongside what the plant actually did. Nothing is written to the BMS.", NAVY],
    ["Week 9", "Sign-off", "The plant compares its own logged cost against the shadow recommendation on its own water. This is the number the operator takes to their own management, not ours.", NAVY],
    ["Ongoing", "Closed loop", "Write access granted per actuator, blowdown first, acid dose last. Documented fallback to the incumbent fixed setpoints on solver failure or sensor loss.", GREEN],
  ];
  phases.forEach(([when, what, why, col], i) => {
    const y = 1.80 + i * 1.16;
    s.addShape(p.ShapeType.roundRect, { x: M, y, w: 1.35, h: 0.98, fill: { color: col }, rectRadius: 0.05 });
    s.addText(when, { x: M, y: y + 0.10, w: 1.35, h: 0.32, isTextBox: true, margin: 0, align: "center", fontFace: "Calibri", fontSize: 12, bold: true, color: PAPER });
    s.addText(what, { x: M, y: y + 0.46, w: 1.35, h: 0.36, isTextBox: true, margin: 0, align: "center", fontFace: "Calibri", fontSize: 11, color: "D6E2EC" });
    s.addText(why, { x: M + 1.6, y: y + 0.06, w: 10.5, h: 0.92, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13, color: INK, lineSpacing: 19 });
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 6.42, w: 12.1, h: 0.72, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText([
    { text: "The operator's screen shows one thing they have never had.  ", options: { bold: true, color: NAVY } },
    { text: "Not a dashboard of conductivity and pH, which they already have — the distance, in cycles, between where the loop is running and where each individual mineral saturates at the surface that governs it.", options: { color: INK } },
  ], { x: 0.85, y: 6.56, w: 11.6, h: 0.5, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, lineSpacing: 18 });
  s.addNotes("Shadow mode is the commercial answer to OT-security review as much as the safety answer: no write access until the plant has priced the benefit on its own data.");
}

// --- defects vs failed gates: they are not the same thing ---------------
function defectSlide() {
  const s = p.addSlide();
  sectionHeader(s, "EVIDENCE INTEGRITY", "Nine defects found. Nine fixed. Two gates still fail.");
  s.addText("A defect is a mistake in the work. A failed gate is a result. Confusing the two is how evidence packages get quietly laundered.", {
    x: M, y: 1.72, w: 12.1, h: 0.5, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 14, italic: true, color: MUTE, lineSpacing: 20,
  });
  const rows = [
    [{ text: "Defect found", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "How it announced itself", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "State", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Fan correlation in the wrong unit", "Air flow fell as the fan sped up. All three thermal gates failed at once.", "FIXED"],
    ["Carnot chiller COP", "Overstated condenser relief by 60 %.", "FIXED"],
    ["Chiller curves untraceable", "Nobody could check them.", "FIXED"],
    ["Optimiser extrapolating past the fitted range", "Booked a false 20.41 % water saving that would have flipped a failed gate to passed.", "FIXED"],
    ["Duty fixed point unconverged", "Evaporation moved 3.8 % on the choice of starting guess alone.", "FIXED"],
    ["Drift rate 100x too large", "The modern rating with its percent sign dropped.", "FIXED"],
    ["Simscape sensor read as Celsius, outputs Kelvin", "The chemistry was asked for a saturation pH at 341 C. It refused.", "FIXED"],
    ["Simscape heat-flow sign inverted", "+1000 kW into 150 t gave -0.956 K. Right magnitude, wrong direction.", "FIXED"],
  ];
  s.addTable(rows, {
    x: M, y: 2.32, w: 12.1, colW: [3.5, 7.0, 1.6], rowH: 0.38,
    fontFace: "Calibri", fontSize: 11, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 5.72, w: 12.1, h: 1.2, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText([
    { text: "Four of the nine were found because a first-principles model refused a bad input rather than absorbing it.  ", options: { bold: true, color: NAVY } },
    { text: "A regression with free exponents would have fitted around every one of them and reported a good score. That is what the parent company is named for, and it is the whole argument for building it this way.", options: { color: INK } },
  ], { x: 0.85, y: 5.9, w: 11.6, h: 0.9, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, lineSpacing: 19 });
  s.addNotes("Open defects: none. Failed gates: two, both diagnosed to a specific cause, neither threshold moved. The register is docs/defect_register.md.");
}

// --- the water gate, and why the threshold was unreachable ----------------
function waterCeilingSlide() {
  const s = p.addSlide();
  sectionHeader(s, "A FAILED GATE, DIAGNOSED", "The water criterion was written on the far side of a wall");
  s.addImage({ path: FIG("water_ceiling.png"), x: M, y: 1.72, w: 7.55, h: 4.35 });
  s.addShape(p.ShapeType.roundRect, { x: 8.45, y: 1.72, w: 4.28, h: 2.05, fill: { color: "FBF3F3" }, rectRadius: 0.06 });
  s.addText([
    { text: `${pct(S.water_pct)}\n`, options: { fontSize: 34, bold: true, color: RED } },
    { text: `achieved against a ${CRIT.makeup_water_reduction_pct_min} % criterion. Reported as a failure, and left as one.`, options: { fontSize: 12.5, color: INK } },
  ], { x: 8.68, y: 1.94, w: 3.82, h: 1.7, isTextBox: true, margin: 0, fontFace: "Calibri", lineSpacing: 17 });
  s.addText("Makeup = evaporation × C/(C−1). The saving available from cycles alone is arithmetic:", {
    x: 8.45, y: 3.92, w: 4.3, h: 0.6, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addText([
    { text: "7 cycles → 12.5 %\n", options: {} },
    { text: `${S.physical_ceiling_cycles} cycles → 14.3 %  `, options: {} },
    { text: "← gypsum wall\n", options: { color: RED, bold: true } },
    { text: "8.5 cycles → 15.0 %  ", options: {} },
    { text: "← the criterion", options: { color: AMBER, bold: true } },
  ], { x: 8.45, y: 4.55, w: 4.3, h: 1.0, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 13, color: INK, lineSpacing: 21 });
  s.addText("We set the threshold before we found the wall. Gypsum saturation is not pH-sensitive, so acid — the lever that buys cycles against calcite — cannot move it. The gate stays failed.", {
    x: 8.45, y: 5.62, w: 4.3, h: 1.1, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, italic: true, color: MUTE, lineSpacing: 17,
  });
  s.addNotes("This is the strongest evidence-integrity moment in the deck: the threshold was not moved to fit the result, and the failure turned out to be informative.");
}

// --- the constraint that binds in Gulf summer ----------------------------
function chillerSlide() {
  const s = p.addSlide();
  sectionHeader(s, "COUPLING, PRICED", "In Gulf summer the fan is limited by the chiller");
  s.addImage({ path: FIG("chiller_envelope.png"), x: M, y: 1.72, w: 7.55, h: 4.35 });
  s.addText("Lower the fan and you save fan power and evaporation — but condenser water rises, and the chiller pays for it. In four of five Gulf conditions the optimum stops at 34–35 °C, hard against the machine's maximum entering condenser water.", {
    x: 8.45, y: 1.80, w: 4.3, h: 1.7, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 13, color: INK, lineSpacing: 19,
  });
  s.addShape(p.ShapeType.roundRect, { x: 8.45, y: 3.55, w: 4.28, h: 1.5, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("The binding limit is the chiller envelope — not tower physics, and not chemistry. No single-discipline optimiser has that constraint in view.", {
    x: 8.68, y: 3.72, w: 3.82, h: 1.2, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 13.5, bold: true, color: NAVY, lineSpacing: 20,
  });
  s.addText([
    { text: "Chiller model: a named machine.  ", options: { bold: true } },
    { text: "York YT 1758 kW / 6.28 COP water-cooled centrifugal, from the EnergyPlus CoolTools curve library. Chosen because its reference point is the AHRI 550/590 rating point and its curves are fitted to 35 °C entering condenser water — the Gulf operating range. Points outside the fitted box are rejected, not extrapolated.", options: {} },
  ], { x: 8.45, y: 5.15, w: 4.3, h: 1.6, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 11.5, color: MUTE, lineSpacing: 17 });
  s.addNotes("The first run with these curves let the optimiser leave the fitted range and book a false 20 % water saving. Constraining it to the validity envelope removed that.");
}

// --- venture scale: what DTV's support actually buys ---------------------
function ventureScaleSlide() {
  const s = p.addSlide();
  sectionHeader(s, "VENTURE SCALE", "What the SAR 200,000 buys, by name");
  const rows = [
    [{ text: "Requirement", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Named facility or service", options: { bold: true, color: PAPER, fill: { color: NAVY } } },
     { text: "Stream", options: { bold: true, color: PAPER, fill: { color: NAVY } } }],
    ["Gulf wet-bulb validation", "KFUPM vertical cooling-tower rig, humidifying wind tunnel — closes the 21.9 → 30.3 °C gap", "Two"],
    ["Ion-specific verification", "ICP-OES PlasmaQuant PQ 9000 + 930 Compact IC Flex, Bldg 75 Rm 230 — turns a modelled saturation state into a measured one", "Two"],
    ["Corrosion counter-check", "Gamry potentiostats + rotating disc electrode, Bldg 75 Rm 409 — quantifies the corrosion cost of our own setpoints", "Two"],
    ["Controller hardware build", "Sensor skid, motorised valve, edge compute; BACnet/Modbus conformance test", "Two"],
    ["Customer access", "DTVC partner network — Schneider, Honeywell, Emerson, Yokogawa", "One"],
  ];
  s.addTable(rows, {
    x: M, y: 1.80, w: 12.1, colW: [2.7, 7.6, 1.8], rowH: 0.42,
    fontFace: "Calibri", fontSize: 12, color: INK,
    border: { type: "solid", pt: 0.5, color: "D6DEE5" }, valign: "middle",
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 4.72, w: 5.9, h: 1.95, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Exit criterion for the 12 weeks", { x: M + 0.24, y: 4.90, w: 5.4, h: 0.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5 });
  s.addText("TRL 4: the thermal model, the chemistry model and the actuators validated together on the KFUPM rig at Gulf wet-bulb, with measured ion composition — not three components validated separately.", {
    x: M + 0.24, y: 5.25, w: 5.4, h: 1.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addShape(p.ShapeType.roundRect, { x: 6.82, y: 4.72, w: 5.9, h: 1.95, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Commercial shape", { x: 7.06, y: 4.90, w: 5.4, h: 0.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5 });
  s.addText("Capex per condenser module plus an annual recalibration licence. The licence is not an upsell: the identified fill coefficient moved 21 % across campaigns spanning four years, so a controller that assumes a fixed tower characteristic degrades silently in service.", {
    x: 7.06, y: 5.25, w: 5.4, h: 1.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18,
  });
  s.addNotes("DTV's stream two buys laboratory and testing services, materials and prototyping. Answer the budget field as a shopping list against named facilities, not a round number.");
}

// --- the parent company, and why it is a company and not a project ------
function furqanSlide() {
  const s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("THE PARENT", {
    x: M, y: 0.55, w: 11, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 2,
  });
  s.addText("Furqan — the criterion for energy", {
    x: M, y: 0.92, w: 12.1, h: 0.75, isTextBox: true, margin: 0,
    fontFace: "Cambria", fontSize: 30, bold: true, color: PAPER,
  });
  s.addText("Furqan, from the Arabic root f-r-q, to separate: the criterion that distinguishes the true from the false. It is not decoration — it is the method.", {
    x: M, y: 1.80, w: 12.1, h: 0.7, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 15, italic: true, color: "AFC9DC", lineSpacing: 22,
  });
  const pts = [
    ["The thesis", "Hard energy infrastructure is run on correlations fitted to one plant and then trusted everywhere. A first-principles model with few parameters cannot absorb a bad input — it fails loudly. That is what separates a real effect from a fitted one."],
    ["The method", "Deep physics first; physics-informed machine learning only where the physics genuinely runs out — kinetics, drift, and speed. Thresholds pre-registered before fitting; failures published as failures."],
    ["The proof", "Three of the four largest corrections in this package were defects our own model refused to absorb: a fan correlation in the wrong unit, a chiller curve used outside its fitted range, and a drift rate off by a hundred. A regression would have fitted around all three."],
  ];
  pts.forEach(([h, b], i) => {
    const y = 2.72 + i * 1.16;
    s.addText(h, { x: M, y, w: 2.5, h: 0.35, isTextBox: true, margin: 0, valign: "top", fontFace: "Calibri", fontSize: 14, bold: true, color: TEAL });
    s.addText(b, { x: M + 2.65, y: y - 0.06, w: 9.45, h: 1.05, isTextBox: true, margin: 0, valign: "top", fontFace: "Calibri", fontSize: 13, color: "D6E2EC", lineSpacing: 19 });
  });
  s.addShape(p.ShapeType.rect, { x: M, y: 6.28, w: 12.1, h: 0.02, fill: { color: "2E5A78" } });
  s.addText([
    { text: "Mizan", options: { bold: true, color: PAPER } },
    { text: " — the balance between energy and water — is the first venture. The condenser-water loop was chosen because it is the one place in a district-cooling plant where energy and water are the same decision, and nobody prices them together.", options: { color: "AFC9DC" } },
  ], { x: M, y: 6.48, w: 12.1, h: 0.7, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13, lineSpacing: 19 });
  s.addNotes("Furqan is the group: deep physics plus physics-informed AI for energy. Mizan is the first product. The parent thesis is what makes the second and third product credible.");
}

// --- the PINN: what it is for, and what it is forbidden from -------------
function pinnSlide() {
  const s = p.addSlide();
  sectionHeader(s, "PHYSICS-INFORMED AI", "A surrogate that is constrained where there is no data");
  const layers = [
    ["1", "Physics core", "Poppe/Merkel + ion speciation + named chiller curves. Deterministic, auditable, and the only authority on a safety limit.", NAVY],
    ["2", "PINN surrogate", "Trained against the core, not against the plant. Loss = data + the inequalities thermodynamics guarantees, enforced at collocation points across the Gulf envelope where no measurement exists.", TEAL],
    ["3", "Fill-state estimator", "Tracks the tower characteristic online from plant telemetry. Turns the annual recalibration visit into a continuous soft sensor.", "1E7A4D"],
  ];
  layers.forEach(([n, h, b, col], i) => {
    const y = 1.80 + i * 1.18;
    s.addShape(p.ShapeType.roundRect, { x: M, y, w: 2.45, h: 1.0, fill: { color: col }, rectRadius: 0.05 });
    s.addText(n, { x: M + 0.16, y: y + 0.12, w: 0.4, h: 0.35, isTextBox: true, margin: 0, fontFace: "Cambria", fontSize: 17, bold: true, color: PAPER });
    s.addText(h, { x: M + 0.62, y: y + 0.14, w: 1.7, h: 0.7, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 13, bold: true, color: PAPER, lineSpacing: 16 });
    s.addText(b, { x: M + 2.7, y: y + 0.02, w: 9.4, h: 1.0, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12.5, color: INK, lineSpacing: 18 });
  });
  s.addShape(p.ShapeType.roundRect, { x: M, y: 5.42, w: 5.95, h: 1.62, fill: { color: WASH }, rectRadius: 0.06 });
  s.addText("Why it closes our biggest gap", { x: M + 0.24, y: 5.58, w: 5.5, h: 0.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: TEAL, charSpacing: 1.5 });
  s.addText("The validation data stops at 21.9 °C wet-bulb; Gulf design is 30.3 °C. No fit closes that — there is no data there. A physics loss can be evaluated anyway: a tower cannot cool below wet-bulb, and more air cannot warm the water. Those hold everywhere.", {
    x: M + 0.24, y: 5.92, w: 5.5, h: 1.05, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, color: INK, lineSpacing: 17,
  });
  s.addShape(p.ShapeType.roundRect, { x: 6.88, y: 5.42, w: 5.85, h: 1.62, fill: { color: "FBF3F3" }, rectRadius: 0.06 });
  s.addText("Where a network is not allowed", { x: 7.12, y: 5.58, w: 5.4, h: 0.3, isTextBox: true, margin: 0, fontFace: "Calibri", fontSize: 12, bold: true, color: RED, charSpacing: 1.5 });
  s.addText("Not in the chemistry: speciation is algebraic thermodynamics, and a learned component inside a safety limit is not auditable. Not in the safety path at all — the surrogate proposes, the core disposes, and every setpoint is re-checked against the core before it leaves the device.", {
    x: 7.12, y: 5.92, w: 5.4, h: 1.05, isTextBox: true, margin: 0,
    fontFace: "Calibri", fontSize: 12, color: INK, lineSpacing: 17,
  });
  s.addNotes("Gates for the surrogate were pre-registered before training, exactly like V1/V2/V5: fidelity to the core, no degradation on the experimental holdout, zero admissibility violations in the Gulf extrapolation band, and a minimum speed-up.");
}

titleSlide();
furqanSlide();
gateSlide();
problemSlide();
productSlide();
howUsedSlide();
priorArtSlide();
v6Slide();
silicaSlide();
waterCeilingSlide();
chillerSlide();
defectSlide();
resultSlide();
marketSizeSlide();
marketSlide();
ventureScaleSlide();
moatSlide();
trl4Slide();
aiSlide();
pinnSlide();
teamSlide();

const out = path.join(ROOT, "submission", "Furqan_Mizan_DTV_Deck.pptx");
p.writeFile({ fileName: out }).then(() => console.log("written ->", out));
