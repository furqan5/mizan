# Deep-research prompt #2 — paste into Gemini Deep Research

> Round 2. The first round answered most of what was open; this round targets four specific numbers that are currently blocking the model, plus two commercial unknowns. Paste the whole thing.

---

## CONTEXT

I am building **Mizan**, a retrofit supervisory controller for cooling-tower / condenser-water loops in Gulf district cooling. It computes mineral saturation with an ion-association model on USGS PHREEQC constants, and — this is the distinguishing part — evaluates **each mineral at the temperature where that mineral is least soluble**: retrograde species (calcite, gypsum, magnesium silicate) at the hot condenser tube skin, prograde species (amorphous silica) at the cold tower basin.

**Established in round 1, do not re-research:**

- Gulf TSE silica sits ~20–60 mg/L; Salbukh (Riyadh) raw water 26.8–30 mg/L measured.
- Amorphous silica is prograde; the true ceiling moves 95 → 143 mg/L across a 15–35 °C basin. Industry uses a static "150 mg/L" rule regardless of basin temperature, which is non-conservative by 37 % at a winter basin.
- Acumer 5000 (polymaleic) raises the workable silica ceiling ~150 → ~250 mg/L.
- French Creek Software and OLI Systems already do full ion-association/Pitzer speciation, offline, from bulk temperature profiles.
- ChemTreat US 11,780,742 B2 claims skin-temperature saturation driving antiscalant dose.
- Aramco reclaimed-water analysis (Badruzzaman 2022) is in hand.

**Rules:** never invent a citation; every claim gets a working URL and a `[C]` / `[A]` / `[UNVERIFIED]` tag; report negatives explicitly; end with "What I could not find" and "What contradicts the thesis".

---

# TASK

## Priority 1 — The magnesium silicate threshold (currently blocking the model)

I have added magnesium silicate to the model as sepiolite (PHREEQC `Sepiolite`, log_k 15.760, ΔH −10.7 kcal), evaluated at the hot skin because it is retrograde. On real Aramco reclaimed water it comes out **supersaturated at every cycle count** — SI +1.56 at 3 cycles rising to +3.50 at 8. Taken literally that forbids all operation, which is obviously wrong since plants run 4–5 cycles on this water. So I have the driving force but no usable threshold.

1. **What operating limit does industry actually use for magnesium silicate in cooling water?** I believe it is an empirical **Mg × SiO₂ product** rather than a thermodynamic index. Find the actual limit, its units, and the temperature it is evaluated at. Vendor technical manuals (Nalco, Veolia, Kurita, ChemTreat, Solenis), Betz/Nalco water handbooks, IWC and AWT conference papers.
2. **Is sepiolite the right mineral proxy**, or should magnesium silicate scale be modelled as amorphous Mg-silicate, talc, chrysotile, or something else? What log_k and ΔH do practitioners use?
3. **Documented cases of magnesium silicate scaling in cooling towers** — at what Mg, SiO₂, pH and skin temperature did it occur?
4. **Does magnesium silicate genuinely precede amorphous silica** as the binding constraint on high-silica, high-magnesium Gulf makeup water? This is the specific criticism levelled at my model and I need it resolved either way.

## Priority 2 — The discharge limit (currently blocking the model)

I modelled a blowdown TDS discharge cap and got a nonsense result: a 3,000 mg/L cap on 1,500 mg/L makeup implies a hard ceiling of 2.0 cycles, well below the 3.5–5.0 the industry demonstrably operates. So either the cap does not apply to cooling-tower blowdown, the blowdown goes to a route the cap does not cover, or my figure is wrong.

5. **What discharge limits actually apply to cooling-tower blowdown in Saudi Arabia and Qatar** — TDS, chloride, sulfate, temperature, phosphate, and any others? Saudi Water Authority, MEWA, Royal Commission for Jubail and Yanbu, Kahramaa, Qatar Ministry of Municipality and Environment, and any municipal sewer-discharge codes.
6. **Where does cooling-tower blowdown actually go** at Gulf district-cooling plants — municipal sewer, evaporation pond, deep-well injection, irrigation reuse, sea outfall? Different routes carry different limits, and this determines whether the constraint binds at all.
7. **Are there financial instruments attached** — sewer surcharges by TDS or volume, discharge fees, water-reuse credits — that change the economics of blowing down more or less?

## Priority 3 — Two numbers I still cannot source

8. **The cost of a cooling-tower or condenser scaling event.** Round 1 found nothing. Try harder and go wider than the Gulf: insurance loss data, arbitration and legal cases, utility incident reports, EPRI/ASHRAE studies, plant-outage postmortems. I want defensible figures for lost condenser capacity, chemical cleaning cost, energy penalty per unit of scale thickness, and downtime cost.
9. **Cooling-tower fill ageing.** Any study quantifying how the fill transfer characteristic degrades over months or years. I have measured a 21 % coefficient drift over four years and Kloppers (2003) explicitly did not study ageing. Even indirect evidence — fill replacement intervals, performance-test histories, capacity-decay curves — would help.

## Priority 4 — Competitive and commercial

10. **Do French Creek Software or OLI Systems have a real-time or online control product**, as opposed to offline design software? Any OEM integration, API, controller partnership, or embedded licensing? This determines how much room the "offline prediction versus online actuation" distinction actually leaves.
11. **Does any vendor evaluate saturation at more than one temperature simultaneously** — i.e. hot surface AND cold basin in the same control decision? This is my core claim and I want it falsified if it is false.
12. **What do Gulf district-cooling operators actually pay for water treatment** — annual chemical spend per plant or per ton of refrigeration, service-contract structures, and who signs. Anything that lets me size a realistic contract value.

---

## OUTPUT FORMAT

Tables with units and a source URL per row. Then:

- **"What I could not find"** — every question that returned nothing.
- **"What contradicts the thesis"** — anything arguing against the approach, unsoftened.
- Full source list with working URLs.
