# What is still needed to make this model robust

**Written 4 September 2026, revised the same day after four fixes and a literature pass.** Ordered by leverage, not by effort. Every claim
here is either measured in this repository or is an internal inconsistency
between the code and its own comments. Nothing is imported from outside without
saying so.

The audit passes, the register stands at forty-nine found / forty-nine fixed / none open
open, and the numbers in every document match the artefacts. That is
*consistency*. It is not the same thing as *robustness*, and the gap between the
two is what this file is about.

---

## 1. ~~The gypsum temperature model~~ — FIXED 4 September (defect 15)

**FIXED.** `log_k_gypsum` now uses the `phreeqc.dat` analytic expression rather than a
single-enthalpy van 't Hoff — the same treatment calcite always had, from the database already
cited, so no new source. Anchored to the same log_k25 (agrees to 0.0009), it has an interior
maximum near 23 °C and 10.8× the temperature response.

**`SI_gypsum` now has a minimum at 43.4 °C and rises above it** — a solubility *maximum*
there, which matches the literature's ~42 °C gypsum–anhydrite transition and was not fitted
to it. Four pre-registered predictions, all passed (`src/gypsum_logk_upgrade.py`).

> **CORRECTED 10 September 2026 — defect 23.** The sentence that used to stand here read
> *"Gypsum is therefore most saturated at the hot skin, which is the mechanism the product
> actually claims."* **That does not follow, and it is false on this water.** A solubility
> *maximum* at 43.4 °C means SI_gypsum is at its **minimum** there — so a condenser skin at
> 38–48 °C sits in the least-saturated part of the curve, not the most. Measured on
> `ARAMCO_RECLAIMED` at 6 cycles, pH 8.0: basin at 30 °C gives **SI 0.2322**, skin at 40 °C
> gives **0.2254** — the basin is more saturated by 0.0068 log units, and the same ordering
> holds at every cycles count tested. SI does not exceed its 20 °C value again until roughly
> 75 °C, far above any condenser skin. See `docs/defect_register.md` defect 23.

**It also dissolved defect 14 as a side effect:** with a temperature function that can turn over,
the ceilings come out **6 and 7 at all five conditions** instead of varying with which condition
you report from. The condition-dependence was an artefact of the wrong temperature model.

The original diagnosis is kept below because it is why the fix was found.

**This was the one that could move the product thesis, so it was first.**

`src/chemistry.py` says, in the comment that decides where each mineral is
evaluated:

> `gypsum   maximum near 35-40 C, weakly retrograde above it`

The implementation is `log_k_gypsum = van 't Hoff(log_k 25 = -4.58, dH = -0.109 kcal)`.
**A single-enthalpy van 't Hoff is monotonic by construction. It cannot produce a
maximum anywhere.** Measured over 10–80 °C it is strictly decreasing, and the
total movement across 25→70 °C is **0.0105 log units**.

The full saturation index moves far more than that, and in the same direction:

| T (°C) | SI_gypsum at 6 cycles |
|---|---|
| 25 | 0.2295 |
| 40 | 0.2028 |
| 55 | ~0.171 |
| 70 | 0.1346 |

**So ~90 % of the temperature response of gypsum in this model comes from
activity coefficients, not from solubility.** And the net effect is that gypsum
looks *less* saturated at the hot tube skin than in the bulk.

Three consequences, all uncomfortable:

1. **Evaluating gypsum "hot" is the permissive choice here, not the conservative
   one.** `MINERAL_EVAL_POINT["SI_gypsum"] = "hot"`, and the code comment already
   concedes *"but the benefit is small"*. For calcite, hot is conservative. For
   gypsum, in this model, hot is generous.
2. **It is what made defect 14 possible.** The published two-ceilings condition is
   the hottest of the five swept, and it returns the most permissive gypsum wall
   (8 cycles against 7 at every operable condition). That is not a coincidence —
   it is this sign.
3. **The public claim is "gypsum saturates at the condenser tube wall, and LSI
   cannot see it."** The second half is solid. The first half is being carried by
   a model whose gypsum response says the wall is the *safest* place in the loop.

The condenser skin in these runs sits near **40 °C** (T_wo ≈ 32 °C plus the
assumed 8 K skin rise) — which is exactly where the comment puts the solubility
maximum, and exactly where a monotonic fit is least defensible.

**What would fix it:** a gypsum solubility model that can turn over — a
temperature-dependent enthalpy, a direct solubility correlation, or a Pitzer
treatment at this ionic strength. Then re-run the ceilings. **Until that is done,
the position of the gypsum wall as a function of skin temperature is not a
result this package should defend hard**, and the two-ceilings claim should be
argued on the *mechanism* (LSI is blind to sulfate) rather than on the integers.

---

## 2. ~~The modelled plant cannot run a Gulf summer~~ — FIXED 4 September (defect 16)

**FIXED.** The cause was one line: `q_avail = Q_evap_kw * capft_here`, where `capft_here` is
normalised to ARI (29.44 °C entering condenser water). That asserted the installed machine is
exactly the size of the load *at a rating point the plant never operates at*. Chillers are selected
at their design entering-condenser temperature. The machine is now selected at the top of its own
fitted range, 35 °C — a **15.0 % margin**, an entirely ordinary selection — and the same nominal
feeds both the capacity check and the power curve.

**All five conditions are feasible again**, and the V5b sweep is now inside the envelope at every
cycle count instead of outside it at all ten. `src/chiller_selection_audit.py`.

Independent corroboration, from a review supplied later: cooling towers *"are oftentimes oversized,
and thus rarely operate at their design points"* (Ghoddousi et al. 2021).

The original diagnosis follows, because it is the argument for the fix.

After defect 11, `gate_v5` reported:

```
Dhahran summer humid    no feasible solution
Doha summer humid       no feasible solution
```

Two of five design conditions have **no feasible operating point at all** — not
"a worse one", none. The single 10 MW module with a fixed duty and one York YT
simply cannot reject the heat at 38 °C / 55 % RH.

Real district-cooling plants demonstrably do operate on those days. So the
finding is not about the Gulf; it is about the **plant model**: fixed duty, one
machine, no staging, no thermal storage, no chiller sequencing. A real plant
stages multiple chillers and lets duty float.

This matters commercially as well as technically: the controller is now
validated over **three** conditions, all of which the machine can serve, and the
two it cannot are the ones a customer would ask about first.

**What would fix it:** let duty float, or model N chillers with staging. This is
the largest single piece of modelling work on the list and it is the one that
decides whether the product has anything to say in a Gulf August.

---

## 3. ~~Defect 14 — ceilings from an unreachable condition~~ — RESOLVED by fixes 1 and 2

**No longer needs the reporting judgement it originally called for.** Defects 15 and 16 removed
both causes. The ceilings are now **6 and 7 at every condition tested**, including the previously
published one, and every row of the sweep sits inside the chiller envelope.

**Still outstanding:** `figs/water_ceiling.png` regenerates from the artefacts, but the chart
attached to the 1 September LinkedIn post is a static image carrying the old pair, and it cannot be
corrected without replacing the post. That is a founder decision, not a code change.

---

## 4. V2 still fails, and the diagnosis is the business model

Evaporation MAPE **9.90 %** against a pre-registered **8.00 %**. Diagnosed as
fill-characteristic drift between campaigns rather than an unaccounted bleed. It
stays failed, and it should — it is the quantitative justification for an annual
recalibration licence.

**What would close it:** per-campaign fill re-identification, which is already
scoped. What would make it *evidence* rather than an argument is the same fill
law identified on a second tower.

---

## 5. The validation envelope, which is the honest limit on everything above

- **62.5 %** of the hours-weighted Dhahran year sits inside the wet-bulb envelope
  the model was validated in. The other **37.5 % is extrapolation**, and no
  weighting scheme fixes that.
- The validation data is **Almeria at 21.9 °C wet-bulb**; the Gulf design point is
  **30.3 °C**. This is listed as OPEN in `HANDOFF.md` and is the only open item
  whose direction is genuinely unknown.
- **There is no field data at all.** One public experimental dataset, plus
  synthetic. Every percentage in every document is a modelled quantity.

---

## 6. Assumptions that carry weight and have never been measured

| Assumption | Where it bites | Status |
|---|---|---|
| **Skin ΔT = 8.0 K**, hardcoded | Sets where every mineral is evaluated, so it sets both ceilings | `results/skin_sensitivity.json` exists; the value is assumed, not measured |
| **Sulfate in the makeup** | `value_of_information.json`: worth **10.2 %** of makeup water, and **no operator measures it** | `sulfate_bounds.py` brackets it to **2.50 cycles against a 2.00 threshold — FAIL**. The threshold was not moved |
| **Fouling resistance** | `fouling_energy.py` prices a given resistance; it is not a rate model | Says what fouling costs, not how fast it arrives |

The sulfate one is the interesting one commercially: it is simultaneously the
largest unmeasured lever and the reason the product exists. It is also the only
place where the honest answer is currently "we cannot bound it tightly enough."

---

## 7. Two safety gaps that customer discovery found, and the model still has

Both came from real operators, both are recorded in `docs/discovery_findings.md`,
and neither is in the code:

1. ~~**No corrosion floor.**~~ **FIXED 4 September.** Saturation is now a *band*, not a
   ceiling: `CORROSION_FLOOR_SI` (default 0.0) is enforced at **bulk** temperature, where LSI
   practice sits, while the scaling ceiling stays at the **skin**. Those being different
   evaluation points is the whole product. Negative-tested — the guard fires above SI 1.83 and
   not below, so it is a real check and not decoration.

   **It costs nothing on this water, and the reason is interesting.** Swept from −0.5 to +1.0,
   the optimum does not move at all: bulk `SI_calcite` at the operating point is **1.830**, far
   above any floor. The optimiser never wants to acidify hard, because **gypsum is what binds and
   acid cannot move gypsum** — so it has no incentive to go anywhere near the aggressive region.
   The guard will bind on a low-sulfate water where calcite is the constraint and acid *is* the
   lever. `src/corrosion_floor_audit.py`.
2. **No acid-dosing interlocks.** A real incident: makeup tripped overnight, acid
   kept pumping, the tubes were destroyed. Needs makeup-flow proving, an
   independent low-pH trip, and a bounded dosing integral.

Until both exist, this controller should not be connected to a dosing pump on a
real plant, and no demonstration should imply that it could be.

---

## 8. Biofouling — a third of the curriculum, and none of the model

The 1992 training syllabus devotes roughly a third of its scale-and-corrosion
content to biological fouling, and the most experienced interviewee called it
*"arguably the most important"* issue on a TSE loop. **Mizan models none of it.**

On treated sewage effluent specifically, this is the gap most likely to be raised
by someone who has actually run one.

---

## 9. NEW — the field ceiling nobody has passed

The Saudi Aramco Dhahran pilot, eight months, published by the operating engineers, is the first
real-plant data this package has:

| | cycles | outcome |
|---|---|---|
| raw groundwater | 2 | **severe scaling on the condenser surfaces** |
| treated sewage effluent | 3.5 | **condenser surface clean, no mineral deposit** |

`src/field_validation.py` scores the model against it and **passes 3 of 4** pre-registered
criteria. The failure, F2, is informative rather than damaging: the model calls TSE at 3.5 cycles
over its *skin* `SI_calcite` limit of 0.5, but 0.5 is a threshold of bulk-LSI magnitude being
applied at the skin — a category error in the limit, not the chemistry. **F2 is not rescored.**

The reported diagnostic beside it is the strongest validation number in the package:

> The plant published its own index as **LSI 0 to 0.5**. This model puts the same water at
> **SI_calcite = 0.484** at 25 °C — **0.016 log units** from the top of the operator's reported
> range, on an analysis entered before the gate existed and never tuned against it.

### Five independent sources converge on the same band

An earlier draft of this file said *"no field data supports operation above 3.5 cycles"*. **That
was too pessimistic and is corrected here.** Widening the search turned up four more sources, and
they agree with each other and with the model:

| source | kind | cycles |
|---|---|---|
| Aramco Dhahran pilot | 8-month field trial, TSE | raised 2 → **3.5**, condenser clean |
| ACS *I&EC Research*, treated municipal wastewater | bench + pilot | *"scaling would not be a significant concern ... operated at **4–6 cycles**, and no anti-scaling chemicals would be required"* |
| Engro Fertilizers Utilities-2 | operating plant, canal water | runs **4–6**, blows down at 8 |
| DOE FEMP BMP #10 | US federal guidance | *"many systems operate at two to four ... while **six cycles or more may be possible**"* |
| **this model** | computed from ion chemistry | economic optimum **6**, gypsum wall **7** |

**Four independent parties, three continents, four different waters, and one physics model all put
the practical ceiling in the same place.** The model was not fitted to any of them.

That is a materially stronger position than the one this file described a few hours earlier, and it
is worth stating precisely because it cuts *for* the product after a day of findings that cut
against it.

**The honest boundary that remains:**

> Nobody has demonstrated **7** cycles, and nobody has demonstrated **6 on this specific Saudi
> TSE**. The convergence supports the band; it does not verify the wall. The wall is the thing the
> product sells, and it is still the thing only a plant can confirm.

## 10. NEW — sulfate attack on the concrete basin, which the model does not have

At 6 cycles the loop runs at roughly **3 400 ppm sulfate**. Sulfate attack on concrete via
ettringite formation is a well-documented durability mechanism, cooling-tower basins are commonly
concrete, and ACI 201's severe exposure band begins around 1 500 ppm.

**The controller has no concrete-durability constraint of any kind.** It optimises against scaling
and, since 4 September, against corrosion of metal — but not against attack on the structure
holding the water. On a plant with an ordinary Portland cement basin this would bind **before**
gypsum, which would make it the real ceiling.

Flagged rather than implemented: the specific thresholds circulating informally (800 / 1 200 ppm)
have no citation, and inventing one would be worse than naming the gap. See
`docs/external_claims_verified.md`.

## 11. NEW — the energy half of the product is prior art

Li, Li & Seem (2012 ACC, Johnson Controls) published a **model-free extremum seeking controller**
that optimises exactly the chiller/fan power trade-off this package computes, using fan speed as
the input, fourteen years ago.

Mizan's own numbers make the consequence unavoidable: the five-condition mean electrical saving is
**2.86 %**, and under **0.6 %** in the four hottest annual bins. An ESC loop would capture most of
that with no model, no chemistry and no licence.

What ESC cannot do is see the wall — it optimises what it measures, and it measures power. Full
argument, and what it implies for pricing and positioning, in `docs/prior_art_esc.md`. **It argues
for a constraint service rather than a rival optimiser**, and that is a founder decision.

## The short version

Ranked by what would most change what this package can defend:

1. ~~Give gypsum a solubility model that can turn over.~~ **Done, defect 15.**
2. ~~Let the plant meet a Gulf summer.~~ **Done, defect 16 — selected at design, not at ARI.**
3. ~~Close defect 14.~~ **Dissolved by 1 and 2; the ceilings no longer depend on condition.**
4. ~~Corrosion floor.~~ **Done, and non-binding on this water for a reason worth understanding.**
   Dosing interlocks remain a specification, not code.
5. **Reprice and reposition around the constraint, not the optimisation** — the energy half is
   2012 prior art and the water half is not. Founder decision.
6. **Resolve the makeup analysis** (defect 17, open). The modelled water fails charge balance by
   −14.3 % and its ions exceed its own stated TDS by 16.8 %. Consequence is bounded to one cycle,
   but a self-inconsistent analysis should not sit under the headline claim.
7. **Get a plant to demonstrate the wall.** The 4–6 band is now corroborated by four
   independent sources; **7 is not, and 6 on this specific TSE is not.**

Items 1–4 are done. Items 5 and 6 are days of work or one decision. **Item 7 is still the only one
that cannot be done from a desk, and it is still the one that decides whether any of the rest is
true.** What changed today is that there is now real plant data to be measured against at all,
the model agrees with it to 0.016 log units where they overlap, and four independent sources put
the operating band exactly where the model computes it.


---

## Corrosion floor — widened from one condition to five, 7 September 2026

`results/corrosion_floor.json` swept the floor at **Dhahran summer peak only** and
found the optimum completely insensitive to it. That was a strong claim resting on
one condition, which is exactly the kind of thing this file exists to name.

`src/corrosion_floor_conditions.py` repeats it at **all five conditions the V5 gate
scores**, with the prediction registered before the run:

```
Dhahran summer peak   6 cycles, fan 60 %, pH 8.25   -> floor slack
Dhahran summer humid  6 cycles, fan 80 %, pH 8.00   -> floor slack
Dhahran shoulder      6 cycles, fan 80 %, pH 8.25   -> floor slack
Doha summer humid     6 cycles, fan 80 %, pH 8.00   -> floor slack
Gulf winter           6 cycles, fan 80 %, pH 8.25   -> floor slack

C1  the floor binds at none of the five                 HELD
```

Identical cycles, fan, pH, makeup and cost at every floor from **-0.5 to +1.0** —
the whole band a real plant chemist works in, and past the top of it. The reason is
visible in the table: every optimum lands at **pH 8.00-8.25**, where SI_calcite is
already far above any floor in that range. The optimiser was never near the
aggressive corner.

**What this does and does not settle.** It settles that adding the floor costs
nothing and that the EPRI objection does not move the answer anywhere in the
envelope. It does **not** settle corrosion: `CORROSION_FLOOR_SI` is a *saturation
proxy*, and EPRI's actual warning is that sulphuric acid replaces protective
alkalinity with **corrosive sulfate** — an attack mechanism that a calcite
saturation index cannot represent at all. The KFUPM potentiostat and coupon work
stays on the list, and it is now the only way to close it.

---

## The chemistry engine, 10 September 2026: what is now closed and what is not

Four defects were found and fixed in the chemistry in one pass (24, 25, 26, 27),
and the engine is now scored against values this repository did not produce.

### Closed

| | evidence |
|---|---|
| **Aqueous ion association** (defect 24) | `speciate()` solves ten ion pairs. USGS gypsum-saturation standard: **−0.0163** against a published 0.000, previously +0.2046. Reproduces the published distribution — free Ca 0.01059 vs 0.01046, CaSO₄ 0.004495 vs 0.004627 |
| **Second, structural benchmark** | predicted gypsum solubility peaks at **40–43 °C**, the textbook maximum. A shape, not a point: only obtainable if both the solubility product and the activity coefficients are right |
| **Acid conservation** (defect 25) | dose charged against `blowdown + drift` = makeup/C. Falls by exactly C at every cycles count |
| **Davies validity** (defect 26) | `pitzer_required()` was computed from the first commit and enforced by nothing. Now a `davies_range` violation at both evaluation sites |
| **Analysis validation** (defect 27) | four objective checks; the product boundary raises rather than absorbing. The controller runs on an analysis that passes all four |
| Mass balance | closes to 1e-12 on every component |
| Convergence | 126/126 across the operating envelope |
| Dilute limit | free → total, pairs → 0 |
| Ionic strength | speciated I < unspeciated I, as complexation requires |
| API trap | `ph_saturation_brucite(T_c, water)` is reversed from the module; a swapped call now raises by name |

### Still open, and honestly

**Defect 17 — the sulfate discrepancy — is NOT closed.** Switching the controller
to `ARAMCO_FIELD_VALIDATED` is not a resolution of it. What the objective tests
establish is narrower and worth stating exactly:

> The published analysis fails TDS closure by +22.7 % and therefore **cannot** be
> right as written. That does not establish that 300 mg/L **is** right, and it
> does not identify which of the reported numbers is wrong. The field account
> also differs on calcium, chloride and bicarbonate, and those numbers were not
> obtainable, so only sulfate is corrected. This is a **partial reconstruction**.

**The silica value is an assumption, not a measurement of this water.** 26.8 mg/L
is Al-Mutaz & Al-Anezi's Salbukh figure for Riyadh water, declared and cited —
not a silica assay of the Aramco TSE. It is now the **binding mineral**, so the
whole ceiling rests on a number imported from a different water.

**One makeup-water analysis closes both.** Sulfate and silica, from the same
sample, on the water a real plant actually runs. That single measurement is worth
more than any further modelling, and it is the highest-value action in the
project.

### What the corrections cost, and what they bought

They cost the two ceilings and the gypsum framing. They bought a chemistry engine
that agrees with a published standard, refuses an analysis that fails its own
closure test, and lands on observed industry practice: **the computed ceiling on
the validated water is ~5.8 cycles against a Gulf empirical band of 3.5–5.0.**

A first-principles limit landing on observed practice, with no parameter fitted
to it, remains the strongest validation in this package — and it survived all
four corrections.
