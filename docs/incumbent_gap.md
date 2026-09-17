# How far is incumbent practice from the computed ceiling?

**17 September 2026.** This is a pre-registered study
(`docs/staged/incumbent_gap_preregistration.md`, committed before any computation). The harness is
`src/incumbent_gap.py`, the results are in `results/incumbent_gap.json`, and the checks are in
`tests/test_incumbent_gap.py`. Every number below comes from that one run.

---

## 1. Verdicts, failures included

| | hypothesis | verdict | the numbers |
|---|---|---|---|
| **H1** | On ≥ 50 % of waters, the LSI incumbent (P1) is ≥ 1.0 cycle from Mizan's ceiling (M) | **HOLDS** | 1 of 1 water; median gap **+8.43** cycles |
| **H2** | On every silica-bound water, P1 with acid permits ≥ 0.5 cycles more than M, at all five conditions | **HOLDS** | 1 silica-bound water; smallest gap **+7.66** |
| **H3** | A cheap rule of thumb (P3) lands within 0.5 cycles of M on ≥ 50 % of waters | **FAILS** | 0 of 1; median gap **−2.41** (the rule is *more* conservative than M) |
| **H4** | This harness reproduces the independent review's null (P1 = M) on the review's own input | **HOLDS** | P1, M, calcite-only and bulk-only all permit **10**, the top of the grid, at all 5 conditions |
| **H4b** | That null survives once silica is declared | **FAILS** | P1 **10**, M **3**, calcite-only **10**, bulk-only **5**, at all 5 conditions |

**Read the verdicts at the width of the panel.** The strict panel is **one water**, and its
silica is **assumed**, not measured. Each "≥ 50 % of waters" is therefore one comparison and is
not a statistic. On the extended panel, which adds the measured Riyadh assay (it fails the
charge-balance check by 0.25 points), the verdicts come out the same: H1 2 of 2, H2 holds with a
smallest gap of +3.90, H3 0 of 2.

**H1 and H2 hold because of how P1 is defined, and that definition is not established practice.**
P1 holds LSI at 2.5. That is the published *technical* limit of an HEDP inhibitor in high-sulfate
water. It is not a level plants are known to run at. The operators in the repository report LSI 0
to 0.5 (the Aramco pilot) and 1.4 (Riyadh). §3.1 shows that at those levels the incumbent sits
*below* M, so the over-cycling verdicts do not describe what plants actually do.

**H4 matters most.** The review's finding (full = calcite-only = bulk-only, gates C2b/C2c failed)
reproduces here exactly, on the silica-free input the review used. It **disappears** on the same
tower with silica declared: M drops to 3 on the review's grid while LSI and calcite-only stay at
10. The review's null holds only because its input carried silica at zero. Declaring silica
removes it. **But the silica figure that removes it is assumed on this water.** So whether the
product adds value here depends on a number nobody has measured.

---

## 2. The panel

Every `Water` in `src/chemistry.py` went through `validate_analysis`:

| water | panel | failed checks | silica | phosphate | class (M at pH 7.8) |
|---|---|---|---|---|---|
| `ARAMCO_FIELD_VALIDATED` (Dhahran TSE) | **strict** | none | **assumed** 26.8 mg/L | measured 8.0 | silica-bound at all 5 conditions; phosphate programme required |
| `ARAMCO_RIYADH_REFINERY_TSE` (NACE 577 Table 1) | extended | charge balance only | **measured** 18.0 | measured 1.0 | silica-bound at all 5 conditions; phosphate programme required |
| every other analysis (Badruzzaman 2022 Table 1 average, groundwater, three DOE effluents, synthetic DOE recipes, silica-omitted variants) | excluded | silica, phosphate, charge balance or TDS closure | — | — | — |

Composition: of 2 panel waters, **2 are silica-bound**, **0 are calcite-bound**, and both are
**phosphate-flagged**. No new water was added. Three published candidates were rejected; the
pre-registration gives the reasons, which are missing Na/K or reporting ranges rather than a
sample.

**Conditions.** These are the five V5 ambients. Temperatures come from the incumbent baseline's own
operating point (3.0 cycles, pH 7.8, 32 °C setpoint):

- bulk return water: 36.24–39.48 °C
- tube skin: 43.69–46.93 °C
- basin: 30.44–33.61 °C
- condenser heat rejection: 11,609–11,750 kW

---

## 3. Cycles permitted, per water and policy

Each value is the median over the five conditions. A positive gap is cycles *above* M.

**Acid regime, pH 7.8 (scored).**

| water | P0 fixed 3.0 | P1 LSI ≤ 2.5 | P2 RSI ≥ 6.0 | P3 LSI + SiO₂ + Mg×SiO₂ | **M** |
|---|---|---|---|---|---|
| Dhahran TSE (strict) | 3.00 (−1.51) | 12.95 (+8.43) | 1.86 (−2.65) | 2.10 (−2.41) | **4.51**, silica |
| Riyadh TSE (extended) | 3.00 (−3.72) | 11.41 (+4.69) | 1.64 (−5.08) | 4.95 (−1.77) | **6.72**, silica |

Across the five conditions, M runs 4.41–4.70 on Dhahran and 6.57–7.00 on Riyadh. On both waters
P3 is bound by the Mg×SiO₂ product rule.

**No acid, atmospheric-CO₂ pH (reported, not scored).**

| water | P0 | P1 | P2 | P3 | M |
|---|---|---|---|---|---|
| Dhahran TSE | 3.00 (+1.81) | 2.96 (+1.77) | 1.14 (−0.04) | 2.10 (+0.91) | 1.19 |
| Riyadh TSE | 3.00 (+1.70) | 2.30 (+1.00) | 1.00 (−0.30) | 2.30 (+1.00) | 1.30 |

**The no-acid M is bound by brucite, and this study stages that as a defect (57).** The brucite
saturation pH combines a hydroxide-form log K with a proton-form enthalpy, which puts it 0.62 pH
units too low at the skin: **8.714 against 9.337** at 44.85 °C, while the two forms agree at 25 °C
(9.940 against 9.952). With the consistent constant, brucite would bind no-acid operation at
**3.435** (Dhahran) and **3.742** (Riyadh) cycles instead of 1.19 and 1.30. That would leave
calcite binding first, at about 2.0 (Dhahran; 2.03 and 1.97 at the two conditions inspected) and
about 1.5 (Riyadh; 1.56 and 1.52). No scored verdict involves brucite: it binds nowhere in the
acid regime, and a test asserts that.

### 3.1 The sensitivity that decides the direction

At Dhahran summer peak and pH 7.8, P1's cycles depend on the LSI it holds:

| LSI_max | 0.5 | 1.0 | 1.4 | 2.0 | 2.5 | 2.8 | M |
|---|---|---|---|---|---|---|---|
| Dhahran TSE | 1.15 | 2.10 | 3.41 | 7.06 | 12.95 | 18.62 | 4.51 |
| Riyadh TSE | 1.01 | 1.85 | 3.01 | 6.22 | 11.41 | 16.41 | 6.72 |

The incumbent's position flips from under-cycling to over-cycling between LSI 1.4 and 2.0 on
Dhahran, and between 2.0 and 2.5 on Riyadh. **At the LSI operators actually report (0 to 1.4), the
LSI incumbent under-cycles on both waters.** It over-cycles into silica only when pushed to the
inhibitor's technical limit.

Four more sensitivities:

- **P2 (Ryznar).** At a fixed pH, RSI = pH − 2·LSI, so P2 is P1 under another name. RSI_min
  4.0 / 4.5 / 5.1 / 5.5 / 6.0 gives 6.26 / 4.62 / 3.21 / 2.52 / 1.86 cycles on Dhahran, and
  5.51 / 4.07 / 2.83 / 2.22 / 1.64 on Riyadh. The UFC cut at 6 is an uninhibited criterion, which
  is why P2 is so conservative.
- **Acid pH 7.5 / 8.0 / 8.25, at Dhahran summer peak.**
  - Dhahran: M 4.51 at all three pH values; P1 18.62 / 10.16 / 7.50.
  - Riyadh: M 6.72 / 6.58 / 4.53 (calcite takes over as pH rises); P1 16.41 / 8.95 / 6.61.
  - At pH 8.25, M on Riyadh is 4.53, which reproduces the Cycle Ceiling Report's 4.52. P1 still
    exceeds M there.
- **LSI at the basin instead of the return water.** This is more permissive: 14.76 against 12.95
  (Dhahran, summer peak).
- **Phosphate.** If a standard phosphate programme is declared and SI_tcp is allowed to bind, M
  collapses to **1.17–1.31** (Dhahran) and **4.82–5.43** (Riyadh). Dhahran then falls below the
  3.5 cycles its own pilot ran clean. That is the defect-29 contradiction, unchanged.

### 3.2 The adversarial rule of thumb: a failure of the primary definition, not a clean win

Under P3's primary definition, the Demadis guideline row for pH > 7.5 (SiO₂ ≤ 100, Mg×SiO₂ ≤
20,000 with Mg as CaCO₃, the basis the source states), the rule caps Dhahran at **2.10** cycles.
That is below the 3.5 cycles the pilot ran clean, so the rule is too conservative for this water
on its own stated basis.

**Some cited variants of the same rule land within 0.5 cycles of M on each water:**

- **Dhahran:** SiO₂ 150 or 200, Mg×SiO₂ 20,000 or 25,000, with **Mg as Mg²⁺**
- **Riyadh:** SiO₂ 150 or 200, Mg×SiO₂ 35,000 or 40,000, with **Mg as CaCO₃**

**No single variant does it on both waters.** A rule of thumb can be tuned to match the ceiling on
a water whose answer is already known. Nothing in this panel shows that one rule, chosen in
advance, reproduces the ceiling across waters. With two waters, that is weak evidence either way,
and the claim has to stay that narrow. The repository itself disagrees on which Mg basis and which
pH > 7.5 form of the rule are correct (staged defect 58).

---

## 4. What the gap is worth

These figures are for a 4.2 MW tower, scaled from the V5 thermal solve. They count makeup (USD
2.144/m³) plus discharge (USD 0.971/m³) at the Marafiq schedule. Each is an annual rate at one
condition, not hours-weighted: median, with the range over the five conditions. Acid is excluded.

| comparison | direction | Dhahran TSE | Riyadh TSE |
|---|---|---|---|
| P0, fixed 3.0 cycles → M | water left on the table | **USD 40,344/yr** (29,909–43,685) | **USD 58,991/yr** (46,339–65,972) |
| P1, LSI 2.5 with acid, vs M | break-even for over-cycling | **USD 33,699/yr** (30,640–40,785) | **USD 12,474/yr** (12,139–15,988) |
| P3, primary rule of thumb → M | water left on the table | USD 112,766/yr (88,797–126,292) | USD 15,050/yr (10,610–15,947) |
| P2, RSI ≥ 6 → M | water left on the table | USD 175,084/yr (116,382–187,644) | USD 275,585/yr (185,467–295,197) |

**How to read it.** The P0 row is the value a fixed-setpoint plant gives up by staying at three
cycles, *if M's ceiling is safe to run at*. M is a scaling ceiling, not an operating ceiling. On
both waters it also requires a phosphate programme that the screen cannot size.

The P1 row is a break-even, not a saving. **The ceiling pays for itself against an LSI-2.5
incumbent if an avoided scaling event is worth more than roughly USD 12,000–34,000 a year.** No
cleaning, retubing or outage cost is cited anywhere in the repository, so nothing more is claimed.

The P2 and P3 rows compare against incumbents far more conservative than any operator in the
repository (1.6–2.1 cycles). They are upper bounds on a strawman and should not be quoted as
savings.

The P0 value, USD 40–59k a year, is below the USD 120–185k per tower it would cost to *measure*
the chemistry (defect 47). The finding stands: the product has to infer the chemistry, not
instrument it.

---

## 5. Limitations

1. **Panel of one water (two with the exception).** No gap in this study generalises beyond the
   Dhahran and Riyadh TSE analyses.
2. **The strict water's silica is assumed** (26.8 mg/L, from brackish groundwater). Every
   silica-bound result on it, and H4b, rests on that assumption.
3. **The conditions barely vary.** The basin runs 30.4–33.6 °C across all five conditions, so this
   study says little about winter or data-centre operation.
4. **Where P1 is placed decides the direction of the gap** (§3.1). No source in the repository
   establishes that any operator runs LSI near 2.5.
5. **Permitted cycles are not chosen actions.** The review scored cost-optimal actions; this study
   scores ceilings. H4 reproduces the review's null qualitatively on its grids, not its costs.
6. **Discharge (RCER-2015 Table 3C, monthly average) is reported and not imposed.** Taking nitrate
   as a conservative tracer, the makeup alone already breaches it on both waters, giving a
   discharge ceiling of 1.0. RCER does not govern Dhahran or Riyadh.
7. **Davies validity** (16.3 and 23.6 cycles) binds nowhere.
8. **Staged defects 57 and 58** (`docs/staged/incumbent-gap_defects.md`) are not fixed here.
   Defect 57 may move controller results wherever the optimiser's pH exceeds the corrected brucite
   limit, and none of those results was rerun.

---

## What the pitch can claim

On the one repository water that passes its own analysis checks (Dhahran TSE, silica assumed), and
on the measured Riyadh assay admitted by exception, the computed ceiling at the V5 conditions is
set by amorphous silica at the cold basin: **4.4–4.7 and 6.6–7.0 cycles**. The Langelier index
cannot see that mineral.

Four claims fit that evidence:

- A plant held at a fixed 3 cycles leaves roughly **USD 40–59k a year** of makeup and discharge on
  a 4.2 MW tower, if the ceiling is safe to operate at.
- An LSI controller pushed to its published inhibitor limit with acid would permit **11–13
  cycles**, well past silica saturation.
- The independent review's finding that the full model changes nothing **reproduces exactly when
  silica is zero and disappears when silica is declared**.
- **The product's value on these waters is therefore the silica term, and it is worth exactly as
  much as the silica assay behind it.**

Four claims the evidence does not support:

- a gap that generalises across waters;
- that real incumbents over-cycle (reported operator LSI of 0–1.4 puts them *below* the ceiling);
- that rules of thumb are beaten (cited variants land within half a cycle on each water, though
  no one variant did on both);
- any avoided scaling cost beyond a break-even of **USD 12–34k a year**.
