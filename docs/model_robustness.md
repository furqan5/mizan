# Model robustness — what the literature says about our choices

Compiled from the project source library (22 papers) plus Kloppers' 2003 Stellenbosch dissertation. Every claim here is traceable to a document in `sources/`.

The purpose is narrow: our fill law fits its training campaign with a log-space R² of 0.372, and we rejected a better-scoring model on physical grounds. Both decisions need external support or correction.

---

## 1. Our candidate fill laws are the canonical ladder

We tested five functional forms before reading Kloppers. They turn out to reproduce the published sequence almost exactly.

| Ours | Kloppers' equation | Original source |
|---|---|---|
| A: `Me = c(m_w/m_a)^n` | **(3.14)** `Me/L_fi = c₁(G_w/G_a)^c₂` | Lowe & Christie 1961 |
| B: separate flows | **(3.15)** `Me/L_fi = c₁ G_w^c₂ G_a^c₃` | Kröger 1998; Baard 1998 |
| D: separate flows + inlet water temp | **(3.16)** `Me/L_fi = c₁ G_w^c₂ G_a^c₃ T_wi^c₄` | Johnson 1989 |
| — | **(3.19)** adds fill height `L_fi^c₅` | Kloppers 2003, general form |

Kloppers' verdict on form A, verbatim:

> *"It is therefore clear that equation (3.14) employed by Lowe and Christie does not always represent the test data accurately. It is only accurate in limited conditions where the exponents c₂ and c₃ in equation (3.15) are close to each other."*

**Our data meets that condition, marginally.** Fitting form B gives `G_w^-0.5431 G_a^+0.4187` — magnitudes 0.543 and 0.419, differing by 26 %. Not equal, but the same order, and our holdout says the ratio form still predicts outlet temperature better (0.542 K vs 0.629 K). We follow the holdout, and we state the tension rather than hide it: Kloppers' guidance mildly favours the separate-flow form, our out-of-sample test does not, and with 114 observational points over a limited L/G range the extra freedom most likely overfits.

## 2. Rejecting the wet-bulb term was right, and Kloppers proves it experimentally

We rejected a four-parameter form containing ambient wet-bulb despite it scoring best on MAE, on the argument that a Merkel number describes fill geometry and wet-bulb is an operating condition.

Kloppers settles it from measurement, in his own conclusion to Chapter 3:

> *"It is also found that the inlet air drybulb and wetbulb temperatures have no significant effect on the loss or transfer coefficients."*

And in §3.3.5, on an apparent air-temperature dependence reported by another author:

> *"It will be shown that the apparent dependence of the Merkel number on the inlet air drybulb temperature… is actually the dependence of the Merkel number on the inlet water temperature."*

So the wet-bulb term our regression wanted is a known artefact — it proxies for something else. Excluding it is the documented correct choice, not merely a defensible one.

## 3. The inlet-water-temperature term: the literature does not agree, so we exclude it

This is the honest state of play, and it is not settled.

| Source | Basis | Water-temperature exponent |
|---|---|---|
| Kloppers 2003, §3.3.4 | Measured, 1.08 m and 1.98 m trickle fill | **−0.2471 and −0.2774** |
| Preprints 2026.1125, 54-run DOE | Lab tower, perforated inclined plates, T = 50–70 °C | **+4.173** (on `k_y a`) |
| This work | PSA pilot data, T_wi = 33–41 °C | **+0.183** |

Kloppers finds the Merkel number **decreases** with inlet water temperature — *"as design loads of cooling towers increase above design specifications, the cooling tower will be less effective."* The DOE study finds `k_y a` **increases** strongly with top water temperature and calls it the dominant factor.

The two are not directly comparable — `k_y a` is a volumetric mass-transfer coefficient, `Me` is normalised by water flow, and the DOE tower ran at 50–70 °C, far above normal cooling-tower service — but the disagreement in sign is real and we cannot resolve it from our data.

**Decision: exclude the term.** Embedding a coefficient whose *sign* is disputed in the literature into a controller that will extrapolate is worse than omitting it. This is a stronger reason than our original one (it did not improve the holdout), and it is the reason we now give.

## 4. Is R² = 0.372 alarming? No — it is the difference between designed and observational data

This was the open question. The comparison answers it.

| Study | Design | R² |
|---|---|---|
| Preprints 2026.1125 | **3-factor, 3-level DOE**, 54 runs, levels deliberately spanned, single rig, one campaign | **0.869** |
| This work | **Observational**, 114 points, uncontrolled covariation, one rig, campaigns spanning 2019–2023 | **0.372** |

A designed experiment sets its factors on a grid and holds everything else fixed; the residual is instrument noise. Observational data from an operating pilot plant carries covariation between factors, seasonal drift and four years of fill ageing. Expecting the same R² from both is a category error.

The meaningful comparison is not R² but **out-of-sample temperature prediction**, which is what we report: 0.542 K MAE on campaigns never used for fitting.

Note also Kloppers' own recommendation, which we follow:

> *"The goodness of fit must also be supplied in the form of a correlation coefficient. This will enable the designer of wet-cooling systems to take the necessary precautions to compensate for any uncertainties."*

Reporting a low R² is the recommended practice. Concealing it would not be.

## 5. Fill ageing is an acknowledged gap in the canonical reference

Our drift analysis found the identified fill coefficient moving 21 % across campaigns spanning four years, and we concluded that periodic recalibration is a functional requirement rather than a commercial add-on.

Kloppers' Chapter 3 conclusion ends:

> *"Ageing effects of the fill are not investigated in this study."*

So the definitive reference on fill performance explicitly leaves this open. Our finding addresses a stated gap rather than rediscovering known ground.

## 6. PID is documented as inadequate for this loop — supporting the MPC choice

Our AI architecture note argues that the answer to multivariable cooling-water control is constrained MPC, not reinforcement learning, and that PID cannot trade chemistry against energy.

*Energies* 18:1232 states the first half directly:

> *"Traditional proportional–integral–derivative (PID) controllers are used for pH neutralization but often struggle with the cooling tower environments' dynamic and nonlinear nature, resulting in suboptimal performance and increased operational costs."*

That paper's own answer is a PSO/neuro-fuzzy hybrid. Ours is constrained MPC. Both agree PID is the wrong instrument; we differ on the replacement, and our reason is that MPC carries hard constraints as first-class objects, which a neuro-fuzzy controller does not.

## 7. A published template for our TRL 4 rig

*Review of Scientific Instruments* 83:024101 (Chien, Hsieh, Li, Monnell, Dzombak & Vidic — Pittsburgh / Carnegie Mellon) describes a **pilot-scale cooling tower built specifically to evaluate corrosion, scaling and biofouling control strategies for impaired makeup water**, operated at N = 4.6 cycles with temperature change 6.6 °C, water velocity 0.66 m/s and air mass velocity 3660 kg/(m²h), held stable for up to two months.

That is, in outline, exactly the KFUPM experiment we propose. It is a peer-reviewed design precedent for the rig, the instrumentation and the control of cycles by conductivity — useful both for building it and for justifying it in the application.

## 8. Industry practice, and why our numbers sit where they do

| Source | Practice |
|---|---|
| Cooling-tower maintenance guide | *"Maintain COC within 3.5–5.0. Below 3.5 wastes water and chemicals; above 5.0 increases scaling and corrosion risk significantly."* |
| *Performance Analysis of Automated Control* (Umm Al-Qura University, Saudi Arabia, 12,000 TR district cooling) | Nalco 3D TRASAR raised cycles from **2.5–3.5 to 4–5**, about **30 % blowdown reduction**, 14,600 m³/year |
| Badruzzaman et al. 2022 (Saudi Aramco, Dhahran) | Switching groundwater → reclaimed water gave **27 % water-consumption reduction** by raising cycles |

Our model puts the gypsum wall on Aramco's measured reclaimed water at **8 cycles**. Industry caps at 5. The gap between 5 and 8 is the addressable headroom — and the reason operators cap at 5 is that their index cannot locate the wall, so they leave margin they cannot quantify.

**This also sets the honest competitive baseline.** 3D TRASAR already moves plants from ~3 to ~5 cycles. We are not the first increment on this problem; we are the next one, and the claim must be framed that way.

---

## Sources

All in `sources/`, extracted to `sources_text/`.

- Kloppers, J.C. (2003) *A Critical Evaluation and Refinement of the Performance Prediction of Wet-Cooling Towers*, PhD dissertation, University of Stellenbosch (promoter D.G. Kröger). Ch. 3, §3.3.1–3.3.5 and Ch. 3 conclusion.
- Badruzzaman, M. et al. (2022) *Municipal reclaimed water as makeup water for cooling systems*, Water Resources and Industry 28:100188. Saudi Aramco, Dhahran. Open access.
- Chien, S.H. et al. (2012) *Pilot-scale cooling tower to evaluate corrosion, scaling, and biofouling control strategies*, Rev. Sci. Instrum. 83:024101.
- Preprints 2026.1125.v1, *Effect of Operating Conditions on the volumetric mass transfer coefficient*, 54-run DOE.
- *Energies* 18:1232, pH controller performance in industrial cooling towers.
- *Performance Analysis of Automated Control System*, Umm Al-Qura University district cooling, Engineering 4:55–67 (2012).
- *Cooling Tower & Condenser Maintenance: Performance Optimization Guide for Power Plants*.
