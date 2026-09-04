# External claims, checked one by one

**Written 4 September 2026.** A block of regional design parameters and
regulatory limits was supplied with the instruction *"got this from internet,
verify first."* That is the right instinct, and it was worth doing: **one of the
numbers is a units error of exactly the kind that produced defects 1 and 7 in
this package**, one contradicts a named operator's own published statement, and
one contradicts eight months of field data.

Each row below is marked **VERIFIED**, **REFUTED**, **UNVERIFIED** or
**CORROBORATED**. Nothing here was adopted into the model on the strength of the
supplied table alone.

---

## 1. The units error

> *"Energy Efficiency · Min Cooling Tower Performance · **> 38.2 L/s/kW** ·
> SBC 601"*

**REFUTED as stated.** The number 38.2 is real and comes from ASHRAE 90.1's
minimum efficiency for open cooling towers with propeller fans, but its units are
**gpm/hp**, not L/s/kW. Converting:

```
38.2 gpm/hp = 38.2 x 0.0630902 L/s / 0.7457 kW = 3.232 L/s/kW
```

**The quoted figure overstates the requirement by 11.8x.** A controller built to
"38.2 L/s/kW" would demand almost twelve times the flow per unit of fan power
that the standard actually asks for.

This is the same failure mode as **defect 1** (a fan correlation read as per cent
when it takes hertz) and **defect 7** (a drift rating read as a fraction when it
was a percentage). Three times now, in one project, a number has been right and
its units wrong. That is the single most productive thing to check in any
borrowed figure.

---

## 2. The claim that contradicts an operator's own statement

> *"Qatar · Cycles of Conc. · **Min Cycles (CoC) > 5.0 - 6.0** · Kahramaa DC
> Code (Water conservation mandate)"*

**UNVERIFIED, and contradicted by two independent sources.**

- **Qatar Cool**, writing about its own district-cooling plants, states that on
  direct TSE a plant *"operates on a maximum of three cycles, before being
  discarded into the sea"*, against roughly nine on polished water.
- The **Saudi Aramco Dhahran pilot** raised TSE from 2 to **3.5** cycles over
  eight months and reported that as a near-doubling worth publishing.

A regulatory *minimum* of 5-6 cycles would put every TSE plant in Qatar in
permanent breach, including the operator that published the figure. Either the
mandate does not exist, or it does not apply to TSE, or it is aspirational rather
than enforced. **It must not be used as a hard constraint until the Kahramaa
document itself is read.**

If it *were* true it would be commercially enormous — a legal floor sitting at
this model's economic ceiling of 6 — which is exactly why it needs a primary
source rather than a summary.

---

## 3. The rule of thumb the field data refutes

> *"Calcium Sulfate · **Ca x SO4 < 500,000** · The 'Product Rule'"*

**REFUTED as a hard limit, on this water, by field observation.**

The rule is real and widely quoted. Applied to the modelled TSE it says stop at
**2 cycles**:

| cycles | Ca (as CaCO3) | SO4 ppm | product | this model, SI_gypsum |
|---|---|---|---|---|
| 3 | 704 | 1 698 | 1 195 653 | -0.233 |
| 4 | 939 | 2 264 | 2 125 606 | -0.053 |
| 5 | 1 174 | 2 830 | 3 321 260 | **+0.092** |
| 6 | 1 408 | 3 396 | 4 782 614 | +0.216 |

The Aramco pilot ran **3.5 cycles for eight months with a condenser that stayed
clean**. At 3.5 cycles the product is already about 1.5 million, three times the
rule's limit, with no gypsum scale observed. **The rule is far too conservative
for an inhibited system**, which is the usual caveat on it: 500 000 is the
uninhibited figure.

So the model and the field agree with each other and disagree with the rule of
thumb.

**A first draft of this section said "no field data supports operation above 3.5 cycles". That was
too pessimistic and is corrected here.** Widening the search found four sources that agree with the
model's band — an ACS *I&EC Research* bench-and-pilot study finding scaling *"would not be a
significant concern ... operated at 4-6 cycles of concentration, and no anti-scaling chemicals
would be required"*; Engro Fertilizers running 4-6 and blowing down at 8; DOE FEMP saying *"six
cycles or more may be possible"*; and the Aramco pilot at 3.5. Full table in
`docs/robustness_gaps.md` §9.

**The boundary that actually remains:**

> Nobody has demonstrated **7** cycles, and nobody has demonstrated **6 on this specific Saudi
> TSE**. Four independent sources support the 4-6 band. **The wall itself is still unverified**,
> and the wall is what the product sells.

---

## 4. A constraint the model does not have, and probably should

> *"Sulfates (SO4) · Target < 800 ppm · Hard Limit 1 200 ppm · **Concrete
> Attack**: >1200 ppm sulfates react with cement in the basin (ettringite
> formation), cracking the structure."*

**MECHANISM VERIFIED, THRESHOLD UNVERIFIED — and this is a real gap.**

Sulfate attack on concrete via ettringite formation is a genuine, well-documented
durability mechanism, and cooling-tower basins are commonly concrete. ACI 201
classes sulfate exposure by concentration, with the severe band beginning around
1 500 ppm; the specific 800/1 200 pair here has no citation and should not be
adopted as written.

But the direction matters more than the exact number: **at 6 cycles this model
runs the loop at about 3 400 ppm sulfate**, which sits in ACI's severe band. The
controller has **no concrete-durability constraint of any kind**. It optimises
against scaling and, since 4 September, against corrosion of metal — but not
against attack on the structure holding the water.

**This is now the leading candidate for the next real constraint**, and it would
bind *before* gypsum on any plant with an ordinary Portland cement basin. Added
to `docs/robustness_gaps.md`.

---

## 5. Claims that check out

| Claim | Verdict | Note |
|---|---|---|
| Design dry bulb, Dhahran coastal 43-45 °C | **CORROBORATED** | the model's Dhahran summer peak runs 45 °C |
| Design wet bulb, Doha 30-32 °C | **CORROBORATED** | the model's Doha summer humid runs 30.31 °C |
| Makeup TDS 300-1 500 ppm | **CORROBORATED** | the modelled TSE is 1 500, at the top of the band |
| LSI corrosion limit around -0.5 | **CONSISTENT** | the corrosion floor added on 4 Sep defaults to 0.0, tighter |
| LSI scale alarm at +2.5 | **CONSISTENT** | the optimiser's bulk SI_calcite sits at 1.83, inside it |
| Potable water banned for district cooling in Qatar | **PLAUSIBLE, UNVERIFIED** | consistent with the TSE-only picture, no primary source read |

---

## 6. What the literature independently confirmed

**The DOE FEMP Best Management Practice #10 validates this model's central
arithmetic**, and it is worth stating precisely because it is the first
independent check of it:

> *"Increasing cycles from three to six reduces cooling tower make-up water by
> **20 %** and cooling tower blowdown by 50 %."*

The model computes makeup as `evaporation x C/(C-1)`. Three to six cycles gives
`1 - 1.2/1.5` = **20.00 %**. An exact match, from a US federal source that has
never seen this model.

**The blowdown half does not match, and the model is the one that is right.**
`blowdown = evaporation/(C-1)` gives a 60 % reduction, not 50 %, and 60 % is what
falls out of the mass balance either way you write it. Given that **defect 7 was
specifically a misreported blowdown rate** — the quantity a discharge permit is
written against — this disagreement is recorded rather than smoothed over.

DOE also states that *"many systems operate at two to four cycles of
concentration, while six cycles or more may be possible."* The model's incumbent
baseline is **4** and its optimum is **6**. Both sit exactly where DOE puts them.

**Ghoddousi et al. (2021), Eur. J. Sustain. Dev. Res. 5(3) em0161** justifies the
model's choice of tower physics directly:

> Merkel and effectiveness-NTU *"could accurately predict the outlet water
> temperature, but were both inadequate in the evaluation of the **evaporated
> water flow rate**"*, while the Poppe model *"was able to predict the states of
> the outlet air accurately."*

Mizan uses Poppe. The quantity the entire water case rests on is evaporation, and
this is the review saying the two commoner models cannot compute it. The same
paper notes cooling towers *"are oftentimes oversized, and thus rarely operate at
their design points"* — which is the independent version of **defect 16**.

---

## What changed in the model because of this

Nothing was adopted on the table's authority. Two things changed because of what
checking it turned up:

1. **A concrete sulfate-attack constraint is now a named gap** in
   `docs/robustness_gaps.md`, with the observation that the loop runs at ~3 400
   ppm sulfate at 6 cycles.
2. **The 3.5-cycle field ceiling is now stated wherever the 7-cycle wall is
   quoted.** The model may well be right about 7. Nobody has shown it.

---

## 7. The rest of the supplied literature, and what each one settled

Sixteen documents and five links were supplied. Every one was opened. The full prior-art argument is
in `docs/prior_art_esc.md`; this is the index of what each settled.

### Energy-side control — seven independent prior arts, none touching chemistry

| source | method | reported saving |
|---|---|---|
| Li, Li & Seem 2012, ACC (Johnson Controls) | extremum seeking, **model-free** | interior optimum found online |
| Ma & Wang 2012, *HVAC&R Research* 18:126 | MPC + fault detection and accommodation | 0.18–5.23 % |
| Lu et al. 2003, *Energy Convers. Manage.* (NTU Singapore) | model-based condenser-loop optimisation | — |
| Huang, Zuo & Sohn 2016, *Building & Environment* | optimise condenser water setpoint, legacy plants | — |
| Chen et al. 2025, *Buildings* 15:3568 | variable-speed pumps **and** tower fans | — |
| *Building Simulation* 17:1085 (2024), Wuhan case | joint pump + fan frequency optimisation | **12–13 %** |
| Zhao et al. 2025, *Energies* 18:6577 | optimal chiller loading, improved PSO | **−25.5 %** |

### Reinforcement learning — three more, one of them live on a plant

| source | setting | saving |
|---|---|---|
| Guo, Coffman & Barooah 2022, arXiv 2203.07500 (U. Florida) | district cooling plant with thermal storage | ~8 % |
| Wang et al. 2025, *Energies* 18:2225 (Hunan/Tsinghua) | DQN/DDQN on condenser loop, OpenAI Gym + EnergyPlus | 14.16 % sim, 10.42 % EnergyPlus |
| Wang, Xu, Fan et al. (Tsinghua, in review) | **deployed in a Guangzhou commercial complex** | **741 MWh, 8.1 %, eight months** |

**This is the strongest single argument against the RL question ever being reopened as a research
topic** — not because RL fails, but because it already succeeded, onsite, and the council's earlier
verdict of "zero hours" is confirmed from the opposite direction: it is done, and it is done on the
half of the problem that is not ours.

### Supporting and corroborating

- **Ghoddousi et al. 2021** — Merkel and e-NTU *"inadequate in the evaluation of the evaporated
  water flow rate"*, Poppe accurate. **Direct justification for this model's tower physics**, on the
  exact quantity the water case rests on. Also: towers *"rarely operate at their design points"*,
  which is defect 16 stated independently.
- **Fan et al. 2021, *Applied Energy* 299:117337** — open-source Modelica chiller-plant models with
  water-side economiser. Useful as a comparison baseline; no chemistry.
- **Liu et al. 2025, *Processes* 13:332** — FCC circulating water, 284 sets of industrial data,
  −11 % water from re-piping parallel to series. Water saving without any chemistry.
- **Hamedani et al. 2021, *Water-Energy Nexus* 4:149** — grey-box ML correcting a white-box model
  for **equipment degradation**. This is prior art for the *annual recalibration licence* idea that
  V2's fill-drift failure justifies.
- **Mujtaba et al. 2025, *Front. Energy Res.* 13:1473946** — AdaBoost on a 1140 MW Pakistani CCPP;
  relative humidity the dominant feature. Site selection, not control.
- **Gulf Experts (Qatar)** — names *fill material thermal degradation* under Gulf heat as a standing
  problem. Independent practitioner support for the V2 fill-drift diagnosis.

### Market, from a Gulf Water Conference paper

**Dawoud, Ewea & Alaswad 2022, *Desalination and Water Treatment* 263:127-138:**

- KSA desalination capacity ~2 500 Mm³/yr, **30 % of world capacity** — the largest producer.
- ~390 Mm³/yr of treated wastewater produced (2018), but **only 10 % of municipal wastewater is
  currently reused** — third largest reuse market after China and the USA.
- **Reuse capacity projected to grow 800 % by 2025**, with **district cooling named explicitly** as
  a target reuse application.

That is the policy tailwind under the TSE thesis, from a source that is not selling anything.

### Not retrieved

- `sciencedirect.com/.../S221471442502149X` — 403, and the identifier did not resolve by search.
  **Unread. Do not cite it.**
- `oxmaint.com` HVAC Middle East page — 403. Unread.
- The LinkedIn cooling-tower series post — not fetched.
