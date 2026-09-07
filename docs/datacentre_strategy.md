# Data centres: what a Mizan / NeuroThermal hybrid can honestly be

**Written 7 September 2026**, after a full pass over this repository and the
prior-art sweep in `prior_art_datacenter.md`.

---

## Part 0 — The asymmetry, stated first

"Mizan + NeuroThermal" is not a merger of two comparable things.

| | Mizan (this repo) | NeuroThermal (the concept doc) |
|---|---|---|
| physics core | validated against 165 PSA Almería points | proposed |
| PINN surrogate | **built and gated**: 0.022 K MAE, 101,802x speed-up, 0 of 5,000 extrapolation violations | proposed |
| chiller model | named machine, York YT 1758 kW, envelope enforced, 1,840 of 6,307 points rejected | proposed |
| chemistry | measured whitespace, three literature sweeps | none |
| defect register | 20 found, 19 fixed, 1 declared open | none |
| gates that failed and were reported | 2 | none |
| **the IT-side loop (CDU, cold plate, GPU)** | **none** | this, and only this |

NeuroThermal contributes **one loop and one customer segment.** Everything else
in it, this repository already has in a better-evidenced form. So the hybrid is
an *extension of Mizan*, and the pitch should never be framed as a merger of
equals — a reviewer who reads both will see the asymmetry immediately.

---

## Part 1 — The honest technical hybrid: extend by exactly one heat exchanger

Mizan today models the chain from the atmosphere inward and stops at the
chiller's evaporator, which is a boundary condition (`Q_evap_kw`).

A liquid-cooled AI hall adds, in series:

```
atmosphere <- tower <- condenser water <- CHILLER <- facility water <- CDU <- cold plate <- GPU
             [Mizan owns this]            [boundary]  [--------- new ---------]
```

**The minimum honest extension is one component: the CDU, modelled as a heat
exchanger with an approach temperature.** That turns the evaporator setpoint
from a boundary condition into an output, and closes this chain:

> chemistry ceiling → max cycles → condenser water temperature → chiller COP
> → facility water temperature → CDU approach → **GPU inlet temperature and its
> margin to the ASHRAE W-class limit**

That chain is the entire product thesis for data centres, and it is the thing
`prior_art_datacenter.md` proved nobody models: the control literature scores
**zero** on chemistry across 735,000 characters, and the water literature scores
**zero** on optimal control.

**Stop at GPU inlet water temperature.** Do not model the die.

**What NOT to build, and why:**

- **No GPU junction / DVFS / ITD model.** That is semiconductor physics none of
  the three founders has, and it is precisely the ground Phaidra occupies. The
  NeuroThermal doc's ITD section is its most impressive-looking part and its
  worst strategic choice.
- **No CDU flow optimiser.** Published: arXiv 2605.15516 already does CDU
  allocation across subloops plus flow/supply-temperature co-design.
- **Never quote the 30 % cooling-energy figure.** arXiv 2603.01198 labels it
  itself as *"without operational constraints, revealing the theoretical maximum
  savings."* Its constrained result is 27.8 % and its flow-only result 20.4 %.
  Quoting the unconstrained number repeats defect 11 on someone else's data.

---

## Part 2 — The strategic reframe, which the biggest threat forces

`market_dossier.md` risk #5 already says: *"Flagship Saudi giga-projects are
going dry-cooled. Red Sea Global's 32,500 TR plant is deliberately zero-water
with dry coolers. If dry cooling becomes the giga-project default, the greenfield
addressable market shrinks."*

**That risk is sharper in data centres than in district cooling, and the reason
is Mizan's own water price.** Trade sources now claim the December 2025 industrial
water tariff — SAR 8.04/m³, the exact number in `commercialisation.md` — has
"destroyed the ROI of evaporative cooling" for Gulf data centres, pushing new AI
halls to closed-loop and dry cooling. `[VERIFY — these are vendor and consultancy
blogs with an interest in selling closed-loop, not primary data.]`

A tower-only product walks into a segment that may be deleting the tower.

**So invert it. The product is not "control the tower." It is "should there be a
tower, and if so how hard can it be pushed?"**

Mizan is the only tool that can answer this from first principles, because it
already computes both sides of the trade:

| | evaporative | dry / closed loop |
|---|---|---|
| rejects to | **wet bulb** (~30 °C Dhahran design) | **dry bulb** (~46 °C Dhahran design) |
| energy | low | penalised by ~16 K of condensing temperature |
| water | `makeup = evap x C/(C-1)`, priced at $3.11/m³ | ~zero |
| ceiling | **gypsum at 7 cycles — Mizan computes it** | none |

That ~16 K penalty is computable **today** with `controller.py`'s existing
bi-quadratic chiller — it is the same curve evaluated at a different entering
condenser water temperature. The crossover depends on tariffs, weather and *how
many cycles the water actually supports*, which is exactly the quantity nobody
else can compute.

**This turns risk #5 from a threat into the product.** If dry cooling wins,
Mizan is the tool that proved it and sizes the adiabatic assist. If evaporative
wins, Mizan controls it. Either way the analysis is the wedge, and Ecolab
shipping *"3D TRASAR Technology for Adiabatic Cooling"* confirms the hybrid
segment is real.

---

## Part 3 — Constraint service, with a channel that now has a name

`prior_art_esc.md` already concluded Mizan should be a **constraint service, not
a rival optimiser.** The data-centre sweep gives that conclusion named
counterparties with a *published, admitted* blind spot:

- **DeepMind's BCOOLER paper**, §7.3, on what degrades their agent: chiller
  performance falls *"due to fouling of the heat exchanger surfaces by mineral
  scaling, biofilms, dust and dirt, and corrosion."* They name the wall, give it
  no state variable, no sensor and no term in the objective.
- **Phaidra** — founded by the people who ran Google's DC-cooling project, selling
  closed-loop RL control of liquid-cooling CDUs and chiller plant to AI data
  centres. Zero chemistry vocabulary on their entire site.

Position Mizan as the device that **publishes a live constraint** — max cycles,
max condenser water temperature before gypsum saturates at the skin — which
whatever supervisory optimiser already exists then respects.

**This also resolves the DTV no-SaaS problem cleanly.** The constraint is a
BACnet/Modbus point emitted by a capex field device, not a cloud subscription.
It is a sensor skid with an opinion, which is exactly what DTV's hardware track
wants.

And it converts the strongest incumbents from competitors into distribution.

---

## Part 4 — What the running experiment is for

`src/annual_datacentre.py` re-runs the Dhahran annual sweep with **one change**:
the load model. `annual.py` uses a comfort-driven load,
`load = clip(0.55 + 0.45 (T_db - 18)/28, 0.35, 1)`, tagged `[A]` in that file. A
data centre's load is IT-driven and flat.

This matters because `HANDOFF.md` calls the energy/water anti-correlation
(r = -0.548) *"the strongest argument in the package for coupling the two
models."* But in `annual.py` cold hours are also **light** hours, so part of that
anti-correlation may be a load effect rather than a weather effect. Flattening
the load separates them.

- If the anti-correlation **survives** at flat load, the coupling argument is
  about the weather and it transfers to data centres. The hybrid has a physical
  basis.
- If it **collapses**, the coupling argument is really about part-load district
  cooling and **does not transfer**. That is a finding, and it must be reported.

Five predictions were pre-registered in that file's docstring before the first
run, including the unfavourable P1 (cool-half energy saving *falls*, because flat
high load pushes entering condenser water toward the 35 °C chiller ceiling even
at low wet-bulb).

### RESULT — run 7 September 2026, flat load 0.90

```
                        district cooling    data centre     delta
annual energy (totals)        5.36 %          6.48 %       +1.12
annual water   (totals)       8.81 %         10.67 %       +1.86
annual cost    (totals)       6.44 %          7.80 %       +1.36
annual money saved         $76,236         $117,760         +54 %

cool half  energy            10.37 %         11.91 %
hot  half  energy             2.06 %          1.39 %
cool half  water              7.18 %         10.75 %
hot  half  water              9.79 %         10.60 %

energy/water correlation     -0.548          +0.439      SIGN FLIP
```

**Predictions: P2, P3, P5 held. P1 FAILED. P4 failed on a manual read.**

**P1 failed and the reason is instructive.** Cool-half energy *rose* to 11.91 %.
The ECWT column shows why the prediction was wrong: at bin 0, wet-bulb 9.7 °C,
entering condenser water sits at **19.45 °C** — nowhere near the 35 °C ceiling.
At low wet-bulb the tower has so much capability that even at 90 % load the
condenser water stays cold, so the fan lever is *more* available at data-centre
load, not less, and it acts on a bigger absolute heat flow. The chiller envelope
only binds in the hot bins. **P4 fails with it:** only **1 of 8** bins reaches
ECWT ≥ 33.5 °C, against four of the five hand-picked V5 conditions — which also
means the V5 condition set over-represents the pinned regime relative to an
hours-weighted year.

**P3 held, but by changing sign rather than weakening — and this is the finding
that matters.** r went from **−0.548 to +0.439**. At data-centre load the energy
and water savings are *positively* correlated across bins: they rise and fall
together instead of trading off.

**So HANDOFF.md's "strongest argument in the package for coupling the two models"
does not survive in the form it is written.** A large part of r = −0.548 was a
**load artefact** of the comfort-driven load model — in district cooling, cold
hours are also light hours, which is what made the energy saving large exactly
where the water saving was small. Flatten the load and the anti-correlation
inverts. That model is tagged `[A]` in `annual.py`, so the package's strongest
coupling claim was resting on an assumption rather than on a measurement.
**`HANDOFF.md` should be amended.**

**The coupling argument survives, in a better form.** Do not argue it from
anti-correlation. Argue it from the *seasonal profiles*, which are still
decisive:

- Across the **hot half a pure energy optimiser collects 1.39 %** — nothing.
- **Bin 6 goes negative, −0.56 %**: the optimiser correctly *spends* power to
  save water, which no energy-only controller would ever do.
- Across the **cool half the value is evenly split**, 11.91 % energy against
  10.75 % water, so a water-only controller leaves half of it behind.

That is a stronger argument than the correlation coefficient ever was, because it
does not depend on the load model at all.

**Caveats, all of which must travel with these numbers:**

1. **Flat load 0.90 is an assumption `[A]`**, the same status as `annual.py`'s
   comfort curve. No data-centre plant data was used anywhere.
2. **More of the money now rests on extrapolation.** Bins 5–7 (3,285 h, 37.5 % of
   the year) are above the validated 21.9 °C wet-bulb. Under district cooling the
   value was concentrated in the cool, validated half; at data-centre load the
   water saving is essentially flat across both halves (10.75 vs 10.60), so
   roughly half the water money now sits in the extrapolated region.
3. **Chemistry is still `ARAMCO_RECLAIMED`, carrying open defect 17.** A data
   centre's makeup water is very likely different.
4. **It assumes the data centre has a cooling tower at all** — see Part 2.

---

## Part 5 — Sequencing, given the calendar

**Do not rewrite the DTV or Sanabil applications.** Sanabil is due 1 October —
three weeks out — and the submitted DTV package is district cooling. Repositioning
now is high-risk and low-reward.

| when | do |
|---|---|
| **now → 1 Oct** | Nothing structural. Add data centres as one *expansion* slide backed by the `annual_datacentre.py` result. Fix the four inconsistent defect counts (Part 6). |
| **Oct → Dec** | The dry-vs-evaporative crossover study (Part 2). It is a re-evaluation of existing curves, not new physics, and it is the strongest single artefact for a data-centre conversation. |
| **Dec → Mar** | The CDU heat exchanger (Part 1), *only if* a real conversation asks for it. |
| **never** | GPU/DVFS/ITD modelling. |

---

## Part 6 — Open risks, ranked, including two that got worse this week

1. **Nalco 3D TRASAR is confirmed, and risk #4 is no longer conditional.**
   `market_dossier.md` lists it as *"HIGH if confirmed — source page returned
   403."* It is now confirmed from Ecolab's own product literature: the Nalco
   Scale Index gives *"a 24/7 view of the system scale boundary"* and *"can
   employ one of three control algorithms to either adjust the blowdown rate
   (cycle control), adjust the system pH, or adjust the chemical treatment
   dosage."*
   **Dead claim:** nobody adjusts blowdown, pH and dose against a scale boundary.
   **Surviving claim, and it is still good:** 3D TRASAR picks *one of three*
   rather than co-optimising all three; its index is an **empirical fluorescent
   tracer surrogate for deposition rate**, not a computed ion-specific
   thermodynamic saturation, so it cannot say *which* mineral and cannot be
   evaluated at skin temperature; and it has **no fan-speed actuator and no
   energy objective**. Mizan's registered claim — a chemical saturation limit
   that bounds a *mechanical thermal energy optimiser* — is untouched.

2. **Dry cooling in greenfield AI halls** (Part 2). Now the top strategic risk.

3. **Defect 17 remains open, and a data-centre pitch makes it worse.**
   `ARAMCO_RECLAIMED` carries SO₄ = 566 mg/L against a field-reported 300; charge
   imbalance −14.3 %, ions summing to 1752 mg/L against a stated TDS of 1500.
   **The gypsum wall rests on sulfate.** Any pitch that claims a cycles ceiling
   invites exactly this challenge.

4. **Seawater-cooled coastal sites.** Marafiq prices sea-water cooling at
   SAR 0.069/m³; at that price blowdown-reduction value is nil. Already risk #6.

5. **ChemTreat US 12,358,820 B2** — listed in `market_dossier.md:340` as a citing
   family member but never read. Now scanned: 90 Langelier hits, 19 calcium
   carbonate, **zero** on gypsum, CaSO₄, skin/wall/surface temperature, cycles of
   concentration and fan speed. Bulk-water, dosing-only. It **confirms** the
   narrowed position rather than threatening it.

---

## Part 7 — Repository findings from this pass

The audit passes: **63 checks, no contradictions.** Gate verdicts reproduce
exactly. The corrosion floor is implemented (`CORROSION_FLOOR_SI`) and the
optimum is **completely insensitive to it from −0.5 to 1.0** — same cycles, fan,
pH, makeup and cost at every floor — so the EPRI corrosion objection does not
change the answer. *(Caveat: swept at one condition only, Dhahran summer peak.)*

Three things to fix:

1. **Four documents give four different defect counts, and the audit does not
   check this.**

   | file | claim |
   |---|---|
   | `docs/defect_register.md:16` | "Twenty found, nineteen fixed, one open" |
   | `docs/defect_register.md:280` | "Eighteen defects were found, seventeen are fixed" *(and "Six of the thirteen" in the same sentence)* |
   | `docs/threshold_revision_memo.md:172` | "Thirteen defects were found and reported" |
   | `docs/ENGINEERING_IN_PLAIN_ENGLISH.md:324` | **"Ten defects found, ten fixed, none open"** |

   The last one is the serious one: it is the document written *for the two
   non-technical co-founders*, and it tells them there are **no open defects**
   when defect 17 — the sulfate number the entire gypsum wall rests on — is open.
   `audit.py` checks that the register's *declared open count* matches its OPEN
   rows, but nothing checks the *total found* count across documents. This is the
   same second-order staleness the register already documents in defect 12.

2. **There is no test suite.** `.pytest_cache/v/cache/nodeids` is `[]` — pytest
   ran and collected **zero tests** — and there is exactly one `assert` in the
   whole `src/` tree. The gates are excellent integration tests, but every one of
   the twenty defects was caught by *manual re-derivation*, so every one of them
   can come back. The unit-error class especially: fan % vs Hz (defect 1), drift
   0.0005 vs 0.0005 % (defect 3), the duty fixed-point seed dependence. A
   regression test pinning each is an afternoon's work and permanently protects
   the numbers.

3. **`docs/ENGINEERING_IN_PLAIN_ENGLISH.md` is stale beyond the defect count** —
   it is the co-founder-facing document and it predates defects 11 and 15–20.
   Regenerate or hand-check it before either co-founder speaks to a customer.
