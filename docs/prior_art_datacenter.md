# The gap replicates in data centres. The energy half is worse prior art there.

**Written 6 September 2026**, replicating the method of `prior_art_esc.md` on the
data-centre cooling-control literature, after the question was raised whether a
data-centre concept ("NeuroThermal": physics-informed MPC for hyperscale CDUs)
should be pursued as a separate venture.

Same nine-term chemistry vocabulary. Same mirror-image test. Same mechanical
scan — full texts downloaded and grepped, not summarised.

---

## Headline

| side | documents | chemistry terms | control terms |
|---|---|---|---|
| data-centre cooling **control** | 10 | **0** | 989 |
| data-centre cooling **water** | 5 | 112 | **0** |

**Zero. Again. Across 735,000 characters of control literature.** The two
literatures do not intersect in data centres either, and the separation is if
anything cleaner than in condenser water, because there is not even a `fouling`
artefact to explain away.

---

## The control corpus (all full text, all scored)

| arXiv | paper | CHEM | control | water |
|---|---|---|---|---|
| 2211.07357 | Controlling Commercial Cooling Systems Using RL *(DeepMind/Google, BCOOLER)* | **0** | 187 | 63 |
| 2603.01198 | Digital Twin-Based Cooling System Optimization for Data Center | **0** | 236 | 57 |
| 2605.15516 | Co-Design Optimization for Data Center Cooling System via Digital Twin | **0** | 147 | 18 |
| 1709.05077 | Transforming Cooling Optimization for Green Data Center via Deep RL | **0** | 107 | 21 |
| 1808.10427 | Reinforcement Learning Testbed for Power-Consumption Optimization | **0** | 98 | 5 |
| 2501.15085 | Data Center Cooling System Optimization Using Offline RL *(deployed, production)* | **0** | 86 | 35 |
| 2602.02137 | DCoPilot: Generative AI-Empowered Policy Adaptation for DC Operations | **0** | 78 | 14 |
| 2601.02275 | Machine Learning Guided Cooling Optimization for Data Centers | **0** | 30 | 4 |
| 2410.05133 | A Digital Twin Framework for Liquid-cooled Supercomputers at Exascale *(ORNL/Frontier)* | **0** | 15 | 22 |
| 2509.16513 | Trace Replay Simulation of MIT SuperCloud for Sustainability Policies | **0** | 5 | 0 |

Extended probe across all ten, for terms that were *not* in the original nine:
`water quality` 1 · `corrosion` 1 · `fouling` 1 · `precipitat*` 1 ·
`water treatment` 0 · `water chemistry` 0 · `conductivity` 0 · `TDS` 0 ·
`biocide` 0 · `chemical` 0 · `dissolved` 0 · `ion` 0.

`scale`/`scaling` returns 72 hits in 10/10 documents and **all but one** mean
*scale up*, *large-scale*, or *reward scale* — the same disambiguation the
condenser-water sweep required. The one exception is the whole point.

## The one exception, and it is the strongest evidence in this file

DeepMind's BCOOLER paper mentions mineral scaling **exactly once**, in section 7.3,
*"Non-stationary dynamics and observations"* — the section about things that
break their agent:

> *"In chiller plants, the chiller's capacity and performance degrades over a
> timescale of months to years, due to fouling of the heat exchanger surfaces by
> mineral scaling, biofilms, dust and dirt, and corrosion. Once the heat
> exchanger is cleaned, the chiller's efficiency immediately increases."*

The best-resourced cooling-control team on earth names mineral scaling as a
disturbance that degrades their learned model, and then gives it no state
variable, no sensor, and no term in the objective. They are not weighing the wall
lightly. **They have written down that the wall exists, that it moves, and that
they cannot see it.**

That is the Mizan thesis, stated by the adversary, in the adversary's own paper.
It is a better citation than any of the zeros.

## The mirror image

| document | CHEM | optimal-control |
|---|---|---|
| ChemTreat US 12,358,820 B2 — online control of chemical treatment using scale saturation indices | 40 | **0** |
| Genesis Water — cooling-tower blowdown / DC water efficiency | 39 | **0** |
| Amiad — DC cooling water, higher cycles of concentration | 17 | **0** |
| Genesis Water — treated wastewater for DC cooling | 14 | **0** |
| Li et al. 2023, *Making AI Less "Thirsty"* (arXiv 2304.03271) | 2 | **0** |

Grundfos's DC water-treatment page was read in full: LSI is used as a *diagnostic*
for manual dosing and cycles adjustment. No setpoint optimisation, no control
loop. It sits on the water side of the gap, exactly like DOE FEMP BMP #10.

## Vendors: same result

| vendor | what it optimises | CHEM |
|---|---|---|
| **Phaidra** (ex-DeepMind team; liquid-cooling CDUs, chiller plant, GPU T-limits) | RL closed-loop cooling control | **0** |
| Vigilent (400 KB scanned) | AI thermal/airflow control | **0** |
| EkkoSense (202 KB scanned) | thermal optimisation, DCIM | **0** |
| DeepMind DC-cooling announcement | autonomous cooling control | **0** |

---

## What this costs the data-centre concept, precisely

The chemistry gap is real in data centres. **The energy pitch is deader here than
it was in condenser water.**

In condenser water the competition was six papers and one live deployment. In
data centres it is:

- **Phaidra**, funded, founded by the people who ran Google's DC-cooling project,
  selling closed-loop RL control of *liquid-cooling CDUs and chiller plant* to AI
  data centres. This is NeuroThermal, already built, already shipping.
- **2501.15085** — physics-informed offline RL, graph neural network, **deployed
  in a large-scale production data centre for closed-loop control**, reporting
  **14–21%** cooling-energy savings without safety violations.
- **Lazic et al. 2018** — MPC on Google's data centres, *"a rigorously documented
  17.9% cost reduction"* (as quoted by 2603.01198).
- **2605.15516** — three-layer optimisation that allocates **CDUs across
  subloops** and co-optimises total flow rate and supply temperature. That is
  NeuroThermal's section 3, published.

And the headline savings number in the concept document does not survive contact
with its own source. 2603.01198 reports three strategies and labels them itself:

| strategy | saving | the paper's own words |
|---|---|---|
| A — flow-only | 20.4% | conservative baseline |
| B — unconstrained co-optimisation | **30.1%** | *"without operational constraints, revealing the theoretical maximum savings"* |
| C — ramp-constrained co-optimisation | 27.8% | actuator rate limits re-imposed |

The 30%+ figure is explicitly the **unconstrained theoretical ceiling**, not an
achievable result — the same shape as [[mizan-chiller-capacity-defect]], where
every headline number fell a third once a logged-but-unenforced limit was
enforced. Quoting B as the value proposition repeats the defect on someone
else's data.

## The honest counter-finding, which narrows a Mizan claim

**ChemTreat Inc, US 12,358,820 B2**, priority 2020-08-25, active to 2042:
*"Systems and methods for online control of a chemical treatment solution using
scale saturation indices."* Real closed-loop control, on a saturation index,
online, in industrial water systems.

So the sentence *"nobody closed-loop-controls on a mineral saturation index"* is
**dead**. Do not say it.

What the patent actually contains, scanned term by term:

| | hits |
|---|---|
| Langelier / LSI | 90 |
| calcite / calcium carbonate | 19 |
| silica | 2 |
| **gypsum / calcium sulfate / CaSO4** | **0** |
| **skin / wall / surface temperature** | **0** |
| **cycles of concentration** | **0** |
| **fan speed** | **0** |
| blowdown | 1 |
| energy | 4 |
| data centre | 0 |

It is LSI/RSI — calcium carbonate, bulk water, **dosing only**, no energy
objective, no fan or blowdown handle, not data-centre specific. It is the
automated version of what the chemical vendor's technician already does, which is
precisely where [[mizan-customer-discovery-2026]] found the field sitting. Note
that its own list of scaling compounds is *"calcium, silica, magnesium"* —
**sulfate is absent there too.** The 1992-syllabus gap shows up in a 2020 patent.

The surviving claim, stated at the width the evidence supports:

> Not: nobody controls on a saturation index.
> **Yes: nobody evaluates an ion-specific saturation at the heat-transfer surface,
> and nobody couples that constraint to an energy objective.**

## Consequence

The data-centre concept should **not** be a separate venture. Its energy half
competes with a funded ex-DeepMind incumbent and a production deployment, from
below and from Lahore. Its chemistry half is empty — and Mizan already owns that,
with a measured whitespace, a physics core and interview evidence.

The move is a **customer-segment extension of Mizan**, not a fifth company: Gulf
data centres run evaporative cooling towers, on TSE makeup, at high cycles, in
45 C ambient, with WUE as a publicly reported and politically exposed number,
and with a far more valuable asset behind the heat exchanger. The cooling-water
loop also sits outside the IT/OT security boundary that makes closed-loop CDU
control a 12–24-month procurement — which is why it is sellable and why nobody is
optimising it.

## Limits of this sweep — read before citing it

1. **Ten control papers is a sample, not a census**, and it is arXiv-biased
   (open-access, English, downloadable full text).
2. **One paper that matters was not read.** *"Physics-informed machine
   learning-based adaptive predictive control for energy-efficient hybrid-cooled
   data centers management"*, Applied Energy 2026 (S0306261926010688), jointly
   models CDU, chiller, cooling tower and pumps. It is the closest published work
   to the data-centre concept and it is paywalled. **Unread. Get it before any
   pitch.**
3. **Vendor homepages are marketing surfaces**, not specifications. A zero there
   is weaker evidence than a zero in a paper.
4. **One patent is not a freedom-to-operate search.** US 12,358,820 is a
   continuation-in-part of 17/001,720; the family was not walked, and Nalco/Ecolab,
   Veolia and Kurita were not searched at all. That is a lawyer's job.

---

## Extension, 7 September 2026: eight more documents, same instrument, same answer

Eight further sources were supplied and scanned with the identical nine-term
vocabulary. Text extracted with `pdftotext` and grepped; no summarisation.

| document | CHEM | control | water |
|---|---|---|---|
| 2603.01198v4 — Digital Twin-Based Cooling System Optimization *(v4 of the paper already in the corpus)* | **0** | 228 | 44 |
| 2605.15516v4 — Co-Design Optimization via Digital Twin | **0** | 171 | 20 |
| 3575813.3595189 — **Phyllis: Physics-Informed Lifelong RL for DC Cooling Control** (NTU, e-Energy '23) | **0** | 92 | 21 |
| 2606.15408v2 — Data Center Life Cycle Co-Design Optimization | **0** | 31 | 12 |
| 2608.19552v1 — End-to-end differentiable transient vapor-compression (JAX) | **0** | 31 | 2 |
| 2606.11163v1 — **Revisiting "Cooler is Better": ITD-Aware Per-CPU Thermal Optimization** | **0** | 28 | 2 |
| j.jcp.2018.10.045 — Raissi et al., Physics-Informed Neural Networks | **0** | 12 | 4 |
| Infineon AN — Tj from transient Rth data | **0** | 0 | 0 |

**Zero across all eight.** A context grep for every chemistry term over the
whole new corpus returns nothing at all — not one hit to disambiguate.

**The corpus is now 18 control-side documents and the count is still zero.**
That includes a *physics-informed* RL controller (Phyllis) and a
*differentiable thermodynamic* framework (2608.19552), which are the two
categories most likely to have carried a chemistry term if anyone had thought
of it.

### The one that changes the thesis: ITD

**2606.11163** is the most important new source, and it is not prior art — it is
the missing half of the physical argument.

It measures, on production Intel Xeon CPUs and *for the first time*, that
inverse temperature dependence produces **a distinct minimum in total power at
an intermediate temperature**, and that *"efficiency-optimal temperatures are
CPU part-specific, and frequently higher than typical data center operating
conditions"* — roughly half of modern high-power CPUs run about **10 °C below**
their efficiency-optimal point, worth **4–13 %** of total data-centre energy.

Put that beside Mizan's result and the two point in opposite directions:

> **The silicon wants to run warmer. The condenser tube wants to run cooler.
> The quantity that decides where you land is ion-specific mineral saturation
> at the heat-transfer surface — and it is in nobody's objective function.**

That is a sharper hybrid thesis than anything in the NeuroThermal concept
document, it is evidenced on both sides, and the 18-document scan says the
coupling is unclaimed. It also inverts the usual framing: ITD says the
efficiency argument for chilling harder is *wrong above the optimum*, which
removes the very lever the incumbent controllers optimise and leaves the
chemistry constraint as the binding one.

### Repository notes, including one licence problem

| repo | licence | note |
|---|---|---|
| `patrick-kidger/equinox` | **Apache-2.0** | fine to use; JAX NN library |
| `HewlettPackard/sustain-cluster` | **MIT** | fine; Gymnasium env for geo-distributed DC scheduling |
| `m-iml/Co-Design_Optimization_Data_Center_Digital_Twin` | **NOASSERTION** | code for 2605.15516; GitHub could not resolve a licence — **treat as all-rights-reserved until confirmed** |
| `alibaba/clusterdata` | **none** | **No licence file at all.** GitHub reports no licence, which by default means all rights reserved — not public domain. |

**`alibaba/clusterdata` having no licence is a real problem**, because it is the
exact dataset the NeuroThermal concept document proposes as its training spine
(*"the training data can be synthesized using publicly available traces, such as
the Alibaba GPU Cluster Trace"*). A venture cannot build a moat on a dataset it
has no licence to use commercially. **Verify the terms before any of it reaches
a pitch**, and note that `sustain-cluster` (MIT) is a licensed alternative for
workload profiles. See [[licensing-posture-by-venture]].
