// Shared house style for the Furqan / Mizan submission documents.
const d = require('docx');
const {
  Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, AlignmentType, HeadingLevel, PageNumber, Footer, Header,
  LevelFormat,
} = d;

// --- page geometry (A4) ----------------------------------------------------
const PAGE_W = 11906, PAGE_H = 16838, MARGIN = 1134;   // 2 cm
const CONTENT = PAGE_W - 2 * MARGIN;                    // 9638 DXA

// --- palette ---------------------------------------------------------------
const INK    = '1A2B33';   // deep slate, body text
const ACCENT = '0E6E6E';   // teal: the balance between energy and water
const MUTED  = '5B6B73';
const RULE   = 'C3CCD1';
const BAND   = 'EDF3F4';   // table header fill
const ZEBRA  = 'F7FAFA';
const PASS   = '1F6B45';
const FAIL   = 'A33227';

const BODY_FONT = 'Cambria';
const HEAD_FONT = 'Cambria';

// --- text helpers ----------------------------------------------------------
// Inline markup understood by every helper below: **bold**, *italic*, `mono`.
function runs(text, base) {
  base = base || {};
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun(Object.assign({ text: text.slice(last, m.index) }, base)));
    const t = m[0];
    if (t.slice(0, 2) === '**') {
      out.push(new TextRun(Object.assign({}, base, { text: t.slice(2, -2), bold: true })));
    } else if (t[0] === '`') {
      out.push(new TextRun(Object.assign({}, base, { text: t.slice(1, -1), font: 'Consolas', size: (base.size || 21) - 2 })));
    } else {
      out.push(new TextRun(Object.assign({}, base, { text: t.slice(1, -1), italics: true })));
    }
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun(Object.assign({ text: text.slice(last) }, base)));
  return out.length ? out : [new TextRun(Object.assign({ text: '' }, base))];
}

function p(text, opts) {
  opts = opts || {};
  return new Paragraph({
    children: runs(text, Object.assign({ font: BODY_FONT, size: opts.size || 21, color: opts.color || INK }, opts.run || {})),
    spacing: { after: opts.after === undefined ? 140 : opts.after, before: opts.before || 0, line: opts.line || 264 },
    alignment: opts.align,
    indent: opts.indent,
    keepNext: opts.keepNext,
  });
}

function h1(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: HEAD_FONT, size: 30, bold: true, color: INK })],
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 380, after: 170 },
    keepNext: true,
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 6 } },
  });
}

function h2(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: HEAD_FONT, size: 24, bold: true, color: ACCENT })],
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 120 },
    keepNext: true,
  });
}

function h3(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: HEAD_FONT, size: 22, bold: true, color: INK })],
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 230, after: 100 },
    keepNext: true,
  });
}

// A pulled-out statement: the wording to paste straight into the form field.
function quote(text) {
  return new Paragraph({
    children: runs(text, { font: BODY_FONT, size: 21, color: INK }),
    spacing: { before: 130, after: 160, line: 264 },
    indent: { left: 340 },
    border: { left: { style: BorderStyle.SINGLE, size: 14, color: ACCENT, space: 12 } },
  });
}

function bullet(text, level) {
  return new Paragraph({
    children: runs(text, { font: BODY_FONT, size: 21, color: INK }),
    numbering: { reference: 'bullets', level: level || 0 },
    spacing: { after: 80, line: 264 },
  });
}

function numbered(text, level) {
  return new Paragraph({
    children: runs(text, { font: BODY_FONT, size: 21, color: INK }),
    numbering: { reference: 'numbers', level: level || 0 },
    spacing: { after: 80, line: 264 },
  });
}

function note(text) {
  return new Paragraph({
    children: runs(text, { font: BODY_FONT, size: 19, color: MUTED, italics: true }),
    spacing: { before: 110, after: 170, line: 252 },
    indent: { left: 200 },
  });
}

function spacer(h) {
  return new Paragraph({ text: '', spacing: { after: h === undefined ? 120 : h } });
}

function rule() {
  return new Paragraph({
    text: '',
    spacing: { before: 60, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 2 } },
  });
}

// --- tables ----------------------------------------------------------------
const NO_B = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };

function cell(text, w, o) {
  o = o || {};
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
    margins: { top: 70, bottom: 70, left: 110, right: 110 },
    verticalAlign: d.VerticalAlign.CENTER,
    columnSpan: o.span,
    borders: {
      top: NO_B,
      bottom: { style: BorderStyle.SINGLE, size: o.head ? 8 : 3, color: o.head ? ACCENT : RULE },
      left: NO_B, right: NO_B,
    },
    children: [new Paragraph({
      children: runs(String(text), { font: BODY_FONT, size: o.size || 19, bold: !!(o.head || o.bold), color: o.color || INK }),
      alignment: o.align || AlignmentType.LEFT,
      spacing: { after: 0, line: 240 },
    })],
  });
}

// header: array of strings (or null for no header row). body: array of arrays.
// widths: DXA per column, summing to CONTENT. opts.align: array of 'L'|'C'|'R'.
function table(header, body, w, o) {
  o = o || {};
  const A = { L: AlignmentType.LEFT, C: AlignmentType.CENTER, R: AlignmentType.RIGHT };
  const al = (o.align || []).map(function (x) { return A[x] || AlignmentType.LEFT; });
  const rows = [];
  if (header) {
    rows.push(new TableRow({
      tableHeader: true,
      children: header.map(function (t, i) {
        return cell(t, w[i], { head: true, fill: BAND, align: al[i], size: o.size || 19 });
      }),
    }));
  }
  body.forEach(function (r, ri) {
    rows.push(new TableRow({
      children: r.map(function (t, i) {
        return cell(t, w[i], {
          align: al[i], size: o.size || 19,
          fill: o.zebra && ri % 2 === 1 ? ZEBRA : undefined,
          bold: o.boldRows ? o.boldRows.indexOf(ri) >= 0 : false,
        });
      }),
    }));
  });
  return new Table({
    rows,
    columnWidths: w,
    width: { size: w.reduce(function (a, b) { return a + b; }, 0), type: WidthType.DXA },
    layout: d.TableLayoutType.FIXED,
  });
}

// Split the content width by a weights array.
function widths(weights) {
  const tot = weights.reduce(function (a, b) { return a + b; }, 0);
  const w = weights.map(function (x) { return Math.floor((CONTENT * x) / tot); });
  w[w.length - 1] += CONTENT - w.reduce(function (a, b) { return a + b; }, 0);
  return w;
}

// --- document chrome -------------------------------------------------------
function footer(docTitle) {
  return new Footer({
    children: [new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 8 } },
      tabStops: [{ type: d.TabStopType.RIGHT, position: CONTENT }],
      children: [
        new TextRun({ text: docTitle, font: BODY_FONT, size: 16, color: MUTED }),
        new TextRun({ text: '\t', font: BODY_FONT, size: 16 }),
        new TextRun({ children: ['Page ', PageNumber.CURRENT, ' of ', PageNumber.TOTAL_PAGES], font: BODY_FONT, size: 16, color: MUTED }),
      ],
    })],
  });
}

function pageHeader(text) {
  return new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      spacing: { after: 40 },
      children: [new TextRun({ text, font: BODY_FONT, size: 16, color: MUTED, characterSpacing: 20 })],
    })],
  });
}

const NUMBERING = {
  config: [
    {
      reference: 'bullets',
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: '—', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 220 } }, run: { color: ACCENT, font: BODY_FONT } } },
        { level: 1, format: LevelFormat.BULLET, text: '·', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 780, hanging: 220 } }, run: { color: ACCENT, font: BODY_FONT } } },
      ],
    },
    {
      reference: 'numbers',
      levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 400, hanging: 260 } }, run: { color: ACCENT, bold: true, font: BODY_FONT } } },
      ],
    },
  ],
};

function sectionProps(docTitle, headerText) {
  return {
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: 1300, bottom: 1200, left: MARGIN, right: MARGIN, header: 620, footer: 560 },
      },
    },
    headers: { default: pageHeader(headerText) },
    footers: { default: footer(docTitle) },
  };
}

// Cover block at the top of every document.
function cover(o) {
  const out = [
    new Paragraph({
      spacing: { after: 60 },
      children: [new TextRun({ text: 'FURQAN', font: HEAD_FONT, size: 34, bold: true, color: INK, characterSpacing: 90 })],
    }),
    new Paragraph({
      spacing: { after: 40 },
      children: [new TextRun({ text: 'The criterion for energy.', font: BODY_FONT, size: 20, italics: true, color: ACCENT })],
    }),
    new Paragraph({
      spacing: { after: 260 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 10 } },
      children: [new TextRun({
        text: 'Deep physics and physics-informed AI for hard energy infrastructure — we separate what is measured from what is merely modelled.',
        font: BODY_FONT, size: 18, color: MUTED })],
    }),
  ];
  if (o.kicker) {
    out.push(new Paragraph({
      spacing: { after: 90 },
      children: [new TextRun({ text: o.kicker, font: BODY_FONT, size: 18, color: ACCENT, bold: true, characterSpacing: 40 })],
    }));
  }
  out.push(new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text: o.title, font: HEAD_FONT, size: 40, bold: true, color: INK })],
  }));
  out.push(new Paragraph({
    spacing: { after: 300 },
    children: [new TextRun({ text: o.subtitle, font: BODY_FONT, size: 22, color: MUTED })],
  }));
  return out;
}

module.exports = {
  d, PAGE_W, PAGE_H, MARGIN, CONTENT, INK, ACCENT, MUTED, RULE, BAND, PASS, FAIL,
  BODY_FONT, HEAD_FONT, p, h1, h2, h3, quote, bullet, numbered, note, spacer, rule,
  table, widths, cell, sectionProps, cover, NUMBERING, runs,
  Paragraph, TextRun, AlignmentType, BorderStyle, PageBreak: d.PageBreak,
};
