# Staged document updates from `fix/weather-envelope`

These changes are for the main session to apply at merge. This branch does not
edit HANDOFF.md, README.md or the defect register.

All "new" values come from the defect-60 re-run
(`results/annual_dhahran.json`, TMYx humidity) or from
`results/annual_weather_sensitivity.json`.

**Weather-source rule.** Pre-registered in
`docs/staged/weather_source_preregistration.md`. Anything marked **[WSD]** is
weather-source-dependent. It must carry both values, or it must not be stated as
a fact about Dhahran.

README.md and CITATION.cff contain none of the patterns searched (`3,285`,
`5,475`, `37.5 %`, `62.5 %`, `−3.31`, `8.23 %`, `8.84 %`, `−0.39 %`, `2.37 %`,
`4.52 %`, `r = −0.66`, "equal-hour bins"), so nothing for the validation branch.

## A. Numbers made stale by defect 60 (the envelope split)

Reference values: inside 5,475 → **5,209 h**; extrapolated 3,285 → **3,551 h**.

| file:line | old | new |
|---|---|---|
| HANDOFF.md:14 | inside the envelope (5,475 h) water is **−3.31 %** and energy **+8.84 %** | inside the envelope (5,209 h) water is **−3.22 %** and energy **+8.82 %** |
| HANDOFF.md:15 | extrapolated (3,285 h) water is **+8.23 %** and energy **−0.39 %** | extrapolated (3,551 h) water is **+5.41 %** and energy **+0.95 %** |
| HANDOFF.md:15–16 | "The whole positive annual water figure is carried by hours never measured at." | Keep it. Add: "**[WSD]** On station humidity the annual water figure is −2.64 % (inside −4.77 %, outside +1.91 %); see `docs/weather_source_sensitivity.md`." |
| HANDOFF.md:522 | −3.31 % inside … +8.23 % outside … the 3,285 hours … +8.84 % inside, −0.39 % outside | −3.22 % inside … +5.41 % outside … the 3,551 hours … +8.82 % inside, +0.95 % outside. Also change "ENERGY is the reverse" to "energy falls to about zero outside". |
| HANDOFF.md:674 | Only **62.5 %** of the weighted year is inside | Only **59.5 %** of the year, counted hour by hour, is inside |
| HANDOFF.md:675 | 37.5 % of even this number rests on extrapolation | 40.5 % **[WSD: 24.3 % on station humidity]** |
| HANDOFF.md:137–147 | "eight equal-hour wet-bulb bins … r = −0.548" plus the cool/hot-half table | Already stale before this branch. The bins are now cut at 21.9 °C, and r across them is **−0.714** (pre-fix artefact −0.836). Mark it superseded or regenerate. |
| docs/deck_2026_09_12.md:134 | 5,475 · **−3.31 %** · +8.84 % | 5,209 · **−3.22 %** · +8.82 % |
| docs/deck_2026_09_12.md:135 | 3,285 · +8.23 % · **−0.39 %** | 3,551 · +5.41 % · **+0.95 %** |
| docs/deck_2026_09_12.md:137 | "Energy is the exact reverse." | "Energy runs the other way: +8.8 % inside, about zero outside." |
| docs/deck_2026_09_12.md:210 | **37.5 % of a Dhahran year** | **40.5 % of the TMYx year (24.3 % on station humidity)** [WSD] |
| docs/deck_content.md:112–113 | 5,475 / −3.31 / +8.84; 3,285 / +8.23 / −0.39 | Regenerate: `python src/make_deck.py` reads `by_envelope`, giving 5,209 / −3.22 / +8.82 and 3,551 / +5.41 / +0.95. Its prose "Energy is the exact reverse" (make_deck.py ~L233) needs the same softening. |
| docs/handoff_external.md:53 | 5,475 · −3.31 % · +8.84 % · +5.32 % | 5,209 · −3.22 % · +8.82 % · +5.32 % |
| docs/handoff_external.md:54 | 3,285 · +8.23 % · −0.39 % · +2.90 % | 3,551 · +5.41 % · +0.95 % · +2.75 % |
| docs/handoff_external.md:55 | 8,760 · +2.37 % · +4.52 % · +4.17 % | 8,760 · +1.31 % [WSD: −2.64 %] · +4.86 % · +4.01 % |
| docs/handoff_external.md:57 | "Energy is the exact reverse." | "Energy runs the other way." |
| docs/handoff_external.md:117 | **37.5 % of a Dhahran year** | **40.5 % of the TMYx year; 24.3 % on station humidity** [WSD] |
| docs/ENGINEERING_IN_PLAIN_ENGLISH.md:463 | **3.3 % MORE** | **3.2 % MORE** (4.8 % on station humidity) |
| docs/ENGINEERING_IN_PLAIN_ENGLISH.md:464–466 | 3,285 hours … **8.23 %** … "a bare 8.2 % collides …" | 3,551 hours … **5.41 %** (1.91 % on station humidity). The collision note no longer applies. |
| docs/ENGINEERING_IN_PLAIN_ENGLISH.md:467 | The annual +2.37 % | The annual +1.31 % (−2.64 % on station humidity) [WSD] |
| docs/ENGINEERING_IN_PLAIN_ENGLISH.md:470 | **+8.8 % inside the envelope, −0.4 %** … | **+8.8 % inside the envelope, +1.0 %** outside (−1.1 to +1.0 % across sources) |
| docs/datacentre_strategy.md:226 | Bins 5–7 (3,285 h, 37.5 % of the year) are above the validated 21.9 °C | Bins 5–7 (3,285 h) are entirely above 21.9 °C, and bin 4 holds 266 h more: 3,551 h, 40.5 %, counted hourly. `annual_datacentre.py` still classifies by bin centroid (see defect 60). |
| docs/robustness_gaps.md:164 | **62.5 %** of the hours-weighted Dhahran year | **59.5 %** of the Dhahran TMYx year, counted hour by hour |
| docs/robustness_gaps.md:165 | **37.5 % is extrapolation** | **40.5 % is extrapolation** (24.3 % on station humidity) |
| docs/threshold_revision_memo.md:207 | only **62.5 %** … The remaining 37.5 % | only **59.5 %** … The remaining 40.5 % |
| docs/poc_report.md:148 | **1.25 %** | **0.31 %** |
| docs/poc_report.md:149 | **-5.00 points** | **-4.07 points** |
| docs/poc_report.md:152 | **1.3 % annually** | **0.3 % annually** |
| docs/poc_report.md:154 | **2.4 %** … The 1.3 % above | **1.3 %** … The 0.3 % above |
| docs/poc_report.md:157 | only **62.5 %** of the weighted year | only **59.5 %** of the year, counted hour by hour |
| docbuild/build_poc.js:202 | only 62.5 % of the weighted year | only 59.5 % of the year, counted hour by hour |
| docbuild/build_poc.js:231 | eight equal-hour wet-bulb bins … **r = −0.664** | eight wet-bulb bins cut at 21.9 °C … **r = −0.714** |
| docbuild/build_poc.js:243 | caption "eight equal-hour wet-bulb bins" | "eight wet-bulb bins cut at the 21.9 °C validation edge" |
| docbuild/build_poc.js:245 | "down to 1.25 % in the mildest summer bin" | Not traceable to the current artefact. The lowest positive energy bin is +0.94 % (bin 7), and bin 6 is −1.26 %. Rewrite from `annual_dhahran.json`. |
| docbuild/build_answers.js:148; build_comm.js:91; build_deck_new.js:299; _fig_handoff.py:10, :63 | r = −0.66, "eight equal-hour bins", cool/hot-half numbers 10.4 / 7.3 / 15.7 / 3.0 % | Stale before this branch. Current r = −0.714 across bins cut at 21.9 °C. The memory note "anti-correlation is a load artefact" applies. Regenerate from the artefact or drop. |

**PoC report.** Prefer regenerating with `python src/make_report.py` on the
merged tree. It now reads the inside fraction instead of typing 62.5 %. A trial
regeneration on this branch was reverted: it also rewrote unrelated tables
(silica ceilings by temperature, the Dhahran-shoulder and Gulf-winter
water-mode rows, a basin-residence column) and absolute figure paths. That
means `poc_report.md` was already out of step with other artefacts in
`results/` before this branch.

**Figures and decks, not rebuilt here (binary):**

- `figs/seasonal_handoff.png`: the bins changed. The footnote generator is
  already fixed.
- The PDF/PPTX builds from `docbuild/*.js`.

`figs/wetbulb_gap.png` is unchanged; `tmy_dhahran.json` moved only in elevation
and new fields.

## B. Statements that are correct on TMYx but weather-source-dependent

Keep the number. Add the qualifier *"on the TMYx file's humidity; 24.3 % with
Dhahran station dew point (W1), 16.1–36.7 % across complete station years
2011–2024"*:

- HANDOFF.md:627: `40.5 % of a Dhahran year (3,551 of 8,760 hours)`
- docs/ENGINEERING_IN_PLAIN_ENGLISH.md:386
- docs/ai_architecture.md:86
- docs/poc_report.md:133 and :429
- docs/defect_register.md:427
- matlab/README.md:102
- docbuild/build_poc.js:184, :603, :639, :735
- docbuild/build_defects.js:134
- docbuild/build_index.js:55
- docbuild/build_answers.js:152
- docbuild/build_deck_new.js:365
- src/make_figures.py:421 (docstring, "two fifths … 84 % of September": TMYx-specific)

Any document stating a **positive annual makeup-water saving** for Dhahran must
also carry the W1 value, −2.64 % (H3 is WEATHER-SOURCE-DEPENDENT). Search for
`annual makeup water` and `water saving` in HANDOFF.md, commercialisation.md,
deck and application answers before sending anything outward.

## C. Defect register

- Paste the rows and the supersession table from
  `docs/staged/weather-envelope_defects.md`.
- Register row 48 (docs/defect_register.md:61) quotes the pre-fix split: 37.5 %,
  −3.31 / +8.23, +2.37, 3,285, +8.84 / −0.39. Leave it as history. Add "(figures
  superseded by defect 60)" so the audit's label rule accepts it.
- The Part 1 header "Fifty found …" and every document count must move together
  (`test_every_document_agrees_on_how_many_defects_were_found`).

## D. Audit and test results on this branch

See the final commit message of this branch for the exact assertion lines. The
expected failure is audit §4h: `docs/poc_report.md` must carry `0.31 %`, the
new `annual_water_pct`. It clears once the PoC report rows above are applied or
the report is regenerated.
