// ==================================================  14. TRACTION ====
{
  const s = slide('Traction', 'None. And we did not manufacture any.');
  body(s, 'No letters of intent, no pilot agreements, no completed customer interviews. A letter of intent is easy to obtain from a friendly contact and worth nothing as evidence, and being caught with a solicited one ends the relationship permanently.', { y: 1.62, h: 0.85, size: 14.5 });

  tbl(s, ['Finished', 'Not started'], [
    ['Named-account qualification across Saudi Arabia and Qatar, with capacities and entry theses', 'Any operator conversation'],
    ['Disqualification of accounts that look addressable and are not — dry-cooled, once-through seawater, regulators', 'Any data-sharing discussion'],
    ['Tariffs verified against published schedules rather than assumed', 'Any pilot or paid diagnostic'],
    ['Pricing and route to market designed through integrators, ESCOs and water-treatment contractors', 'Any revenue'],
  ], [7.6, 4.3], { y: 2.62, rowH: 0.52, size: 12.5 });

  s.addText([
    { text: 'The plan: ', options: { bold: true } },
    { text: '30 structured conversations in 90 days — 10 operators, 8 controls and water integrators, 6 ESCOs, 6 consultants. Kill gate: fewer than 15 conversations and 3 data-sharing discussions by 15 September and we narrow the segment or stop.', options: {} },
  ], { x: M, y: 5.05, w: CW, h: 0.7, fontFace: FONT, fontSize: 13.5, color: INK, valign: 'top', lineSpacing: 19 });

  pullquote(s, 'One question decides whether this business exists, and we wrote it down so we cannot quietly stop asking it: what is your current cycles setpoint, and what set it?', { y: 5.88, h: 0.8, bold: true, size: 13.5 });
}

