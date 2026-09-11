# Mizan, explained from scratch

> **SUPERSEDED IN PART — 10 September 2026.** Four chemistry defects were found
> and fixed (register 24–27) and defect 17 was resolved. Every annual figure in
> this document moved, and the *narrative* moved with them: water was the
> headline term and is now the smallest one.
>
> | | as written here | corrected |
> |---|---|---|
> | annual makeup water | 8.8 % | **2.72 %** |
> | annual operating cost | 6.4 % | **3.77 %** |
> | annual electrical power | 5.4 % | **4.33 %** |
> | V5 water gate | 10.83 %, failed | **6.65 %, still failed** |
> | ceilings | 6 and 7, gypsum | **5 and 6, amorphous silica** |
>
> Inline figures below are tagged where they occur. **The pitch is not rewritten
> here — that is a founder decision**, because energy is now the largest term and
> `docs/prior_art_esc.md` shows the energy half is prior art seven times over.



**For Damia, Ahsan and Furqan. Written so that any of us can hold a technical
conversation with an operator without the others in the room.**

No equations. Every term is defined the first time it appears. Every number in
here is one we can defend, and where a number is uncertain it says so.

Last updated 30 August 2026.

---

## Part 1 — What we built, in one page

A large building or industrial plant is cooled by a machine called a **chiller**.
The chiller makes cold water for the building, and in doing so it produces waste
heat. That heat has to go somewhere. It goes into a second water loop — the
**condenser water loop** — which carries it to a **cooling tower** on the roof.

The cooling tower gets rid of the heat by evaporating some of the water into the
air. This works extremely well, and it is why almost every large plant in the
Gulf uses one. It also means the plant continuously loses water to the sky, and
that water has to be replaced.

Three things get adjusted on that loop every day:

| Handle | What it does | Who sets it today |
|---|---|---|
| **Fan speed** on the tower | More fan = colder water = the chiller works less hard, but the fan itself uses power and more water evaporates | The building management system |
| **Blowdown** — deliberately dumping some water | Stops dissolved minerals building up to the point where they form deposits | The water-treatment contractor |
| **Acid dose** | Lowers the water's pH, which keeps certain minerals dissolved | The water-treatment contractor |

**The whole product is this:** those three handles are not independent. Every
one of them changes what the other two should be. But they are set by two
different parties who never speak, using two fixed setpoints that were chosen
once and rarely revisited.

Mizan is a small retrofit box that measures the loop, computes what is actually
happening at the surfaces where deposits form, and sets all three handles as one
decision.

---

## Part 2 — The vocabulary

Learn these eight and you can follow any conversation on this topic.

**Cooling tower** — the structure that rejects heat by evaporating water.

**Condenser** — the heat exchanger inside the chiller where the waste heat moves
from the refrigerant into the condenser water. It is a bundle of tubes. The
water flows inside the tubes; the tube walls are the hottest wetted surface in
the whole loop.

**Makeup water** — the fresh water added to replace what evaporated and what was
dumped as blowdown.

**Blowdown** — water deliberately removed from the loop to stop minerals
concentrating too far. Sometimes called bleed.

**Cycles of concentration (often just "cycles" or CoC)** — how many times more
concentrated the loop water is than the makeup water. If the makeup has 100 mg/L
of something and the loop has 400 mg/L, the loop is at 4 cycles.

> Running at higher cycles means less blowdown, which means less makeup water,
> which saves money. It also means everything dissolved in the water is more
> concentrated, which makes deposits more likely. **This is the central trade of
> the whole water side.**

**Scale** — hard mineral deposit that forms on surfaces when the water can no
longer hold a mineral in solution. It insulates the tube, so the chiller has to
work harder for the same cooling. It is the thing everybody is afraid of.

**Saturation** — the point at which water cannot hold any more of a given
mineral. Past that point the mineral comes out of solution and deposits. Each
mineral has its own saturation point, and it moves with temperature and pH.

**Treated sewage effluent (TSE)** — municipal wastewater cleaned up and reused.
Saudi Arabia and Qatar are pushing cooling plants onto it because fresh water is
scarce. It is harder to manage than fresh water because it carries more
dissolved material.

---

## Part 3 — The physics, in plain terms

### 3.1 Why deposits form where they do

Most substances get **more** soluble as you heat them — sugar dissolves better in
hot tea. A handful of minerals do the opposite: they get **less** soluble as
they get hotter. That behaviour is called **retrograde** solubility.

Calcium carbonate — ordinary limescale — is retrograde. So is gypsum, above
about 38 °C. So is magnesium hydroxide.

This has one enormous consequence:

> **Retrograde minerals deposit on the hottest surface in the loop, which is the
> condenser tube wall — exactly the surface whose cleanliness the plant's
> efficiency depends on.**

But not all of them behave that way. **Amorphous silica is prograde** — it
behaves normally and gets *more* soluble as it heats up. So silica does the
opposite: it deposits in the **coldest** part of the loop, which is the tower
basin where the water has just been cooled.

This is not our theory. EPRI, the US electric power research institute, states
it directly in their cooling-water review: calcium carbonate "forms
preferentially on the hotter surfaces... usually the heat exchanger tubing",
while silica "is therefore found in cooler areas of the system such as the
cooling tower fill."

### 3.2 Why that breaks standard practice

Every conventional controller does one of two things. It either watches the
**bulk water temperature** — the average temperature of the water sloshing
around the loop — or it watches **electrical conductivity**, which is a rough
proxy for "how much stuff is dissolved in here".

Both are measured in the bulk. Neither can see the tube wall. And the tube wall
runs several degrees hotter than the bulk, because that is where the heat is
crossing.

So the plant computes its safety margin at a temperature that is not the
temperature where the danger is.

Our model evaluates **each mineral at the temperature where it is least
soluble** — the hot tube wall for the retrograde ones, the cold basin for
silica. That is the single sentence that describes what is different about
Mizan.

### 3.3 The other half: the energy trade

Slow the tower fan down and you save fan power, and less water evaporates. But
the condenser water comes back warmer, so the chiller has to push against a
higher temperature and burns more compressor power.

Speed the fan up and the opposite happens: colder condenser water, the chiller
gets more efficient, but you spend fan power and evaporate more water.

There is an optimum, and it moves with the weather, the load, and the water
chemistry. Nobody is currently solving for it, because doing so requires the
thermal model and the chemistry model to be the same model.

### 3.4 The result that makes this a real product

When we ran the controller across a whole year of real Dhahran weather, the
energy saving and the water saving turned out to be **anti-correlated** — when
one is large the other is small. Statistically, a correlation of −0.55.

| Half of the year | Power saved | Water saved | Total cost saved |
|---|---|---|---|
| Cool half (4,380 hours) | **10.4 %** | 7.2 % | 9.1 % |
| Hot half (4,380 hours) | 2.1 % | **9.8 %** | 4.7 % |
| **Whole year, as a ratio of totals** | **5.4 % [SUPERSEDED 10 Sep 2026 -> 4.33 %]** | **8.8 % [SUPERSEDED 10 Sep 2026 -> 2.72 %]** | **6.4 % [SUPERSEDED 10 Sep 2026 -> 3.77 %]** |

In the cool half the controller runs the fan **up**, spending fan power to buy
compressor power. In the hot half it slows the fan down to save evaporation.
Two completely different strategies, and the total cost saving stays between
5.6 % and 10.9 % all year because they hand off to each other.

> **This is the best argument we have.** A water-treatment controller collects
> almost nothing across the cool half of a Dhahran year. An energy optimiser
> collects almost nothing across the hot half. Only something that prices both
> holds the saving across all 8,760 hours.

---

## Part 4 — What we actually built

Four pieces of software, all written from published equations rather than copied.

**1. A moist-air properties library.** Everything about how much water air can
hold at a given temperature and humidity. Written from the ASHRAE handbook.
Independently checked: it reproduces ASHRAE's own published design conditions
for Dhahran to within **0.20 K**.

**2. A cooling tower model.** The Poppe method — a standard, rigorous way of
computing heat and water transfer between falling water and rising air. It
tells us how cold the water gets and how much evaporates.

**3. A water chemistry engine.** Computes what is dissolved in the loop, what
form it is in, and how close each mineral is to depositing. The chemical
constants come from PHREEQC, the US Geological Survey's standard database — so
anyone can check our chemistry against the accepted reference.

**4. A supervisory optimiser.** Searches over fan speed, cycles and pH, prices
each combination in dollars per hour, rejects any that would cross a saturation
limit at the tube wall or push the chiller outside its safe operating window,
and picks the cheapest one left.

Everything was then **written a second time, independently, in MATLAB and
Simulink** and the two versions compared. They agree on outlet water temperature
to **0.000014 K**. That proves the Python results are not a coding accident in
one codebase.

---

## Part 5 — How we tested it, and why that matters more than the results

This is the part that will impress a good reviewer, and it is worth all three of
us being able to explain it.

**We wrote down the pass marks before we ran the test.** Six criteria, with
numeric thresholds, fixed and printed before any fitting was done. Then we
calibrated the model on one experimental campaign, and tested it **once** on two
completely different campaigns it had never seen.

That is called a **pre-registered holdout**, and it is what separates a real
validation from a demonstration. If you tune the model until it passes, you have
proved nothing — you have just described your own data back to yourself.

The data is a published set of 165 experiments on a real cooling tower at a
research facility in Spain, released under an open licence. We check its
fingerprint (an MD5 hash) so we can prove we used the published version
unmodified. Anyone can download it and re-run our whole package in four
commands.

---

## Part 6 — The results, in plain language

| What we tested | Pass mark | Result | |
|---|---|---|---|
| Can it predict how cold the water gets? | within 1.00 °C | **0.54 °C** | Pass |
| Can it predict how much heat is rejected? | within 6.00 % | **5.94 %** | Pass |
| Can it predict how much water is consumed? | within 8.00 % | 9.90 % | **Fail** |
| Does the controller cut total operating cost? | at least 3 % | **5.75 %** | Pass |
| Does the controller cut makeup water? | at least 15 % | 10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %] | **Fail** |
| Does it ever cross a scaling limit? | never | never | Pass |

Alongside those we report, but do **not** count as a test, the electrical power
reduction: **2.86 %** averaged over the test conditions, **5.4 % [SUPERSEDED 10 Sep 2026 -> 4.33 %]** over a real
Dhahran year. We do not count it because we computed it after seeing the
results, and setting a pass mark after you know the answer is not a test.

### Why we report the two failures

Because a package with no failures in it is not credible, and because both
failures turned out to teach us something the passes did not.

---

## Part 7 — The two failures, and what they actually found

### Failure 1: the water prediction

**The short version:** we found a mistake in our own code, fixed it, and the fix
turned a pass into a failure.

A cooling tower loses a small amount of water as droplets blown out of the tower
— called **drift**. Manufacturers quote drift as a percentage of the water
flowing: modern equipment is around 0.001 %. We had written 0.0005 into the code
as a plain fraction, when the published figure was 0.0005 **per cent**. So our
model thought the tower was losing a hundred times more water as droplets than
it really does.

That extra fictional water was padding our prediction by about 5 %, which was
most of what made the original 7.11 % result look like a pass. We corrected the
constant, the padding vanished, and a real shortfall appeared underneath it.
**That earlier 7.11 % pass is withdrawn and superseded by the 9.90 % figure above.**

Then we asked why the shortfall existed. Two possible explanations, and
critically, **they predicted opposite things**:

- Maybe the real tower had a small leak or bleed we did not know about.
- Maybe the tower's own performance had changed over the four years the
  experiments span — the packing inside a cooling tower fouls and degrades.

If it is a leak, re-fitting the model to each campaign separately cannot help,
because a leak is something our model does not contain at all. If it is
degradation, re-fitting per campaign should fix it almost completely.

We ran it. Every campaign came inside the 8 % pass mark on its own fitted
values — 6.55 %, 7.80 %, 4.50 %. **The leak explanation is dead.** The tower's
own characteristic moved by 23.5 % over four years.

> **Why this matters commercially:** it is the proof that the annual
> recalibration licence is a functional requirement and not an upsell. A
> controller shipped with fixed factory settings goes quietly stale as the tower
> ages. This failed test is the measurement of how fast.

### Failure 2: the water saving

**The short version:** we set ourselves a target that was physically impossible,
and only discovered why after we missed it.

The maths of makeup water is fixed. If you raise cycles from 4 to 7, you save
exactly 12.50 %. To 8, exactly 14.29 %. To hit 15 % you need **8.5 cycles**.
This is arithmetic, not modelling — there is no cleverness available.

Our chemistry says **gypsum** — calcium sulphate, the mineral in plasterboard —
saturates at **8 cycles** on Gulf treated effluent. And here is the part that
matters: gypsum saturation **is not affected by pH**. EPRI states this
explicitly. So the acid dose, which is the one lever a water-treatment programme
has for buying more cycles against limescale, does absolutely nothing against
gypsum.

> We set a 15 % target that needed 8.5 cycles, and the physics stops at 8. **No
> control strategy of any kind reaches 15 % on this water.** The target was
> mis-specified, not missed.

We left the pass mark where it was and we report the gate as failed. The lesson
went into the project record: check a target against the physical ceiling of the
system before you fix it.

**What the failure discovered, which is the part to say out loud:**

- The mineral that binds first on Gulf treated effluent is **gypsum, not
  limescale**. The Langelier Index the entire industry controls on describes
  limescale only, and cannot represent gypsum at all.
- That limit is **immune to the acid lever**.
- On this water the cost curve falls right up to the last safe point, so an
  operator following the money walks straight at a wall **with no instrument
  that can see it**.

A target that is missed teaches nothing. A target that is *unreachable* tells
you where the physics stops.

---

## Part 8 — The mistakes we found in our own work

Fifty defects found, **all fifty fixed**. The four worth knowing about:

**The fan correlation was in the wrong units.** The published equation for air
flow takes fan frequency in hertz; the dataset's own text described that column
as a percentage. Read the wrong way, the equation says air flow *falls* as the
fan speeds up past 62 % — which no fan on earth does. Our first test run failed
everything with a 1.5 °C bias. That bias is what exposed it.

**The optimiser cheated.** Given a free hand, it drove the fan to its minimum in
four of five conditions, which pushed condenser water outside the range our
chiller data was actually fitted over — and then collected a large fake water
saving from that extrapolation. It scored 20.41 % and would have turned a failed
gate into a passed one. We now enforce the chiller's real operating window as a
hard limit; 1,840 of 6,307 candidate operating points get rejected rather than
extrapolated.

**The solver was not converging.** The condenser heat load depends on the
chiller power, which depends on the water temperature, which depends on the
heat load — a loop that has to be solved iteratively. We were stopping after six
steps, which stopped short by an amount that depended on the starting guess.
Evaporation moved 3.8 % on the starting guess alone.

**The magnesium silicate chemistry was the wrong mineral.** We first modelled it
as sepiolite, a crystalline phase, and got answers saying no plant anywhere
could operate — which is plainly false. EPRI confirms the mechanism "is not well
understood" and that published sources disagree on which magnesium silicate
actually forms. We replaced it with an empirical rule that matches what plants
demonstrably do.

> **Four of those ten were caught because the physics refused a bad input.** A
> statistical model fitted to the data would have quietly absorbed the fan unit
> error, reported a good score, and carried a broken air-flow model into a
> customer's plant. That is the entire argument for building it the way we did,
> and it is why the company is called Furqan — the criterion that separates
> true from false.

---

## Part 9 — What we still do not know

Say these out loud in customer conversations. They cost us nothing and they buy
enormous credibility.

**1. Our test data is from Spain, and 40.5 % of a Dhahran year is hotter and
more humid than anything in it.** 3,551 hours out of 8,760, and 84 % of
September. This is the single biggest gap and no amount of modelling closes it.
It is exactly what the KFUPM wind tunnel is for — it humidifies, so it can reach
Gulf conditions directly.

**2. We assumed the tube wall runs 8 °C hotter than the bulk water, and we never
computed it.** Our own code contains the calculation and never calls it. Run
properly it gives 2.4–3.7 °C for a *clean* tube; 8 °C corresponds to a fouled
one. This matters, and it mattered less than we first thought: when this was
written the wall was believed to be gypsum at 8 cycles, moving in to 7 on a
clean tube. Correcting the aqueous speciation moved the binding mineral to
**amorphous silica** at 6 cycles — and silica is *prograde*, so it binds at the
cold basin rather than the hot skin and the skin assumption barely moves it.
The skin temperature still decides the calcite and phosphate limits. We found this by
auditing our own code and we report it.

**3. Acid dosing at high cycles may make the water corrosive, and our controller
cannot see it.** EPRI warns that sulphuric acid replaces protective alkalinity
with corrosive sulphate, and that sulphate and chloride both concentrate as
cycles rise. Our optimiser raises cycles *and* doses acid — exactly that
combination. **Answered in part, 12 September 2026 — and the answer inverts the
objection.** `src/corrosion.py` adds the aggressive-anion term, and working it
out shows the two levers are *not* both guilty. Larson-Skold is a RATIO of
anions, and concentrating a water multiplies every ion equally, so **cycles
move it by exactly zero**. Acid moves it from 4.60 to 55.0 as alkalinity is
destroyed. Chloride pitting is the mirror: cycles move it, acid does not.

So the corrosion exposure is carried by the acid lever alone — and that lever
is separately switchable. **A Jubail site under RCER may not dose acid at all,
so it takes none of this risk.** The regulation that costs us the acid lever
also removes the objection to it.

What remains genuinely open is a corrosion RATE, which needs coupons. The
acceptance criteria are already loaded (UFC 3-230-13 Table 5-9) and the coupon
rack is on the bill of materials.

**4. Our model is about 2.5 times less accurate than the measurement uncertainty
of the experiment.** Meaning there is a real residual error we cannot yet
explain. We report the honest number rather than the floor.

**5. All the chemistry is computed, never measured — and measuring it is priced
out of the market.** The constants are from the standard reference database and
we have never put this water in front of an instrument. We costed doing so:
silica, calcium, alkalinity and phosphate online is **$120,000-185,000 per
tower**, against an **$89,000/year** saving on a 4.2 MW tower. The instruments
cost more than the thing they optimise. That is structural and it is why no
incumbent sells this.

**What we do instead costs nothing.** Specific conductance is a known function
of ion composition, and the conductivity sensor is already on the skid because
the cycles calculation needs it. So we compute what the assumed composition
*should* read, compare it to what the sensor *does* read, and the gap tells us
when the assumption has stopped being true. It does not measure ions — one
conductivity and one pH cannot resolve eight — but the **direction** is
diagnostic: precipitation removes ions from solution, so the measured
conductance falls below prediction. That is the scaling alarm, for free.

**6. In a cold climate our controller cannot do its job with a fan alone, and
this is a product requirement, not a caveat.** The silica floor is a *minimum*
water temperature — below it, silica comes out of solution in the basin. In hot
air you hold that floor by slowing the fan. In cold air you cannot: a cooling
tower in 16 °C air over-cools even at its slowest usable fan speed, so the water
lands below the floor whatever the controller does. On the Frankfurt profile that
is **ten hours out of twenty-four**. The answer is a **tower bypass** — route
part of the flow around the tower so it stays warm — which is a valve, not
software.

Say this before a customer finds it. It is also a *selling* point in the Gulf,
where the problem does not arise, and it tells a European customer exactly what
they must install for the product to work. We found it because our own model was
quietly claiming compliance in those hours; the fault is recorded as defect 42.

**7. Our water saving is negative where the model has been validated, and
positive only where it has not.** This is the hardest sentence in the document
and it must be said before a customer finds it. Splitting the Dhahran year at
the edge of our test data: inside the validated wet-bulb envelope the
controller uses **3.3 % MORE** water than the baseline; outside it, in the
3,285 hours hotter and wetter than anything we have measured, it saves
**8.23 %** — a figure that must always be written to two decimals, because a
bare "8.2 %" collides with a superseded annual cost number and our own audit
will reject it. The annual +2.37 % is entirely carried by the unvalidated
half.

The energy result is the exact reverse — **+8.8 % inside the envelope, −0.4 %
outside**. So the two halves of the product are validated to opposite degrees.
**Lead with energy, which is defensible on our own data, and treat water as
the thesis the pilot exists to test.** That is also the honest reading of why
the water gate keeps failing.

**8. We do not know what our own product costs to build.** So we do not quote a
payback. We searched the Internet Archive's PDF collection across fifteen cost,
controls and retrofit queries and found nothing citable on what a cooling-tower
supervisory controller costs installed — the figures appear to be commercial and
unpublished. Instead we invert the question and quote a **bound**: on a 4.2 MW
tower saving about $89,000 a year of water, the system may cost up to **$267,000
installed** and still pay back in three years. That is a ceiling on a price, not
a price. Never let it be quoted as one.

---

## Part 10 — What it is worth, and the numbers to quote

Per 10 MW of condenser cooling — roughly a 2,840 ton plant:

| | Value |
|---|---|
| Operating cost saved | **$157,975 per year** |
| Water saved | **26,711 m³ per year** |
| Scaling | roughly linear with plant size |

At a 30 MW plant that is about **$474,000 a year**, against a first-year cost
near $50,000 per loop. Payback under three months.

**The prices are published, not assumed:** electricity at $0.074/kWh from the
Saudi business tariff, and water at $3.11/m³ from Marafiq's own approved
schedule. That water figure is unusually strong because it counts both the
makeup you do not buy *and* the industrial wastewater you do not discharge —
both line items from the same published document. For a Jubail or Yanbu
operator, the whole business case computes from their own numbers.

### Numbers to quote, and numbers not to

| Say this | Not this | Why |
|---|---|---|
| 8.8 % [SUPERSEDED 10 Sep 2026 -> 2.72 %] water, 6.4 % [SUPERSEDED 10 Sep 2026 -> 3.77 %] cost, 5.4 % [SUPERSEDED 10 Sep 2026 -> 4.33 %] power — annual | 10.83 % [SUPERSEDED 10 Sep 2026 -> 6.65 %], 5.75 %, 2.86 % | The second set is the average of the five test conditions and is a different metric. The first is a real weighted year |
| Gypsum wall "7 cycles" | "8 cycles", or hedging it against fouling | Measured 4 Sep across a clean-to-fouled tube wall, 2.4 K to 8.0 K: the wall does not move. It is 7 at every one |
| "Prototype, validated against public experimental data" | "Proven", "deployed", "in use at" | We have no installed base |
| "Two of our six criteria failed and we report them" | Silence | It is the most credible thing we have |

---

## Part 11 — The ten hardest questions, and how to answer them

**"How do I know your model is right?"**
You don't, and neither do we beyond what we measured. We fixed six pass marks
before testing, scored once on data the model had never seen, and published two
failures. It regenerates from a public dataset in four commands, so you can
check it yourself.

**"Isn't this just what my water treatment company already does?"**
They predict chemistry offline, at average water temperature, and they don't
control anything. We compute it live, at the tube wall, per mineral, and we
close three actuators on it. Also — their revenue is chemical volume. Ours is a
device that reduces chemical volume.

**"We already have a conductivity controller."**
A conductivity probe returns one number for the whole loop. At a zero-blowdown
trial at the Stanford Linear Accelerator Center, cycles measured five different
ways in the *same sample on the same day* read 19, 20, 23, 43 and 50. A single
number cannot represent that.

**"What is your cycles setpoint?"** *(You ask them this.)*
And then: what set it? If the answer is "it was set at commissioning and nobody
has touched it", that is the whole opportunity in one sentence.

**"What if my plant is already running near the limit?"**
Then we have no business with you, and we would rather find that out in this
meeting than in a year. It is the single thing most likely to kill our company
and we are actively testing it.

**"Will this void my chiller warranty / break my BMS?"**
It ships read-only. It watches and advises until you have satisfied yourself on
your own data. Nothing gets write access until you grant it.

**"Who else is using it?"**
Nobody. We are at prototype stage with no installed base. We are looking for the
first site and we are not going to pretend otherwise.

**"What about corrosion if you dose more acid?"**
Fair, and currently our biggest unanswered question. EPRI warns that acid at
high cycles concentrates corrosive sulphate and chloride. We have no corrosion
term in the model yet, and it is the top priority for the laboratory programme.

**"Does it work on seawater?"**
No, and we exclude it. Where cooling water is nearly free the value collapses.
Our market is freshwater and treated effluent loops only.

**"You're three fresh graduates."**
Yes. The evidence package is public, reproducible, and contains two failed
criteria and ten documented defects. Judge the work.

---

## Part 12 — Where everything lives

| What | Where |
|---|---|
| Full technical report | `DTV_Submission/Furqan_Mizan_PoC_Report.pdf` |
| Defects and failed gates | `DTV_Submission/Furqan_Mizan_Defect_Register.pdf` |
| Commercial plan and budget | `DTV_Submission/Furqan_Mizan_Commercialisation_and_Budget.pdf` |
| Prior art and IP position | `DTV_Submission/Furqan_Mizan_IP_and_Prior_Art.pdf` |
| Customer plan, target accounts | `DTV_Submission/Furqan_Mizan_Customer_Development_Plan.pdf` |
| Form answers, 300-char fields | `DTV_Submission/FORM_ANSWERS_300char.md` |
| Saudi outreach messages | `mizan/docs/outreach_messages_saudi.md` |
| The code | `mizan/src/` — run `python src/audit.py` to check consistency |

To regenerate everything from scratch:

```
pip install -r requirements.txt
python src/fetch_zenodo.py      # download and verify the dataset
python src/calibrate.py         # the prediction tests
python src/run_controller.py    # the controller tests
python src/annual.py            # the real-year figures
python src/audit.py             # 49 consistency checks
```
