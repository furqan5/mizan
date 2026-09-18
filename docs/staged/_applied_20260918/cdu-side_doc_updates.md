# Staged doc updates: data-centre claims (review/cdu-side, 17 Sep 2026)

For the main session to apply. The deck markdown was **not** edited here. Sources for every number:
`results/cdu_joint_policy_20260917/run.json` and `docs/staged/cdu-side_defects.md` (63–66). All dollar
figures are one 24-hour design day ×365, and three of the four regions use sinusoidal weather [A].

## `docs/deck_2026_09_12.md`

**Line 88** (316 row)
- OLD: `| **316 stainless pitting** | **1.85 cycles** | CDU plate packs are routinely 316 |`
- NEW: `| **316 chloride screen** | **1.85 cycles** (Riyadh refinery water; 0.76 on the Dhahran TSE) | A guidance ratio, not a measured onset. It binds only on surfaces tower water touches: the tower-isolation exchanger, or a CDU plate only where tower water is piped through it. The CDU's TCS side is a closed loop |`

**Line 100**
- OLD: `24-hour coupled study. Blind free cooling vs chemically-bounded, 5 cycles, silica floor **31.8 °C**.`
- NEW: `24-hour design-day study, one day per region (Dhahran real TMYx; the other three sinusoids). Blind free cooling vs chemically-bounded, 5 cycles, silica floor **31.8 °C** — on an **assumed** 26.8 mg/L makeup silica. At 18 mg/L the floor is 12.6 °C and no region scales; at the 8 mg/L printed for Riyadh refinery TSE there is no floor at 3–7 cycles.`

**Lines 102–107** (table). Replace the `PUE b→c` column. The Dhahran 3.537 is a model artefact:
two hours need 233–265 MW of pumping (defect 63).
- OLD header: `| Region | IT load | PUE b→c | WUE b→c | Peak silica saturation b→c | Scaling hours b→c |`
- NEW header: `| Region | IT load | PUE b→c (OEM 55 °C return) | WUE b→c | Peak silica saturation b→c | Scaling hours b→c |`
- Dhahran: `3.537 → 3.556` → `1.047 → 1.045`
- Loudoun County: `1.049 → 1.159` → `1.040 → 1.036`
- Frankfurt: `1.041 → 1.350` → `1.040 → 1.035`. Scaling hours `20 → 8` → `20 → 8 (of 20 that solve)`
- Balloki: `1.083 → 1.162` → `1.049 → 1.039`
- The WUE, peak-saturation and scaling-hour cells re-ran identically on the current engine and stay as they are.

**Line 109**
- OLD: `**Blind free cooling runs the loop supersaturated in silica for 12 to 24 hours out of every 24.** It is depositing on the exchanger, and nothing an operator watches — PUE, WUE, approach — shows it happening.`
- NEW: `**On a 27 mg/L-silica makeup, blind free cooling runs the loop supersaturated in silica for 12 to 24 hours of a design day** — unchanged under measured AI-training and hyperscale PDU load shapes. It deposits where the tower water is coldest, and nothing an operator watches — PUE, WUE, approach — shows it happening. **Whether it happens at all is set by the makeup silica, so measure it first.**`

**Line 111**
- OLD: `> **Do not sell this as an energy saving. It is an energy cost.** Bounded control costs +$107k/yr in Dhahran, +$1.6M/yr in Loudoun, +$9.8M/yr in Frankfurt. What it buys is knowing where the floor is. Say that plainly; a data-centre operator will check.`
- NEW: `> **Do not quote a dollar cost of bounding.** The earlier +$107k / +$1.6M / +$9.8M held cycles at 5 and assumed a 42 °C cold-plate return. $7.6M of Frankfurt's figure was two hours at 5× design pump flow. Let cycles drop from 5 to 4 and the cost falls to +$30k (Loudoun), −$94k (Frankfurt) and −$21k (Balloki) per design-day-year, for 3.7–4.7 % more makeup. At the GPU OEM's published 45 °C-in operating point, holding the floor at 5 cycles is cheaper than blind free cooling in all four regions. What bounding buys is knowing where the floor is and which lever to pull. A data-centre operator will check, so say that.`

**Line 113**: no change. The 8 floor-unreachable Frankfurt hours re-ran identically.

**Line 171**
- OLD: `| **metallurgy-safe** | Larson–Skold + chloride pitting | 316 stainless caps at **1.85 cycles** |`
- NEW: `| **metallurgy-safe** | Larson–Skold + chloride screen | 316 screen at **1.85 cycles** on refinery TSE — for tower-water-wetted surfaces only |`

## The same claims elsewhere (main session decides; not all are live documents)

- `HANDOFF.md:24-26` and `:523` repeat "316 … 1.85 cycles … hardest on the CDU, where plate exchangers are routinely 316". Apply defect 65's wording.
- `docs/handoff_external.md:89`: same 316/CDU sentence.
- `docs/yzi_application_answers.md:116`, `:128-133` (the PUE table and the +$107k/+$1.6M/+$9.8M line) and `:139`. These are submitted application answers; record them as superseded rather than rewriting them.
- `docs/r3sidency_application_answers.md:65`: "316 stainless at 1.85 cycles".
- `scripts/generate_pitch_artifacts.py` docstring says "a MEASURED Gulf TSE silica — 18.0 mg/L, NACE Paper 577 Table 1". That transcription is defective (the page prints 8), which the chemistry branch owns.
- `src/hybrid_supervisor.py` comment block "THE ENERGY CLAIM": "PUE 1.047 -> 1.150, fan -100 kW against secondary pump +1,028 kW" rests on defect 63's 42 °C return. It should be annotated. It was not edited here, so the file's hash still matches the one recorded in the joint-policy run's registration.
