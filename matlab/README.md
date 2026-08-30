# The MATLAB model — start here

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

You do not need to know thermodynamics to use this. Read section 1, run the demo, and you will have seen the whole idea.

---

## 1. What the product does, in plain English

A district-cooling plant makes cold water for a whole district. To do that it has to throw heat away, and the cheapest way to throw heat away is to evaporate water in a **cooling tower**.

Evaporation leaves the minerals behind. So the water going round and round the loop gets steadily saltier, and if it gets too salty the minerals crystallise on the inside of the condenser tubes. That is **scale**: it insulates the tubes, the plant works harder for the same cooling, and eventually the plant has to be shut down and cleaned.

To stop it, operators throw some water away and top the loop up with fresh water. Throw away too little and you get scale. Throw away too much and you waste desalinated water, which in the Gulf is expensive.

Everyone in the industry knows this. Here is what they do not measure.

**Scale does not form in the water. It forms on the hottest surface touching the water** — the skin of the condenser tube, several degrees hotter than the water around it. And for one important scale-forming mineral, **the limit gets tighter as that surface gets hotter**. So the same tower, with its pH meter and its conductivity meter both reading perfectly steady, is safe in the morning and laying down scale in the afternoon.

That is the gap Mizan closes.

---

## 2. Run this first

```matlab
>> cd matlab
>> mizan_demo
```

It simulates one hot day in Dhahran and prints, hour by hour, what the plant's instruments saw and what was actually happening. It writes one figure, `figs/matlab_one_gulf_day.png`, with three panels:

1. **the temperatures** — including the tube skin, which no instrument on a real plant measures
2. **the scale limit** — which falls as the load rises, crossing the line the plant actually runs at
3. **what the plant's own two instruments showed** — two flat lines, all day

The gap between panels 2 and 3 is the entire commercial argument.

---

## 3. The files, and what each is for

| File | What it is |
|---|---|
| `mizan_demo.m` | **Start here.** One Gulf day, narrated in plain English. No Simulink needed. |
| `mizan_verify.m` | Proves this MATLAB model agrees with the Python model that was validated against real experimental data. |
| `mizan_simulate.m` | Runs the Simulink plant model and explains the result. |
| `build_mizan_model.m` | Builds `mizan_plant.slx` from scratch, so the model is text, not a binary. |
| `mizan_control_design.m` | Curve Fitting, System Identification, Control System, MPC and Optimization, each doing one real job. |
| `mizan_pinn.m` | Trains a small neural network to imitate the physics, fast enough for a controller. Needs Deep Learning Toolbox. |
| `mizan_tower_step.m`, `mizan_chiller_step.m`, `mizan_chem_step.m` | The three physics calls the Simulink model makes each step. |
| `+mizan/` | The physics itself, one function per file. Every file says what it does and why. |

If you only run one thing, run `mizan_demo`. If you only run two, add `mizan_simulate`.

Inside `+mizan/`:

| File | What it computes |
|---|---|
| `pws.m`, `ws.m`, `hmoist.m`, `wetbulb.m`, … | Properties of moist air (ASHRAE standard formulas) |
| `poppe_derivs.m`, `integrate_poppe.m` | Heat and moisture exchange between falling water and rising air |
| `solve_outlet.m` | How cold the tower actually gets the water |
| `chiller.m`, `chiller_power.m` | How much electricity the chiller draws — a **named** machine, not a generic curve |
| `water_balance.m` | Evaporation, drift, blowdown, makeup |
| `ph_sat_brucite.m` | **The scale limit at the tube skin.** This is the one nobody else computes. |

---

## 4. Why you can trust it

This MATLAB model is a second implementation of a physics model that was validated against a published experimental dataset (a cooling-tower pilot plant at Plataforma Solar de Almería, 165 measured operating points, freely available and MD5-verified).

A second implementation is worth nothing unless it agrees with the first. So:

```matlab
>> mizan_verify
```

scores the agreement against limits that were fixed **before it was first run**. As of the last run:

| Quantity | Worst disagreement | Limit | |
|---|---|---|---|
| Outlet water temperature | 0.000014 K | 0.010 K | PASS |
| Evaporation rate | 0.00018 % | 0.50 % | PASS |
| Chiller electrical power | 0.000000 % | 0.10 % | PASS |
| Brucite saturation pH | 0.0014 | 0.005 | PASS |

So anything this model says can be traced back to physics that was scored against a real experiment.

---

## 5. The neural network, and its limits

```matlab
>> mizan_pinn
```

The physics model is exact but slow — about 15 ms per operating point in MATLAB. A controller has to try hundreds of options before choosing one, so it needs something faster. `mizan_pinn.m` trains a small network to imitate the physics.

It is **physics-informed**, which is the part that matters. A network trained only on data can say anything at all where there is no data — and our measurements stop at 21.9 °C wet-bulb, and an hourly TMY year for Dhahran puts **40.5 % of all hours above that** (ASHRAE 2025 design wet-bulb 30.5 °C at 1 %). So alongside "match the model", the training enforces four things thermodynamics guarantees everywhere, at points across the full Gulf range where no data exists:

1. a wet tower cannot cool water below the wet-bulb temperature
2. more air cannot make the water hotter
3. hotter water in cannot give colder water out
4. the water coming out cannot be hotter than the water going in

Rules 1 is built into the network's structure so it *cannot* be broken. Rules 2–4 are enforced during training.

**Results against gates fixed before training:**

| Gate | Limit | Result | |
|---|---|---|---|
| Faithfulness to the physics model | ≤ 0.10 K | 0.030 K | PASS |
| Physical violations over 4,000 Gulf points | 0 | 0 | PASS |
| Speed-up over the physics model | ≥ 500× | 298× | **FAIL** |

**The speed gate is reported as failed and the threshold has not been moved.** Two things explain it, and both are worth stating rather than hiding:

- The 500× threshold was written for the Python implementation, whose physics core takes 141 ms per point. MATLAB's core is ten times faster at 14.7 ms, so the same surrogate scores a smaller *ratio* against a faster baseline.
- At a batch of 60, MATLAB's per-call `dlarray` overhead dominates the 49 µs per point.

The absolute number is the one that matters for the product: **49 µs per candidate operating point**. That is what turns a grid search that takes minutes into one that takes a fraction of a second, which was the entire purpose. But the gate as written says FAIL, so FAIL is what is recorded.

**Where the network is never allowed:** nowhere near the chemistry, and nowhere in the safety path. The saturation limits that bound the controller are computed exactly, every time. The surrogate proposes; the physics decides.

---

## 6. The Simulink plant model

```matlab
>> mizan_simulate
```

Builds `mizan_plant.slx` if it is not there, runs one Dhahran summer day, and explains the result. About 90 seconds.

The model is **built by a script**, `build_mizan_model.m`, rather than shipped as a binary. Every block, parameter and connection is therefore reviewable as text and sits under version control — which matters, because three real defects were found in it and each is recorded in the comments where it happened.

| Part | What it is |
|---|---|
| Cooling tower | the validated Poppe model, in a MATLAB Function block |
| Chiller | the named York YT curves |
| **Loop thermal mass** | **a Simscape physical network** — 150 t of basin water, a heat source and a temperature sensor. This is what makes the plant *slow*, and slow is what makes it a control problem |
| Scaling limit | brucite saturation pH at the tube skin |
| **Supervisor** | **a Stateflow chart**: SHADOW → ADVISORY → CLOSED LOOP, with a hard FALLBACK on any fault |

What the run produces:

| | |
|---|---|
| basin water | 26.9 to 32.4 °C |
| condenser tube skin | 38.4 to 46.2 °C |
| scale limit at the skin | pH 8.43 to 8.89 — it **moves**, by 0.46 pH units |
| hours above the scaling limit | 11.1 of 24 |
| entering condenser water inside the chiller envelope | yes, all day |

Those numbers match `mizan_demo.m`, which reaches the same conclusion by a completely different route with no Simulink involved. Two independent paths through the same physics landing in the same place is the point of having both.

### Three defects this model exposed

None was a physics error. All three were the kind of thing a physical model refuses rather than absorbs.

1. **The Simscape sensor reads Kelvin.** The first run treated it as Celsius, so the chemistry was asked for the saturation pH at 341 °C and the chiller reported itself out of envelope for the entire day. Both refused. It is the fourth unit defect in this project and the fourth caught the same way.
2. **The heat-flow sign was inverted.** Pushing +1000 kW into a 150 t mass for 600 s gave −0.956 K: exactly the right magnitude, exactly the wrong direction. That signature is a sign convention, not a physics error, and the only reliable way to settle it is to push a known heat flow into a known mass and check against arithmetic.
3. **An algebraic loop.** Simulink refused to run a model in which the controller acted on a measurement it was causing in the same instant. It was right to: an instantaneous sensor does not exist. One 60-second step of delay is both the fix and the truth.

## 7. Control design — five toolboxes, five jobs

```matlab
>> mizan_control_design
```

| | Job | Result |
|---|---|---|
| **Curve Fitting** | confidence bounds on the fill law | c = 1.2741, 95 % CI [1.2312, 1.3170] — the 21 % drift seen across campaigns is **wider than** a single campaign's interval, so it is a real physical change, not fitting noise |
| **System Identification** | the loop's real time constant | τ = 513 s at a 99.9 % fit, against 314 s from inventory alone. The 1.6× gap is the condenser feedback, and it is the same coupling this product exists to price |
| **Control System** | a PI and its margins | Kp = -15.40, Ki = -0.09005, phase margin 60° |
| **MPC** | the chiller ceiling as a **hard** constraint | entering condenser water capped at 35.0 °C. This is the constraint the optimiser once walked straight through; a PI cannot express it |
| **Optimization** | replace the grid search | finds a better point, but is **8× slower** against the exact physics |

That last result is reported as it came out. A gradient method estimates derivatives by finite differences, so each step costs several full physics solves, and one solve is a bracketed root find over an RK4 integration. **Optimisation does not beat a grid search until the objective is cheap to differentiate** — which is the argument for the physics-informed surrogate, and the reason it exists.

Two methodological notes, both learned the hard way here:

- **Identify a settled plant.** The first attempt stepped a loop still coming off its initial condition and `tfest` returned a time constant of 1.9×10¹⁷ seconds at an 11 % fit — a number with no physical meaning, produced because the data held a start-up transient and a step response on top of each other.
- **Give the estimator a baseline.** A step that begins at sample one leaves nothing to separate the plant's dynamics from its initial condition, and `tfest` says so.

## 8. OpenModelica

Written but not runnable here: see `modelica/README.md`. The reason it is the destination rather than a curiosity is that the **LBNL Buildings library ships the same CoolTools chiller data the Python core uses**, so a Modelica plant and the Python reference would be driven by one dataset instead of two. `python src/run_modelica.py` detects whether OpenModelica is installed and says plainly what is missing.

## 6. What this model is not

- It is **not** validated against an operating plant. No field data exists yet.
- It is **not** a scaling-*rate* model. It tells you when you are past the limit, not how fast scale then grows. Rates are site-specific and need laboratory work.
- The experimental data behind it tops out at **21.9 °C wet-bulb**, and Gulf design is **30.3 °C**. Closing that gap needs the KFUPM humidifying wind tunnel. It is the largest open item in the whole package and it is not papered over anywhere.
