# The energy half of this product is prior art. The chemistry half is empty.

**Written 4 September 2026**, after reading Li, Li & Seem, *"Extremum Seeking
Control of Cooling Tower for Self-optimizing Efficient Operation of Chilled Water
Systems"*, 2012 American Control Conference, pp. 3396-3401 (Johnson Controls /
UW-Milwaukee / UT Dallas).

This is the most commercially important paper in the literature reviewed so far,
and it is uncomfortable reading in the right way.

---

## What that paper already does

An **extremum seeking controller** takes the combined power of the chiller
compressor and the tower fan as feedback, uses **tower fan speed as the control
input**, and searches in real time for the minimum. Its Figure 2 is the exact
trade-off curve this product is built around: chiller power falling as tower
airflow rises, fan power rising as its cube, a convex total with a clear interior
optimum near 0.75 relative airflow.

Three things about it matter here:

1. **It is nearly model-free.** No tower model, no chiller curve, no calibration.
   It measures power and walks downhill.
2. **It is from Johnson Controls**, published in 2012, on real chiller-plant
   hardware assumptions, with the anti-windup and fan-saturation handling worked
   out.
3. **Fan speed is the input**, chosen deliberately over condenser-water setpoint
   because *"with the typical variable-speed drive equipped for the cooling
   towers nowadays, setting the VSD frequency or the motor speed is direct and
   simple. No cost or uncertainty is needed for the temperature sensor."*

**So: a self-optimising cooling-tower fan controller that captures the
energy trade-off has existed as published work for fourteen years, needs no model
at all, and comes from the largest incumbent in building controls.**

---

## What this costs Mizan, precisely

It removes the energy pitch. Not weakens — removes.

Mizan's own numbers make that unavoidable. After defects 11, 15 and 16, the
five-condition mean **electrical** saving is **2.86 %**, and in the four hottest
of eight annual bins it is **under 0.6 %** because the chiller capacity limit
blocks the fan-slowing move. An ESC controller would capture most of what is
left, model-free, with no chemistry, no calibration and no annual licence.

Any pitch of the form *"we optimise fan speed and chiller power together"* is
answered by a 2012 ACC paper and a Johnson Controls product line. **It should not
be made.**

---

## What it does not touch, and why that is the whole company

An extremum seeking controller optimises what it can measure, and it measures
**power**. It has no state variable for water chemistry. Which means:

> **An ESC controller walking downhill on total power will drive the condenser
> water wherever power is lowest, with no knowledge whatsoever of mineral
> saturation at the tube skin. It cannot see the wall. It is not that it weighs
> the wall lightly — the wall is not in its objective, its feedback, or its
> sensors.**

That is not a criticism of the method. It is the boundary of the method, and it
is precisely the boundary this product exists to cross. The same is true of every
conductivity-setpoint blowdown controller and every LSI-based dosing programme:
each optimises one of the three handles, none of them sees the coupling, and
**none of them can represent gypsum at all.**

So the honest positioning is narrower and much stronger than "we save energy and
water":

- **Not**: we optimise the fan/chiller trade-off. *(Prior art, 2012, model-free,
  incumbent-owned.)*
- **Yes**: we compute the constraint that every existing controller optimises
  blindly against — ion-specific saturation at the condenser skin — and we hand
  it to whatever is already doing the optimising.

That framing also fits the commercial evidence: **water is 56 % of the money and
electricity 45 %**, and the electrical share collapses to near zero in the half
of the Gulf year that matters.

---

## The measurement: fifteen papers, two literatures, no overlap

The claim above was an argument until it was measured. Fifteen supplied documents were scanned for
the vocabulary of water chemistry — *saturation index, Langelier, gypsum, CaSO4, calcite, cycles of
concentration, blowdown, sulfate, silica* — and for the vocabulary of optimal control.

**Every control paper scored zero on chemistry. Not low. Zero.**

| paper | what it does | energy terms | chemistry vocabulary |
|---|---|---|---|
| Li, Li & Seem 2012 (ACC) | extremum seeking, model-free | 14 | **none** |
| Ma & Wang 2012 (HVAC&R Res.) | MPC + fault detection, 0.18–5.23 % | 15 | **none** [†] |
| Zhao et al. 2025 (Energies 18:6577) | optimal chiller loading, PSO, −25.5 % | 33 | **none** |
| Wang et al. 2025 (Energies 18:2225) | RL / DQN on condenser loop, 14.16 % | 46 | **none** |
| Guo et al. 2022 (arXiv 2203.07500) | RL for district cooling plants, ~8 % | 18 | **none** |
| Wang et al. (Tsinghua, in review) | RL **deployed onsite**, 741 MWh / 8.1 % | — | **none** |
| Buildings 15:03568 | chiller plant control | 29 | **none** |
| J. Build. Environ. 2016 | condenser water control | 37 | **none** |
| J50 Modelica chiller plant models | open-source plant models | 14 | **none** |
| Hamedani et al. 2021 (Water-Energy Nexus) | grey-box ML for degradation | 5 | **none** |

[†] Ma & Wang's eight apparent hits are all the single word *fouling* — a heat-transfer
resistance term, not water chemistry. The two RL papers each contain *"scaling"* exactly once,
in the sense of scaling up an algorithm.

And the mirror image, in the same set:

| document | chemistry terms | optimal-control terms |
|---|---|---|
| DOE FEMP BMP #10 | **39** | 0 |
| Ghoddousi et al. 2021 review | **22** | 1 |
| Liu et al. 2025 (Processes 13:332) | 6 | 0 |

**The two literatures do not intersect.** People who optimise condenser-water energy do not model
water chemistry, and people who manage water chemistry do not optimise. That gap is the entire
thesis of this product, and it is now measured across fifteen documents rather than asserted.

It also sharpens what is *not* defensible. Six independent groups have published condenser-water
energy optimisation with reported savings of **8 %, 8.1 %, 14.2 %, 25.5 %, 0.18–5.23 %** — one of
them deployed on a real plant for eight months. **Mizan's five-condition mean electrical saving is
2.86 %.** Competing on energy means entering a crowded field from the bottom of the range.

---

## The consequence for the product, stated plainly

This argues for Mizan being a **constraint service** rather than a rival
optimiser. An ESC or BMS loop already exists on most plants and will keep
existing. What none of them has is a live answer to *"how high can I run cycles
today, on this water, at this skin temperature, before gypsum saturates?"*

That is a smaller product than "supervisory controller for the whole loop". It is
also defensible, does not compete head-on with Johnson Controls' installed base,
and is the only part of the system where this package holds something the
literature does not.

**Three things follow immediately and all are uncomfortable:**

1. The `commercialisation.md` pricing is built on equipment plus commissioning
   plus an annual licence for a *controller*. A constraint service prices
   differently and probably lower per site.
2. The energy figures should stop appearing before the water figures in every
   document. They are the weaker half and they invite the comparison that loses.

3. **There is no pump term in the objective at all.** `p_total = p_fan + p_chiller`, and
   condenser water flow is pinned at 478 kg/s. Zhao et al. found pumps *"held a disproportionately
   large energy-saving potential of over 25 %"* despite being under 20 % of consumption. The
   omission is internally consistent — fixed flow means constant pump power, which drops out of an
   optimisation — but it means a documented lever is invisible to this model. Added to
   `docs/robustness_gaps.md`.

**Not yet done.** These are founder decisions. What is no longer in doubt is the direction: the
measurement above says the energy pitch competes with six published groups and one live
deployment. The clause that used to end this sentence — *"and the chemistry pitch competes with nobody"* — was **withdrawn on 24 September 2026** and is corrected below.


---

## OLI Systems, and the sentence above that is now wrong

**Verified 24 September 2026** against OLI's own public pages, after an
independent review flagged it. The correction is not marginal: it removes a
whole class of claim from this package.

**What OLI documents publicly.** OLI Systems sells `OLI Flowsheet: ESP`, a
first-principles electrolyte flowsheet simulator with *"100+ unit operations
designed for electrolytes"*, and it publishes a **cooling-tower digital twin**
built on it. Their material states the model *"simulates real operating
conditions of cooling towers, calculates scaling tendencies based on full ionic
speciation, and forecasts the impact of blowdown, cycles of concentration (CoC)
changes, and heat loads."* The `OLI Process API` puts the same engine in the
cloud and, on their description, *pulls data from historians (flow rates,
conductivity, weather), triggers cloud simulations with up-to-date inputs, and
returns outputs such as optimized blowdown rate, scaling risk and species
concentrations*, with an optimisation step that recommends a blowdown rate to
minimise scale risk and an ML layer over it. They also ship a general
`OLI Optimizer` in Flowsheet: ESP V11 and advertise it can *"Minimize energy
consumption in water, wastewater treatment and industrial applications"*, and
they present scaling **and corrosion** prediction for cooling towers in
Platform V10.

**So three claims this package used to make are dead, and must not be said
again:**

1. That ion-specific speciation for cooling water exists only **offline**. It
   does not. OLI runs it against live historian data in a cloud loop.
2. That nobody builds a **real-time chemistry digital twin** of a
   cooling-tower loop. OLI publishes exactly that, as a pilot solution.
3. That *"the chemistry pitch competes with nobody."* It competes with OLI.

**What their public material does not cover, stated as absence of documentation
and not as a claim about their capability.** OLI's engine is a general
flowsheet simulator and a competent user could very likely build most of what
follows in it; the point is that none of it appears in the cooling-tower
material we can read, and two of the pages that would settle it are behind a
support login or a seminar video.

| Element | In OLI's published cooling-tower material |
|---|---|
| Full ionic speciation of the circulating water | **Yes**, stated explicitly |
| Real-time loop against plant historian data | **Yes** |
| Optimisation of **blowdown rate** against scale risk | **Yes** |
| Corrosion prediction alongside scaling | **Yes**, Platform V10 |
| Retrograde minerals evaluated at a **hot heat-transfer surface** rather than in the bulk | **Not found** |
| A prograde species (amorphous silica) evaluated at the **cold basin** | **Not found** |
| **Chiller or fan electricity** in the objective | **Not found.** Their cooling-tower economic analysis prices only makeup water at *"$0.50/m³"* and blowdown disposal at *"$15/m³"*; energy cost is absent, and the article points at future ML work rather than a joint optimisation |
| An **air-side handle** — fan speed or condenser-water setpoint — as a decision variable | **Not found.** The published decision variable is blowdown rate |
| A **discharge-permit** ceiling reported beside the chemistry ceiling | **Not found** |
| Closed loop rather than advisory | **Advisory** on their own wording: it *"provides recommendations"* |
| Maturity | Described as a **pilot solution** |

**The corrected width.** What is left is not novelty in chemistry. It is a
specific integrated decision: a supervisory controller that moves the **air-side
and water-side handles together** — fan speed, blowdown and acid dose — against
an ion-specific saturation limit evaluated **per mineral at the temperature
where that mineral is least soluble**, inside a **chiller capacity and
temperature envelope**, and with a discharge ceiling reported beside the
chemistry one. Every one of those pieces exists somewhere. The coupling of a
surface-evaluated chemistry constraint to a thermal-energy objective is what we
could not find, and that is the only sentence this package is entitled to.
