# Commercialisation plan and budget

**Furqan** · *Deep physics for hard infrastructure*
Product: **Mizan** — supervisory controller for condenser-water loops
Prepared for DTV .dvp Cohort 2 · 29 August 2026

Every figure is tagged. `[M]` derives from the validated model in this repository. `[A]` is an assumption. `[VERIFY]` is an open item with a named source. Nothing here is presented as measured field performance, because none of it is yet.

---

## 1. What is sold

Not software. A **retrofit edge controller**, priced as equipment:

| Component | Detail |
|---|---|
| Sensor skid | Conductivity, pH, ORP, temperature, makeup and blowdown flow |
| Actuation | Motorised blowdown valve; fan VFD setpoint via existing BMS |
| Edge compute | Runs the validated physics core; BACnet/Modbus; no cloud dependency |
| Licence | Annual model recalibration and water-chemistry update |

The controller ships **read-only in shadow mode**. Blowdown and dosing stay advisory until site validation. That is a deliberate commercial choice as well as a safety one: it lets a plant quantify the benefit on its own data before granting write access, which is the shortest path past OT-security review.

**Why not SaaS:** DTV's programme excludes it, and more importantly the value is inseparable from instrumentation. The saturation limit cannot be computed from a plant's existing sensors — bulk conductivity does not determine ion composition, and no existing instrument reads skin temperature. The hardware is not packaging around software; it is what makes the calculation possible.

## 2. Value created, from the model

Per 10 MW condenser-water module, weighted across five Gulf ambient conditions `[A: duty weighting]`, on **published tariffs** rather than assumptions:

| | Baseline | Optimised | Saving |
|---|---|---|---|
| Operating cost | $228.76/h | $210.72/h | **$157,975/yr (7.88 %)** `[M]` |
| Makeup water | 23.6 m³/h | 20.6 m³/h | **26,711 m³/yr** `[M]` |

Scaling linearly by condenser duty:

| Plant size | Annual saving `[M]` |
|---|---|
| 10 MW (~2,840 RT) | $157,975 |
| 30 MW (~8,530 RT) | $473,927 |
| 60 MW (~17,060 RT) | $947,855 |
| 100 MW (~28,430 RT) | $1,579,759 |
| 176 MW (~50,000 TR plant) | $2,780,376 |

### The tariff inputs, and why they are defensible

| Input | Value | Source |
|---|---|---|
| Electricity | $0.074/kWh (SAR 0.277) | Saudi business all-in retail, Dec 2025 `[C]` |
| Water avoided | **$3.11/m³** | Marafiq / RCJY approved schedule, eff. 7 Dec 2025: process water SAR 8.04/m³ **plus** industrial wastewater SAR 3.64/m³ not discharged `[C]` |
| Sulphuric acid | $0.19/kg | Bulk 98% Saudi, mid-range of a $0.148–0.380 four-quarter band `[C]` |

The water figure is the one that carries the case, and it is stronger than a simple tariff lookup: a cubic metre of blowdown avoided saves **both** the makeup not purchased and the industrial wastewater not discharged, and both line items come from the same approved schedule. For a Jubail or Yanbu operator, the value case computes from the customer's own published numbers.

Two constraints came with the verification:

- **No published time-of-use tariff exists** for Saudi commercial or industrial customers. The fan leg is therefore valued at a flat energy price. Claiming peak-shifting arbitrage would not survive review. `[C]`
- **Acid prices roughly doubled between Q1 and Q2 2026**, attributed to Strait of Hormuz disruption constraining sulphur supply. The base case sits mid-range deliberately. Acid-price volatility is an argument *for* dose optimisation, not against it. `[C]`

**These remain modelled savings, not measured.** Field measurement is a TRL 4 objective.

## 3. Pricing

| Line | Price `[A]` | Basis |
|---|---|---|
| Controller + sensor skid, per condenser loop | $28,000 – 42,000 | Equipment capex |
| Commissioning and integration | $8,000 – 15,000 | One-off |
| Annual recalibration licence | $10,000 – 14,000 | Per loop per year |
| Paid diagnostic (wedge) | $6,000 – 12,000 | Credited against a later purchase |

At a 30 MW plant saving ~$474,000/yr, first-year cost of roughly $50,000 per loop gives **payback in well under three months** and a first-year return above 9×. That ratio is what makes the sale possible without a salesperson: the arithmetic argues for itself in front of an engineer.

Conversion rule we hold ourselves to: no move from pilot to purchase unless independently metered benefit is **≥ 3× the first-year fee**.

## 4. Route to market

**Sell through the contractor, not around them.** Controls integrators, ESCOs and water-treatment contractors already hold site access, commissioning crews and framework agreements. They convert in weeks where a direct utility sale takes quarters.

There is a structural opening here worth stating plainly. The incumbent water-treatment model earns on **chemical volume**. A device whose purpose is to cut blowdown *and* dosing is something the incumbent is disincentivised to build — but a contractor competing for a service contract on total cost of ownership has every reason to carry it.

**Beachhead:** Saudi and Qatari district cooling running treated sewage effluent, plus industrial cooling in Jubail and Yanbu. TSE at high cycles is exactly the regime where the incumbent index fails, so the technical argument is sharpest where the water policy is strongest.

### Verified target accounts

Saudi Arabia `[C]`:

| Account | Site | Capacity | Entry thesis |
|---|---|---|---|
| Saudi Tabreed | Portfolio | 349,000 TR contracted | Largest independent KSA operator — one relationship, many retrofit units |
| Saudi Tabreed | KAFD, Riyadh | 100,000 TR | 10-year contract extension signed — long horizon to amortise a retrofit |
| Saudi Tabreed | King Salman Park | 60,000 TR, 25-yr | Greenfield with a 25-year O&M horizon |
| Saudi Tabreed | King Faisal Specialist Hospital, Jeddah | 62,000 TR | Healthcare — zero tolerance for condenser fouling |
| Saudi Tabreed | Jabal Omar, Makkah | 55,000 TR | Makkah water scarcity is acute |
| Saudi Tabreed | **Saudi Aramco cooling** | 32,000 TR | Proof Aramco procures third-party district cooling |
| Saudi Aramco | Ras Tanura, Abqaiq, Hawiyah | Refinery-scale | Maintains its **own engineering standards for open evaporative recirculating cooling water** — a technical governance framework to plug into |
| Marafiq / Marafiq Cool | Jubail & Yanbu | 4.8 GW power | **Publishes its own approved water tariff schedule** — the value case computes from the customer's own numbers |

Qatar `[C]`:

| Account | Site | Capacity | Entry thesis |
|---|---|---|---|
| **Qatar Foundation** | Education City central plants | **185,000 TR** | Plants run **completely on TSE** for condenser cooling — highest-scaling-risk makeup in the region, single owner |
| **Qatar Cool** | West Bay, 3 plants | 92,500 TR | **Switched to TSE and publicly documented the resulting condenser-chemistry difficulty** — a warm, self-identified pain point |
| Qatar Cool | The Pearl-Qatar | 130,000 TR | Largest single addressable loop in Qatar |
| Marafeq Qatar | Lusail City | 500,000 TR connected | Largest DC scheme in the Gulf |
| QatarEnergy | Ras Laffan common cooling | 937,000 m³/hr | Confirmed **recirculating seawater towers with blowdown** — but see the seawater caveat below |

### Discarded after checking — this list is a credibility asset

| Candidate | Why not |
|---|---|
| **Red Sea Global** | District cooling plant is **dry-cooled, zero water consumption**. No tower, no blowdown. |
| **Saudi Electricity Company** | Coastal thermal fleet is **once-through seawater**, not evaporative. Relevant only as the electricity-tariff counterparty. |
| **ACWA Power** | No evidence of evaporative condenser-water loops; fleet is coastal seawater-cooled `[UNVERIFIED]` |
| **Saudi Water Authority / SWPC** | Producer/regulator and procurement entity. Not cooling-tower operators. |
| **Kahramaa** | Qatari **regulator** and tariff-setter, not an operator. Route to market, not a customer. |
| **NEOM / ENOWA** | 25,000 TR OXAGON plant confirmed **planned**, not operating. Pipeline only. |

**The seawater caveat, stated plainly.** Marafiq's approved schedule prices sea-water cooling at SAR 0.069/m³. Where cooling water is effectively free, blowdown-reduction value collapses to near zero. **Once-through and seawater-makeup loops are not our market** — the target is freshwater and TSE evaporative loops. This disqualifies part of the apparent Gulf opportunity and should be said before a reviewer says it.

**Qatar bridge:** identical physics, equipment and water policy — and Qatar's TSE adoption in district cooling is further advanced than Saudi Arabia's, which makes it arguably the stronger beachhead rather than the second market.

## 5. GTM designed for engineers who do not sell

The pitch is a technical demonstration, not a sales call: we run the prospect's own makeup water analysis through the model and show them their two ceilings — the economic optimum and the physical limit — and where their current conductivity setpoint sits relative to both. That is a peer conversation between engineers, which all three founders can hold credibly.

- **Furqan Shakeel (CTO)** owns the physics core, controller and validation programme, and joins calls for technical qualification.
- **Damia Baig (CEO)** and **Muhammad Ahsan (Commercial Development)** own discovery and pipeline between them.
- Disagreement protocol: the CEO decides commercial scope, the CTO decides technical architecture; deadlocks resolve toward whoever has more customer evidence.

Two of three founders on commercial is deliberate. The technical risk is now largely retired — the evidence package is built and reproducible — and the binding risk from here is traction velocity, which is a headcount problem.

Target: 30 structured conversations in 90 days — 10 operators, 8 controls/water integrators, 6 ESCOs, 6 consultants.

## 6. Budget

### DTV in-kind (SAR 200,000, product-development stream) — not runway

| Item | Indicative SAR `[A]` | Buys |
|---|---|---|
| Instrumentation (conductivity, pH, ORP, flow) | 45,000 | Gate V2/V3 as measurement, not calculation |
| Motorised blowdown valve + edge hardware | 30,000 | Closed-loop TRL 4 integration |
| Heated-coupon side-stream rig | 35,000 | Scaling kinetics — the data the learned residual needs |
| ICP-OES water analysis, campaign | 25,000 | Ion-specific validation against real Gulf water |
| OT-security assessment | 40,000 | Removes the largest procurement blocker |
| IP counsel / freedom-to-operate opinion | 25,000 | Third-party subject-matter expert — an in-kind line item, not founder cash |
| Third-party validation report | 25,000 | Countersignable evidence for the first pilot |

These are deliberately cheap experiments — salt, coupons, instrumentation and laboratory time on a rig that already exists at KFUPM.

### Cash requirement — the binding constraint

DTV support is in-kind. It cannot fund residence in Dhahran from 18 Oct 2026 to 11 Jan 2027, and QDB's decision does not land until 25 Nov at the earliest.

DTV covers travel and accommodation for **two members** at the bootcamp and Demo Day only — not for the 12-week residency, and not for a third founder.

| Item | USD `[A]` |
|---|---|
| One founder resident in Dhahran, 12 weeks | 5,000 – 8,000 |
| Second founder, part-time Dhahran presence | 3,000 – 5,000 |
| Doha travel and visa for the QDB in-person phase | 1,000 – 2,000 |
| Third founder, bootcamp/Demo Day travel not covered by DTV | 1,000 – 1,500 |
| Entity formation and compliance | 4,000 – 10,000 |
| Contingency 20 % | 2,800 – 5,300 |
| **Minimum viable bridge** | **~17,000** |
| **Prudent target** | **~32,000** |

A third founder raises the bridge by roughly $5,000. The mitigation is that only one founder needs continuous Dhahran residency; the commercial pair can work the Gulf pipeline remotely between the covered trips.

**Stated plainly: with zero liquid founder cash, the Dhahran residency period is not fundable from the programme itself.** The honest options are a paid diagnostic closed before 15 October, a disclosed family or third-party bridge, or declining the on-site component. This should be raised with DTV directly rather than discovered in December.

## 7. Milestones and kill gates

| Date | Gate | Kill criterion |
|---|---|---|
| 31 Aug 2026 | DTV submission | Submit only with the honest TRL 3 claim; no LOI is invented |
| 5 Sep 2026 | QDB submission | Only after written sector/entity eligibility confirmation |
| 15 Sep 2026 | Discovery | Fewer than 15 conversations and 3 data-sharing discussions → narrow or stop |
| 15 Oct 2026 | Bridge | No unrestricted bridge cash → do not enter Dhahran residency |
| 25 Nov 2026 | QDB decision | No paid diagnostic and no QDB → stay Lahore-based, defer incorporation |
| 11 Jan 2027 | DTV Deal Day | No TRL 4 evidence → do not apply to YC Spring; take Fall 2027 |

## 8. What would falsify the business

Written down in advance, so it is not rationalised away later:

1. **Tariff sensitivity.** If verified Saudi water and electricity tariffs move the modelled saving below ~3 %, payback exceeds a year and the sale gets much harder.
2. **The gap closes.** If real plants with competent antiscalant programmes already run near the physical ceiling, the margin we claim to recover does not exist. This is the single most important thing to test in customer conversations, and it is testable by asking one question: *what is your current cycles setpoint, and what set it?*
3. **Chemistry does not survive contact with a real loop.** V3 and V5b are calculations. If measured Gulf loop chemistry disagrees materially with the speciation model, the differentiator weakens to a conventional energy optimiser in a crowded market.
4. **The incumbent bundles it.** Nalco or Veolia adding skin-temperature saturation to an existing controller would compress the window fast — though their chemical-volume revenue model works against it.
5. **A Gulf patent filing appears.** ChemTreat's skin-temperature claim currently has no visible Saudi, Qatari or GCC family member, which is why the beachhead is clear. If that changes, the design-around (saturation driving blowdown and fan speed, not chemical dose) is the fallback — and it is already the architecture, not a retreat from it.
