// ----------------------------------------- 11. MATLAB / SIMULINK ----
A(h1('11. Independent re-implementation in MATLAB and Simulink'));

A(p('A single implementation of a model is a single point of failure. Every result in sections 4 to 10 comes from one Python codebase, and a coding error inside it would be invisible to every gate in this document, because each gate tests the model against data rather than against another model. The whole package was therefore re-implemented a second time, independently, in MATLAB and Simulink, and the two were cross-validated against each other.'));

A(h2('The cross-implementation gate'));

A(p('Thresholds were fixed before the comparison was run, in the same discipline used for the physical gates, and set deliberately tight: the outlet-temperature tolerance is one fiftieth of the model’s own holdout error against experiment, so the test can only pass if the two implementations agree far more closely than either agrees with reality.'));

A(table(
  ['Quantity compared', 'Threshold', 'Worst-case disagreement', 'Verdict'],
  [
    ['Outlet water temperature', '≤ 0.010 K', '**1.4 × 10⁻⁵ K**', 'PASS'],
    ['Brucite saturation pH at the skin', '≤ 0.005', 'within threshold', 'PASS'],
    ['Evaporation rate', 'pre-registered', 'within threshold', 'PASS'],
    ['Chiller electrical power', 'pre-registered', 'within threshold', 'PASS'],
  ],
  widths([2.4, 1.2, 1.8, 0.9]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Four gates pass. The two independent implementations agree on outlet water temperature to fourteen microkelvin — roughly forty thousand times tighter than the 0.542 K error the model carries against the experiment. That establishes that the Python results are not an artefact of one codebase.'));

A(note('What this is, and what it is not. This is verification, not validation: it proves the equations were implemented correctly twice, not that the equations are right. Validation against measurement is section 4, and the agreement there is far weaker, as it should be.'));

A(h2('The fill law, re-identified with an independent toolchain'));

A(p('The MATLAB build re-identifies the fill characteristic using the Curve Fitting Toolbox, which returns confidence intervals the Python implementation does not compute. The comparison is a genuine check, because the two used different fitting machinery on the same measurements.'));

A(table(
  ['Parameter', 'Python (adopted)', 'MATLAB estimate', 'MATLAB 95 % confidence interval'],
  [
    ['Coefficient c', '1.2401', '1.2741', '1.2312 to 1.3170'],
    ['Exponent n', '−0.5014', '−0.5453', '−0.5997 to −0.4908'],
  ],
  widths([1.4, 1.5, 1.5, 2.2]), { align: ['L', 'C', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('Both adopted Python values fall inside the MATLAB confidence intervals. The identification is therefore not sensitive to the fitting method, and the width of those intervals gives an honest picture of how well two parameters can be pinned down from this experiment at all.'));

A(h2('Control design, on licensed toolboxes'));

A(bullet('**System identification.** The loop’s thermal response to a fan-speed step is first order with a time constant of **513 s** and a gain of −0.0677 K per per-cent fan, identified at 99.9 % fit.'));
A(bullet('**Classical control.** A proportional-integral regulator tuned on that plant achieves a **60° phase margin**, which is the stability evidence a controls engineer will ask for and which the Python optimiser alone cannot provide.'));
A(bullet('**Model-predictive control.** A twenty-step-horizon controller enforces the 35 °C entering-condenser-water ceiling as a **hard constraint** rather than a penalty, which is the correct structure for a limit that must never be crossed.'));
A(bullet('**Optimiser benchmark, reported against ourselves.** Sequential quadratic programming finds a marginally better operating point than our grid search — $180.30/h against $181.48/h, a 0.65 % improvement — but takes **56.1 s against 7.0 s**, eight times longer. On an edge controller with a bounded execution budget the grid search is the correct engineering choice, and we report the gap rather than hide it.'));

A(h2('A Gulf day in Simulink, and the result that came out of it'));

A(p('The Simulink model couples a Simscape thermal network to a Stateflow supervisor and runs a full diurnal cycle at Gulf conditions. It reproduces the chemistry, the chiller envelope and the thermal response together over twenty-four hours, which no steady-state calculation can.'));

A(table(
  ['Quantity over one simulated Gulf day', 'Range'],
  [
    ['Cold water leaving the tower', '26.9 to 32.4 °C'],
    ['Condenser skin temperature', '38.4 to 46.2 °C'],
    ['Brucite saturation pH at the skin', '8.43 to 8.89'],
    ['Chiller electrical power', '933 to 1,605 kW'],
    ['Hours inside the chiller operating envelope', '24 of 24'],
    ['**Hours in the magnesium-silicate depositing regime**', '**11.1 of 24**'],
  ],
  widths([3, 1.6]), { align: ['L', 'C'], zebra: true }));

A(spacer(140));
A(quote('That last row is the sharpest single number in this document. On a simulated Gulf day at typical operating pH, the loop spends **eleven hours of every twenty-four above the brucite saturation pH at the tube skin** — while the bulk pH never moves. A plant watching bulk pH sees a flat line all day, while the surface crosses into deposition around mid-morning and back out in the evening.'));

A(p('The steady-state gates in section 10 established that this regime exists. The dynamic model establishes how much of a real day is spent inside it, and that is the number that turns a chemistry curiosity into an operating cost.'));

A(h2('The physics-informed surrogate, scored twice'));

A(p('The learned surrogate was built in both environments and scored against the same pre-registered criteria. It is trained against the physics core rather than against a plant, and no gate result in this document depends on it.'));

A(table(
  ['Metric', 'Python implementation', 'MATLAB implementation'],
  [
    ['Outlet temperature error against the core', '0.022 K', '0.030 K'],
    ['Constraint violations', '0', '0'],
    ['Speed-up over the core', '101,802×', '**298× — FAILS the 500× gate**'],
    ['Verdict', 'All four criteria pass', 'Three pass, one fails'],
  ],
  widths([2.4, 1.6, 1.8]), { align: ['L', 'C', 'C'], zebra: true }));

A(spacer(140));
A(p('The MATLAB surrogate fails its speed-up criterion and is reported as failing. The cause is not that the network is worse — its accuracy is comparable — but that the MATLAB physics core it is measured against is itself much faster, at 14.7 ms per evaluation, so the ratio is smaller. Both numbers are correct, and neither should be quoted without the other.'));

A(note('A note on OpenModelica. A Modelica description of the loop exists in the repository, but OpenModelica is not installed on the development machine, the model has never been compiled or run, and it therefore supports no claim in this document. It is mentioned here so that its presence in the repository is not mistaken for a result.'));

