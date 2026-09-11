# Session handoff — Furqan / Mizan

> **SUPERSEDED IN PART — 10 September 2026.** Four chemistry defects were found
> and fixed (register 24-32) and defect 17 was resolved. Every annual figure in
> this document moved, and the *narrative* moved with them: water was the
> headline term and is now the smallest one.
>
> | | as written here | corrected |
> |---|---|---|
> | annual makeup water | 8.8 % | **2.72 %** |
> | annual operating cost | 6.4 % | **3.77 %** |
> | annual electrical power | 5.4 % | **4.33 %** |
> | V5 water gate | 10.83 %, failed | **6.65 %, still failed** |
> | ceilings | 6 and 7, gypsum | **5 and 6, amorphous silica** |
>
> Inline figures below are tagged where they occur. **The pitch is not rewritten
> here — that is a founder decision**, because energy is now the largest term and
> `docs/prior_art_esc.md` shows the energy half is prior art seven times over.



**Paste this whole file as the first message of the next session.**

---

## Who and what

Three energy engineers in Lahore.

**FURQAN** — the parent. *"The criterion for energy."*
Deep physics and physics-informed AI for hard energy infrastructure — we separate what is measured from what is merely modelled. Furqan (الفرقان), from the Arabic root **f-r-q**, to separate: the criterion that distinguishes the true from the false. The name is the method, not decoration.

**MIZAN** — the first venture. *"The balance between energy and water."*
A retrofit supervisory controller for cooling-tower / condenser-water loops in Gulf district cooling. Mizan (الميزان): the balance, the scale, the measure held level.

Brand strings live in one place: `src/brand.py`. The report title page, the deck title slide and the running footers all read from it.

- **Engr. Furqan Shakeel** — Co-founder & CEO, owns the physics core. engr.furqan.shakeel@gmail.com · +92 302 1044259 · linkedin.com/in/furqan-shakeel
- **Engr. Damia Baig** — Co-founder, commercial. baigdamia@gmail.com · +92 331 6491787 · linkedin.com/in/damia-baig
- **Engr. Muhammad Ahsan** — Co-founder, commercial development. muhammadahsan4203@gmail.com · +92 310 4550698 · linkedin.com/in/-m-ahsan

Target: **DTV .dvp Cohort 2** (Dhahran Techno Valley / KFUPM), then QDB Pre-Accelerator, then YC. **DTV excludes SaaS** — the product is a physical retrofit device, sold as capex plus an annual recalibration licence.

Working directory: `C:\Users\Nouman\Desktop\Furqan's Docs\Startup\mizan`

---

## The product, in one paragraph

A sensor skid (conductivity, pH, ORP, temperature, makeup and blowdown flow) plus a motorised blowdown valve and edge compute, speaking BACnet/Modbus. It co-optimises **fan speed, blowdown and acid dose** against **ion-specific mineral saturation evaluated per mineral at the temperature where that mineral is least soluble** — calcite and magnesium silicate at the hot condenser skin; amorphous silica at the cold tower basin. **Gypsum is also routed to the skin, and defect 23 records that on this water that is the permissive choice, not the conservative one:** SI_gypsum has an interior minimum at 43.4 °C, so the skin is the *least* saturated point and the basin is worse by 0.0068 log units at 6 cycles. The integer ceilings do not move (max cycles 6.672 at the skin against 6.606 at the basin), but the one-line claim must not say gypsum saturates at the wall. Ships read-only in shadow mode.

---

## The differentiation claim, as narrowed by evidence three times

**Not ours** (all confirmed taken): ion-association/Pitzer speciation (French Creek since 1990, OLI Systems); skin-temperature saturation (ChemTreat US 11,780,742 B2, granted Oct 2023 — US + PCT only, **no Gulf family member**); blowdown control on a saturation index (US 4,460,008 / 4,464,315, 1984, expired).

**What is open**, and three independent literature sweeps found nobody doing it:

> *"No academic paper, patent, or commercial product literature describes a closed-loop control scheme where a chemical saturation limit directly bounds or dynamically alters the mechanical thermal energy optimizer."*

---

## Validated results — all reproducible, all in `results/`

```
V1  outlet water temp MAE      0.542 K   <= 1.00 K    PASS
V1  heat rejection MAPE        5.94 %    <= 6.00 %    PASS
V2  evaporation vs measured    9.90 %    <= 8.00 %    FAIL, and now DIAGNOSED
V3  bulk overstates limit      6.9-7.1 % typical, 15.2-15.6 % fouled
V5  total cost reduction       5.75 %    >= 3 %       PASS
V5  makeup water reduction     10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %]   <  15 %      FAIL, reported as a failure
V5  skin SI violations         0                      PASS
V5b physical wall              7 cycles, gypsum -- and the cost curve NEVER TURNS OVER
                               before it. Cost falls monotonically to 6, the last
                               feasible point. There is no interior economic optimum
                               on this water; the economics point straight at the wall.
ENERGY (reported, NOT a gate)  2.86 % mean total electrical power reduction across
                               all 5 V5 conditions; 12.35 % in the winter one, and
                               -1.79 % at Dhahran summer peak, where the optimiser
                               correctly SPENDS power to save water.
                               5.36 % across a Dhahran year, as a ratio of totals --
                               and essentially ALL of it comes from the cool half of
                               the year: 10.37 % across the cool half against 2.06 %
                               across the hot half.
V6  Mg-silicate envelope       safe <34 C skin; depositing >46 C at Gulf pH 8.5-9.0
```

Thresholds were fixed and printed **before** fitting. The water gate fails and stays failed — do not rescore it.

### The energy term is now reported separately (added 30 Aug 2026)

Electrical power was always the FIRST TERM of the controller's objective —
`cost = elec x P_total + water + acid + antiscalant`, with `P_total = P_fan + P_chiller`
([controller.py:186](src/controller.py) and again in `_cost_at_ph`). It is the only reason
fan speed is an actuator at all. But it was monetised into `cost_pct` and never reported
on its own, which made an energy venture look like a water venture. `run_controller.py`
and `annual.py` now emit it. **It is a reported diagnostic, not a pre-registered gate** —
attaching a threshold after seeing the answer is not a test.

**The finding that came out of it.** Across eight equal-hour wet-bulb bins of a Dhahran
year the energy saving and the water saving are **anti-correlated, r = -0.548**:

```
cool half (4,380 h, wb  9.7-19.3 C)   energy 10.37 %   water  7.18 %   cost 9.10 %
hot  half (4,380 h, wb 21.4-28.5 C)   energy  2.06 %   water  9.79 %   cost 4.74 %
hours-weighted year                   energy  5.36 %   water  8.81 %   cost 6.44 %
```

*(Ratios of hour-weighted totals, recomputed 4 Sep after defects 15 and 16. The
anti-correlation is now r = -0.548 across the eight bins.)*

Total cost saving stays between **3.6 % and 10.4 % in every bin**, produced by a
different physical mechanism in each half. A water controller collects almost nothing
across the cool half; an energy optimiser collects almost nothing across the hot half.
**This is the strongest argument in the package for coupling the two models**, and it was
invisible until the energy term was pulled out of the cost figure.
Figure: `figs/seasonal_handoff.png`, generated by `fig_seasonal_handoff` in `make_figures.py`.

> **AMENDED 7 September 2026 — do not quote the correlation coefficient.**
> `src/annual_datacentre.py` re-runs this sweep changing exactly one thing: the
> comfort-driven load model `clip(0.55 + 0.45 (T_db - 18)/28, 0.35, 1)`, which
> is tagged `[A]` in `annual.py`, becomes a flat data-centre load of 0.90.
> **At flat load r = +0.439. The correlation changes sign.**
>
> In district cooling, cold hours are also *light* hours, so a large part of
> r = -0.548 is a **load artefact**, not a fact about the weather. The coupling
> claim above was resting on an assumption rather than on a measurement.
>
> **The coupling argument survives, and the surviving form is stronger because
> it does not depend on the load model at all.** Argue it from the seasonal
> profiles: across the hot half a pure energy optimiser collects **1.39 %**;
> bin 6 goes **negative at -0.56 %**, because the optimiser correctly *spends*
> power to save water, which no energy-only controller would ever do; and
> across the cool half the split is even, 11.91 % energy against 10.75 % water,
> so a water-only controller leaves half of it behind.
>
> Data-centre load is also better commercially on every axis: energy 6.48 %
> against 5.36 %, water 10.67 % against 8.81 %, cost 7.80 % against 6.44 %, and
> **$117,760/yr against $76,236** at the same 10 MW nameplate. But **more of
> that money rests on extrapolation**: the water saving is now flat across both
> halves (10.75 vs 10.60), so roughly half of it sits above the validated
> 21.9 °C wet-bulb, where under district cooling the value sat in the validated
> half. Artefact: `results/annual_datacentre.json`. Five predictions were
> pre-registered before the run; P1 and P4 failed and are reported as failures.
> Analysis in `docs/datacentre_strategy.md` Part 4.

### A factual error was found and corrected in the generators

`make_report.py` and `make_deck.py` both asserted unconditionally that the economic
ceiling is where "total cost turns back up". On this water it does not — the V5b table
printed directly beneath that sentence shows cost falling monotonically from $209.08/h
at 3 cycles to $191.22/h at 7. `run_controller.py` already branched on a `turns_over`
flag and printed the correct text; the two document generators did not. Both now branch
the same way. The old LaTeX PDFs in `build_tex/` and the shipped zip still carry the
wrong sentence.

The corrected framing is also the stronger one: where a cost curve turns over, an operator
following the money stops short of the wall by themselves. Here the money points straight
at it, and LSI-based control cannot see gypsum at all.

**Gate V2 now FAILS, and the earlier pass was not real.** The drift constant was `0.0005` used as a FRACTION of circulating flow -- the modern eliminator rating of 0.0005 **per cent** with its percent sign dropped, and so a hundred times too much drift. `tower.drift_loss` feeds `calibrate.py`, so that inflated term was padding predicted water consumption by about five per cent, which is most of the distance between the 7.11 % previously reported and the 8 % threshold. With a defensible 0.001 % the holdout scores **9.90 %**.

The shortfall is campaign-dependent: Exp2 (the training campaign) 0.83 %, Exp1 9.88 %, Exp3 8.60 %. Regressing the residual on circulating flow (a fixed bleed) gives R2 = -0.06; on evaporation (a model deficiency) gives R2 = 0.06. Neither explains it. What does fit is that the model matches the campaign it was identified on and not the two it was not -- the same campaign-to-campaign movement already documented in the fill characteristic. Two candidates stay open `[VERIFY]`: the measured channel is TOTAL water consumption, so it includes any bleed, and the rig's bleed policy and drift-eliminator rating are both unpublished.

**The cause is now established and the [VERIFY] is closed.** Two explanations
were possible and they make OPPOSITE predictions, which is what made the
question answerable: an unaccounted bleed in the measured channel, or the
fill characteristic drifting between campaigns. Re-identifying the fill law
per campaign cannot help if it is a bleed -- a bleed is a term the model does
not contain -- but should close the gap if it is drift.

```
campaign   identified c   evaporation MAPE with its own fill law
Exp1          1.5320                6.55 %
Exp2          1.2401                7.80 %
Exp3          1.3826                4.50 %
```

**Every campaign falls inside the 8 % gate** (worst 7.80 %). The bleed
hypothesis is REJECTED. The fill coefficient moves **23.5 %** across four
years -- the same drift already measured in the thermal channel, now confirmed
independently in the water channel.

So V2 fails as a SINGLE-CALIBRATION gate, for a physical reason and not a
modelling one: the gate holds one fill law fixed while the tower itself
changed. The model is not deficient; the assumption that a tower's
characteristic is constant is. That points the same way as the commercial
argument -- **periodic recalibration is a functional requirement, and this
gate measures how fast a fixed characteristic goes stale.**

**Do not restore the old drift value to recover the pass.** See
`docs/defect_register.md`, which separates defects (forty-one found, forty-one fixed,
none open) from gate outcomes (two failed, both diagnosed).

**The water gate is now DIAGNOSED, and that is worth more than passing it.** Makeup = evaporation x C/(C-1), so the saving available from cycles alone is arithmetic: 7 cycles gives 12.50 %, 8 gives 14.29 %, and **15 % requires 8.5 cycles**. Gypsum saturates at **7** -- defect 15 moved the wall in by one cycle, so the criterion is further out of reach than when it was written, not closer. The criterion was written on the far side of a wall that had not been found yet, and gypsum saturation is not pH-sensitive, so the acid lever that buys cycles against calcite cannot move it. No control strategy of any kind reaches 15 % on this makeup water. The controller gets to 10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %], and it lands on **6 cycles** in every condition -- so cycles alone (10.00 %) accounts for almost all of it, with the air-side lever adding the remainder and moving individual conditions from 7.27 % to 12.71 %.

**Two different walls were being reported as one. RESOLVED 4 September.** V5 stops at 6 cycles, which its own log calls "the chemistry constraint boundary". V5b used to report the gypsum wall at 8 -- but it ran at *Dhahran summer humid*, one of the two conditions V5 then discarded as infeasible, and its output said `10 of 10 cycle counts sit outside the machine's validity envelope`. Registered as defect 14 and **closed the same day by defects 15 and 16 rather than by a reporting judgement**: with gypsum on a solubility that can turn over, and the chiller selected at design rather than at ARI, the ceilings come out **6 and 7 at all five conditions**, every row inside the envelope. The condition-dependence was an artefact, not a fact about the water.

The two-ceilings *result* was never in doubt and is unchanged: two distinct limits, binding mineral gypsum, invisible to LSI. What moved is the pair of integers, and **6 and 7 are now the most stable numbers in the package** -- they no longer move with the weather, and defect 19 showed they no longer move with the assumed skin temperature either. **The pre-registration was mis-specified, not merely missed** -- check a threshold against the system's physical ceiling before fixing it.

---

## Key findings, so they are not re-derived

1. **Fan correlation units.** The PSA dataset's `w_fan` column is a percentage but the published air-flow correlation takes **hertz**. Read as percent it turns over at 62 % (air flow falling as the fan speeds up). Cost ~1 K of accuracy and a +1.5 K bias before it was caught.
2. **Silica is prograde** — it binds at the *cold basin*, not the hot skin. Industry uses a static "150 mg/L" rule regardless of basin temperature; the true ceiling moves **95 → 143 mg/L** across 15–35 °C, i.e. the standard rule is **non-conservative by 37 % at a winter basin**.
3. **At realistic Saudi silica (26.8 mg/L, Salbukh measured) the model computes 4.4–4.9 max cycles — the industry's empirical band is 3.5–5.0.** A first-principles limit landing on observed practice is the strongest validation in the package.
4. **Magnesium silicate binds before amorphous silica** on Gulf water. Sepiolite was the wrong proxy (kinetically inhibited, gave indices forbidding all operation). Industry uses an **empirical Mg × SiO₂ product**: 35,000 standard / 25,000 utility, with **Mg as ppm Mg²⁺** — the "as CaCO₃" reading gives 2.78 cycles, below observed practice, so it is wrong.
5. **V6, the sharpest result.** Two-step mechanism: brucite precipitates at the skin, then reacts with silica. Brucite's saturation pH is retrograde, so **deposition occurs when bulk pH > pH_s(brucite) at the skin**. The same tower deposits at high load and not at low load. Needs thermal model + chemistry model + acid actuator together.
6. **Chiller model, now a named machine.** Carnot (η=0.55) overstated the value of cooling the condenser by ~60 %. Replaced with the EnergyPlus `Chiller:Electric:EIR` bi-quadratic, coefficients from **York YT 1758 kW (500 TR) / 6.28 COP / inlet vanes**, `datasets/Chillers.idf` lines 6001-6083 (CoolTools library). Chosen because its reference point IS the AHRI 550/590 rating point and its curves are fitted over **15.56-35.00 °C entering condenser water** — the Gulf range; most of the library stops at 26.11 °C. Gives 2.36 %/K over 30-36 °C against 2.62 % for the untraced set it replaced.
   - **The Gemini chiller report returned NULL on this.** The coefficients ship inside EnergyPlus. Parse `datasets/Chillers.idf` directly — 160 machines, 110 water-cooled centrifugal.
   - **ASHRAE 90.1-2022 Appendix J curves were examined and REJECTED** (`datasets/CodeCompliantEquipment.idf`, PNNL). Newer, exactly unity at the AHRI point, stated valid to 40 °C — but they imply **0.4-0.5 %/K**, i.e. 3 % COP loss from 30 to 36 °C where Carnot loses 21 % and every named machine loses 13-17 %. They are fitted to reproduce rated full-load and IPLV points, and the IPLV condenser schedule runs *downward* with load, so above 30 °C they are unconstrained by data. **A stated validity range is not a fitted range.**
9. **The optimiser will exploit a correlation outside its fitted box.** With the new curves it drove the fan to the grid floor in 4 of 5 conditions, putting entering condenser water at 36.5-40.5 °C — outside the fit — and booked a false **20.41 %** water saving that would have flipped a failed gate to passed. The entering-condenser-water window is now a hard constraint; it is also the machine's permitted range, since below it head pressure collapses and oil return fails, and above it the machine trips on high head. 1,840 of 6,307 candidate points are now rejected rather than extrapolated.
10. **New result: in Gulf summer the binding limit on fan speed is the CHILLER**, not tower physics and not chemistry. All four summer optima sit at 33.9-34.7 °C, hard against the 35 °C ceiling.
11. **A numerical defect sitting directly on the reported number.** The condenser duty fixed point was solved by 6 steps of successive substitution at 5 mK. The map contracts at ~0.5 per step, so ~26 steps are needed — and every grid point was seeded from ONE nearby solve, so the baseline came out accurate and the optimum did not. **Evaporation moved 5.199 → 5.396 kg/s (3.8 %) on the choice of seed alone**, an order of magnitude larger than the margin the water gate was failing by. Now Aitken delta-squared with a bracketed Brent fallback; 360/360 converge to 1e-5 K, and the two solvers agree to the second decimal place.
7. **Fill drift.** The identified fill coefficient moves **21 % across campaigns spanning 2019–2023**. Periodic recalibration is a functional requirement, not an upsell. Kloppers (2003) explicitly did not study fill ageing.
8. **Uncertainty.** Model error is **2.48× the propagated measurement uncertainty** — a negative result, reported. ~30 % is fill drift, ~70 % residual.

---

## Flags closed this session, with the evidence

1. **Chiller coefficients** — were untraced. Now **York YT 1758 kW / 6.28 COP / inlet vanes**, EnergyPlus `datasets/Chillers.idf` (CoolTools). Its reference point IS the AHRI 550/590 point and its curves are fitted to 35 C entering condenser water. `[C]` The Gemini deep-research report returned NULL on this; the coefficients ship inside EnergyPlus.
   **Rejected, and worth keeping:** ASHRAE 90.1-2022 Appendix J curves. Newer, exactly unity at the AHRI point, stated valid to 40 C — and they imply **0.4-0.5 %/K** where Carnot loses 21 % and every named machine loses 13-17 % over 30->36 C. They are fitted to IPLV points whose condenser schedule runs *downward* with load, so above 30 C they are unconstrained by data. **A stated validity range is not a fitted range.**

2. **Discharge TDS cap** — was an assumed 3,000 mg/L that contradicted observed practice. Resolved against the primary regulation, **RCER-2015 Vol. I** (Royal Commission for Jubail and Yanbu): `[C]`
   - Table 3B, discharge to the central wastewater treatment facilities: TDS **2,000 mg/L Jubail / 2,500 Yanbu**, chloride 1,000/400, sulfate 800/400
   - Table 3C, **direct discharge to coastal waters including the seawater cooling return: NO TDS LIMIT** (physical parameters are floating particles and temperature only)
   - Table 3D, irrigation: TDS 2,000 max, 1,750 monthly average

   So a TDS cap is **a property of the discharge route, not of the loop.** On 1,500 mg/L makeup a sewer cap allows 1.33 cycles, which would forbid evaporative cooling on reclaimed water outright — plants run 3.5-5.0, so they are not discharging there. Now modelled as `chemistry.DISCHARGE_TDS_CAPS` keyed by route, defaulting to `coastal_outfall` (no cap).

3. **Drift eliminator rate** — `drift_fraction=0.0005` was the modern spec **0.0005 %** with the percent sign dropped, i.e. 100x too much drift. Same defect class as the fan correlation in the wrong unit. Corrected to `1e-5`. `[C]` Makeup water is **provably unaffected** (drift cancels out of `makeup = evap + drift + blowdown` while blowdown stays positive, verified numerically: 25.584 and 22.386 m3/h before and after). What was wrong is the reported **blowdown**, 27 % low at seven cycles — the number a discharge permit is written against. It appears in no results artefact, so no published figure moves.

4. **Duty fixed-point convergence** — six substitution steps at 5e-3 K was both unconverged and **seed-dependent**. Evaporation moved 5.199 -> 5.396 kg/s (3.8 %) on the choice of seed alone, an order of magnitude larger than the margin the water gate was failing by, and biased because every grid point was seeded from one nearby solve. Now Aitken delta-squared with a bracketed Brent fallback: **0 of 360 non-converged**, and the two solvers agree on the gates to two decimals.

5. **Chiller validity envelope** — the optimiser was driving the fan to its lower bound, putting entering condenser water at 36.5-40.5 C, outside the fitted range, and collecting a **false 20.41 % water saving** from the extrapolation. The envelope is now a hard constraint (it is also the machine's permitted ECWT window). **1,840 of 6,307** candidate points are now rejected rather than extrapolated.

6. **PINN surrogate — three defects, then all four gates passed.** `src/pinn.py`, thresholds fixed and printed before training.

   | Gate | Threshold | Result | |
   |---|---|---|---|
   | P1 fidelity to core, Tout MAE | <= 0.10 K | **0.022 K** | PASS |
   | P1 fidelity to core, evaporation MAPE | <= 1.0 % | **0.964 %** | PASS |
   | P3 admissibility, Gulf extrapolation band | 0 of 5,000 | **0 of 5,000** | PASS |
   | P4 speed-up over the core | >= 500x | **101,802x** | PASS |

   141 ms per point for the core, 1.38 us for the surrogate. Zero violations on every individual constraint, at Gulf wet-bulbs the training data never reached.

   The three defects, all encoding errors rather than training failures:
   - physics loss stuck at 57.7 because **42 % of collocation points had inlet water below the wet bulb**, demanding `T_wo >= T_wb` and `T_wo <= T_wi` at once. The sampler was wrong, not the network.
   - evaporation at **32.9 % MAPE**: trained unnormalised at order 1e-2 kg/s against a normalised temperature target, so the head got almost no gradient.
   - normalising made it **worse, 69.4 %**: the head was `softplus(x)*sigma + mu`, range [mean, inf), which cannot represent the **60 %** of points below the mean. A positive quantity needs [0, inf).

   No threshold was moved. Each failure was traced to a defect, the defect was fixed, and the run was re-scored.

---

## Where the value actually comes from

Splitting the annual money saved across levers, at published tariffs: `[C]`

```
water        48.2 %   of the saving   (11,809 m3/yr, $36,726)
energy       53.1 %                   (547 MWh/yr,   $40,498)
acid etc     -1.3 %   the optimiser SPENDS more on acid to buy cycles
total                                 ($76,236/yr at a 10 MW plant)
```

Computed from `results/annual_dhahran.json` bins at the tariffs in
`controller_summary.json`. Recompute it there rather than carrying it by hand;
this figure had no artefact behind it until 4 Sep and went stale twice.

**The split has crossed over, and this matters commercially.** It was 66.0 / 35.4
before defect 11 and 56.0 / 45.3 after it. Defect 16 gave the machine back the two
Gulf-summer conditions it could not previously serve, and **energy is now the
majority term at 53.1 %.** That points the money at the half of the product that
`docs/prior_art_esc.md` shows is already prior art seven times over, and it is the
strongest single argument for repositioning as a constraint service rather than as
a rival optimiser. It is a founder decision and it is now overdue.

Energy is the majority term in Gulf winter (74 % of that condition's saving) and the minority in summer, where the chiller envelope caps how far the fan can be backed off. Both terms are in the objective; neither dominates everywhere. That is the whole argument for optimising them together.

---

## Data and sources

- **Validation data:** Zenodo 10806201 (Plataforma Solar de Almería), MD5 `ac94e0076a9217b58e032a2545bf9fc4`, CC BY 4.0, 165 steady-state points. **Limitation:** its summer wet-bulb tops at 21.9 °C; Gulf design is 30.3 °C.
- **Makeup water:** measured Saudi Aramco reclaimed-water analysis, Badruzzaman et al. (2022), *Water Resources and Industry* 28:100188.
- **Silica:** Al-Mutaz & Al-Anezi (2004), King Saud University / Riyadh Water Treatment Project.
- **Tariffs (published, not assumed):** electricity $0.074/kWh; water **$3.11/m³ avoided** (Marafiq/RCJY: process water SAR 8.04 + industrial wastewater SAR 3.64); acid $0.19/kg. **No Saudi time-of-use tariff exists** — never claim peak-shifting.
- 22+ PDFs in `sources/`, extracted to `sources_text/`. Four Gemini deep-research reports on the Desktop.

---

## Code map

```
src/psychro.py        ASHRAE psychrometrics, in-house (no CoolProp on py3.14)
src/tower.py          Poppe/Merkel, fixed-step RK4, fogged-air branch
src/chemistry.py      speciation, per-mineral eval points, Mg-silica rules, brucite
src/water_activity.py salinity coupling
src/controller.py     bi-quadratic chiller, fan affinity, optimiser
src/calibrate.py      gates V1, V2 (pre-registered thresholds)
src/run_controller.py gates V3, V5, V5b
src/mg_silicate_envelope.py  gate V6
src/uncertainty.py    Monte Carlo measurement-uncertainty propagation
src/drift.py          fill drift vs model deficiency
src/fill_law.py       model selection with extrapolation check
src/brand.py          Furqan / Mizan names, taglines, meanings -- one source
src/pinn.py           physics-informed surrogate + its own pre-registered gates
src/audit.py          consistency audit -- run it before shipping anything
src/export_matlab_cases.py  writes the case file the MATLAB twin is scored on

matlab/README.md              START HERE for a non-technical reader
matlab/mizan_demo.m           one Gulf day in plain English, no Simulink
matlab/mizan_verify.m         MATLAB twin vs the Python core, gates in advance
matlab/mizan_simulate.m       runs the Simulink model and explains it
matlab/build_mizan_model.m    builds mizan_plant.slx from text, not a binary
matlab/mizan_control_design.m Curve Fitting / System ID / Control / MPC / Optim
matlab/mizan_pinn.m           the surrogate in Deep Learning Toolbox
matlab/+mizan/                the physics, one function per file
modelica/MizanLoop.mo         the OpenModelica leg -- written, NOT yet run
src/run_modelica.py           detects OpenModelica and says what is missing
src/make_figures.py   ALL figures, report + slide variants (replaces make_figure*.py)
src/make_report.py    results -> docs/poc_report.md
src/make_latex.py     markdown -> XeLaTeX -> submission PDFs (Times New Roman, 12 pt)
src/make_pdf.py       superseded fpdf2 route, kept for reference
src/make_deck.py
src/build_deck.js     pptxgenjs DTV deck
```

Reproduce: `python src/fetch_zenodo.py && python src/calibrate.py && python src/run_controller.py && python src/make_figures.py && python src/make_report.py && python src/make_latex.py && node src/build_deck.js`

**Before every commit: `python -m pytest` (about 3 s), then `python src/audit.py`.**
The suite was added 7 September 2026 — until then pytest collected **zero**
tests and there was one `assert` in all of `src/`. It pins one test per named
defect, the physical invariants no refactor may break, and pre-registration
integrity — that a threshold is never quietly moved to turn a failure into a
pass. 48 passed, 1 xfailed; the xfail is open defect 17 and is `strict`, so
fixing the water analysis turns the suite red with XPASS as the prompt to close
the defect. See `tests/README.md`.

The audit now runs **65** checks, up from 63. The two new ones derive the total
defect count from the register's own table and cross-check it against every
document that states one — defect 22, which is defects 12, 13 and 21 one more
time: a figure maintained by hand in five documents, stale in all five,
including the co-founder-facing one, which said *"none open"* while the register
declared defect 17 OPEN.

`run_controller.py` now takes roughly 25 minutes rather than 4. The duty fixed point is solved to convergence instead of being truncated at six iterations; that is the cost of the number being right.

---

## Session of 30 Aug 2026, later pass — what changed

**Papers read and cited.** Five external sources now appear in PoC section 14,
and three of them independently confirm central claims:

- **EPRI 3002001276** states that calcium sulphate scale "is not pH sensitive as
  is calcium carbonate scale" (our gypsum-wall argument), that gypsum forms in
  the hot end of exchanger tubes above ~38 C, and that silica "is therefore
  found in cooler areas of the system such as the cooling tower fill" -- which
  is per-mineral temperature routing, stated by an industry authority.
- **SLAC-PUB-6097** (zero-blowdown trial, DOE-funded) measured cycles of
  concentration five different ways in ONE sample: 19 (alkalinity), 20 (calcium),
  23 (silica), 43 (magnesium), 50 (sulfate). **A factor of 2.6 on the same
  quantity.** That is the strongest external evidence that a conductivity
  setpoint cannot represent the loop. Also: fill deposit 93 % calcite while the
  heat-transfer surface deposit was 62 % silica/Mg-silicate -- per-location
  speciation observed in the field.
- **KFUPM** (Hasan & Mokheimer) modelled counterflow towers across 42 Saudi
  cities. Useful because it is the host institution's own work.

**A risk we had not modelled, found in the literature.** EPRI warns that raising
cycles reduces corrosion risk ONLY until sulphuric acid is applied, after which
"sulphuric acid replaces protective bicarbonate and carbonate alkalinity with
corrosive sulfate... often rendering the water very corrosive." Our optimiser
raises cycles to 7 AND doses acid. **There is no corrosion term in the
controller.** Now the top laboratory priority and an open item in every document.

**The skin temperature is a hardcoded 8 K and was never computed.**
`chemistry.wall_bulk_delta_t` exists and is never called; `run_controller.py`
never passes `skin_delta_k`. The film calculation gives 2.4-3.7 K clean; 8 K is
fouled. **Re-measured 4 September and the answer reversed** -- the paragraph that
used to stand here said a clean 3 K moved the gypsum wall in from 8 cycles to 7
and made the V5 optimum infeasible, which was true of the van 't Hoff solubility
and is not true of the one adopted in defect 15. `SI_gypsum` now has an interior
minimum at **44.5 C** and the skin sits near 40 C, on the flat bottom of it, so
across the whole band **2.4 K to 8.0 K the wall stays at 7 cycles and the last
feasible count at 6.** The assumption is no longer load-bearing for either
ceiling, and the reported zero saturation violations is no longer conditional on
a fouled condenser. Still worth replacing the literal with a call to
`wall_bulk_delta_t`: an assumption that happens not to bind is still an
assumption. See defect 19 in the register. Gates were NOT rescored.

**A stale figure was withdrawn.** `figs/water_ceiling.png` carried the discredited
9/10-cycle pair and asserted the cost curve turns over. Moved to
`figs/_superseded/` with a README. It was produced by a one-off script never in
`FIGURES`, so it never regenerated when the results changed. **Check any figure
not in the `FIGURES` list before trusting it.**

**Also fixed:** `make_report.py` and `make_deck.py` asserted unconditionally that
the economic ceiling is where cost "turns back up"; both now branch on a
`turns_over` flag as `run_controller.py` already did. Defect register said
"42 checks"; the audit runs 49.

**TRL finding.** DTV's guide runs separate hardware and software tracks. Our PoC
justified "not TRL 4" using the HARDWARE wording. On the SOFTWARE track we meet
three of four TRL 4 criteria already (integration; interoperability, via the
1.4e-5 K MATLAB/Python agreement; relevant environment defined). We still claim
TRL 3 -- performance in the relevant environment is predicted, not tested -- but
we now say so explicitly, which is worth more than the level.

**CV data received** from the founders' own CV PDFs and `people.json` is now
complete. Ahsan's mobile is +92 310 4550698 (both numbers are his; this one
chosen). Furqan's venture email engr.furqan.shakeel@gmail.com confirmed.

**Plain-English write-up** for all three founders:
`docs/ENGINEERING_IN_PLAIN_ENGLISH.md` -- definitions, physics, every result,
every open item, and the ten hardest customer questions with answers.

## Word / PowerPoint submission set — `../DTV_Submission/` (30 Aug 2026)

Built by `docbuild/*.js` (docx + pptxgenjs, house style in `docbuild/style.js`). Every
document is emitted as both `.docx` and `.pdf`. This set replaces the LaTeX PDFs for the
actual application; the LaTeX build is left in place but is now behind.

```
00_Submission_Contents            map of the folder to the form's upload slots
Application_Answers               wording for every free-text field
PoC_Report                        21 pp, 6 figures, all numbers from results/
Commercialisation_and_Budget      pricing, route to market, accounts, budget, kill gates
IP_and_Prior_Art                  stands in for the patent slot -- we hold none
Customer_Development_Plan         stands in for the LOI slot -- we hold none
CV_Furqan_Shakeel / _Damia_Baig / _Muhammad_Ahsan
Pitch_Deck                        15 slides, .pptx and .pdf
```

**Roles are now fixed** (confirmed by the founder, 30 Aug 2026), and every document uses
them consistently. Earlier documents disagreed with each other:

- **Furqan Shakeel** — Founder & CTO
- **Damia Baig** — Co-founder & CEO
- **Muhammad Ahsan** — Co-founder & Head of Commercial Development

**CV data is complete** (30 Aug 2026). All three CVs generate with no missing
sections. Source of truth is `docbuild/people.json`; the generator omits an empty
section rather than printing a placeholder, so a missing field would show up as
`[still to supply: ...]` in the build log. It currently prints `[complete]` for
all three.

Contact decisions, settled by the founders and consistent across every document:

```
Furqan Shakeel  engr.furqan.shakeel@gmail.com  +92 302 1044259  linkedin.com/in/furqan-shakeel
Damia Baig      baigdamia@gmail.com            +92 331 6491787  linkedin.com/in/damia-baig
Muhammad Ahsan  muhammadahsan4203@gmail.com    +92 310 4550698  linkedin.com/in/-m-ahsan
```

Ahsan gave two mobile numbers; both are his and +92 310 4550698 was chosen. His
LinkedIn handle begins with a hyphen and he has chosen to keep it -- the URL
resolves, and the package no longer flags it. Self-deprecating skill and language
markers were removed from all three CVs (`B2`, `IELTS 6.0`, `German (basic)`).
Levels were NOT inflated: the markers were dropped, and German at basic level was
removed rather than promoted.

The product line is now **"energy-water supervisory controller"** in `src/brand.py`,
not "supervisory controller" — the old wording buried the energy half.

## Deliverables in `submission/` (LaTeX build — superseded)

15 PDFs + `Furqan_Mizan_DTV_Deck.pptx` (**18 slides**). Everything is now built through **XeLaTeX** (`src/make_latex.py`): A4, real Times New Roman, 12 pt, booktabs tables, `placeins` float barriers so a figure can never straddle a page break or drift out of its section. That replaces the fpdf2 route, which had no float model and cut figures at page boundaries.

New slides in the deck: *In service* (how a plant actually uses it, day 0 to closed loop), *A failed gate, diagnosed*, *Coupling, priced* (the chiller envelope), *Market sized from regulators*, and *Venture scale* (what the SAR 200,000 buys, against named KFUPM facilities). Every headline number on a slide is now read from `results/*.json` at build time — they used to be typed in and had gone stale.

Figures are generated in two variants by `src/make_figures.py`: `figs/*.png` for the report (page proportions, source footnote, LaTeX supplies the caption) and `figs/slide/*.png` for the deck (larger type, deck aspect ratio, no embedded title). Neither carries an editorial title inside the image — that was the cause of the double-titled figure slides.

---

## Open items — do not paper over these

| Item | Direction it cuts | State |
|---|---|---|
| Almeria wet-bulb 21.9 C vs Gulf 30.3 C | **Unknown** — the only two-sided one | OPEN. Closed by KFUPM's humidifying wind tunnel. The PINN's physics loss is the interim mitigation, not a substitute |
| Model error 2.48x measurement uncertainty | Against us | OPEN, reported |
| Water gate missed (10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %] vs 15 %) | Against us | **DIAGNOSED** — the threshold required 8.5 cycles and gypsum saturates at 7. Mis-specified, not missed. Stays failed, and it now misses by 4.17 points against 0.17 as originally reported |
| Bi-quadratic chiller coefficients | Unknown | **CLOSED** — York YT 1758 kW / 6.28 COP, EnergyPlus `datasets/Chillers.idf` (CoolTools). Reference point IS the AHRI point; fitted to 35 C |
| Discharge TDS cap | Unknown | **CLOSED** — RCER-2015 Vol. I. Table 3B (sewer) 2,000 mg/L Jubail / 2,500 Yanbu; **Table 3C (coastal outfall, incl. seawater cooling return) has NO TDS limit**; Table 3D (irrigation) 2,000. It is a property of the discharge ROUTE, not the loop |
| Drift eliminator rate | Was wrong | **CLOSED** — was 0.0005 used as a fraction (0.05 %); the spec is 0.0005 **%**. 100x too large. Makeup unaffected (drift cancels while blowdown > 0) but reported blowdown was 27 % low |
| Duty fixed-point convergence | Was wrong | **CLOSED** — 6 substitution steps at 5e-3 K was unconverged AND seed-dependent; evaporation moved 3.8 % on the seed alone. Now Aitken + Brent fallback, 0/360 non-converged |
| Chiller validity envelope | Was being violated | **CLOSED** — the optimiser was leaving the fitted range and booking a false 20.41 % water saving. Envelope now a hard constraint; 1,840 of 6,307 candidate points rejected |
| Mg-silicate SI threshold | Unknown | OPEN, handled by the empirical Mg x SiO2 product rule instead |
| No traction, no LOIs, no patents | Neutral | OPEN — Cohort 1 winners had none either |
| Simscape Fluids | Blocked | **NOT LICENSED** on this machine (installed, but License Manager Error -5). Plan changed — see below |

## The MATLAB / Simulink stack, and what it showed

Built and running. Everything uses only toolboxes that check out on this
machine; Simscape **Fluids** does not, and is not used.

**Agreement with the validated Python core**, gates fixed before the first run:

```
outlet water temperature   0.000014 K   <= 0.010 K    PASS
evaporation rate           0.00018 %    <= 0.50 %     PASS
chiller electrical power   0.000000 %   <= 0.10 %     PASS
brucite saturation pH      0.0014       <= 0.005      PASS
```

**The Simulink model** (`mizan_plant.slx`, built by script so it is text):
Simscape thermal network for the loop's 150 t inertia, Stateflow supervisor
(SHADOW -> ADVISORY -> CLOSED LOOP with a hard FALLBACK), MATLAB Function
blocks for the Poppe tower, the named York YT chiller and the brucite limit.
One day in ~90 s. Basin 26.9-32.4 C, skin 38.4-46.2 C, scale limit moving
over pH 8.43-8.89, **11.1 of 24 hours above it** with both plant instruments
flat. Matches `mizan_demo.m`, which gets there with no Simulink at all.

**Five toolboxes, five real jobs** (`mizan_control_design.m`):
Curve Fitting gives the fill law a 95 % CI of [1.2312, 1.3170] on c, so the 21 %
campaign drift is wider than one campaign's interval and therefore physical.
System Identification measures tau = 513 s at 99.9 % fit against 314 s from
inventory alone -- the 1.6x gap is the condenser feedback. Control System
gives a PI at 60 deg phase margin. MPC carries the chiller's 35 C ceiling
as a HARD constraint. Optimization finds a better point but is **8x SLOWER**
against the exact physics -- reported as it came out, and it is the argument
for the surrogate rather than against it.

**Three more defects found, none of them physics errors:**

1. The Simscape temperature sensor reads **Kelvin**; the first run treated it
   as Celsius. The chemistry was asked for a saturation pH at 341 C and the
   chiller reported itself out of envelope all day. Both refused. Fourth unit
   defect in this project, fourth caught the same way.
2. The heat-flow **sign was inverted**: +1000 kW into a 150 t mass for 600 s
   gave -0.956 K. Right magnitude, wrong direction -- the signature of a sign
   convention, settled by pushing a known heat flow into a known mass.
3. An **algebraic loop**: Simulink refused a model where the controller acted
   on a measurement it was causing in the same instant. It was right to.

Two methodological notes from the identification: identify a **settled**
plant (stepping one still coming off its initial condition returned a time
constant of 1.9e17 s at an 11 % fit), and give the estimator a pre-step
baseline.

**OpenModelica** is written (`modelica/MizanLoop.mo`) but **not installed**,
so it has not run and makes no claim. It stays the destination because the
LBNL Buildings library ships the same CoolTools chiller data the Python core
uses -- one dataset instead of two.

**`python src/audit.py`** runs 34 consistency checks across code, results and
documents and must pass before anything ships.

---

## Real Dhahran weather arrived, and it changed two things

A TMYx file for **station 404160, Dhahran-Abdulaziz AB, 2011-2025** (8,760
hourly rows) is now in the package. `python src/tmy.py <path>` parses it.

**1. The psychrometrics are now independently validated.** The EPW header
carries the **2025 ASHRAE Handbook design conditions** for the same station,
computed by ASHRAE from the same hours by their own method. Recomputing them
from the hourly file with our own in-house code:

```
                 ASHRAE 2025     ours      diff
0.4 % wet-bulb      31.4 C      31.34 C   -0.06 K
1.0 % wet-bulb      30.5 C      30.45 C   -0.05 K
2.0 % wet-bulb      29.6 C      29.69 C   +0.09 K
worst over six design percentiles: 0.20 K
```

Neither side was fitted to the other. Until now every gate tested the tower
model and the psychrometrics *together*, so an error in one could have been
absorbed by the other. That is no longer possible: the psychrometric layer is
correct on its own.

It also **sources a number the package had been asserting**. Gulf design
wet-bulb was quoted as 30.3 C from nowhere. ASHRAE 2025 gives **30.5 C at
1 % and 31.4 C at 0.4 %** for Dhahran. Close, but now cited. `[C]`

**2. The largest open item now has a number on it.** "Almeria tops out at
21.9 C wet-bulb and the Gulf is hotter" was carried qualitatively for the
whole project. With an hourly year:

```
40.5 % of a Dhahran year (3,551 of 8,760 hours) is above 21.9 C wet-bulb
84 % of September hours
annual max wet-bulb 34.6 C
```

**Two fifths of the operating year is outside the validated envelope.** That
is a much sharper statement of the risk than the package had before, and it
cuts against us. It is exactly what the KFUPM humidifying wind tunnel is for,
and it is now the strongest possible justification for asking for that rig.

---

## The annual figure, and an uncomfortable one

`python src/annual.py` bins the TMY year by wet-bulb and runs the controller
at each bin centroid, weighting by hours actually spent there. This was
attempted as **option C** in the revision memo -- the hope being that an
honest weighting might help the failed V5 gate.

**It does the opposite.**

```
five-condition unweighted mean (what gate V5 scores) : 10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %] water
hours-weighted annual, real Dhahran year             : 8.42 % water
                                                       -2.41 points
ratio of annual totals -- THE FIGURE TO QUOTE        : 8.81 % water
```

The saving is still larger when it is hot -- 6.0 to 8.6 % across the cooler half of
the year, 5.6 to 14.0 % across the hotter half -- and the five hand-picked
conditions were four summer and one winter. **The gate's metric is flattering the
product by 2.41 points**, up from 1.10 before defects 15 and 16, so the case for
quoting the annual figure rather than the gate figure is stronger than ever.

Two consequences, and neither is optional:

1. **Quote 8.8 % [SUPERSEDED 10 Sep 2026 -> 2.72 %] annually to customers, not 10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %].** The gate figure
   belongs only to the specific five-condition comparison it was computed
   for and should not travel outside it. Note there are TWO annual numbers:
   the hours-weighted mean of ratios (8.42 %) and the ratio of hour-weighted
   totals (8.81 %). `annual_dhahran.json`'s own `weighting_note` says the
   second is the one to quote outside the repository. The full outward-facing
   set is **8.8 % [SUPERSEDED 10 Sep 2026 -> 2.72 %] water, 6.4 % [SUPERSEDED 10 Sep 2026 -> 3.77 %] cost, 5.4 % [SUPERSEDED 10 Sep 2026 -> 4.33 %] electrical energy**.
2. Option C is dead as a route to a passing gate. It was the only revision
   that was real work rather than re-labelling, and the work came back
   against us.

Only **62.5 %** of the weighted year is inside the validated wet-bulb
envelope, so 37.5 % of even this number rests on extrapolation.

---

## One decision is waiting for you

`docs/threshold_revision_memo.md` (and its PDF). Two gates fail, neither can
be made to pass by better modelling, and the memo sets out what a defensible
revision would look like with all the numbers worked out. **Nothing has been
applied** -- the package reports both as failed, and `src/audit.py` will fail
if the pre-registered 15 % threshold is changed without the memo being
updated to say so.

The thing that had not been looked at until now: **four of the five V5
conditions clear 15 % on their own** (18.37, 16.34, 15.56, 15.45 %). The gate
fails on the unweighted MEAN, dragged down by Gulf winter at 8.45 % -- where
the optimiser correctly trades water for energy, because energy is 74 % of
that condition's saving in winter.

The recommendation in the memo is to leave both failed, and it gives three
reasons. The short one: DTV screens a maturity gate first, and two diagnosed
failures with untouched thresholds are better evidence of a working method
than six passes.

---

## Next actions, in order

1. ~~Chiller coefficients~~ **DONE** — see finding 6.
2. **Simulink without Simscape Fluids.** Licence *checkouts* on this machine: Simulink OK, Simscape (base) OK, Stateflow OK, MPC Toolbox OK, System Identification OK, Optimization OK, Curve Fitting OK, Simulink Control Design OK, **Deep Learning OK**, Parallel Computing OK, MATLAB Coder OK, Simulink Compiler OK. **Simscape Fluids FAILS — License Manager Error -5, installed but not licensed** (`ver` lists installed products, not licensed ones); Simscape Electrical / Driveline / Multibody and Embedded Coder also fail.

   **Recommended replacement: OpenModelica + the LBNL Modelica Buildings Library.** Free, BSD, and it contains exactly the components needed — `Buildings.Fluid.HeatExchangers.CoolingTowers.Merkel` and `Buildings.Fluid.Chillers.ElectricEIR`. The detail that decides it: the library ships the **same CoolTools chiller curve data we are already using** (`ElectricEIRChiller_York_YT_1055kW` is in it), so the Modelica plant and the Python core would be driven by one chiller dataset rather than two.

   Two coupling routes, in order of preference:
   - **(a) OMMatlab** — MATLAB drives the OpenModelica model directly. No FMU, no import block, nothing extra to license. Preferred.
   - **(b) FMU** — export FMI 2.0 Co-Simulation from OpenModelica and import into Simulink. **Checked: base Simulink here has no FMU Import block** (it is not in `simulink/User-Defined Functions`). Needs the free **FMI Kit for Simulink** (Modelon/Dassault). OpenModelica FMUs are known to need the OM `bin` directory on PATH before MATLAB starts.

   Neither OpenModelica nor OMPython is installed yet. The HIL demo is still V6 — drive a load transient and show the brucite criterion crossing in real time while pH and conductivity stay flat.

3. **PINN surrogate — `src/pinn.py` exists and runs.** Gates pre-registered before training, same discipline as V1/V2/V5. Purpose: (a) a differentiable, ~1000x faster stand-in so the grid search can become gradient-based MPC on edge hardware, and (b) the only honest thing that can be said about Gulf wet-bulb before the KFUPM rig exists — the physics loss is evaluated at collocation points at 30 C wet-bulb *where there is no data*, enforcing the inequalities thermodynamics guarantees everywhere: cannot cool below wet-bulb, more air cannot warm the water, hotter inlet cannot cool the outlet, outlet cannot exceed inlet. It is **never** the authority on a safety limit and is **forbidden from the chemistry** — speciation is algebraic thermodynamics and must stay exactly computable.

4. **3D CAD via MCP, for CFD later.** FreeCAD is the realistic option: free, scriptable, several MCP servers exist, exports STEP/STL, and one of them ships OpenFOAM/FluidX3D hooks. Nothing installed yet. The engineering reason to want it: parametric condenser-tube and sensor-skid geometry -> STEP -> OpenFOAM boundary-layer CFD would let the **+8 K skin-temperature rise** be derived rather than assumed. That single number is currently the least-defended input in the whole chemistry chain, and every V3/V5 result is proportional to it.

5. **Customer interviews.** Four logged against a pre-registered gate of fifteen by 15 September, so this is behind and it is the binding constraint on the DTV form's mandatory interview-count field. Two are Gulf district cooling conversations reached cold on LinkedIn, at the same operator and independent of each other; two are Pakistani industrial contacts whose names the founder still has to fill in. The roster is in `results/interviews.csv`, which is gitignored because it names real people and this repository is public. **The finding so far cuts both ways.** Nobody analyses the deposit, which is the blind spot the product claims exists. But the deposit was then described as dark brown and black, and neither calcite nor gypsum is dark, so the model may be computing a minority phase. That is recorded as evidence against, not explained away. The DTV form has a mandatory interview-count field. Kit in `docs/linkedin_outreach.md`; figure `figs/silica_seasonal.png`. One question above all: *"What is your current cycles-of-concentration setpoint, and what set it?"*
6. **CV gaps** — education and experience rows for all three founders.

---

## How to work on this

Pre-register thresholds before fitting; report failures as failures. When a gate fails, **check for a unit or scaling defect before concluding the model is inadequate** — three of the four biggest corrections in this project were exactly that. Prefer first-principles models with few parameters precisely because they cannot absorb a bad input and fail loudly instead. Never invent a citation or a coefficient; tag `[C]` / `[A]` / `[VERIFY]`. If a computed number contradicts observed industry practice, **the number is probably wrong** — say so rather than shipping it.
