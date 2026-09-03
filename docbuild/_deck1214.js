// ==============================================  12. DEFENSIBILITY ====
{
  const s = slide('Defensibility', 'Not data volume, not UI, not AI-applied-to-X');
  bullets(s, [
    'Poppe integration with the water-activity coupling that lets chemistry change tower performance at all',
    'Ion-specific speciation at skin temperature, routed per mineral, rather than at bulk',
    'The separation of the economic ceiling from the physical ceiling, which needs both models at once',
    'The calibration library: which fill laws transfer, how fast a characteristic drifts, which mineral binds first on which water',
  ], { y: 1.68, h: 2.15, size: 13.5 });

  body(s, 'A competent generalist reproduces the tower model in weeks. What they do not reproduce is knowing the published fan correlation is in hertz not per cent, that gypsum binds before calcite on Gulf treated effluent, or that the water saving must be discounted for the evaporation the energy optimum adds back. Each came out of the physics, and each changed the answer.', { y: 3.92, h: 1.05, size: 13.5 });

  s.addText([
    { text: 'And no AI contributes to any result in this package. ', options: { bold: true } },
    { text: 'The surrogate is trained against our own physics core, not a plant, and is excluded by construction from the chemistry and every safety constraint. The only load-bearing learned component is the scaling-kinetics residual, at TRL 4. We rejected reinforcement learning (no hard-constraint guarantee), chemistry soft-sensing (signal an order of magnitude below the noise floor) and a weather LSTM (numerical weather prediction already exists).', options: { color: MUTED } },
  ], { x: M, y: 4.98, w: CW, h: 1.05, fontFace: FONT, fontSize: 12.5, color: INK, valign: 'top', lineSpacing: 18 });

  pullquote(s, 'We would rather be an energy company that uses machine learning exactly where the physics runs out than an AI company looking for a boiler to point at.', { y: 6.02, h: 0.72, bold: true, size: 13.5 });
}

