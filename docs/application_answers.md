# DTV application — answer bank

Drafted answers for every field DTV's form asks about, so the 30–40 minute sitting is transcription rather than composition. Numbers here match `results/` exactly; if you re-run the gates, re-check them.

Fields marked **[YOU]** need founder input and cannot be drafted.

---

## Technology, category and TRL

**Focus area:** Energy — with a genuine secondary fit to Water & Sustainability. If the form allows only one, choose **Energy**: the validated cost result is dominated by the energy trade, and the water result is the one that missed its threshold. Claiming Water primary would put our weakest number in front.

**Technology in one sentence:**
> A retrofit edge controller that co-optimises cooling-tower fan speed, blowdown and acid dose against ion-specific mineral saturation evaluated at condenser tube skin temperature, rather than against a fixed conductivity setpoint in the bulk water.

**TRL claimed: 3.**
> Core concept demonstrated through analytical and computational studies validated against measured experimental data. A first-principles Poppe heat-and-mass-transfer model coupled to a PHREEQC-based hydrochemistry engine predicts measured outlet water temperature to 0.542 K MAE, measured heat rejection to 5.94% MAPE, and measured water consumption to 9.90% MAPE, on 50 experimental points from campaigns the model was never fitted to, against thresholds fixed before fitting. The first two thresholds were met; the 8% water-consumption threshold was not, and is reported as a failure.

**Quote their own definition back.** DTV's TRL guide defines TRL 3 for software as *"limited functionality to validate critical properties and predictions using non-integrated software components,"* with the exit criterion *"documented analytical/experimental results validating predictions of key parameters."* The evidence package meets that as written: five gates, thresholds fixed before fitting, scored once on an untouched holdout.

**Why not TRL 4:** no components integrated or validated in a laboratory environment yet. That is precisely what the 12-week programme is for, and Section 7 of the PoC report specifies the experiments on KFUPM's existing vertical cooling tower and psychrometric wind tunnel.

## The problem

> A Gulf condenser-water loop is run by three parties setting three handles independently: the BMS sets fan speed on a fixed condenser-water setpoint; the water-treatment contractor sets blowdown on a fixed conductivity setpoint and acid dose on a fixed pH setpoint.
>
> These are not independent variables. Concentrating the loop to save water raises scaling risk and changes evaporation. Cooling the condenser to save compressor power costs fan power and evaporates more water. No one solves them together, because doing so requires the thermal model and the water-chemistry model to be one problem rather than two.
>
> The consequence is measurable: the plant operates between two limits it cannot see. Our model puts the economic optimum at 9 cycles of concentration and the physical saturation limit at 10 — one cycle apart. A fixed conductivity setpoint locates neither, and at real Gulf water prices the economics push operation right up against a scaling limit the plant cannot see.

## The solution

> A retrofit edge controller — sensor skid (conductivity, pH, ORP, temperature, makeup and blowdown flow), motorised blowdown valve, and edge compute running a validated physics core over BACnet/Modbus. It ships read-only in shadow mode; blowdown and dosing stay advisory until site validation, which is both a safety position and the shortest route past OT-security review.
>
> This is equipment, not software. The saturation limit cannot be computed from a plant's existing instruments: bulk conductivity does not determine ion composition, and nothing installed reads skin temperature. The hardware is what makes the calculation possible.

## Competitive advantage

**State plainly what is not ours.** A prior-art and competitor sweep found that three of the ingredients are already taken, and claiming any of them would be falsified in minutes:

- **Ion-association / Pitzer speciation is not novel.** French Creek Software (WaterCycle, since 1990) and OLI Systems both run full ionic speciation and scale prediction. The technique has been in use by the water-treatment majors since the 1970s.
- **Skin-temperature saturation is not novel.** ChemTreat holds granted **US 11,780,742 B2** (Oct 2023) claiming skin temperature driving chemical dosage.
- **Blowdown control against a saturation index is public domain**, dating to US 4,460,008 / 4,464,315 (1984, expired).

**What is open, stated precisely:**

> **Routing each mineral to its own governing temperature, computed live, and closing three actuators on the result.**

Three things make that specific rather than a repackaging:

1. **Per-mineral evaluation temperature.** Calcite, gypsum and magnesium silicate are retrograde and govern at the hot condenser skin. Amorphous silica is **prograde** and governs at the cold tower basin. Evaluating everything at one temperature is wrong for one group or the other. French Creek works from **bulk** temperature profiles — a full-text search of its manual returns zero occurrences of "skin" or "surface temperature" — and advises checking "the lowest and highest temperatures anticipated" as a *design* exercise. ChemTreat evaluates at skin but with LSI-family indices, which describe calcite.

2. **The ceiling is dynamic, and industry treats it as static.** Commercial practice sets a fixed silica limit — typically "do not exceed 150 mg/L" — *regardless of basin temperature*. Because silica is prograde and the basin tracks ambient wet-bulb, the true ceiling moves from **95 mg/L at a 15 °C winter basin to 143 mg/L at 35 °C**. The static rule is **non-conservative at every basin temperature in the Gulf range, by 37 % in winter**. An offline design tool evaluated at design conditions cannot produce a moving setpoint; this is a static-versus-dynamic distinction, not a software-versus-hardware one.

3. **Actuation.** Speciation packages predict. They do not close a loop. No incumbent or startup was found actuating fan speed, blowdown and acid dose together against a saturation objective.

**The sharpest single demonstration.** Magnesium silicate deposits when bulk pH exceeds the brucite saturation pH *at the condenser skin*, and that saturation pH is retrograde. On Gulf TSE at pH 8.5–9.0, a skin below 34 °C is safe and a skin above 46 °C is depositing across the entire operating band. **The same tower, same water, same pH, deposits at high load and not at low load.** Detecting that requires a live thermal model, a chemistry model and an acid actuator operating as one system.

Three independent literature sweeps returned the same answer on this point: *"No academic paper, patent, or commercial product literature describes a closed-loop control scheme where a chemical saturation limit directly bounds or dynamically alters the mechanical thermal energy optimizer."* That negative is the differentiation.

**Replication test:** a competent generalist team reproduces the tower model in weeks. What they do not reproduce is knowing the published fan correlation is in hertz not percent, that gypsum binds before calcite on Gulf TSE, or that the water saving must be discounted for evaporation the energy optimum adds back. Each came from the physics, and each changed the result.

## IP status

> No patents filed, none pending. All third-party components are used under licence and attributed: the validation dataset is CC BY 4.0 (Zenodo 10806201); equilibrium constants are from the USGS PHREEQC `phreeqc.dat` database. All model code is original — the psychrometric library, Poppe integrator and speciation engine were implemented from published formulations, not copied from any repository.
>
> **A prior-art search has been conducted and is disclosed rather than omitted.** The closest art is ChemTreat **US 11,780,742 B2** (granted 10 Oct 2023), which claims determining heat-exchanger skin temperature and using a scale saturation parameter to set **chemical treatment dosage**. Also relevant: Ecolab **US 11,668,535 B2** (heat-exchanger efficiency to fouling classification to chemical dose) and the expired **US 4,460,008 / 4,464,315** (LSI-based blowdown trip points, 1984).
>
> **Our position relative to that art is deliberate and architectural.** Claim 1 of US 11,780,742 requires, as its final elements, determining a dosage of a chemical treatment solution and controlling its application. Mizan's saturation objective drives **blowdown rate and cooling-tower fan speed** — actuators the claim does not recite. Acid is dosed to a conventional pH setpoint rather than to a dose computed from a skin-temperature saturation parameter.
>
> **Jurisdiction.** The published family for that patent comprises the US grant and the PCT publication. No Saudi, Qatari or GCC national-phase member is visible on the public record, and the GCC is not a PCT contracting state, so Gulf coverage would require separate national filings. A US patent has no effect in our beachhead markets.
>
> No freedom-to-operate opinion has been commissioned, and none is claimed. One will be obtained before any patent filing or first commercial sale in a jurisdiction where relevant art is in force — a scope that suits DTV's product-development stream, which covers third-party subject-matter experts.

*Disclosing this strengthens the application rather than weakening it. A reviewer who finds the ChemTreat patent themselves, after we claimed novelty, is a reviewer we have lost. Note this is our own reading of a public claim, not legal advice, and it is presented as such. DTV states that startups retain their IP and that standard support creates no claim; the risk here is overclaiming, not underclaiming.*

## Proof of concept

> Complete and reproducible in four commands against a public dataset. See the attached Proof-of-Concept report. Five validation gates with thresholds fixed and printed before fitting; a campaign-wise holdout scored once. Four gates pass, one fails and is reported as failing, and a unit defect found in our own first run is documented in the report rather than quietly corrected.

## Market opportunity

> Per 10 MW condenser-water module the model gives **$76,236/yr** in operating cost and **11,809 m³/yr** of water across a real Dhahran meteorological year, scaling approximately linearly with condenser duty — about $762,000/yr at 100 MW, or $1.34M/yr at a 50,000 TR plant. Against a first-year cost near $50,000 per loop, payback is under nine months on a single module. *(Rebased 4 Sep 2026: these figures were previously $157,975 and $2.78M, computed by multiplying one condition's hourly saving by 8,760 hours. See defect 20.)*
>
> Beachhead is Saudi and Qatari district cooling running treated sewage effluent, plus industrial cooling at Jubail and Yanbu. TSE at high cycles is exactly the regime where the incumbent index fails, so the technical argument is sharpest where national water-reuse policy is strongest. Qatar needs no rework: same physics, same equipment, same water policy.

Tariffs underpinning these figures are now taken from **published schedules**, not assumed: electricity $0.074/kWh (Saudi business all-in, Dec 2025); water $3.11/m³ avoided (Marafiq/RCJY approved schedule — process water SAR 8.04 plus industrial wastewater SAR 3.64 not discharged); acid $0.19/kg. **No time-of-use tariff is published for Saudi commercial customers, so no peak-shifting arbitrage is claimed.** Verified named accounts are in the market dossier; Red Sea Global, SEC and ACWA were checked and discarded, and once-through seawater loops are explicitly outside the market.

### The national-priority hook

Cooling is roughly half of Saudi building electricity and up to 70–80 % of summer peak demand. The National Water Strategy's second objective is verbatim *"Enhance water demand management across all uses."* Mizan is one control action that moves both levers at once, which maps precisely onto `.dvp`'s first two focus areas.

The sharper version: **SEEC's 26 energy-efficiency regulations, and the 2021 EER→SEER switch, all govern equipment specification. None governs the operating point of an already-installed water-cooled plant.** The policy intent exists; the lever does not. That gap is the product.

**Pre-empt the obvious counter.** Saudi greenfield district cooling is trending toward air-cooled and zero-water designs — Red Sea Global's plant is dry-cooled with no tower at all. Mizan is explicitly a **retrofit for the existing installed base**, not a bet on new-build. Say this in one line before a reviewer says it for you.

## Early traction

> None. No letters of intent, no pilot agreements, no customer interviews completed at time of submission.

*State this plainly. DTV screens the maturity gate first and scores traction after; a fabricated LOI is the one unrecoverable error in this ecosystem. The honest position — strong evidence, zero traction, a dated plan to build it — is credible. An invented one is not.*

## Commercialisation plan and budget

See the attached commercialisation document. Summary: equipment sale ($28–42k per condenser loop) plus commissioning ($8–15k) and an annual recalibration licence ($10–14k), sold through controls integrators, ESCOs and water-treatment contractors who already hold site access. Entry wedge is a paid diagnostic ($6–12k) credited against purchase.

**On the SAR 200,000 in-kind stream:** instrumentation, blowdown valve and edge hardware, heated-coupon scaling rig, ICP-OES water analysis, OT-security assessment, third-party validation. Modelled as physical-validation capability, never as runway.

**On cash: state the constraint honestly.** DTV support is in-kind and cannot fund the Dhahran residency from 18 Oct to 11 Jan. The minimum bridge is ~$12,000 and the prudent target ~$24,000. Raise this with DTV during selection rather than discovering it in December.

## Team

**[YOU]** — for each founder: full name, email, mobile with country code, position in the venture, LinkedIn URL with a legible username. CVs per `submission/CV_TEMPLATE.md`.

Framing to use:
> Two energy engineers, both full-time and unemployed by choice to pursue this. One owns the thermal and control core, the other the chemistry and commercial track. Neither is a salesperson, which is why the go-to-market is built around a technical demonstration — we run the prospect's own makeup water analysis through the model and show them where their conductivity setpoint sits between their two ceilings. That is a peer conversation between engineers, which both founders can hold credibly.

## Uploads checklist

| Item | File | Status |
|---|---|---|
| Pitch deck (PDF) | `submission/Furqan_Mizan_Deck.pdf` | ready |
| PoC report | `submission/Furqan_Mizan_PoC_Report.pdf` | ready |
| Commercialisation plan and budget | `submission/Furqan_Mizan_Commercialisation.pdf` | ready |
| Supporting — AI architecture | `submission/Furqan_Mizan_AI_Architecture.pdf` | ready |
| CVs with LinkedIn URLs | from `submission/CV_TEMPLATE.md` | **[YOU]** |
| Patent / IP documentation | n/a — none held | n/a |
| Letters of intent | n/a — none held | n/a |
