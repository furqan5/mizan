# Staged defects: CDU / data-centre side (review/cdu-side, 17 Sep 2026)

These are candidate rows for `docs/defect_register.md`, numbered **63–66**. The main session
applies them. The register, HANDOFF and robustness_gaps were **not** edited, and no
count was changed. Every number below comes from this session's artefacts:

- `results/cdu_joint_policy_20260917/run.json` and `hours.json`. The study was pre-registered in
  `docs/staged/cdu_joint_policy_preregistration.md` (commit 78efbc3).
- `results/cdu_hybrid_rescore_20260917/run.json`, R1: the registered script, unchanged.
- `results/cdu_hybrid_rescore_corrected_20260917/run.json`, R2: defects 25, 30 and 44 corrected.
- The harness crashed on its first attempt. That run is kept in
  `results/cdu_joint_policy_20260917_attempt1_crashed.log` and `_attempt1_registration.json`;
  its cause is defect 63 below.

| # | Defect | How it showed up | State |
|---|---|---|---|
| 63 | **The data-centre PUE and most of the "cost of bounding" come from an uncapped cubic pump law, extrapolated far past a 42 °C cold-plate return budget, with no trim cooling** | `hybrid_supervisor.required_secondary_flow` raises secondary flow without limit to hold the TCS return at `COLD_PLATE_RETURN_MAX_C = 42`, and `pump_power_kw` scales it by the cube. At 5 K approach and 10 K design rise, the warmest facility water this allows at design flow is **27.0 °C**. Dhahran's design day never gets below **30.34 °C**, so **all 24 blind hours run above 1.5× design flow**. Hours 10–11 need **10.9–11.4×** (**233–265 MW** of secondary pumping for a 9 MW hall, hourly PUE 26.9–30.5). That is the whole cause of the deck's **PUE 3.537**. It is not a unit or heat-versus-power error: excluding hours above 3× flow gives **1.148**. In Frankfurt, **$7.55M of the $9.77M/yr** comes from two hours (4 and 6) at **4.95×** flow, 48 MW each. The same law sent the primary plate wall to **111.9 °C** in B1. In the joint study it let B2 select a Dhahran state at **18.1×** flow with a **325 °C** wall, which the chemistry engine accepted because nothing checks its temperature validity. In attempt 1 a candidate's speciation went complex and crashed the run. With the return limit at the GPU OEM's published operating point (45 °C in, ~55 °C out; NVIDIA blog, 21 Jun 2026), every flow ratio is **1.00** and PUE is **1.035–1.049** in all four regions. | **OPEN.** Two remedies: a sourced return limit, and a flow cap that marks hours needing trim cooling as infeasible rather than pricing them. Neither was applied, because no pump run-out source is held and the return limit is a modelling decision. `evaluate` should also refuse a plate-wall temperature outside the chemistry engine's validated range |
| 64 | **The deck prices chemistry-awareness at fixed 5 cycles, and annualises one design day ×365** | The supervisor's own documentation (`docs/water_modes_and_free_cooling_floor.md` §2) says the correct response to the floor is to lower cycles, not to raise flow. `generate_pitch_artifacts.py` holds cycles at 5 anyway, then multiplies a single 24-hour design day by 365: Dhahran's highest-mean-wet-bulb TMYx day, and sinusoids for the other three regions. That is defect 20's shape in a new place. The pre-registered joint policy (B2: cycles 2–10 plus a fan-grid point) gave a cost of bounding **≤ 50 % of B1's in 3 of 4 regions, so H-B2 PASSES**. Loudoun **+$1,601,383 → +$30,234**, Frankfurt **+$9,769,622 → −$93,515**, Balloki **+$533,603 → −$21,483**, at **+4.68 / +4.19 / +3.69 %** makeup against blind. Dhahran does **not** support H-B2: **+$106,579 → +$21,705,498**, entirely defect 63 (B2 bought an admissible-by-rule state at 18× flow). The fan-only decomposition B1f equals B1 in all four regions, so the whole advantage comes from choosing cycles. | **OPEN.** The claim is withdrawn in `cdu-side_doc_updates.md`. The recomputation belongs in `generate_pitch_artifacts.py`, which is outside this branch's files |
| 65 | **"316 pits at 1.85 cycles; CDU plate packs are routinely 316" conflates two loops, two waters and a guidance screen with a measured onset** | (a) **Loops.** The CDU heat exchanger separates the facility water (FWS) from the technology cooling system (TCS), and the TCS is a closed loop that never carries tower water (OCP Cooling Environments CDU material, as summarised in search; ASHRAE TC 9.9 2021 white paper p. 25). The FWS reaches heat rejection "which could include … cooling towers", directly or through a tower-isolation exchanger (ASHRAE p. 14 describes facility water "through the approach temperature of the cooling tower and heat exchanger"). Alfa Laval sells the "cooling tower interchanger" specifically to protect downstream equipment from "scale formation and … chloride corrosion". So tower water wets a CDU plate **only** where the FWS is open to the tower. `hybrid_supervisor` assumes exactly that ("the tower outlet IS the facility supply") and never states it. (b) **Waters.** 1.85 = 400 mg/L ÷ **216** mg/L Cl on the **Riyadh refinery** TSE. The deck's data-centre study runs on `run_controller.TSE`, the Dhahran field TSE at **528** mg/L Cl, where the same screen gives **0.76 cycles**: the makeup already exceeds it before any concentration. (c) **Screen, not onset.** Buecker & Janikowski (Power Engineering, 10 Oct 2019) give 400 mg/L for 316 at neutral pH, 35 °C, clean flowing water. Alfa Laval's plate guidance for SS316 (FHE and BHE, doc 200011185-2-EN-GB Table 2) gives **1050 mg/L at 50 °C, pH 8.25** (linear in pH): **4.86 cycles** on the refinery water and **1.99** on the Dhahran TSE, with non-artefact plate walls at 37.5–38.5 °C. At pH 7 the same row gives **1.39 / 0.57**. (d) **Braze.** Alfa Laval BHE Table 3 (copper) requires SO₄ < 100 ppm and HCO₃/SO₄ > 1.5. The refinery makeup is **326 mg/L, ratio 0.52**, and the Dhahran TSE **300 mg/L, 0.35**, so both fail before concentration. A copper-brazed exchanger exposed directly to either water is outside the vendor's guidance at 1 cycle. **No criterion is held for duplex 2205, titanium or Cu-Ni, so no cycles limit was derived for them.** | **OPEN (claim).** `corrosion.py` is unchanged. The deck wording is corrected in `cdu-side_doc_updates.md`. The model should carry an explicit `fws_topology = open | isolated` and apply the plate chemistry only when the topology is open |
| 66 | **The registered one-CDU study (`cdu_hybrid.py`) was scored before the chemistry corrections, reproduces three fixed defects locally, and models a chilled-water plant** | The run of 7–8 Sep came before defects 24, 25, 27, 29, 30 and 44. Its makeup carried **no silica**: `SI_silica_am` at every optimum was about **−27.3**. The script also re-implements acid-on-makeup (25), the discharge fee on makeup (30) and an 8 K skin (44). Re-scored unchanged (R1) and corrected (R2), with thresholds untouched, **no verdict changes**: H1a FAIL, H1b PASS (minimum SI increase 0.0885 → **0.0239 / 0.0247**), H2-cycles PASS (8 bins, binding minerals now **calcite + silica**, previously calcite + gypsum), H2-temperature FAIL, H3/H4 NOT_IDENTIFIABLE. The annual coupled-vs-baseline figures moved: energy **12.40 → 11.06 / 11.85 %**, water **11.13 → 5.63 / 4.01 %**, cost **11.79 → 9.12 / 9.79 %**, and the optimum moved from **6 cycles in all 8 bins to 4–5**. Independently, the facility-water grid is the York chiller's CHWS range, so all **909** accepted states have FWS **4.44–8.89 °C**, GPU inlet water **9.44–13.89 °C**, and a running compressor. ASHRAE (2021, p. 14) says "Most cold plate solutions today can live easily on W32 water" and (p. 25) that the efficiency benefit "largely means eliminating mechanical cooling equipment such as chillers". The study's energy percentages therefore describe a chilled-water design that current direct-liquid-cooling practice avoids. | **FIXED as a record.** The re-scores are stored, and a staleness note is added to `docs/cdu_hybrid_readme.md`. The chilled-water framing needs a founder decision before any number from it is quoted |

## Dependency flags (not numbered, owned elsewhere)

- **Silica transcription (chemistry branch).** The coordinator verified from the page image that NACE
  Paper 577 Table 1 prints SiO₂ = **8 mg/L**, not the repository's 18. The deck's data-centre study
  does **not** use the refinery water. Its makeup, `run_controller.TSE`, carries an **assumed** 26.8 mg/L,
  and every slide-6 silica number depends on that assumption. Measured this session:
  - **26.8 mg/L**: floors 7.6 / 20.7 / 31.8 / 41.4 / 50.1 °C at 3–7 cycles.
  - **18 mg/L**: floors 1.0 / 2.8 / 12.6 / 21.0 / 28.6 °C. At 5 cycles blind free cooling never scales in any region, because the lowest blind facility water is 18.31 °C (Frankfurt).
  - **8 mg/L**: **no floor at all** at 3–7 cycles.
  The "12 to 24 hours out of every 24" claim and the whole silica case on slide 6 are conditional on makeup silica
  being well above the only measured Gulf TSE value.
- **Defect 54 (safety branch, acid sulfate omitted from gypsum).** No slide-6 result depends on gypsum: B1
  enforces silica only, and B2 admits on all limits with no acid dosed in `hybrid_supervisor`. The
  `cdu_hybrid.py` H1b verdict **is** a gypsum hypothesis, and its `chemistry_at` doses acid, so it inherits 54.
- **Weather (weather branch).** Dhahran's row uses the highest-mean-wet-bulb day of
  `results/tmy_hourly.npy`, the TMYx file under investigation for a humidity mismatch. The other three regions use
  sinusoids at constant RH [A].

## Plausibility results (pre-registered §5)

| Check | Result |
|---|---|
| P-PUE (> 1.54) | **FAIL, Dhahran 3.537** (both mean-of-hours and ratio-of-totals). Root cause: defect 63. Every other region passes, and all four give 1.035–1.049 at the OEM return |
| P-T (class) | The supervisor study sits in W32 territory: facility water 18.3–36.5 °C, no chiller. `cdu_hybrid.py` **FAILS**: FWS 4.44–8.89 °C, all on a chiller (defect 66) |
| P-RET | The model's 42 °C return is **13 K below** the published OEM operating point (45 °C in, ~55 °C out). At 55 °C, B1's cost of bounding is negative everywhere: Dhahran −$17,618, Loudoun −$113,430, Frankfurt −$170,339, Balloki −$66,499 per yr (design day ×365) |
| P-APP | Model 5 K against Deschutes 3 °C [R]. The model runs 2 K pessimistic on the floor |
| P-WUE | 7 hour-instances out of 192 exceed my all-latent bound ×1.05 by ≤ 4 % (Dhahran hour 12; Balloki hours 12–14 and 20–22). All are hot-dry hours with dry bulb 35–40 °C above facility water at 29–31 °C, where air adds sensible heat that evaporates extra water. **The bound was mis-specified [J], not the model.** Model WUE is 1.58–2.07 L/kWh on design days, against NVIDIA's ≈ 1.12 L/kWh annual tower-system figure; the bases differ (design day at 5 cycles versus annual) |
| P-CAP | The model sends 100 % of heat to liquid. That matches NVIDIA's statement for Rubin; it is unverified for earlier generations |
| P-FLOW (> 1.5×) | **FAIL.** Dhahran B0 and B1: 24 of 24 hours. Frankfurt B1: 14 of 20. Balloki B0 7, B1 24. Loudoun B1 24 |

## Load-shape sensitivity (pre-registered §6)

By the pre-registered rule the verdict is **"depends on load shape" = True**, triggered only by Frankfurt:
**20 → 24** silica scaling hours under L1 (NLR flat at 0.946), L2 (PowerData2019 amplitude 0.060) and L3
(0.155). The cause is that Frankfurt's four hours that failed to solve at nameplate (defect 43) solve at
≤ 0.946 load, and all four are supersaturated. Dhahran (12), Loudoun (24) and Balloki (21) do not move under
any shape. The cross-region range stays **[12, 24]**. So the measured load shapes do not weaken the claim, and
the one movement strengthens it. **Weather and assumed silica drive the claim; load does not.**
