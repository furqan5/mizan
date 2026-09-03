# Deep-research prompt — finding the next venture thesis

For Gemini Deep Research, or any equivalent. Use it only if Mizan is killed at
one of the gates in the commercialisation plan, or alongside it if we decide the
Gulf beachhead is wrong.

**The important design choice in this prompt:** it does not ask for "energy
startup ideas". Anyone can generate those and they are all worthless. It asks
for a *specific structural pattern* — the one that made Mizan findable — and
requires evidence that the pattern is present. Read Part 2 below before you
change anything, because that is where the leverage is.

---

## The prompt

```
ROLE
You are a technical due-diligence researcher for a deep-tech venture team. You
are not writing a pitch and you are not brainstorming. You are searching for a
specific, falsifiable structural pattern in real industrial systems, and
reporting only cases where you can evidence that the pattern is present.
Accuracy matters enormously more than the number of ideas. Five well-evidenced
candidates are worth more than thirty speculative ones.

WHO THIS IS FOR
Three energy engineers, all with B.Sc. Energy Engineering, based in Lahore,
Pakistan, working full-time on a venture. Capabilities that are real and
demonstrated, not aspirational:

- First-principles modelling of thermal and fluid systems: heat and mass
  transfer, thermodynamics, psychrometrics, evaporative processes, heat
  exchanger design (Gnielinski, Bell-Delaware)
- Aqueous chemistry and mineral saturation modelling on standard
  thermodynamic databases
- Control systems: system identification, classical control, model-predictive
  control, constrained optimisation
- Physics-informed machine learning, used only where physics runs out
- Python (NumPy/SciPy), MATLAB/Simulink/Stateflow, EnergyPlus, ETAP, PVsyst,
  QBlade, SolidWorks
- Validation discipline: pre-registered thresholds, held-out test sets, and
  publishing failed criteria

Hard constraints:
- Near-zero capital. Any thesis must be testable to a credible technology-
  readiness level 3 using PUBLIC data and desk modelling only, in about eight
  weeks, before any money is spent.
- Must not be pure software-as-a-service. Target programmes exclude it. The
  venture must have a physical or instrumentation component.
- Target markets are Saudi Arabia and Qatar first, then wider MENA and Pakistan.
- No laboratory of our own. Access to university facilities is possible but
  must be requested, so the desk phase has to stand alone.

THE PATTERN TO SEARCH FOR
The team's previous thesis was found by noticing a specific structure. Find
more instances of the SAME STRUCTURE in other industrial energy systems. All
six elements must be present for a candidate to qualify:

1. A physical system where TWO OR MORE engineering disciplines each control
   their own handle, optimising their own objective, using their own
   instrument.
2. Those handles are PHYSICALLY COUPLED — moving one changes the correct
   setting of the others — but the parties setting them do not coordinate, and
   often work for different companies.
3. The binding constraint on the system is INVISIBLE to the instrument the
   incumbents actually use. Typically because it acts at a surface, an
   interface, or a local condition that bulk measurement cannot resolve.
4. There is a real, priced cost to the gap — wasted energy, wasted water,
   wasted reagent, shortened asset life, or unplanned downtime.
5. A PUBLIC experimental dataset, standards-body test code, or open reference
   database exists that would let a first-principles model of the system be
   validated without site access.
6. The fix is a RETROFIT to installed base, not a redesign of new equipment.

Report the six elements explicitly for each candidate, with a source for each.
If you cannot evidence element 3 or element 5, the candidate does not qualify
and should be listed under "rejected" instead.

WHERE TO LOOK
Industrial and energy systems where more than one discipline touches the same
equipment. Suggestions, not limits:
- Boiler and steam systems: water treatment vs combustion vs steam demand
- Compressed air: leak management vs pressure setpoint vs dryer regeneration
- Refrigeration and cold chain: defrost strategy vs superheat vs product load
- Desalination: antiscalant dosing vs recovery ratio vs energy recovery device
- District heating and cooling networks: hydraulic balancing vs supply
  temperature vs building-side control
- Electric machines and transformers: thermal loading vs insulation life vs
  dispatch
- Solar plants in dust-heavy climates: soiling and cleaning schedule vs water
  use vs degradation
- Biogas and anaerobic digestion: feedstock mix vs temperature vs retention
- Furnaces and kilns: refractory life vs excess air vs throughput
- Gas processing: glycol or amine circulation vs reboiler duty vs emissions
- Wastewater treatment: aeration control vs sludge age vs effluent limits
- Battery energy storage: thermal management vs C-rate vs calendar ageing

OUTPUT FORMAT
For each qualifying candidate, a section with these headings exactly:

  1. The system, in three sentences a non-specialist follows
  2. The disciplines and their handles      (element 1 and 2)
  3. The coupling nobody prices             (element 2, stated physically)
  4. The invisible constraint               (element 3 — name the instrument
                                             used today and say precisely what
                                             it cannot resolve)
  5. The cost of the gap                    (element 4 — a number, with source)
  6. Public data that would validate it     (element 5 — name the dataset,
                                             standard, or database, with a link
                                             and licence)
  7. What a retrofit would physically be    (element 6 — sensors, actuators)
  8. Prior art and incumbents               (name granted patents and
                                             commercial products; say plainly
                                             what is already taken)
  9. The single test that would kill it     (one question answerable by desk
                                             modelling or one phone call)
 10. Why this team specifically             (map onto the capability list
                                             above; if it needs a skill they
                                             do not have, say so)

Then a comparison table across all candidates:
| Candidate | Public data available? | Desk-testable in 8 weeks? | Prior art crowded? | Gulf-relevant? | Retrofit? | Kill test |

HARD RULES
- Do NOT invent datasets, patents, standards or numbers. Every factual claim
  needs a working link.
- If a candidate's public dataset does not exist, say so and reject it. The
  absence of validation data is disqualifying for this team, because they
  cannot buy site access.
- Prefer systems where a STANDARDS BODY publishes a test code (ASHRAE, ASME,
  CTI, ISO, IEC), because that supplies both the method and often the data.
- Actively look for reasons each candidate is a BAD idea and state them. A
  candidate presented without its weaknesses is not useful.
- Flag anything where the incumbent's revenue model would make them a
  determined enemy rather than a partner.
- Do not include ideas whose novelty is "apply machine learning to X". The
  team's edge is first-principles modelling; a candidate whose only content is
  a regression on operating data is explicitly out of scope.

ALSO RETURN
A. Which of these systems is most prevalent in Saudi Arabia and Qatar
   specifically, with evidence of installed base.
B. Any open competition, grant or accelerator in the energy sector with a
   deadline in the next nine months for which an early-stage physics-modelling
   venture with no revenue would be eligible. Include eligibility rules.
C. Public experimental datasets in industrial energy systems, under open
   licences, that would support first-principles model validation — regardless
   of whether they map to a candidate above. This list is independently
   valuable to us.
D. What you could NOT establish, listed explicitly.

Aim for 5 to 8 qualifying candidates and a longer rejected list. The rejected
list with reasons is as useful as the qualifying one.
```

---

## Part 2 — Why the prompt is shaped this way

Worth understanding before you edit it, because the obvious "improvements" all
make it worse.

**It searches for a structure, not a topic.** "Energy startup ideas" returns
hydrogen, carbon capture and smart meters every time, because those are what the
internet talks about. The six-element pattern is what actually made Mizan
findable, and it is rare enough to filter hard.

**Element 5 is the one that protects us.** A brilliant thesis with no public
validation data is useless to a team with no capital and no site access. It was
the existence of the Plataforma Solar de Almería dataset — 165 published
experiments under an open licence, with a measured water-consumption channel —
that made the whole Mizan evidence package possible on a desk. Without it we
would have had opinions instead of a validated model. Do not relax this.

**Element 3 is where the defensibility comes from.** If the incumbent instrument
can already see the constraint, the gap will close on its own and somebody
better funded will close it. The value is precisely in the constraint that acts
somewhere bulk measurement cannot reach — a surface, a boundary layer, a local
hot spot, a transient.

**Element 6 keeps the market real.** New-build is a bet on someone else's
capital cycle. Installed base already exists and already has the problem.

**The "reasons this is a bad idea" rule** is there because the research tools
are relentlessly positive by default, and an idea list without weaknesses costs
more time than it saves.

**The machine-learning exclusion** is deliberate and it is about our own edge.
Four of the ten defects in the Mizan package were caught because a
first-principles model refused a bad input. A regression cannot do that — it
absorbs the error and reports a good score. If the next thesis is a regression
on operating data, we have thrown away the only thing we are unusually good at.

---

## Part 3 — Before you act on anything it returns

Run each surviving candidate through these four before spending a week on it.

1. **Find the public dataset yourself and open it.** Research tools hallucinate
   datasets more readily than they hallucinate anything else. If you cannot
   download it and see real columns in it, the candidate is not real.
2. **Search the patents yourself.** Mizan's prior-art sweep found that two of
   three ingredients were already granted to somebody else. Assume the same
   until proven otherwise, and assume the closest art will be found by a
   reviewer if you do not find it first.
3. **Write the kill test down before you start.** For Mizan it is *"what is your
   current cycles setpoint, and what set it?"* — one question, answerable in one
   phone call, that decides whether the market exists. If a candidate has no
   such question, you do not understand it yet.
4. **Check the threshold against the physical ceiling before you fix it.** This
   is the lesson the failed water gate cost us. Ask what the arithmetic maximum
   of the quantity is *before* you promise a number.
