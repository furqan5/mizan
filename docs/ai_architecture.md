# Where AI belongs in the Furqan controller — and where it does not

**Status:** decision record. Written 29 Aug 2026, before the DTV submission.
**Test applied:** DTV Filter 8 — AI counts only if it is load-bearing and physics-coupled. It fails if (a) it is a wrapper, (b) deleting it leaves the product intact, or (c) it substitutes for physics instead of being constrained by it.

Two of the four proposals are adopted, one is adopted only after being reframed, and one is rejected on evidence we generated ourselves.

---

## 1. Reinforcement learning for dual-variable control — REJECT for v1

The premise is right: a PID cannot trade chemistry against energy, because PID is single-loop and has no notion of a constraint. But the standard answer to that premise is not RL — it is **constrained model-predictive control**, which was invented for exactly this problem and carries hard constraints as first-class objects.

Against RL specifically:

- **No hard-constraint guarantee.** RL optimises expected reward. A penalty term for "keep pH in 7.2–7.8" is a soft preference, not a bound. A supervisory controller that can violate a scaling constraint even at low probability is not sellable to a plant operator, because the cost of the rare violation — a fouled condenser, a chemical clean, lost capacity — dominates the average-case saving.
- **Sim-to-real gap sits on top of an already-uncertain model.** RL trained in our simulator inherits every error in that simulator, and scaling kinetics is the least certain part of it. We would be optimising hard against our own modelling error.
- **It fails the removal test in the wrong direction.** Delete the RL agent, substitute MPC, and the product is *better*, not broken. That is a Filter 8 fail by definition.
- **Procurement reality.** OT cybersecurity and HSE review will ask what the controller does in a state it has never seen. "It learned a policy" does not clear that review. "It solves a constrained optimisation and falls back to the incumbent setpoint if infeasible" does.

**Adopted instead:** economic nonlinear MPC over fan speed, blowdown and acid dose, with saturation constraints as hard bounds and a documented fallback to baseline setpoints on solver failure or sensor loss.

**Revisit when:** after TRL 4 and field data, and then only as *shielded* RL — a policy filtered through the same constraint set, kept only if it beats MPC by a margin that survives the added review burden.

## 2. Fouling and scaling prediction from the thermal residual — ADOPT. This is the one.

Genuinely load-bearing, and the right home for a learned component.

- Physics gives the **expected** overall heat-transfer coefficient `UA` for the measured duty, flows and temperatures.
- The gap between expected and observed `UA` is the **fouling resistance** `R_f` — a physically meaningful state, not a statistical artefact.
- `R_f` should first be estimated by a **recursive estimator** (EKF/UKF or recursive least squares), not a neural network. Fouling resistance is observable from thermal data and slowly varying; a Kalman filter on a physical state is more robust, more interpretable and far more data-efficient, and it returns an uncertainty band for free.

The learned component belongs one level deeper, and this distinction is the important one:

> **Thermodynamics is known; kinetics is not.** Our chemistry engine computes the saturation index — the *driving force* for precipitation — from first principles with published equilibrium constants. But the *rate* at which scale actually forms depends on nucleation, surface condition, crystal habit, flow shear and antiscalant residual. Those are site-specific, poorly characterised in the literature, and genuinely not derivable from first principles.

So: **first principles for the driving force, a calibrated learned residual for the kinetics.** `dR_f/dt = k(site) · f(SI_skin, shear, inhibitor)`, where physics supplies `SI_skin` and the learned term supplies `k` and the shape of `f`.

Delete that term and you can still compute *whether* scale is thermodynamically possible, but not *when* it will cost the plant money — which is the entire commercial proposition. That passes Filter 8 cleanly.

**Prerequisite:** labelled data — coupon mass-gain and cleaning events from the KFUPM rig at TRL 4, then field data. Until then this is declared a TRL 4 research objective, not claimed as evidence.

## 3. Soft-sensing water chemistry from thermal variables — REJECT as stated; a narrower version adopted

The stated version — infer TDS or scaling index from flows, temperatures and pump power — is not merely difficult. It is **unobservable**, and we can now show that quantitatively from our own model.

Dissolved solids influence tower thermal behaviour through exactly one channel: they lower water activity, which depresses interface vapour pressure and hence evaporation rate. We computed that channel for the Saudi TSE composition:

| Cycles | Circulating TDS | Vapour-pressure depression |
|---:|---:|---:|
| 2  |  3,000 mg/L | 0.097 % |
| 4  |  6,000 mg/L | 0.194 % |
| 6  |  9,000 mg/L | 0.291 % |
| 8  | 12,000 mg/L | 0.388 % |
| 10 | 15,000 mg/L | 0.485 % |

The entire thermal signature of moving from 2 to 10 cycles is **under half a percent**. Plant-grade instrumentation cannot resolve that: the PSA rig's own water-flow uncertainty is ±0.65 % of reading and its RH sensor ±3 %. The chemistry signal sits **an order of magnitude below the measurement noise floor**. No estimator recovers a state that is not in the data — an observability fact, not a modelling shortfall.

**Adopted instead — sensor-drift detection by physical redundancy.** The useful version inverts the idea. Conductivity is cheap and robust; pH and ORP probes are the ones that foul and drift. Given conductivity, the makeup analysis and the water balance, the carbonate system and charge balance **predict** what pH should be. Compare predicted with measured:

- agreement → both instruments trustworthy;
- divergence → the pH probe has drifted or fouled; fall back to the predicted value and raise a maintenance flag.

That is a physics soft-sensor doing real work — protecting the control loop from its least reliable instrument — without pretending to observe something unobservable.

## 4. Weather-forecast-driven predictive dosing — ADOPT the idea, REJECT the LSTM

The insight is correct and valuable: cooling load and evaporation are driven by wet-bulb temperature, and concentration dynamics are slow (hours), so a controller that sees tomorrow's weather can pre-position the loop instead of chasing it.

But an LSTM is the wrong instrument. You do not need to *learn* the weather — you can *obtain* it. National meteorological services run numerical weather prediction from atmospheric physics on supercomputers; an LSTM trained on a few site-years would be strictly worse, and would be exactly the "AI where physics already suffices" that Filter 8 penalises.

**Adopted:** feed the NWP forecast into the MPC as a **disturbance preview** across the prediction horizon. Standard, defensible, no learned component required. A small learned correction on the *local* bias of the forecast — site microclimate versus grid-cell forecast — is legitimate later, once site history exists to fit it, and it stays bounded, auditable and removable.

---

## 5. A physics-informed surrogate of the tower model — ADOPT, and it is now built

`src/pinn.py`. Gates pre-registered before training, in the same way as V1, V2 and V5.

**What it is.** A small network that reproduces the validated physics core — outlet water temperature and evaporation from ambient, flows and inlet water temperature. It is trained **against the core, not against the plant**, so it is a surrogate and inherits every limitation the core has. It is scored on how faithfully it reproduces the model, never on whether the model is right.

**Why bother, when the core already exists.** Two reasons, and the second is the one that matters.

1. **Speed and differentiability.** One duty fixed point costs a bracketed root-find over an RK4 integration — measured at **148 ms per point**. The optimiser solves hundreds per decision, which is why the shipped optimiser is a grid search rather than a gradient method. A differentiable surrogate at microsecond cost turns a five-minute advisory into a one-second setpoint, and makes constrained MPC feasible on edge hardware.

2. **It is the only honest thing that can be said about Gulf wet-bulb before the KFUPM rig exists.** The validation dataset tops out at 21.9 °C wet-bulb, and an hourly TMY year for Dhahran puts **40.5 % of all hours above that** — 84 % of hours in September (ASHRAE 2025 design wet-bulb 30.5 °C at 1 %). No amount of fitting closes that, because there is no data there. But a *physics-informed* network can be constrained where there is no data. The physics loss is evaluated at **collocation points sampled across the full Gulf envelope**, enforcing the inequalities thermodynamics guarantees everywhere:

   - a wet tower cannot cool water below the ambient wet bulb;
   - more air, at fixed duty, cannot make the water hotter;
   - hotter inlet water, at fixed air, cannot make the outlet colder;
   - the outlet cannot exceed the inlet.

   The second and third are **derivative** constraints, which is precisely what automatic differentiation is for. This does not invent measurements. It stops the fitted surface doing something physically absurd in the region the product is actually meant to operate in — which a purely data-driven surrogate has no defence against at all.

**Architectural discipline.** The wet-bulb bound is enforced **structurally**, not by penalty: the network predicts an approach, and the outlet is wet-bulb plus a strictly positive quantity. A hard physical bound belongs in the architecture; only the soft ones belong in the loss.

**Where it is forbidden.**

- **Not in the chemistry.** Speciation is algebraic thermodynamics with tabulated constants. A network there would add error, destroy auditability, and place a learned component inside a safety limit. The saturation state that bounds the optimiser is computed exactly, always.
- **Not in the safety path at all.** The surrogate proposes and the physics core disposes: any setpoint it suggests is re-checked against the core before it leaves the device.

**Result against the pre-registered gates.**

| Gate | Threshold, fixed before training | Result | |
|---|---|---|---|
| P1 fidelity to the core, outlet temperature MAE | ≤ 0.10 K | **0.022 K** | PASS |
| P1 fidelity to the core, evaporation MAPE | ≤ 1.0 % | **0.964 %** | PASS |
| P3 admissibility violations, Gulf extrapolation band | 0 of 5,000 | **0 of 5,000** | PASS |
| P4 speed-up over the physics core | ≥ 500× | **101,802×** | PASS |

141 ms per point for the core against 1.38 µs for the surrogate. The P3 breakdown is zero on every individual constraint: none below wet-bulb, none with ∂T/∂ṁₐ > 0, none with ∂T/∂T_wi < 0, none with outlet above inlet, across 5,000 points sampled at Gulf wet-bulbs the training data never reached.

**Three defects it exposed before it passed, all recorded.** None of them was a training failure; all three were encoding errors that a physical constraint refused to absorb, which is the same pattern as the fan correlation in hertz and the drift rate off by a hundred.

1. **The physics loss would not converge** — flat at 57.7. The sampler, not the network, was wrong: 42 % of collocation points had inlet water below the ambient wet bulb, where a wet tower is a heater rather than a cooler, so those points demanded both `T_wo ≥ T_wb` and `T_wo ≤ T_wi` simultaneously. Sampling inlet water *relative to the wet bulb* dropped the loss to 1e-4.
2. **Evaporation scored 32.9 % MAPE** against a 1 % gate. Loss-scaling defect: evaporation was trained unnormalised at order 1e-2 kg/s against a normalised temperature target, so that head received almost no gradient.
3. **Normalising it made the score worse, 69.4 %.** Architecture defect, and the clearest of the three: the head was `softplus(x)·σ + μ`, whose range is [mean, ∞). It could not represent the **60 %** of operating points whose evaporation lies below the mean. A strictly positive quantity needs range [0, ∞) — `softplus(x)·scale`, no offset. With that corrected the same network scored 0.964 %.

The gate thresholds were never moved. Each failure was diagnosed to a specific defect, the defect was fixed, and the run was scored again.

## The resulting stack, in dependency order

| Layer | Method | Status |
|---|---|---|
| Psychrometrics, tower heat/mass transfer | First principles (ASHRAE, Poppe) | Built, validated |
| Water and ion balance, evaporation | First principles, checked against measured water loss | Built, validated |
| Speciation, saturation at skin temperature | First principles (phreeqc.dat constants) | Built |
| Parameter calibration | Least squares / Bayesian on telemetry | Statistical estimation, not AI |
| Supervisory control | Constrained economic MPC + NWP preview | Next |
| Fouling state `R_f` | Recursive estimator (EKF/UKF) | TRL 4 |
| **Scaling kinetics residual** | **Learned, physics-bounded** | **TRL 4 — the load-bearing AI** |
| Shielded RL | Only if it beats MPC after TRL 4 | Deferred, may never |

**The one-line Filter 8 answer for the DTV form:** *No AI is claimed at TRL 3; the validated evidence is first-principles. The load-bearing learned component is the scaling-kinetics residual, which corrects a term the physics provably cannot supply — precipitation rate — while remaining bounded by a thermodynamic driving force the physics does supply. Remove it and the controller can still say whether scale is possible, but not when it will cost money, which is the product.*

## On Simulink and Simscape

Right tool, wrong week.

- **Not before 31 Aug.** The evidence package must be reproducible by a reviewer with no licence. Python with an open dataset and pinned requirements is auditable; a model needing a commercial toolbox is not.
- **Yes for TRL 4.** Simscape Fluids is the natural home for the plant model once hardware is in the loop, and Simulink Real-Time is the standard route to hardware-in-the-loop testing on the KFUPM rig. It is a defensible line item against DTV's SAR 200,000 product-development stream — precisely what that stream exists for.
- **Sequence:** validated Python physics core → Simscape plant model for HIL → generated embedded code for the edge controller. The Python core remains the reference implementation the Simscape model is checked against, so the two cross-validate rather than duplicate.
