"""
FURQAN / MIZAN :: the corrosion term the optimiser did not have.
================================================================

WHY THIS EXISTS, AND WHY IT IS THE MOST DANGEROUS GAP THE PACKAGE HAD.

This controller has exactly two chemical levers and it pushes both of them in
the direction that corrodes the plant:

    RAISE CYCLES   -> chloride and sulfate concentrate together
    DOSE ACID      -> bicarbonate alkalinity is destroyed and replaced by
                      sulfate

Until this module existed the only corrosion term in the package was
`controller.CORROSION_FLOOR_SI`, which holds SI_calcite above a small positive
value so a protective calcium-carbonate film survives. That is a real
mechanism with a named provenance -- it is what Langelier's 1936 paper was FOR,
and a plant chemist in our own customer discovery holds LSI at 0.8-1.0 for
exactly that reason -- but it is a thin defence and the published consensus is
that it is not enough on its own.

The aggressive-anion side had no representation at all. This module adds it.

    Langelier, W.F. (1936) "The Analytical Control of Anti-Corrosion Water
    Treatment", J. AWWA 28(10), 1500-1521. doi:10.1002/j.1551-8833.1936.tb13785.x

THE STATEMENT THAT MATTERS MOST FOR THE PITCH, and it is not ours:

    "This index [LSI] was originally designed to predict calcium carbonate
     scale in potable water. There are serious deficiencies in the accuracy of
     this index; consequently, IT HAS LOST ITS PRACTICAL APPLICATION FOR
     COOLING WATER SYSTEMS."
        -- UFC 3-230-13 S5-3.4.1, US Department of Defense, 1 March 2023

A US defence standard says the incumbent index does not work for our
application. We have been making that argument from first principles; it turns
out we can make it by citation. [C, verified from the document text]

AND THE MECHANISM, ALSO NOT OURS:

    "chemical additions of sulfuric acid can yield higher sulfate levels than
     those species cycled up naturally."
        -- UFC 3-230-13 S5-2.1.2.2  [C, verified]

    "The use of acid in cooling towers may not be appropriate for use at
     military installations due to the associated risk of corrosion."
        -- UFC 3-230-13 S5-3.5.1  [C, verified]

Source: UFC 3-230-13, *Industrial Water Treatment Operation and Maintenance*,
US DoD, 1 March 2023, https://www.wbdg.org/FFC/DOD/UFC/ufc_3_230_13_2023.pdf
Supersedes UFC 3-240-13FN (2005).

WHAT THIS MODULE REFUSES TO DO.

It does not predict a corrosion RATE. Nothing here has seen a coupon, and a
rate needs metallurgy, velocity, oxygen, temperature and an inhibitor
programme, none of which this package models. It computes published INDICES
and reports which band they fall in, with the calibration envelope of each one
attached -- because the single most likely way to misuse this file is to
evaluate a Gulf tower at pH 8.6 and 44 C with an index whose underlying data
stopped at pH 8.3 and room temperature.
"""

from __future__ import annotations

import math

import chemistry as chem

# Equivalent weights, g/eq. Arithmetic, not a citation.
_EQ_WEIGHT = {"Cl": 35.453, "SO4": 48.031, "HCO3": 61.017, "CO3": 30.005}


# ---------------------------------------------------------------------------
# Larson-Skold
# ---------------------------------------------------------------------------
LARSON_SKOLD_SOURCE = (
    "Larson, T.E. and Skold, R.V. (1958) 'Laboratory Studies Relating Mineral "
    "Quality of Water to Corrosion of Steel and Cast Iron', Corrosion 14(6), "
    "43-46. doi:10.5006/0010-9312-14.6.43")

LARSON_SKOLD_BANDS = ((0.8, "chlorides and sulfate probably will not interfere "
                            "with natural film formation"),
                      (1.2, "chlorides and sulfates may interfere with natural "
                            "film formation; higher-than-desired corrosion "
                            "rates might be anticipated"),
                      (math.inf, "tendency toward high corrosion rates of a "
                                 "local type should be expected as the index "
                                 "increases"))
"""The 0.8 / 1.2 band set.

CHOSEN, NOT OBVIOUS. At least three threshold sets circulate under Larson and
Skold's name -- 0.2/0.6 (ChemTreat's handbook), <0.3 (Florida Water Resources
Journal's recommendation table) and 0.8/1.2. The 1958 paper itself is behind
AMPP's paywall and we have NOT read it, so which set is the authors' own is
UNVERIFIED.

0.8/1.2 is used here because two independent sources attribute it explicitly
to the 1958 criteria and one of them is a US federal document:

  US Bureau of Reclamation, water-quality evaluation documentation, p. 13
  https://www.usbr.gov/tsc/techreferences/mands/mands-pdfs/WQeval_documentation.pdf

  Hill, C.P. (2020) 'The Role of Corrosion Indices in Establishing Effective
  Corrosion Control Treatment', Florida Water Resources Journal, Nov 2020,
  34-40. https://fwrj.com/techarticles/1120%20t2.pdf

The threshold is a parameter for exactly this reason. A site that believes
0.3 should pass 0.3.
"""

# The conditions the 1958 data was taken under. Everything outside this is
# extrapolation, and a Gulf cooling tower is outside it on two axes at once.
LARSON_SKOLD_VALIDITY = {
    "pH": (6.8, 8.3),
    "T_c": (15.0, 30.0),            # "room temperature"
    "velocity_m_s": (0.03, 0.30),   # 0.1-1.0 ft/s
    "metals": ("mild steel", "cast iron"),
    "note": ("Derived from in-situ corrosion of mild steel lines carrying "
             "GREAT LAKES water. USBR: 'Because the L&SkI is an empirical "
             "correlation, its utility for describing corrosion for other "
             "types of water is questionable.' There is no temperature term "
             "and no velocity term in the index at all, and no published "
             "basis for applying it to stainless steel or copper alloys."),
}


def larson_skold_index(water):
    """Ratio of aggressive to film-forming anions, on an equivalents basis.

        LSkI = (epm Cl + epm SO4) / (epm HCO3 + epm CO3)

    The divalent charge on sulfate is already carried by the equivalent
    weight; the '2x sulfate' some secondary sources mention is that, not an
    extra factor.
    """
    num = (water.Cl / _EQ_WEIGHT["Cl"]) + (water.SO4 / _EQ_WEIGHT["SO4"])
    den = water.HCO3 / _EQ_WEIGHT["HCO3"]
    if den <= 0.0:
        return float("inf")     # no film-forming alkalinity left at all
    return num / den


def larson_skold_verdict(water, pH=None, T_c=None, velocity_m_s=None):
    """The index, its band, and whether the index is entitled to an opinion."""
    v = larson_skold_index(water)
    band = next(text for edge, text in LARSON_SKOLD_BANDS if v < edge
                or edge == math.inf)
    outside = []
    lo, hi = LARSON_SKOLD_VALIDITY["pH"]
    if pH is not None and not (lo <= pH <= hi):
        outside.append(f"pH {pH:.2f} outside the calibration range {lo}-{hi}")
    lo, hi = LARSON_SKOLD_VALIDITY["T_c"]
    if T_c is not None and not (lo <= T_c <= hi):
        outside.append(f"{T_c:.1f} C outside the calibration range {lo}-{hi}")
    lo, hi = LARSON_SKOLD_VALIDITY["velocity_m_s"]
    if velocity_m_s is not None and not (lo <= velocity_m_s <= hi):
        outside.append(f"{velocity_m_s:.2f} m/s outside {lo}-{hi}")
    return {
        "index": v,
        "band": band,
        "corrosive": v > 1.2,
        "marginal": 0.8 <= v <= 1.2,
        "in_calibration_envelope": not outside,
        "outside_because": outside,
        "applies_to": LARSON_SKOLD_VALIDITY["metals"],
        "source": LARSON_SKOLD_SOURCE,
    }


# ---------------------------------------------------------------------------
# Ryznar and Puckorius -- the two indices UFC prefers over LSI
# ---------------------------------------------------------------------------
def ryznar_index(water, T_c, pH=None):
    """RSI = 2*pHs - pH.  Ryznar (1944) J.AWWA 36(4), 472-483.

    Below 6 scale-forming, 6-7 equilibrium, above 7 undersaturated and mildly
    aggressive to steel. UFC 3-230-13 S5-3.4.1 gives the simpler cut at 6.
    """
    pH = chem.ph_atmospheric_equilibrium(water, T_c) if pH is None else pH
    lsi = chem.langelier_index(water, T_c, pH=pH)
    pHs = pH - lsi
    return 2.0 * pHs - pH


def equilibrium_ph(water):
    """pH_eq = 1.465 log10(M-alkalinity as CaCO3) + 4.54.

    Puckorius & Brooke (1991), Corrosion 47(4), 280-284,
    doi:10.5006/1.3585256, as reproduced in UFC 3-230-13 S5-3.4.2.

    WHY THIS EXISTS AT ALL, and it is precisely our operating regime. UFC:
    'The measured pH does not always relate correctly to bicarbonate
    alkalinity because of the buffering effect of other ions. Rather than
    using the measured pH in calculating the PSI, an adjusted or equilibrium
    pH is used.' Under acid feed at high cycles, measured pH and bicarbonate
    alkalinity DECOUPLE -- which is the one condition this controller
    deliberately creates.

    [C for the formula's provenance; the 1.465/4.54 coefficients did not
    survive text extraction from the UFC PDF and are taken from the widely
    reproduced form. Tagged rather than silently trusted.]
    """
    alk_caco3 = water.HCO3 * 50.04 / 61.017
    if alk_caco3 <= 0.0:
        return float("nan")
    return 1.465 * math.log10(alk_caco3) + 4.54


def puckorius_index(water, T_c, pH=None):
    """PSI = 2*pHs - pH_eq.

    NOTE THE SIGN. ChemTreat's handbook prints this inverted as
    2*pH_eq - pHs. UFC 3-230-13 gives 2*pHs - pH_eq in two places and that is
    what the original does.
    """
    pH = chem.ph_atmospheric_equilibrium(water, T_c) if pH is None else pH
    lsi = chem.langelier_index(water, T_c, pH=pH)
    pHs = pH - lsi
    return 2.0 * pHs - equilibrium_ph(water)


# ---------------------------------------------------------------------------
# What a coupon is allowed to read
# ---------------------------------------------------------------------------
CORROSION_RATE_BANDS_MPY = {
    "mild_steel_piping": ((1.0, "excellent"), (3.0, "good"), (5.0, "fair"),
                          (10.0, "poor"), (math.inf, "unacceptable")),
    "mild_steel_hx_tubing": ((0.2, "excellent"), (0.5, "good"), (1.0, "fair"),
                             (1.5, "poor"), (math.inf, "unacceptable")),
    "copper_and_copper_alloys": ((0.1, "excellent"), (0.2, "good"),
                                 (0.3, "fair"), (0.5, "poor"),
                                 (math.inf, "unacceptable")),
    "galvanized_steel": ((2.0, "excellent"), (4.0, "good"), (8.0, "fair"),
                         (10.0, "poor"), (math.inf, "unacceptable")),
    "stainless_steel": ((0.1, "acceptable"), (math.inf, "unacceptable")),
}
"""UFC 3-230-13 Table 5-9, 90-day corrosion coupon test. [C, verified from the
document text.]

Carried as the ACCEPTANCE CRITERIA for the field trial this package cannot yet
run, not as something the model predicts. Nothing here has seen a coupon.

UFC's own note, and it is the one that decides a trial: 'Determine pitting on
coupons by visual observation; ANY PITTING IS UNACCEPTABLE.' A rate inside
band with pits is a failure.

Corroborated independently by Boffardi, B.P., 'Standards for Corrosion Rates',
Association of Water Technologies Technical Committee, Cooling Water
Subcommittee, whose open-recirculating table gives the same carbon-steel
bands and copper within 0.05 mpy.
"""


def rate_verdict(mpy, metal="mild_steel_hx_tubing"):
    """Which band a measured coupon rate falls in."""
    if metal not in CORROSION_RATE_BANDS_MPY:
        raise ValueError(f"unknown metal {metal!r}; "
                         f"choose from {sorted(CORROSION_RATE_BANDS_MPY)}")
    for edge, label in CORROSION_RATE_BANDS_MPY[metal]:
        if mpy < edge:
            return label
    return "unacceptable"


# ---------------------------------------------------------------------------
# The finding this module was built to produce
# ---------------------------------------------------------------------------
def lever_conflict(makeup, cycles_lo, cycles_hi, T_c=40.0):
    """Both of the controller's levers push the aggressive-anion ratio UP.

    This is the substance of the EPRI concern, expressed as arithmetic:

      * raising cycles concentrates Cl and SO4 AND HCO3 together, so the ratio
        itself is cycles-invariant -- concentrating a water does not change
        the ratio of its anions;
      * dosing acid destroys HCO3 and leaves SO4 behind, so it moves the
        ratio and nothing else in the loop does.

    So the corrosion risk from this controller is carried almost entirely by
    the ACID lever, not the cycles lever -- which is the opposite of what the
    'raises cycles AND doses acid' framing suggests, and it matters because
    the two are separately switchable. A site that forbids acid (Jubail, under
    RCER) takes none of this risk.

    Returns the index at both cycle counts and the acid-driven change.
    """
    lo = larson_skold_index(makeup.concentrate(cycles_lo))
    hi = larson_skold_index(makeup.concentrate(cycles_hi))
    return {
        "cycles_lo": float(cycles_lo), "cycles_hi": float(cycles_hi),
        "larson_skold_lo": lo, "larson_skold_hi": hi,
        "cycles_effect": hi - lo,
        "cycles_effect_is_negligible": abs(hi - lo) < 1e-9,
        "note": ("Concentrating a water multiplies every ion by the same "
                 "factor, so a RATIO of ions cannot move with cycles. Acid is "
                 "the only lever in this controller that moves Larson-Skold, "
                 "and it moves it the wrong way."),
    }


def acid_driven_index(makeup, cycles, alkalinity_destroyed_frac):
    """Larson-Skold after acid has removed a fraction of the alkalinity.

    Sulfuric acid converts HCO3 to CO2 and leaves SO4 in the water, so the
    numerator RISES as the denominator FALLS. Both halves are modelled; a
    treatment that only dropped the alkalinity would understate the effect.
    """
    f = min(max(float(alkalinity_destroyed_frac), 0.0), 1.0)
    conc = makeup.concentrate(cycles)
    # mg/L divided by g/mol is MILLImol/L, so the sulfate falls straight out
    # in mg/L with no further scaling. Getting this wrong by 1000 produced a
    # first draft that reported 100,000 mg/L of sulfate and an index of 339.
    hco3_removed_mmol = (conc.HCO3 * f) / 61.017
    #   2 HCO3- + H2SO4 -> 2 CO2 + 2 H2O + SO4(2-)
    so4_added_mg = hco3_removed_mmol * 0.5 * 96.06
    import dataclasses
    dosed = dataclasses.replace(
        conc, name=conc.name + f" [{100*f:.0f} % alkalinity acidified]",
        HCO3=conc.HCO3 * (1.0 - f), SO4=conc.SO4 + so4_added_mg)
    return {
        "alkalinity_destroyed_frac": f,
        "HCO3_mg_l": dosed.HCO3,
        "SO4_mg_l": dosed.SO4,
        "larson_skold": larson_skold_index(dosed),
        "water": dosed,
    }


# ---------------------------------------------------------------------------
# The cycles-dependent half: chloride pitting, which IS a concentration limit
# ---------------------------------------------------------------------------
CHLORIDE_LIMITS_MG_L = {
    "304_stainless": 150.0,
    "316_stainless": 400.0,
}
"""Maximum chloride for austenitic stainless condenser tubing.

Buecker, B. (ChemTreat) and Janikowski, D. (Plymouth Tube), 'How much
chloride? Power Plant Heat Exchanger Materials Selection', Power Engineering,
10 October 2019. Underlying technical paper: Janikowski, D.S., 'Factors for
Selecting Reliable Heat Exchanger Tube Materials', 33rd Electric Utility
Chemistry Workshop, University of Illinois, 11-13 June 2013. Basis is PREn
against critical crevice temperature by ASTM G48.

FOUR CAVEATS THAT TRAVEL WITH THE NUMBERS, from the source:
  * basis is neutral pH, 35 C, FLOWING water
  * lower the limit if T > 35 C -- our skin runs at 44 C
  * lower the limit if pH < 7
  * 'limits assume clean surfaces because deposits allow significantly higher
    LOCALIZED concentrations' -- a scaling controller and a pitting limit are
    coupled, and not in our favour

Janikowski also records these are about half what was accepted twenty years
ago (304 was 200 ppm, 316 was 1000 ppm), attributed to modern heats sitting at
minimum ASTM Cr/Ni/Mo rather than to new corrosion data.

NO NUMERIC CHLORIDE LIMIT was found for admiralty brass or copper-nickel in
any source consulted; those alloys are governed in practice by a corrosion
RATE limit and by velocity, not a chloride threshold. Absent, not zero.
"""


def chloride_pitting_check(makeup, cycles, alloy="316_stainless"):
    """Does the loop chloride exceed the pitting limit for this tubing?

    THIS is the cycles-dependent corrosion risk, and it is the one the
    Larson-Skold ratio cannot see. A ratio is scale-invariant, so cycles do
    not move it at all; an absolute concentration limit is the opposite --
    cycles move it proportionally and acid does not move it at all.

    So the two corrosion terms in this module partition the controller's two
    levers exactly: acid owns Larson-Skold, cycles own chloride pitting.
    Neither lever is free, and they are not free in the same way.
    """
    if alloy not in CHLORIDE_LIMITS_MG_L:
        raise ValueError(f"no published chloride limit held for {alloy!r}; "
                         f"have {sorted(CHLORIDE_LIMITS_MG_L)}")
    limit = CHLORIDE_LIMITS_MG_L[alloy]
    cl = makeup.Cl * float(cycles)
    return {
        "alloy": alloy,
        "cycles": float(cycles),
        "chloride_mg_l": cl,
        "limit_mg_l": limit,
        "exceeds": cl > limit,
        "margin_mg_l": limit - cl,
        "max_cycles_on_chloride": (limit / makeup.Cl) if makeup.Cl > 0
                                  else float("inf"),
        "caveat": ("limit is quoted at neutral pH, 35 C and clean surfaces; "
                   "a hotter skin, a lower pH or any deposit all reduce it"),
    }


def main() -> int:
    import run_controller as rc

    waters = [("Riyadh measured TSE", chem.ARAMCO_RIYADH_REFINERY_TSE),
              ("Dhahran field-validated", chem.ARAMCO_FIELD_VALIDATED),
              ("Aramco reclaimed", chem.ARAMCO_RECLAIMED)]
    print("=" * 78)
    print("CORROSION -- the term the optimiser did not have")
    print("=" * 78)
    print("\nLarson-Skold index, (Cl + SO4) / (HCO3 + CO3) on equivalents\n")
    print(f"{'water':28}{'LSkI':>8}{'band':>12}   in envelope?")
    for name, w in waters:
        v = larson_skold_verdict(w, pH=8.25, T_c=44.5)
        tag = ("CORROSIVE" if v["corrosive"] else
               "marginal" if v["marginal"] else "ok")
        print(f"{name:28}{v['index']:>8.2f}{tag:>12}   "
              f"{'yes' if v['in_calibration_envelope'] else 'NO -- ' + '; '.join(v['outside_because'])}")

    print("\n\nWHICH LEVER CARRIES THE RISK\n")
    w = chem.ARAMCO_RIYADH_REFINERY_TSE
    lc = lever_conflict(w, 3.0, 6.0)
    print(f"  cycles 3.0 -> 6.0 moves Larson-Skold by {lc['cycles_effect']:+.4f}")
    print(f"  ...because {lc['note']}")
    print()
    print(f"  {'alkalinity acidified':>22}{'HCO3':>9}{'SO4':>9}{'LSkI':>9}")
    for f in (0.0, 0.25, 0.50, 0.75, 0.90):
        a = acid_driven_index(w, 3.0, f)
        print(f"  {100*f:>21.0f} %{a['HCO3_mg_l']:>9.1f}{a['SO4_mg_l']:>9.1f}"
              f"{a['larson_skold']:>9.2f}")
    print("\n\nTHE OTHER HALF -- chloride pitting, which cycles DO move\n")
    print(f"  {'water':28}{'alloy':>16}{'Cl at 3 cy':>12}{'max cycles':>12}")
    for name, wx in waters:
        for alloy in ("304_stainless", "316_stainless"):
            c = chloride_pitting_check(wx, 3.0, alloy)
            flag = "  EXCEEDED" if c["exceeds"] else ""
            print(f"  {name:28}{alloy:>16}{c['chloride_mg_l']:>12.0f}"
                  f"{c['max_cycles_on_chloride']:>12.2f}{flag}")
    print()
    print("  A ratio is scale-invariant, so cycles cannot move Larson-Skold.")
    print("  A concentration limit is the opposite. The two terms partition")
    print("  the controller's two levers exactly: ACID owns Larson-Skold,")
    print("  CYCLES own chloride pitting. Neither lever is free.")
    print("\n  The acid lever is the whole of the corrosion exposure, and it is")
    print("  separately switchable. A Jubail site under RCER cannot dose acid")
    print("  at all, so it takes none of this risk -- the regulation that")
    print("  costs us the acid lever also removes the objection to it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
