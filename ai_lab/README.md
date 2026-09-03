# AI / ML lab — what machine learning is actually worth here

**FURQAN** · *The criterion for energy.*
**MIZAN** · *The balance between energy and water.*

This directory answers one question: **can machine learning save more water?**

It answers it in the order that costs least — bound the prize before building
anything, then build the simplest thing that could claim it, then see what is
left for a model to do. Two scripts, both with thresholds fixed before they
were first run.

```bash
python ai_lab/value_of_information.py   # what is knowing something worth?
python ai_lab/sulfate_bounds.py         # can we get it without ML?
```

---

## 1. Bound the prize first

A cooling tower's water use is arithmetic once the cycle count is known:
makeup = evaporation × C/(C−1). The controller cannot pass the cycle count
where a mineral saturates at the condenser skin. **So every cubic metre ML
could save has to come from moving that ceiling** — and the ceiling only moves
if something we are currently unsure about turns out better than assumed.

That makes the value of a model computable *without building it*: sweep the
uncertain input, find the ceiling at each value, and the spread in makeup water
is the absolute most that perfect knowledge could be worth. A real model is
worse than perfect, so these are ceilings on the benefit, not estimates.

| input | ceiling range | makeup at stake | measured? |
|---|---|---|---|
| **Ca** calcium | 5.25 – 10.50 cycles | **10.5 %** | **measured** — routine hardness |
| **SO₄** sulfate | 4.75 – 8.25 cycles | **10.2 %** | **NOT measured** — by anyone |
| **HCO₃** alkalinity | 5.00 – 7.25 cycles | 7.2 % | measured — it is inside LSI |
| skin ΔT | 7.00 – 7.25 cycles | 0.6 % | not measurable |

**Size is not the criterion. Measuredness is.** Calcium is the biggest lever
and is already on every plant's daily log — that is a data-entry problem, not
an inference problem. Skin temperature is unmeasurable but worth almost nothing
here, so the coupon rig is worth doing for other reasons and not this one.

> **The ML problem is sulfate.** 10.2 % of makeup water, and the largest lever
> that nobody measures. Three operator interviews confirm it: plants track TDS,
> pH, calcium hardness and alkalinity, and not one measures sulfate. The 1992
> training syllabus in `docs/discovery_findings.md` shows why — scale was taught
> as a carbonate phenomenon and sulfate was filed under corrosion.

### A gate that was wrong, and what replaced it

G-V2 required the sweeps to be monotonic. Two failed, and **both times the gate
was wrong, not the chemistry**:

- **Sulfate.** Below ~450 mg/L the binding mineral is *calcite*, not gypsum.
  Adding sulfate there raises ionic strength, lowers activity coefficients and
  genuinely raises apparent calcite solubility. "More sulfate cannot raise the
  ceiling" only holds once gypsum binds.
- **Skin temperature.** The gate assumed gypsum is retrograde. In this model it
  is not — SI_gypsum falls from 0.341 at 25 °C to 0.244 at 70 °C — so a hotter
  skin makes gypsum look *safer*. `docs/defect_register.md` already said so;
  the gate was written without reading it.

Replaced by per-mineral monotonicity, which is stricter: the claim is only
asserted inside the region where a given mineral actually binds.

---

## 2. Then try to win it without ML

The obvious move is to train a model to predict sulfate. It needs paired data —
routine analyses alongside full ion inventories — which does not exist here, and
a model fitted to water it has never seen is a confident guess dressed as a
measurement.

Sulfate is not free to be anything. Two conservation laws pin it:

```
electroneutrality   2[Ca] + 2[Mg] + [Na] + [K] = [HCO₃] + [Cl] + 2[SO₄] + [NO₃]
TDS closure         Σ dissolved species ≈ TDS
```

Given what a plant already measures, those bound sulfate from both sides. No
fitting, no training data, nothing that can be wrong about an unfamiliar water.

**Test:** the Aramco analysis has a measured SO₄ of 566 mg/L. It was withheld
and used only to score.

| gate | result | |
|---|---|---|
| **G-S1** interval contains the withheld truth | 566 ∈ [44, 928] mg/L | **PASS** |
| **G-S2** ceiling band ≤ 2.0 cycles | **2.50 cycles** | **FAIL** |
| **G-S3** a real interval, not a point estimate | 884 mg/L wide | **PASS** |

**G-S2 failed and the threshold has not been moved.** Conservation laws alone
put the gypsum ceiling somewhere between 5.50 and 8.00 cycles. That is correct,
it does contain the truth at 7.25 — and it is too wide to run a plant on. It
says "somewhere between comfortable and unsafe."

---

## 3. So ML now has a job, and a number to beat

The failure is the useful part. It converts a vague ambition into a
specification:

> **Tighten the gypsum-ceiling band from 2.50 cycles to ≤ 2.00, using only
> measurements plants already take.**

The width is driven almost entirely by the sodium sweep — 15 % to 45 % of TDS —
because nobody titrates sodium. But **regional groundwater is not a random
draw.** Punjab tubewells share a hydrogeology; the operator interviewed quoted
calcium hardness of roughly 120 ppm in Lahore, 240 in Sheikhupura, 250 in
Faisalabad. A prior over Na/Cl ratios learned from public groundwater chemistry
would narrow the sodium range and therefore the band.

**That needs a real dataset, so it is scoped and not faked.** No model is
committed here on synthetic data.

### What is deliberately not being built

- **A sulfate predictor trained on synthetic water.** It would learn the
  chemistry model's own covariance, not groundwater's, and score well against
  itself. Circular.
- **Reinforcement learning for dosing control.** No plant data, and the failure
  mode is a chemist's account of acid pumping all night after the makeup tripped
  and eating the tower tubes. That is an interlock problem, not a policy problem.
- **Anything described as "AI-powered".** The existing PINN earned its place by
  surrogating a 141 ms physics solve and is reported *with* its failed speed
  gate. The bar here is the same.

---

## Files

| File | What it does |
|---|---|
| `value_of_information.py` | Bounds what perfect knowledge of each input is worth, in makeup water. Decides which ML problem to work on — or whether to. |
| `sulfate_bounds.py` | Bounds sulfate from routine measurements by conservation laws alone. Scored against a withheld true value. |

Outputs: `results/value_of_information.json`, `results/sulfate_bounds.json`.

## What this lab is not

- It is **not** validated against plant data. No cooling tower has been
  instrumented, and the interviews are conversations, not measurements.
- The value-of-information sweeps run at a **fixed reference condition**
  (T_wi 40 °C, T_wo 32 °C, pH 8.0), not at the controller's operating point.
  They rank inputs; they do not predict the controller's ceiling.
- Sweep ranges are **engineering judgement**, and the answers are only as good
  as they are. They are stated in the source so they can be argued with.
