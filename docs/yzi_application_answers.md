# YZi Labs — EASY Residency application

Rewritten 12 September 2026 as **solo founder**, focused on **CDU / liquid-cooled data centres**.

> ## ⚠️ THE FORM HAS STOPPED SAVING
>
> It accepted one round of edits and now reverts everything — I tried JavaScript
> value setters, React synthetic events, and real keystrokes with an 8-second
> wait, on both steps. Most likely an expired draft session. **Reload the page
> fresh (and re-auth if it asks) before you edit anything by hand.**
>
> **What is safely saved right now:** step 1 holds the solo + data-centre
> version — role, the 1,845-character background, the 692-character duration
> answer, the 1,928-character resourcefulness answer, 40% equity, GitHub, and
> all four radio buttons. That version is coherent and submittable as it stands.
>
> **What did not land:** the newest "final model / still building" refinements
> and the dual-domain positioning line (§2 below), step 2's two answers (§4),
> and the AI-prompts field (§3). All four texts are below, ready to paste.

---

## 1. Step 1 — Founder profile · SAVED AND VERIFIED

| Field | Value |
|---|---|
| Role | Solo founder — I own all of it, and the physics core is the part I'd defend |
| Currently in school | No |
| Exclusive commitment · Full time | Yes · Yes |
| Equity, fully diluted | 40% |
| Builds AI skills | Yes |
| GitHub | https://github.com/furqan5 |

**Background** (1,845 chars), **How long** (692), **Resourcefulness** (1,928) — all saved, all rewritten around the data-centre work: the Deschutes-spec CDU, the free-cooling supervisor, and the instrument economics that forced the product design.

---

## 2. PASTE INTO — Step 1, the three "final model" upgrades

These sharpen the framing to *achieved this, still building it, solo*. The versions currently saved are good; these are better.

### Role

> Solo founder. I own every part of it — physics core, controller, validation, and the commercial work.

### Background — replace the existing one

> I'm an energy engineer. Most of what makes me useful here I learned by building this and then breaking it.
>
> Degree in Energy Engineering (University of the Punjab, 2021–2025). Interned at LESCO, Lahore's distribution utility, where I first saw how far real plant operation sits from the textbook. Since 2024, independent systems consulting on industrial and renewable energy — which taught me to model plants I cannot visit, the exact constraint I work under now.
>
> What I am building is one controller for two markets: Saudi district cooling and liquid-cooled data centre CDUs. The line I am working toward is "a dual-domain AI supervisory controller that runs district cooling plants and data-center CDUs at the true water–energy ceiling — chemistry-aware, metallurgy-safe, permit-compliant." Each of those three is a module I have already written, not an adjective. Chemistry-aware is an ion-association engine benchmarked against PHREEQC. Metallurgy-safe is a corrosion module that says 316 stainless caps this water at 1.85 cycles, below what operators actually run. Permit-compliant is the Saudi discharge tables, which bind at 3.33 cycles on nitrate — before the chemistry binds at 4.52.
>
> That is what I have achieved. What I have not is a plant running on it, and I will not write the verb "runs" until one does.
>
> The way I work is the part I would actually point at. Thresholds are pre-registered before the test runs, so I cannot move them afterwards. Two gates are failing right now and they are in the deck. Fifty defects are logged with what each cost — one took a third off every headline number, one showed my water saving is negative inside the envelope I had validated and positive only outside it, and one was my fix for an earlier defect reproducing that same defect. I wrote a test that maps every constraint to the file that must enforce it; it caught an eighth instance on its first run.
>
> I am still building this, alone, and I intend to keep going until a plant runs on it.

### How long have you been working on this — replace the existing one

> Six weeks full time, and continuing. First commit 30 August 2026; 193 tests and fifty logged defects since. I date it from the commit rather than the idea — anyone can say they have been thinking about something for a year.
>
> The data centre half is about three weeks old. I started on Gulf district cooling, then found the same chemistry gap unaddressed in liquid-cooled data centres, where the loads are larger and the constraint is tighter. Rather than choose, I made the controller dual-domain, because the physics underneath is identical and only the equipment on top changes.
>
> This is now the thing I am working on until it is finished. Not a project I am exploring — the one I have committed to, solo, and the model I intend to take to a pilot.

---

## 3. PASTE INTO — "Share the three AI prompts you are most proud of"

I filled this **three times**, including once with a proper React synthetic event that provably worked on the field directly above it seconds earlier. It reloads empty every time. That is a bug on their side, not a technique problem. Paste it last, right before you submit, and check it is still there.

> These are three I actually use, not three I wrote for this form.
>
> **1. THE DEEP-RESEARCH PROMPT THAT REFUSES TO BE FLATTERED**
>
> The header is: "I want my assumed values corrected, not just supplemented." It ships the model a table of every constant I have assumed, with its source and its status tag, and asks the research agent to find primary sources that CONTRADICT them. Most research prompts ask for supporting evidence and get it, which is worthless. This one is scored on what it overturns.
>
> It is how I found that the heat-flux band I was using was twice too wide, and how I found the Saudi regulation that bans the acid lever I had assumed was available in the Gulf.
>
> **2. THE ADVERSARIAL DEFECT HUNT**
>
> "Here is a result I believe. Assume there is a defect in my code that produces it. Find it." Then I hand over the module and the number.
>
> It is phrased that way because asking a model to review code gets you style notes. Asking it to explain a result you have already decided is wrong gets you the actual bug. Most of my fifty logged defects came out of some version of this, and the two most expensive were the same class of error found four days apart: a constant wrong by a factor of a hundred, which produces plots that look entirely reasonable.
>
> **3. THE CONSTRAINT-APPLICATION AUDIT**
>
> "Find every function in this package that computes a limit, a ceiling or a criterion. For each one, grep for its call sites and tell me which are computed but never enforced."
>
> I wrote this because the same failure had happened six times: a constraint computed correctly, documented, unit-tested, and applied by nothing that makes a decision. It reads like coverage, which is why it survives review. The first run found a seventh instance and then an eighth, and the eighth was the fix I had written for the fourth. That one is now a permanent test rather than a prompt, which I think is the right end state for any prompt that keeps finding the same thing.

---

## 4. PASTE INTO — Step 2, Founding team

**Step 2 does not autosave and will not accept an update.** It saved once, on the very first Continue click, and has refused every write since — four attempts, three techniques (form fill, React synthetic events, real keystrokes + Continue). It still shows the three-founder text. Select all in each box, delete, and paste.

### "How did the founding team come together?"

> Solo founder. I am building this alone.
>
> I would rather explain the working method than pretend there is a team story. I run the whole thing — the chemistry engine, the CDU and tower models, the controller, the validation, the defect register and the commercial research — and the discipline I use in place of a co-founder is adversarial review of my own work.
>
> Concretely: every threshold is pre-registered before the test runs, so I cannot move the goalposts afterwards. Gates that fail stay failed and get published as failures — two of mine are failing right now and they are in the deck. Every defect goes in a register with what it cost. Fifty so far, forty-eight of which changed a number. When I found that my headline water saving was negative inside the envelope I had actually validated and positive only outside it, I put that on the results slide rather than wait for a reviewer to find it.
>
> That is not a substitute for a co-founder who argues back, and I am not going to claim it is. It is the closest thing to that function I have been able to build alone.

### "Is the founding team complete? If not, what kind of co-founder are you seeking?"

> Not complete. I need one co-founder and I can name the role precisely: someone who has operated or commissioned liquid cooling in a live data centre.
>
> Everything I know about how these plants actually run is second-hand — published specs, regulations, conference papers, a handful of operator conversations. That has taken me further than I expected. But there is a category of knowledge it cannot reach, and I know the exact moment I learned that. A technician who opens condensers for a district cooling utility told me the deposit he removes is dark brown and black with white between it. He calls it lime scale, and lime scale is white. Two of the three things he said cut against my model. No amount of desk research produces that sentence.
>
> On the data centre side the equivalent unknown is sharper. My model says a 316 stainless plate exchanger on the Saudi treated effluent I benchmarked against reaches its chloride pitting threshold at 1.85 cycles of concentration — below the 3.0 that operators actually run, and well below the 4.5 the scaling chemistry allows. CDU plate packs are routinely 316. If that number is right it is a serious finding for anyone deploying liquid cooling on recycled water in the Gulf. If it is wrong, it is wrong because the published limit is too conservative for a flowing, inhibited, oxygenated loop — and only someone who has run one can tell me which.
>
> Why founder level and not a hire. The largest risk in this company is that the model is confidently wrong about a plant I have never stood inside. That risk sits above the product: it decides which claims I am allowed to make and which pilots are worth doing. Someone reporting to me would tell me what I asked. Someone with equity will tell me I am wrong, which is the entire point.

---

## 5. CDU numbers to have ready for steps 3–5

From `results/pitch_artifacts.json`. 24-hour coupled study, cycles 5.0, chemical floor **31.8 °C**, blind free cooling vs chemically-bounded:

| Region | IT load | PUE b→c | WUE b→c | peak silica SR b→c | scaling hours b/c |
|---|---|---|---|---|---|
| Dhahran | 9 MW | 3.537 → 3.556 | 1.96 → 1.94 | 1.028 → **1.000** | 12 → **0** |
| Loudoun County | 20 MW | 1.049 → 1.159 | 1.88 → 1.74 | 1.178 → **1.000** | 24 → **0** |
| Frankfurt | 20 MW | 1.041 → 1.350 | 1.58 → 1.57 | 1.314 → 1.121 | 20 → 8 |
| Balloki | 8 MW | 1.083 → 1.162 | 2.07 → 1.92 | 1.165 → **1.000** | 21 → **0** |

**Read this correctly before you pitch it.** The bounded policy **costs** energy — it is not an energy saving. Dhahran +$107k/yr, Loudoun +$1.6M/yr, Frankfurt +$9.8M/yr. What it buys is that blind free cooling is running the loop supersaturated in amorphous silica for **12 to 24 hours out of every 24**, depositing on the exchanger, and nobody watching PUE can see it happening.

The pitch is **"here is where your floor is, and here is the price of respecting it"** — not "we save you money." Three claims that survive scrutiny:

1. **The floor is computable and nobody computes it.** 31.8 °C on this water at these cycles. Operators either guess low and scale, or guess high and throw away free-cooling hours.
2. **Frankfurt needs a tower bypass.** Eight hours a day the floor is physically unreachable at the slowest usable fan — the tower over-cools in cold air. That is a **design requirement discoverable before construction**, and it is a valve, not a caveat.
3. **316 stainless pits at 1.85 cycles** on this water. CDU plate packs are routinely 316. This constrains the deployment, and it is checkable.

---

## 6. Still blocking

| | |
|---|---|
| **1-minute founder video** | **Hard gate.** Notes written: `docs/founder_video_notes.md`. Steps 3–5 (Company, Progress, Curious) will not open. Continue throws "Please fill out this field" and `?step=3` clamps back to Founding team |
| Co-founder invites | Leave empty — you are applying solo. The form explicitly says "Solo founder? Skip this" |
| "Something you built besides this company" | Optional, left blank |
| X / Twitter, website, calendar | Optional, don't have them |

**Nothing was submitted.**

---

## 7. One inconsistency to settle

`HANDOFF.md` names three founders — you as Founder & CTO, Damia Baig as CEO, Muhammad Ahsan as commercial development — and `docs/application_answers.md` says "two energy engineers, both full-time". This application now says solo.

That is your call about your own company and I have written it as you asked. But **the repo will contradict this application if anyone reads both**, and the GitHub link in the form points at the repo. Worth reconciling the docs before an interview.
