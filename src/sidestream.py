"""
FURQAN / MIZAN :: side-stream treatment, and what it is worth.

THE QUESTION THIS ANSWERS, WHICH NOBODY CAN ANSWER TODAY.

A plant on treated effluent is stuck at two or three cycles. The controller
can tell it the true ceiling is five or six, which is worth 17-20 % of its
makeup water. But the ceiling itself is set by ONE species -- on this water,
amorphous silica -- and that species can be removed.

So the real operating question is not "what is my ceiling" but:

    If I spend money removing the mineral that binds me, what does my
    ceiling become, and how much may that treatment cost before it stops
    paying for itself?

No incumbent tool answers this, because answering it requires a speciation
model to find which mineral binds and a water balance to price the result.
Ecolab, ChemTreat, Veolia and Kurita compute LSI. French Creek has the
chemistry but no control loop and no economics. This module joins them.

WHY IT RETURNS A BREAK-EVEN COST AND NOT A PAYBACK.

A payback needs a capex number, and a capex number for a side-stream softener
or membrane skid is a vendor quotation for a specific site, not something
this package may invent. Inventing one and reporting a payback would be the
defect-12 shape: a typed constant presented as a result.

Instead this returns **the maximum all-in treatment cost, in currency per
cubic metre treated, at which the intervention still breaks even**. That is a
number the model can honestly compute, and it converts a procurement question
into a single figure an operator can take to a supplier: *"quote me below this
and it pays."*

WHAT A SAND FILTER DOES NOT DO.

Encoded deliberately, because the literature gets it wrong. Granular media
filtration removes SUSPENDED solids. It does not remove DISSOLVED silica,
calcium or alkalinity, so it cannot move a saturation ceiling at all. A 2026
Water-Energy Nexus paper reports a sand filter cutting conductivity from
1700 to 700 uS/cm and evaporation by 20.5 %; neither is physically possible
from media filtration at constant duty, and the makeup reduction it reports
is therefore confounded with something else that changed. `TECHNOLOGIES`
below carries sand filtration with zero dissolved-species removal so the
model cannot reproduce that error.
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import chemistry as chem            # noqa: E402
import controller as ctl            # noqa: E402


# ---------------------------------------------------------------------------
# Technologies, and what each actually removes
# ---------------------------------------------------------------------------
# Removal fractions are of the DISSOLVED species named, applied to the stream
# that passes through the unit. Every figure carries its basis; none is a
# vendor quotation for a specific site.
#
# STREAM POSITION, and why it is recorded rather than assumed.
#
# This module models treatment of a fraction of the MAKEUP stream. That is
# the right topology for lime softening and for a side-stream RO on makeup,
# and it is the WRONG topology for electrocoagulation, which every published
# reference applies to BLOWDOWN. Treating blowdown and returning it is
# blowdown recycle, and it raises effective cycles by a different arithmetic
# than reducing the incoming load does.
#
# The `stream` key records which is which. The break-even calculation below
# currently prices ALL of them as makeup treatment, so a blowdown-stream
# technology's economics are APPROXIMATE and flagged in the result. Modelling
# recycle properly needs a second water balance and is not done here; saying
# so is better than quietly applying the wrong one.
TECHNOLOGIES = {
    "sand_filtration": {
        "removes": {},                       # suspended solids only
        "note": "Granular media. Removes suspended solids and turbidity. "
                "Removes NO dissolved species, so it cannot move a "
                "saturation ceiling. Included so the model refuses to "
                "reproduce a published claim that it can. [C]",
    },
    "lime_softening": {
        "removes": {"SiO2": 0.50, "Ca": 0.70, "HCO3": 0.80, "Mg": 0.60},
        "note": "Lime, or lime-soda, at pH about 10. Silica is adsorbed onto "
                "magnesium and calcium hydroxide floc. Published removal is "
                "'over 50 percent of the silica'; calcium and alkalinity "
                "removal is the primary function and is higher. [C Veolia "
                "Water Handbook ch.7; Chardon Labs]",
    },
    "lime_softening_with_magnesia": {
        "removes": {"SiO2": 0.80, "Ca": 0.70, "HCO3": 0.80, "Mg": 0.40},
        "note": "Lime softening with added magnesium oxide or dolomitic "
                "lime, which is the standard way to push silica removal "
                "above the plain-lime figure. The 0.80 is the upper end of "
                "the published range and should be treated as optimistic "
                "until a jar test on the actual water says otherwise. [U]",
    },
    "reverse_osmosis": {
        "removes": {"SiO2": 0.85, "Ca": 0.97, "Mg": 0.97, "Na": 0.95,
                    "K": 0.95, "Cl": 0.95, "SO4": 0.98, "HCO3": 0.90,
                    "NO3": 0.90, "PO4": 0.97},
        "note": "Side-stream RO. The 0.851 silica rejection is the measured "
                "value from Kornboonraksa (2016) on tertiary municipal "
                "wastewater; the others are conventional brackish-water "
                "rejections. RO also produces a concentrate stream that must "
                "be disposed of, which this model charges as a recovery "
                "penalty rather than ignoring. [C silica; A others]",
        "recovery": 0.75,
    },
    "electrocoagulation": {
        "removes": {"SiO2": 0.95, "Ca": 0.40, "Mg": 0.60},
        "stream": "blowdown",
        "note": "Aluminium electrodes, CONTINUOUS reactor, on COOLING TOWER "
                "BLOWDOWN at 1500 C/L charge loading and 9 mA/cm2: silica "
                "removal ~95 %. That is the entry for this exact duty in the "
                "literature review of Dutta et al., 'Removal of Calcium and "
                "Silica from Simulated Blowdown Water Using CO2-Assisted "
                "Magnesium Electrocoagulation', ES&T Water (Oak Ridge "
                "National Laboratory), Table S1. Neighbouring entries: "
                "boiler blowdown 95 %, synthetic groundwater 95+/-4 %, "
                "semiconductor wastewater ~100 %, RO reject ~79 %. "
                "[C silica; A calcium and magnesium] "
                "RAISED from 0.80 on 11 Sep 2026 -- the earlier figure was "
                "an unsourced bench-scale guess and was too low.",
    },
}


def treat(water, technology, fraction_treated=1.0):
    """The makeup water after a side stream removes part of its load.

    `fraction_treated` is the fraction of the MAKEUP stream passed through
    the unit. Treating half the makeup at 80 % removal is the same blended
    result as treating all of it at 40 %, which is exactly the trade an
    operator makes when sizing a skid.
    """
    if technology not in TECHNOLOGIES:
        raise ValueError(f"unknown technology {technology!r}; expected one "
                         f"of {tuple(TECHNOLOGIES)}")
    if not 0.0 <= fraction_treated <= 1.0:
        raise ValueError("fraction_treated must lie in [0, 1]")

    spec = TECHNOLOGIES[technology]
    kw = {}
    for s in chem.SPECIES:
        c0 = getattr(water, s)
        r = spec["removes"].get(s, 0.0)
        kw[s] = c0 * (1.0 - r * fraction_treated)
    tds = water.TDS
    if tds is not None:
        # scale TDS by the mass actually removed, so the analysis stays
        # self-consistent and still passes its own closure check
        before = sum(getattr(water, s) for s in chem.SPECIES)
        after = sum(kw.values())
        tds = tds * (after / before) if before > 0 else tds
    return chem.Water(name=f"{water.name} + {technology}"
                           f" ({fraction_treated:.0%})",
                      pH=water.pH, TDS=tds, **kw)


def ceiling_with(water, T_hot, T_cold, limits=None, pH=None,
                 lo=1.0, hi=30.0):
    """Ceiling and binding mineral for a water, at the two evaluation points.

    `pH` matters and defaults matter more. `chemistry.max_cycles_split()`
    resolves pH by atmospheric CO2 equilibrium, which is the UNCONTROLLED
    case -- no acid dosed. A plant that runs three cycles on this water is
    dosing acid to do it, so comparing a treated and an untreated water at
    atmospheric pH answers a question nobody is asking.

    Passing a pH evaluates both waters at the setpoint the controller would
    actually hold, which is the comparison a treatment decision needs.
    """
    limits = chem.OPERATING_LIMITS if limits is None else limits
    if pH is None:
        c = chem.max_cycles_split(water, T_hot, T_cold, limits=limits,
                                  lo=lo, hi=hi)
        return c, chem.binding_mineral_split(water, c, T_hot, T_cold,
                                             limits=limits)

    def margin(cy):
        s = chem.saturation_state_split(water.concentrate(cy), T_hot, T_cold,
                                        pH_hot=pH, pH_cold=pH)
        return min(limits[k] - s[k] for k in limits)

    if margin(lo) < 0:
        c = float(lo)
    elif margin(hi) > 0:
        c = float(hi)
    else:
        from scipy.optimize import brentq
        c = float(brentq(margin, lo, hi, xtol=1e-3))
    s = chem.saturation_state_split(water.concentrate(c), T_hot, T_cold,
                                    pH_hot=pH, pH_cold=pH)
    return c, min(limits, key=lambda k: limits[k] - s[k])


def davies_validity_cycles(water, lo=1.0, hi=40.0):
    """Highest cycles count at which this model is entitled to an opinion.

    DEFECT 26, one module over. Above ionic strength 0.5 mol/kg the Davies
    equation is outside its range and every activity coefficient in every
    saturation index is an extrapolation. Removing the binding species raises
    the ceiling, and a raised ceiling walks straight at this boundary -- a
    treated water that reads "30 cycles" is not a finding, it is the model
    being asked a question it cannot answer.

    Reported alongside every ceiling so the two can be compared, rather than
    computed and ignored, which is what defect 26 was.
    """
    I_max = chem.ANALYSIS_TOLERANCES["ionic_strength_max"]
    if water.concentrate(hi).ionic_strength() <= I_max:
        return float(hi)
    if water.concentrate(lo).ionic_strength() > I_max:
        return float(lo)
    from scipy.optimize import brentq
    return float(brentq(
        lambda cy: water.concentrate(cy).ionic_strength() - I_max,
        lo, hi, xtol=1e-3))


def makeup_m3_h(evap_kg_s, cycles):
    """Makeup at a given cycles count, for a fixed evaporation rate."""
    wb = ctl.water_balance(evap_kg_s, 0.0, cycles)
    return wb["makeup"] * 3.6


def break_even_cost(water, technology, evap_kg_s, tariffs, T_hot, T_cold,
                    baseline_cycles=3.0, fraction_treated=1.0, limits=None,
                    hours_per_year=8760.0, pH=None):
    """The most a treatment may cost per cubic metre treated and still pay.

    The benefit is the water no longer bought and the blowdown no longer
    discharged, once the higher ceiling is actually reached. The cost basis
    is the volume passing through the unit.

    Returns None where the treatment does not raise the ceiling at all --
    which is the honest answer for sand filtration, and the reason it is in
    the technology table.
    """
    limits = chem.OPERATING_LIMITS if limits is None else limits
    treated = treat(water, technology, fraction_treated)

    c_before, m_before = ceiling_with(water, T_hot, T_cold, limits, pH)
    c_after_raw, m_after = ceiling_with(treated, T_hot, T_cold, limits, pH)

    # DEFECT 26 applied here. A chemistry ceiling past the Davies limit is an
    # extrapolation, not a ceiling, so it is CAPPED and the cap is reported.
    davies_after = davies_validity_cycles(treated)
    c_after = min(c_after_raw, davies_after)
    model_limited = c_after_raw > davies_after + 1e-6

    # The plant cannot run above the ceiling, and will not run below its
    # existing setpoint, so the achievable cycles are bounded both ways.
    run_before = max(min(c_before, c_before), baseline_cycles)
    run_after = max(min(c_after, c_after), baseline_cycles)

    mk_base = makeup_m3_h(evap_kg_s, baseline_cycles)
    mk_before = makeup_m3_h(evap_kg_s, run_before)
    mk_after = makeup_m3_h(evap_kg_s, run_after)

    # water no longer bought, plus blowdown no longer discharged
    p_m = tariffs.get("water_makeup_per_m3", tariffs["water_per_m3"])
    p_b = tariffs.get("water_discharge_per_m3", 0.0)

    def cost_of(mk, cycles):
        bd = mk / cycles if cycles > 0 else mk
        return p_m * mk + p_b * bd

    saving_h = cost_of(mk_before, run_before) - cost_of(mk_after, run_after)

    # RO rejects a concentrate stream, so the volume treated exceeds the
    # volume recovered and the concentrate has to go somewhere.
    recovery = TECHNOLOGIES[technology].get("recovery", 1.0)
    treated_m3_h = mk_after * fraction_treated / max(recovery, 1e-6)
    reject_m3_h = treated_m3_h - mk_after * fraction_treated
    saving_h -= p_b * reject_m3_h

    if c_after <= c_before + 1e-6:
        return {
            "technology": technology, "raises_ceiling": False,
            "ceiling_before": c_before, "ceiling_after": c_after,
            "binding_before": m_before, "binding_after": m_after,
            "break_even_per_m3": None,
            "note": TECHNOLOGIES[technology]["note"],
        }

    be = saving_h / treated_m3_h if treated_m3_h > 0 else float("nan")
    stream = TECHNOLOGIES[technology].get("stream", "makeup")
    return {
        "technology": technology,
        "stream": stream,
        "economics_approximate": stream != "makeup",
        "raises_ceiling": True,
        "fraction_treated": fraction_treated,
        "ceiling_before": c_before,
        "ceiling_after": c_after,
        "ceiling_after_unlimited": c_after_raw,
        "davies_validity_cycles": davies_after,
        "model_limited": model_limited,
        "binding_before": m_before,
        "binding_after": ("MODEL VALIDITY (Davies)" if model_limited
                          else m_after),
        "baseline_cycles": baseline_cycles,
        "cycles_run_before": run_before, "cycles_run_after": run_after,
        "makeup_baseline_m3_h": mk_base,
        "makeup_before_m3_h": mk_before, "makeup_after_m3_h": mk_after,
        "water_saved_vs_baseline_pct": 100.0 * (mk_base - mk_after) / mk_base,
        "water_saved_vs_untreated_pct": (100.0 * (mk_before - mk_after)
                                         / mk_before),
        "treated_m3_h": treated_m3_h,
        "reject_m3_h": reject_m3_h,
        "saving_per_h": saving_h,
        "saving_per_year": saving_h * hours_per_year,
        "break_even_per_m3": be,
        "note": TECHNOLOGIES[technology]["note"],
    }


def survey(water, evap_kg_s, tariffs, T_hot, T_cold, baseline_cycles=3.0,
           fraction_treated=1.0, limits=None, pH=None):
    """Every technology, ranked by the ceiling it delivers."""
    out = []
    for t in TECHNOLOGIES:
        out.append(break_even_cost(water, t, evap_kg_s, tariffs, T_hot,
                                   T_cold, baseline_cycles, fraction_treated,
                                   limits, pH=pH))
    return sorted(out, key=lambda r: -r["ceiling_after"])


# ---------------------------------------------------------------------------
# COST REALITY CHECK -- DEFECT 36
# ---------------------------------------------------------------------------
# The break-even figures this module returns are the price per cubic metre at
# which a treatment would pay for itself on avoided water and chemicals. Until
# 11 September 2026 nothing compared them to what treatment ACTUALLY costs,
# and the omission flattered every recommendation the module made.
#
# A costed engineering study closes that gap. DiFilippo, M., "Equipment Cost
# Analysis for Cooling Tower Blowdown Treatment Systems", technical
# memorandum for Sylvan Source, 24 October 2023 (update of a May 2017
# version). A coal-fired power plant, 1 MGD of cooling tower blowdown, with
# budgetary equipment costs and installation factors. [C]
#
# Its Table 2 is also a real, complete cooling-tower blowdown analysis:
#
#   Na 6,368  K 276  Ca 400  Mg 236  HCO3 46  Cl 4,160  F 21
#   SO4 9,791  SiO2 176  B 4  TDS 21,494  TSS 5  (all mg/L)
#
# and its pre-treated column gives the removal actually achieved by a
# precipitation softener followed by media filtration and weak-acid-cation
# polishing:  SiO2 176 -> 18 mg/L, Ca 400 -> 12, Mg 236 -> 24.
#
# THE NUMBER THAT MATTERS. For that duty -- 1 MGD, 157.7 m3/h, 1.38 Mm3/yr --
# the pretreatment train costs $25,440,000 installed and $2,793,000 a year in
# chemicals alone. That is
#
#     chemicals only                      $2.02 / m3 treated
#     + capital over 20 years, no interest $0.92 / m3
#     + capital over 10 years              $1.84 / m3
#
# against a break-even this module computes at $0.39/m3 for lime softening on
# Gulf tariffs. **Chemicals alone are 5.2x the break-even, and the whole train
# is roughly eight times underwater.**
#
# SO: SIDE-STREAM SOFTENING DOES NOT PAY ON WATER VALUE AT GULF TARIFFS. It
# pays when discharge is PROHIBITED and the alternative is zero liquid
# discharge, which is why the study exists -- its plant cannot use evaporation
# ponds. That is a regulatory driver, not a water-price one, and the
# distinction decides whether any of this is a business.
#
# WHAT IS NOT FAIR ABOUT THE COMPARISON, stated so it is not overclaimed: this
# is a ZLD pretreatment train on a very concentrated blowdown (TDS 21,494,
# silica 176), sized for 1 MGD. A smaller side-stream on weaker water costs
# less per cubic metre. But the chemical dose scales with the hardness and
# silica actually removed, which is the entire point of the unit, so it does
# not scale away -- and an eightfold gap does not close on scale alone.
REAL_COST_BENCHMARK = {
    "source": ("DiFilippo, M., Equipment Cost Analysis for Cooling Tower "
               "Blowdown Treatment Systems, Sylvan Source technical "
               "memorandum, 24 Oct 2023"),
    "duty_m3_per_h": 157.7,
    "duty_m3_per_yr": 1_381_437.0,
    "pretreatment_installed_usd": 25_440_000.0,
    "pretreatment_chemicals_usd_per_yr": 2_793_000.0,
    "silica_removed_pct": 89.8,            # 176 -> 18 mg/L, measured
    "calcium_removed_pct": 97.0,           # 400 -> 12
    "magnesium_removed_pct": 89.8,         # 236 -> 24
    "zld_unit_opex_usd_per_m3": {          # whole-train, for scale
        "sylvan_core": 3.60, "ro_plus_vce": 5.38, "vce": 3.97},
}


def real_cost_per_m3(amortise_years=20.0):
    """What side-stream softening actually costs per cubic metre treated."""
    b = REAL_COST_BENCHMARK
    chem = b["pretreatment_chemicals_usd_per_yr"] / b["duty_m3_per_yr"]
    cap = b["pretreatment_installed_usd"] / amortise_years / b["duty_m3_per_yr"]
    return {"chemicals_per_m3": chem, "capital_per_m3": cap,
            "total_per_m3": chem + cap, "amortise_years": amortise_years}


def passes_cost_reality_check(break_even_per_m3, amortise_years=20.0):
    """Does a computed break-even survive contact with a costed study?

    Returns a dict rather than a bool, because the RATIO is the useful
    output: a break-even eight times under the real cost is not a marginal
    case to be resolved by better estimating.
    """
    real = real_cost_per_m3(amortise_years)
    be = float(break_even_per_m3)
    return {
        "break_even_per_m3": be,
        "real_cost_per_m3": real["total_per_m3"],
        "real_chemicals_only_per_m3": real["chemicals_per_m3"],
        "shortfall_ratio": real["total_per_m3"] / be if be > 0 else float("inf"),
        "pays": be >= real["total_per_m3"],
        "pays_on_chemicals_alone": be >= real["chemicals_per_m3"],
        "note": ("Benchmarked against a ZLD pretreatment train on concentrated "
                 "blowdown; a smaller side-stream on weaker water costs less "
                 "per m3, but the chemical dose scales with what is removed."),
    }


# ---------------------------------------------------------------------------
# THE COUNTER-EXAMPLE -- and it corrects the paragraph above
# ---------------------------------------------------------------------------
# `REAL_COST_BENCHMARK` says side-stream treatment is five to twelve times
# underwater on water value. A real district cooling operator does it anyway,
# profitably enough to win an industry award for it, and the difference is
# WHICH STREAM IS TREATED.
#
# Austin Energy Downtown District Energy & Cooling System, IDEA System of the
# Year 2023 submission. Three plants, DCP1-DCP3. In their own words: [C]
#
#   "A typical cooling tower has an average of 2 to 4 cycles of concentration.
#    By using sulfuric acid in our condenser water chemical treatment systems
#    at DCP2 and DCP3, we cycled our towers up to 12 cycles of concentration.
#    This will realize a total savings of over 25 million gallons of water
#    each year. At DCP1, we utilize a SOFTENED WATER SYSTEM for our condenser
#    water system. Our DCP1 cycles of concentration is between 15 to 18. At a
#    minimum, 10 million gallons of water is saved yearly at DCP1."
#
# and elsewhere: "Utilize sulfuric acid to increase cycles of concentration
# from 6 to 12".
#
# WHAT THIS CORRECTS. The Sylvan Source benchmark is a ZERO LIQUID DISCHARGE
# train on CONCENTRATED BLOWDOWN -- TDS 21,494, silica 176 mg/L, sized for
# 1 MGD, $25.4 M installed. This module treats a fraction of the MAKEUP, which
# is a far weaker stream and a far smaller unit. Pricing makeup softening
# against a blowdown ZLD train was not a fair comparison, it was flagged as
# such in the note above, and Austin is the empirical proof that the caveat
# mattered: DCP1 softens makeup and reaches 15-18 cycles.
#
# So the honest statement is narrower than "treatment does not pay":
#
#   * MAKEUP-side softening pays, and is in service at scale. [C Austin]
#   * BLOWDOWN ZLD does not pay on water value, and is driven by a discharge
#     prohibition instead. [C Sylvan Source]
#   * This module models the makeup side, so REAL_COST_BENCHMARK is an upper
#     bound on its costs, not an estimate of them.
#
# WHAT DOES NOT TRANSFER TO THE GULF, and it is the whole regulatory finding:
# Austin's main lever is SULFURIC ACID, 6 -> 12 cycles. RCER-2015 section
# 3.6.3 forbids exactly that in Jubail and Yanbu. A Gulf plant under Royal
# Commission jurisdiction cannot copy DCP2 and DCP3; it can only copy DCP1,
# the softened one. The acid ban does not merely cost cycles -- it forces the
# capital route.
AUSTIN_COUNTER_BENCHMARK = {
    "source": ("Austin Energy Downtown District Energy & Cooling System, "
               "IDEA System of the Year 2023 submission"),
    "typical_cycles": (2.0, 4.0),          # their words, for a typical tower
    "acid_cycles": (6.0, 12.0),            # DCP2, DCP3 with sulfuric acid
    "softened_cycles": (15.0, 18.0),       # DCP1, softened makeup
    "water_saved_gal_per_yr": {"acid_plants": 25_000_000,
                               "softened_plant": 10_000_000,
                               "total": 35_000_000},
    "lever_banned_in_RC_jurisdiction": "sulfuric acid, RCER-2015 s.3.6.3",
}


def typical_cycles_evidence():
    """Five independent sources on what a tower actually runs at.

    This is the baseline the V7 gate is scored against, and it is no longer
    an assumption: every source lands in 2 to 4 cycles. Two continents, five
    operators, a refinery, a district-cooling utility, a municipal utility and
    a food plant -- and none of them reaches the 5 to 7 cycles that the
    textbook and most vendor literature quote as normal.

    The fifth, WCTI, is the lowest of the five AND has the highest makeup
    silica (32 ppm, against our 18), which is the direction the silica thesis
    predicts. Found 11 Sep 2026 in the Wayback PDF index; see
    docs/chemistry_evidence.md S4.3.
    """
    return [
        ("Austin Energy (IDEA 2023)", "typical cooling tower", (2.0, 4.0)),
        ("Qatar Cool", "TSE, stated maximum", (None, 3.0)),
        ("Aramco Riyadh Refinery (NACE 577)", "measured, average 2.9", (1.6, 4.0)),
        ("Aramco Dhahran pilot (WRI 2022)", "groundwater 2.0, TSE 3.5", (2.0, 3.5)),
        ("WCTI food-processing plant", "makeup SiO2 32 ppm, 'typically "
         "operate below 2.1 cycles'", (None, 2.1)),
    ]


# ---------------------------------------------------------------------------
# DEFECT 39. A ceiling reported from an analysis that failed its own check.
# ---------------------------------------------------------------------------
def charge_closure_bracket(water, T_hot, T_cold, pH=None, limits=None):
    """How much of the ceiling rests on an unclosed charge balance.

    WHY THIS EXISTS. The Cycle Ceiling Report defaults to the measured Aramco
    Riyadh assay, and that assay FAILS its own charge-balance check at
    -5.25 % against a +/-5 % tolerance. The report printed `ceiling 4.52
    cycles` anyway, on one console line, with the failed check visible only
    further down the HTML. A number that leaves this package in a pitch deck
    must carry its own caveat, because the deck will not.

    The imbalance is NEGATIVE, meaning the published cations do not account
    for all the published anions. On SECONDARY treated sewage effluent there
    is an obvious candidate: secondary treatment nitrifies only partially, so
    the stream carries ammonium, and NH4+ is not in this model's species list
    at all. The deficit of 0.806 meq/kg closes with 11.3 mg/L as N -- squarely
    inside the range a secondary effluent carries. So the most likely reading
    is not that the assay is wrong but that it is INCOMPLETE, in a way this
    model cannot represent.

    That is an explanation, not a licence. This function does not add the
    missing ion. It closes the balance BOTH WAYS -- once by adding sodium,
    once by removing chloride -- and reports the spread in the ceiling, so the
    question "does the ceiling depend on this?" is answered with a number
    rather than an argument.

    On the Riyadh assay the answer is that it does not: 4.50 to 4.53 cycles,
    a spread of 0.7 %. The ceiling is set by calcite, and neither sodium nor
    chloride appears in the calcite ion product -- they move the result only
    through the ionic strength, third-decimal stuff at I = 0.021 mol/kg. The
    check must still be reported as failed. What it does not do is invalidate
    the ceiling.

    Returns a dict with the three ceilings, the spread, and whether the spread
    is material -- defined as more than 0.25 cycles, the resolution at which
    a cycles setpoint is actually adjustable in the field.
    """
    import dataclasses

    m = water.molality()
    cat = sum(m[s] * water._charge(s) for s in chem.SPECIES
              if water._charge(s) > 0)
    an = sum(-m[s] * water._charge(s) for s in chem.SPECIES
             if water._charge(s) < 0)
    deficit = an - cat                       # +ve means cations are missing

    as_pub, bind = ceiling_with(water, T_hot, T_cold, pH=pH, limits=limits)
    na = dataclasses.replace(water, name=water.name + " [Na closure]",
                             Na=water.Na + deficit * 22.99 * 1000.0)
    cl = dataclasses.replace(water, name=water.name + " [Cl closure]",
                             Cl=max(water.Cl - deficit * 35.45 * 1000.0, 0.0))
    c_na, _ = ceiling_with(na, T_hot, T_cold, pH=pH, limits=limits)
    c_cl, _ = ceiling_with(cl, T_hot, T_cold, pH=pH, limits=limits)

    lo, hi = min(as_pub, c_na, c_cl), max(as_pub, c_na, c_cl)
    return {
        "imbalance_pct": water.charge_balance_pct(),
        "cation_deficit_meq_kg": deficit * 1000.0,
        "closes_with_NH4_mg_l_as_N": deficit * 14.007 * 1000.0,
        "ceiling_as_published": as_pub,
        "ceiling_Na_closure": c_na,
        "ceiling_Cl_closure": c_cl,
        "binding_mineral": bind,
        "spread_cycles": hi - lo,
        "spread_pct": 100.0 * (hi - lo) / lo if lo else 0.0,
        "material": (hi - lo) > 0.25,
    }


# ---------------------------------------------------------------------------
# The same discipline, applied to OUR OWN product.
# ---------------------------------------------------------------------------
def controller_break_even_capex(annual_saving_usd, target_payback_years,
                                annual_licence_usd=0.0, discount_rate=0.0):
    """The most the Mizan controller may cost installed and still pay back.

    WHY THIS EXISTS, AND WHY IT IS NOT A PAYBACK NUMBER.

    A payback needs an installed cost. We do not have one -- there is no
    hardware, no quotation, and no comparable. A second sweep of the Wayback
    PDF collection (docs/chemistry_evidence.md S4.4) ran fifteen queries
    across cost, controls and retrofit terms and returned hundreds of results
    and NOTHING CITABLE on the installed cost of a cooling-tower supervisory
    controller. The figures appear to be commercial and unpublished.

    So the honest move is the one this module already makes for side-stream
    treatment: invert the question. Not "what is the payback?", which needs a
    number we would have to invent, but "what is the most this may cost and
    still pay?", which needs only the saving -- and the saving is what this
    package computes.

    It converts the weakest slide in the deck from an invented IRR into a
    procurement constraint we can actually defend in a room: quote the build
    below this and the economics close.

    An annual licence is subtracted from the annual benefit BEFORE the capex
    is sized, because a licence is a recurring cost and capitalising it would
    flatter the answer. `discount_rate` is offered for completeness and
    defaults to zero: at a three-year horizon the discounting is smaller than
    the uncertainty on the saving itself, and a discounted figure would imply
    a precision this input does not have.
    """
    net = float(annual_saving_usd) - float(annual_licence_usd)
    if net <= 0.0:
        return {
            "net_annual_benefit_usd": net,
            "break_even_capex_usd": 0.0,
            "pays": False,
            "note": ("the licence alone exceeds the saving; no installed cost "
                     "is low enough, including zero"),
        }
    n, r = float(target_payback_years), float(discount_rate)
    factor = n if r == 0.0 else (1.0 - (1.0 + r) ** -n) / r
    return {
        "net_annual_benefit_usd": net,
        "annual_licence_usd": float(annual_licence_usd),
        "target_payback_years": n,
        "discount_rate": r,
        "break_even_capex_usd": net * factor,
        "pays": True,
        "note": ("maximum installed cost at which the stated payback is met. "
                 "NOT a price and NOT a cost estimate -- a ceiling on one."),
    }
