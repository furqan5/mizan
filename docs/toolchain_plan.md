# Simulation and CAD toolchain — decision record

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

Date: 29 August 2026. Tags: `[C]` verified on this machine or from a named source · `[A]` engineering judgement · `[VERIFY]` unresolved.

---

## 1. The problem: Simscape Fluids is not available

The plan of record was a Simscape Fluids plant model with the Python physics core as the reference and the controller as a supervisory layer. That is blocked.

`ver` lists **installed** products, not **licensed** ones. Checking out each product in turn on this machine gives: `[C]`

| Product | `license('checkout', ...)` |
|---|---|
| Simulink | OK |
| Simscape (base) | OK |
| Stateflow | OK |
| Model Predictive Control Toolbox | OK |
| System Identification Toolbox | OK |
| Control System Toolbox / Simulink Control Design | OK |
| Optimization Toolbox | OK |
| Curve Fitting Toolbox | OK |
| Deep Learning Toolbox | OK |
| Parallel Computing Toolbox | OK |
| MATLAB Coder | OK |
| Simulink Compiler | OK |
| **Simscape Fluids** | **FAIL — License Manager Error −5** |
| Simscape Electrical / Driveline / Multibody | FAIL |
| Embedded Coder | FAIL |

Base Simulink on this installation also has **no FMU Import block** — it is not present in `simulink/User-Defined Functions`. `[C]`

---

## 2. Recommendation: OpenModelica + the LBNL Modelica Buildings Library

Not merely a substitute. For this specific problem it is a better fit than Simscape Fluids was.

**Why.** The Modelica Buildings Library is developed by Lawrence Berkeley National Laboratory, is free and open source, and contains the exact components this plant needs rather than generic fluid primitives: `[C]`

- `Buildings.Fluid.HeatExchangers.CoolingTowers.Merkel` — a Merkel cooling tower, the same formulation as our core
- `Buildings.Fluid.Chillers.ElectricEIR` — the EnergyPlus `Chiller:Electric:EIR` bi-quadratic model
- `Buildings.DHC.Plants.Cooling` — district-cooling plant assemblies

**The detail that decides it.** The library ships the **same CoolTools chiller performance data we are already using**, including named records of the form `ElectricEIRChiller_York_YT_1055kW`. `[C]` Our Python core now runs on York YT 1758 kW / 6.28 COP from `datasets/Chillers.idf`, which is the same curve library. The Modelica plant and the Python reference would therefore be driven by **one** chiller dataset, not two that have to be reconciled. With Simscape Fluids they would have been two.

### 2.1 Coupling route (a) — OMMatlab. Preferred.

MATLAB drives the OpenModelica model directly through the OMMatlab API: build the model, set parameters, simulate, read results back as MATLAB arrays. No FMU, no import block, nothing further to license. `[C]`

The supervisory controller stays in MATLAB/Simulink where the licensed toolboxes are (MPC, Stateflow, System Identification), and the plant lives in Modelica.

### 2.2 Coupling route (b) — FMU. Fallback.

Export FMI 2.0 Co-Simulation from OpenModelica (`buildModelFMU`, or *File → Export → FMU* in OMEdit) and import into Simulink. `[C]`

Two cautions, both documented: `[C]`

1. Base Simulink here has no FMU Import block, so this needs the free **FMI Kit for Simulink** (Modelon/Dassault, open source).
2. OpenModelica-generated FMUs are known to fail to load in Simulink unless the OpenModelica `bin` directory is on the Windows `PATH` **before MATLAB starts** — Simulink loads the FMU's main DLL in a way that does not find the auxiliary DLLs inside the archive.

### 2.3 Setup

Neither OpenModelica nor OMPython is installed on this machine. `[C]`

```bash
# 1. OpenModelica (Windows installer, includes OMEdit and omc)
#    https://openmodelica.org/download/download-windows/
# 2. In OMEdit: Tools -> Library Browser -> install "Buildings"
#    or clone https://github.com/lbl-srg/modelica-buildings
# 3. MATLAB binding
pip install OMPython          # for the Python side
#    OMMatlab: https://github.com/OpenModelica/OMMatlab
```

### 2.4 What the HIL demo becomes

Unchanged in substance: **the demo is V6.** Drive a load transient through the Modelica plant, and show the brucite deposition criterion crossing in real time — while bulk pH and conductivity, the two things the plant actually instruments, stay flat. That is the single clearest demonstration that a saturation limit at the tube skin is not visible from bulk measurements.

---

## 2.5 What was actually built, and it runs today

The OpenModelica route above is the destination. It requires an install that has not happened yet, so the interim step was taken instead and it is complete: **a MATLAB twin of the validated physics core, in `matlab/`, using only toolboxes that check out on this machine.**

### What it contains

| File | Purpose |
|---|---|
| `matlab/mizan_demo.m` | One Gulf day, narrated in plain English. Written to be readable by someone with no thermodynamics. |
| `matlab/mizan_verify.m` | Scores the MATLAB twin against the validated Python core, on limits fixed before it was first run. |
| `matlab/mizan_pinn.m` | The physics-informed surrogate, in Deep Learning Toolbox. |
| `matlab/+mizan/` | The physics: ASHRAE psychrometrics, the Poppe integrator, the named chiller curves, the water balance, and the brucite saturation limit. |

### It agrees with the validated core

A second implementation of the same physics is worth nothing unless it is shown to reproduce the one that was actually scored against experiment. `mizan_verify` does that, against thresholds fixed in advance:

| Quantity | Worst disagreement | Limit | |
|---|---|---|---|
| Outlet water temperature | 0.000014 K | 0.010 K | PASS |
| Evaporation rate | 0.00018 % | 0.50 % | PASS |
| Chiller electrical power | 0.000000 % | 0.10 % | PASS |
| Brucite saturation pH | 0.0014 | 0.005 | PASS |

The case file both sides answer is written once, from the Python side, by `src/export_matlab_cases.py`.

### The MATLAB surrogate

| Gate | Threshold, fixed before training | Result | |
|---|---|---|---|
| Faithfulness to the physics model | ≤ 0.10 K | 0.0298 K | PASS |
| Physical violations over 4,000 Gulf points | 0 | 0 | PASS |
| Speed-up over the physics model | ≥ 500× | 298× | **FAIL** |

**The speed gate is failed and the threshold has not been moved.** Two things explain it and both are worth stating rather than hiding. The 500× threshold was written against the Python core at 141 ms per point; MATLAB's core is ten times faster at 14.7 ms, so the same surrogate scores a smaller *ratio* against a faster baseline. And at a batch of 60 the per-call `dlarray` overhead dominates the 49 µs per point.

The absolute figure is the one that matters for the product: **49 µs per candidate operating point**, which is what turns a grid search taking minutes into one taking a fraction of a second. But the gate as written says FAIL, so FAIL is what is recorded.

### The Simulink model, and the toolboxes around it

`matlab/build_mizan_model.m` constructs `mizan_plant.slx` programmatically, so the model is reviewable as text rather than shipped as a binary. It runs one Dhahran day in about 90 seconds.

- **Simscape** (base Foundation library, no Fluids): the loop's thermal inertia as a physical network — 150 t of basin water, a heat-flow source and a temperature sensor, with the network on its own fixed-step local solver as an edge device would run it.
- **Stateflow**: the supervisor. SHADOW → ADVISORY → CLOSED LOOP, with a hard FALLBACK on sensor loss or on leaving the chiller envelope. The product ships read-only and earns write access one actuator at a time.
- **MATLAB Function blocks**: the validated Poppe tower, the named York YT chiller curves, and the brucite limit at the tube skin.

Result: basin 26.9–32.4 °C, tube skin 38.4–46.2 °C, scale limit moving over pH 8.43–8.89, and **11.1 of 24 hours above that limit** with both plant instruments reading flat. Those figures match `mizan_demo.m`, which reaches the same conclusion with no Simulink involved at all.

**Three defects the model exposed, none of them a physics error:**

1. **The Simscape sensor reads Kelvin**, and the first run treated it as Celsius. The chemistry was asked for a saturation pH at 341 °C and the chiller reported itself out of envelope for the whole day. Both refused. Fourth unit defect in this project, fourth caught the same way.
2. **The heat-flow sign was inverted.** +1000 kW into a 150 t mass for 600 s gave −0.956 K — right magnitude, wrong direction, which is the signature of a sign convention rather than a physics error.
3. **An algebraic loop.** Simulink declined to run a model in which the controller acted on a measurement it was causing in the same instant. It was right to. One 60-second step of delay is both the fix and the truth.

### Control design: five toolboxes, five jobs

`matlab/mizan_control_design.m`.

| Toolbox | Job | Result |
|---|---|---|
| Curve Fitting | confidence bounds on the fill law | c = 1.2741, 95 % CI [1.2312, 1.3170]. The 21 % drift across campaigns is **wider than** one campaign's interval, so it is physical, not fitting noise |
| System Identification | the loop's real time constant | τ = 513 s at 99.9 % fit, vs 314 s from inventory alone. The 1.6× gap is the condenser feedback |
| Control System | a PI and its margins | Kp -15.40, Ki -0.09005, phase margin 60° |
| Model Predictive Control | the chiller ceiling as a **hard** constraint | entering condenser water capped at 35.0 °C — the constraint the optimiser once walked straight through |
| Optimization | replace the grid search | finds a better point but is **8× slower** against the exact physics |

That last line is reported as it came out. A gradient method estimates derivatives by finite differences, so each step costs several full physics solves. **Optimisation does not beat a grid search until the objective is cheap to differentiate** — which is the argument for the surrogate, and the reason it exists.

Two methodological notes, both learned here: identify a *settled* plant (a step applied to a loop still coming off its initial condition returned a time constant of 1.9×10¹⁷ s at an 11 % fit), and give the estimator a pre-step baseline.

### The MATLAB surrogate

| Gate | Threshold, fixed before training | Result | |
|---|---|---|---|
| Faithfulness to the physics model | ≤ 0.10 K | 0.0298 K | PASS |
| Physical violations over 4,000 Gulf points | 0 | 0 | PASS |
| Speed-up over the physics model | ≥ 500× | 298× | **FAIL** |

The speed gate is failed and the threshold has not been moved. The 500× figure was written against the Python core at 141 ms per point; MATLAB's core is ten times faster at 14.7 ms, so the same surrogate scores a smaller ratio against a faster baseline, and at a batch of 60 the per-call `dlarray` overhead dominates the 49 µs per point. The absolute figure — **49 µs per candidate** — is what matters for the product, but the gate as written says FAIL.

### Why this does not replace the OpenModelica plan

The MATLAB twin is a faithful reimplementation, which means it inherits the maintenance cost of every physics correction being made twice. That is exactly the reason the Modelica route is still preferred for the plant model: it lets the Python core stay the single reference. The MATLAB twin's job is the **demonstration** — a legible, runnable artefact that a reviewer can execute in one command — and for the hardware-in-the-loop work it is the fallback if OpenModelica integration stalls.

---

## 3. Alternatives considered and rejected

| Option | Verdict |
|---|---|
| **Buy Simscape Fluids** | Not rejected on merit — rejected on cash. Zero founder runway; and the Modelica route is not a downgrade. `[A]` |
| **Dymola** | Same Modelica language, commercial licence. No advantage over OpenModelica at this stage. `[A]` |
| **Plain Simulink + MATLAB Function blocks** porting the Python core | Viable and needs nothing new, but it duplicates the physics in a second language, and every future correction then has to be made twice. Reserved as the fallback if OpenModelica integration stalls. `[A]` |
| **SimulationX / Modelon Impact** | Commercial. Modelon Impact does host the Buildings Library, which is worth knowing if a partner offers access. `[C]` |

---

## 4. 3D CAD via MCP, and CFD afterwards

### 4.1 Why we want it — the engineering reason, not the novelty

The chemistry chain has one number in it that is assumed rather than derived: the **condenser tube skin temperature rise, taken as +8 K above bulk**. Every V3 and V5 result scales with it. It is currently supported by literature convention, and it is the least-defended input in the package.

A boundary-layer CFD of the condenser tube — real geometry, real water-side velocity, real fouling-layer thickness — would let that number be **computed** instead of assumed, and would let it move with load rather than staying fixed. That is worth doing, and it is the reason to want CAD in the loop at all.

### 4.2 Recommendation: FreeCAD

FreeCAD is the only realistic option for this stack: free, fully scriptable in Python, exports STEP and STL, and several Model Context Protocol servers already exist for it — one of which ships OpenFOAM and FluidX3D hooks so a design → simulate → analyse loop can run without touching the GUI. `[C]`

Nothing is installed yet. `[C]`

**Route.** FreeCAD MCP → parametric condenser-tube and sensor-skid geometry → STEP → OpenFOAM (conjugate heat transfer, water side + tube wall) → skin temperature as a function of load, velocity and fouling thickness → back into `chemistry.py` as a computed `skin_delta_k` rather than a constant.

**Second use, and it is the commercial one.** The sensor skid is a physical product that has to be manufactured. Parametric CAD of the skid — sensor ports, valve, flow path, enclosure — is a deliverable DTV can see, and it is the difference between "a controller" and "a device".

### 4.3 Honest caveat

CFD is a large piece of work with its own validation burden, and it would arrive with no experimental verification of its own. It should not be started before the KFUPM rig closes the wet-bulb gap, because the rig is the thing that actually moves the evidence package. Sequence it **after** TRL 4, not instead of it. `[A]`

---

## 5. Where the physics-informed network fits

See `src/pinn.py`, whose gates were pre-registered before training in the same way as V1, V2 and V5. In short:

- **It is a surrogate for the physics core, scored against the core** — not a model of the plant, and not evidence about the plant.
- **Its purpose is speed and differentiability**, so the grid search can become a gradient method on edge hardware, and
- **its physics loss is evaluated where there is no data** — at collocation points across the Gulf envelope, enforcing the inequalities thermodynamics guarantees everywhere: a wet tower cannot cool below the ambient wet bulb; more air cannot warm the water; hotter inlet water cannot cool the outlet; the outlet cannot exceed the inlet. That is the only honest thing that can be said about 30 °C wet-bulb operation before the KFUPM rig exists.
- **It is forbidden from the chemistry and from the safety path.** Speciation is algebraic thermodynamics and must stay exactly computable; the surrogate proposes and the core disposes.
