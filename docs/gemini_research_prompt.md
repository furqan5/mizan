# Deep-research prompt — paste into Gemini Deep Research

> Everything above the line is context Gemini needs. Everything below the line is the task. Paste the whole thing.

---

## CONTEXT — what already exists, so you do not repeat it

I am building **Mizan**, a retrofit supervisory controller for cooling-tower / condenser-water loops in Gulf district cooling and industrial cooling. It co-optimises tower fan speed, blowdown (cycles of concentration) and acid dose against **ion-specific mineral saturation evaluated per mineral at the temperature where each mineral is least soluble** — calcite and gypsum at the hot condenser tube skin, amorphous silica at the cold tower basin.

A validated physics model already exists: Poppe/Rögener heat-and-mass transfer (Kloppers & Kröger formulation) coupled to an ion-association speciation engine built on USGS PHREEQC constants. It predicts held-out experimental data to 0.542 K outlet-temperature MAE and measured water consumption to 7.11% MAPE. *(As sent. That water figure was later corrected to 9.90 % when a drift-rate defect was found — see the PoC report.)*

**Already found — do NOT spend effort re-finding these:**

- Badruzzaman et al. (2022), *Water Resources and Industry* 28:100188 — Saudi Aramco, Dhahran. Measured ion analysis of reclaimed water used as cooling-tower makeup on a 4.2 MW tower; 27% water reduction. **Silica is not reported in it.**
- Al-Mutaz & Al-Anezi (2004), Int. Conf. Water Resources & Arid Environment — Saudi brackish well water silica 20–60 ppm; Salbukh (Riyadh) raw 26.8–30 mg/L.
- Kloppers (2003) PhD, Stellenbosch — fill transfer-characteristic correlations; air temperatures shown not to affect the transfer coefficient; fill ageing explicitly not studied.
- ChemTreat US 11,780,742 B2 (2023) — skin-temperature saturation index driving antiscalant dose. US + PCT only; no Gulf family member found.
- Nalco 3D TRASAR benchmark — raised cycles 2.5–3.5 → 4–5, ~30% blowdown reduction, at Umm Al-Qura University, Saudi Arabia (12,000 TR).
- Industry rule of thumb: maintain cycles of concentration 3.5–5.0.
- Zenodo 10806201 — Plataforma Solar de Almería wet cooling tower dataset, 165 steady-state points.

**Key result I am trying to stress-test:** with realistic Saudi silica (20–60 mg/L) in the makeup, my model computes a maximum safe cycles of concentration of **2.2–6.5**, centring on **4.4–4.9 at Salbukh-measured silica**. That coincides with the industry's empirical 3.5–5.0 band. I want to know whether this coincidence is real or whether I am fooling myself.

---

# TASK

Research the following. **Never invent a citation.** For every claim give a working URL and tag it `[C]` confirmed, `[A]` your inference, or `[UNVERIFIED]` with a note on what you tried. **Report negative results explicitly** — "searched X, found nothing" is a valuable answer. Prefer primary sources, peer-reviewed papers, patents, standards and operator/utility publications over vendor marketing.

## Priority 1 — Silica in Gulf treated sewage effluent (the single biggest gap)

1. **Measured silica (SiO₂, mg/L) in treated sewage effluent or reclaimed water in Saudi Arabia, Qatar, UAE, Kuwait, Oman or Bahrain.** I need TSE specifically, not brackish well water. Municipal wastewater treatment plant effluent analyses, district-cooling makeup water analyses, water-reuse studies, utility annual reports, Kahramaa or Saudi Water Authority publications.
2. **Full ionic analyses of Gulf TSE used as cooling-tower makeup** — Ca, Mg, Na, K, HCO₃, CO₃, SO₄, Cl, SiO₂, PO₄, NO₃, TDS, pH, alkalinity. Ideally analyses that charge-balance.
3. **How silica concentration changes through wastewater treatment** — does biological treatment raise or lower it relative to the source water?

## Priority 2 — Is the silica limit really where I compute it?

4. **Published maximum silica concentrations actually run in operating cooling towers**, with and without silica-specific inhibitors. I have a saturation-ratio limit of 1.2 (typical) and 2.5 (stressed) from IWC-11-77. Corroborate, correct, or better it.
5. **Named silica polymerisation inhibitors / dispersants and their documented performance ceilings** — how far above amorphous-silica saturation can a real programme hold silica, and at what dose and cost?
6. **Amorphous silica solubility as a function of temperature and pH** in the 20–50 °C, pH 7–9 range relevant to cooling water. I use the PHREEQC `SiO2(a)` value (log_k −2.71, ΔH +3.59 kcal). Is there better data?
7. **Documented cooling-tower silica scaling incidents** — what silica level, what cycles, what happened, what did it cost to remediate?
8. **Does anyone evaluate silica saturation at the coldest point of the loop** rather than at the heat-transfer surface? This is a specific claim of mine and I want to know if it is standard practice, novel, or wrong.

## Priority 3 — Independent validation data

9. **Open, row-level experimental or operational cooling-tower datasets** with inlet/outlet water temperature, wet-bulb, water and air flow — and ideally evaporation, blowdown or makeup. Repositories (Zenodo, Figshare, Mendeley Data, IEEE DataPort, OSF), supplementary materials, national lab datasets. I have one; I want a second.
10. **Published cooling-tower model validation accuracies** — what outlet-temperature MAE or RMSE do Merkel/Poppe/e-NTU implementations achieve against experiment? I need to know whether 0.542 K is good, typical or poor.
11. **Cooling-tower fill ageing and fouling over time** — any study quantifying how the fill transfer characteristic degrades over months or years. Kloppers explicitly did not study this and I have measured a 21% coefficient drift across four years.

## Priority 4 — Commercial reality

12. **What a condenser fouling or scaling event actually costs** a district-cooling or industrial plant — lost capacity, chemical cleaning, energy penalty, downtime. Real numbers from real incidents.
13. **Cycles of concentration actually operated at named Gulf district-cooling plants** — Qatar Cool, Qatar Foundation, Marafeq, Saudi Tabreed, Marafiq. Any published operating data.
14. **Whether any commercial cooling-water controller uses ion-association/speciation modelling rather than empirical indices (LSI, RSI, Puckorius, Larson-Skold, Stiff-Davis).** Check Nalco/Ecolab, Veolia, Kurita, ChemTreat, Solenis, French Creek Software, and any startup. This is my core differentiation claim and I need it falsified or confirmed.
15. **Patents filed 2020–2026 on cooling-water blowdown or cycles optimisation against saturation indices**, especially any with Saudi, Qatari, GCC, EP or CN family members.

## Priority 5 — Regulatory and policy levers

16. **Any Saudi or Qatari regulation, standard or utility requirement governing cooling-tower water efficiency, blowdown discharge limits, or mandated TSE use in district cooling.** Saudi Water Authority, MEWA, Kahramaa, Royal Commission for Jubail and Yanbu, SEEC.
17. **Discharge limits on cooling-tower blowdown** in Saudi Arabia and Qatar — do they constrain how high cycles can be run, or create a cost that rewards raising them?

---

## OUTPUT FORMAT

- Organise by the priority headings above.
- Numeric findings in tables, with units and source URL per row.
- A final section titled **"What I could not find"**, listing every question that returned nothing. This is as important as what you did find.
- A final section titled **"What contradicts the thesis"**, listing anything that argues against the approach. Do not soften it.
- Full source list with working URLs.
