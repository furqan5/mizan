"""
MIZAN :: sulfate exposure of a concrete basin -- REPORTED, not imposed
======================================================================

THE GAP. `docs/robustness_gaps.md` section 10: the loop concentrates sulfate,
cooling-tower basins are commonly concrete, sulfate attacks cement paste through
ettringite and gypsum formation, and the controller had no concrete-durability
term. The gap was left open because the thresholds circulating informally had
no citation. These do.

THE THRESHOLDS, AND EXACTLY HOW FAR EACH WAS VERIFIED.

ACI 318-19 Table 19.3.1.1, exposure category S, "dissolved sulfate (SO4 2-) in
water, ppm" (determined by ASTM D516 or D4130):

    S0   SO4 < 150
    S1   150 <= SO4 < 1,500   (or seawater)
    S2   1,500 <= SO4 <= 10,000
    S3   SO4 > 10,000

  Verified from two reproductions, not from the code itself (paywalled):
  (1) Obla & Lobo, "Selecting Exposure Classes and Requirements for
      Durability", Concrete International, May 2023, "Table 4: Exposure
      classes for sulfate exposure (based on Table 19.3.1.1)", copy provided
      with permission from ACI, hosted by NRMCA:
      https://www.nrmca.org/wp-content/uploads/ACI_CI_NRMCA_Guide-to-Selecting_Exposure_Classes.pdf
      S0, S1 and S3 read as above. ITS S2 WATER CELL IS A TYPESETTING ERROR --
      it repeats S1's "150 <= SO4 < 1500" -- so S2 is not taken from it.
  (2) ACI CRC 117 final report to the ACI Foundation (Ideker, Drimalas,
      Kurtis, Thomas et al., 13 July 2020), "Table 9: Sulfate exposure class
      table": "S2 Severe ... 1500 <= SO4 <= 10,000", "S3 Very severe ... >
      10,000", consistent with (1):
      https://www.acifoundation.org/Portals/12/Files/PDFs/RecommendationsforUnifiedDurabilityGuidance_CRC117.pdf
  Cement requirements, ACI 318-19 Table 19.3.2.1 via (1) Table 5: S1 w/cm
  0.50, ASTM C150 Type II; S2 w/cm 0.45, Type V; S3 Type V plus pozzolan or
  slag at w/cm 0.45, or Type V at 0.40. (Type I or III is permitted in S1/S2
  if C3A is below 8 % / 5 %; not modelled.)

EN 206 Table 2, "limiting values for exposure classes for chemical attack from
natural soil and ground water", SO4 2- in ground water, mg/L:

    XA1  >= 200 and <= 600
    XA2  >  600 and <= 3,000
    XA3  > 3,000 and <= 6,000

  Verified from Whittaker & Black (2015), "Current knowledge of external
  sulfate attack", Advances in Cement Research, Table 1, "Limiting value for
  exposure classes for chemical attack from groundwater (BS EN 206:2013, BSI,
  2013)", University of Leeds deposit:
  https://eprints.whiterose.ac.uk/id/eprint/84114/
  The numbers are read directly. The INEQUALITY AT EACH BOUNDARY is decoded
  from the PDF's symbol font (the same glyph mapping reads the pH row as
  "<= 6.5 and >= 5.5", which is the familiar XA1 pH range) and is therefore
  [UNVERIFIED at the boundary]. Above 6,000 mg/L the table does not classify.
  The table's scope -- natural ground water, and as usually quoted 5-25 C and
  near-static flow -- is [UNVERIFIED]; a 30 C circulating basin is outside
  that scope on both counts, in the more aggressive direction.

UNITS. ACI writes ppm (mass/mass) and EN 206 mg/L (mass/volume). At cooling-
water salinity the density is within about half a per cent of 1 kg/L, so they
are treated as equal, and the helpers take mg/L.

WHY REPORTED AND NOT IMPOSED. The limit is a property of the concrete -- its
cement and w/cm -- and this package cannot know what a stranger's basin is made
of. So the constraint binds only when a site DECLARES basin material and cement
type. Undeclared means INACTIVE, which is not the same as satisfied: the report
still prints the exposure class the water puts the basin in.
"""
from __future__ import annotations

import math

INF = math.inf

ACI_318_19_SULFATE_WATER = (          # class, lower, upper, severity
    ("S0", 0.0, 150.0, "not applicable"),
    ("S1", 150.0, 1500.0, "moderate"),
    ("S2", 1500.0, 10000.0, "severe"),
    ("S3", 10000.0, INF, "very severe"),
)
EN_206_XA_SULFATE_GROUNDWATER = (
    (None, 0.0, 200.0, "below XA1"),
    ("XA1", 200.0, 600.0, "slightly aggressive"),
    ("XA2", 600.0, 3000.0, "moderately aggressive"),
    ("XA3", 3000.0, 6000.0, "highly aggressive"),
    ("beyond XA3", 6000.0, INF, "outside EN 206 Table 2"),
)

ACI_ORDER = ("S0", "S1", "S2", "S3")
# ACI 318-19 Table 19.3.2.1 (cementitious type only; w/cm is not checked here)
CEMENT_MAX_ACI_CLASS = {
    "ASTM_C150_TYPE_I": "S0",
    "ASTM_C150_TYPE_III": "S0",
    "ASTM_C150_TYPE_II": "S1",
    "ASTM_C595_MS": "S1",
    "ASTM_C1157_MS": "S1",
    "ASTM_C150_TYPE_V": "S2",
    "ASTM_C595_HS": "S2",
    "ASTM_C1157_HS": "S2",
    "ASTM_C150_TYPE_V_PLUS_POZZOLAN_OR_SLAG": "S3",
}

SOURCES = {
    "aci_318_19": "ACI 318-19 Table 19.3.1.1 via Concrete International May "
                  "2023 (Obla & Lobo, NRMCA) and ACI CRC 117 Table 9",
    "en_206": "EN 206 Table 2 via Whittaker & Black (2015), Adv. Cem. Res., "
              "Table 1 (BS EN 206:2013); boundary inequalities UNVERIFIED",
}


def aci_318_class(so4_mg_l):
    x = float(so4_mg_l)
    if x < 150.0:
        return "S0"
    if x < 1500.0:
        return "S1"
    if x <= 10000.0:
        return "S2"
    return "S3"


def en_206_class(so4_mg_l):
    x = float(so4_mg_l)
    if x < 200.0:
        return None
    if x <= 600.0:
        return "XA1"
    if x <= 3000.0:
        return "XA2"
    if x <= 6000.0:
        return "XA3"
    return "beyond XA3"


def concrete_sulfate_exposure(so4_mg_per_l):
    """Exposure classes of concrete in contact with water at this sulfate."""
    return {"so4_mg_l": float(so4_mg_per_l),
            "aci_318_19": aci_318_class(so4_mg_per_l),
            "en_206": en_206_class(so4_mg_per_l),
            "sources": SOURCES}


def acid_sulfate_mg_l(makeup, cycles, target_ph, T_c):
    """Sulfate the acid dose ADDS to the circulating water at steady state.

    `controller.acid_dose_for_ph` returns kg H2SO4 per kg circulating water;
    each mole of acid leaves one mole of sulfate (diprotic acid, 2 eq of
    alkalinity per mole), so the circulating increment is that dose x
    MW_SO4/MW_H2SO4. No defect-25 multiplier here: this is a concentration in
    the loop, not a flow rate.
    """
    import controller as ctl
    kg_per_kg, _ = ctl.acid_dose_for_ph(makeup, float(cycles), float(target_ph),
                                        float(T_c))
    return kg_per_kg * 96.06 / 98.079 * 1e6


def basin_sulfate_mg_l(makeup, cycles, target_ph=None, T_c=30.0):
    s = makeup.SO4 * float(cycles)
    if target_ph is not None:
        s += acid_sulfate_mg_l(makeup, cycles, target_ph, T_c)
    return s


BOUNDARIES = (("ACI S1", 150.0), ("ACI S2", 1500.0), ("ACI S3", 10000.0),
              ("EN XA1", 200.0), ("EN XA2", 600.0), ("EN XA3", 3000.0),
              ("EN beyond XA3", 6000.0))


def cycles_at_class_boundaries(makeup_so4_mg_l, makeup=None, target_ph=None,
                               T_c=30.0, hi=60.0):
    """Cycles at which basin water crosses each class boundary.

    With only a makeup sulfate this is boundary / makeup_SO4, sulfate being
    conservative. With `makeup` and `target_ph` it includes the sulfate the
    acid dose adds, which moves every boundary to fewer cycles. A value below
    1.0 means the makeup itself is already past that boundary. Gypsum
    precipitation, which would cap sulfate, is not modelled.
    """
    out = {}
    so4 = float(makeup_so4_mg_l)
    for name, b in BOUNDARIES:
        if makeup is None or target_ph is None:
            out[name] = b / so4 if so4 > 0 else INF
            continue
        from scipy.optimize import brentq

        def f(c):
            return basin_sulfate_mg_l(makeup, c, target_ph, T_c) - b
        if f(1.0) >= 0:
            out[name] = b / so4
        elif f(hi) < 0:
            out[name] = INF
        else:
            out[name] = float(brentq(f, 1.0, hi, xtol=1e-6))
    return out


def concrete_sulfate_constraint(makeup, cycles, basin_material=None,
                                cement_type=None, target_ph=None, T_c=30.0):
    """The concrete-sulfate limit as a REPORTED constraint.

    Binds only when the site declares `basin_material="concrete"` AND a
    `cement_type` from CEMENT_MAX_ACI_CLASS. Otherwise `active` is False and
    `binds` is None: inactive, not satisfied.
    """
    so4 = basin_sulfate_mg_l(makeup, cycles, target_ph, T_c)
    out = {"cycles": float(cycles), "so4_mg_l": so4,
           "exposure": concrete_sulfate_exposure(so4),
           "boundaries_cycles": cycles_at_class_boundaries(
               makeup.SO4, makeup, target_ph, T_c),
           "active": False, "binds": None, "max_cycles": None,
           "basin_material": basin_material, "cement_type": cement_type}
    if basin_material is None:
        out["status"] = ("INACTIVE: basin material not declared. Inactive is "
                         "not satisfied.")
        return out
    if str(basin_material).lower() != "concrete":
        out["status"] = f"not applicable to a {basin_material} basin"
        return out
    if cement_type not in CEMENT_MAX_ACI_CLASS:
        out["status"] = ("INACTIVE: concrete basin declared but cement type "
                         "not declared or not recognised")
        return out
    permitted = CEMENT_MAX_ACI_CLASS[cement_type]
    nxt = ACI_ORDER.index(permitted) + 1
    if nxt >= len(ACI_ORDER):
        max_c = INF
    else:
        max_c = out["boundaries_cycles"][f"ACI {ACI_ORDER[nxt]}"]
    out.update({"active": True, "permitted_aci_class": permitted,
                "max_cycles": max_c, "binds": float(cycles) > max_c,
                "status": (f"{cement_type} is specified up to ACI {permitted}; "
                           f"basin water is ACI {out['exposure']['aci_318_19']}")})
    return out


def main() -> int:
    import chemistry as chem
    w = chem.ARAMCO_FIELD_VALIDATED
    print(f"makeup: {w.name}, SO4 {w.SO4:g} mg/L")
    print("class boundaries, cycles (no acid):")
    for k, v in cycles_at_class_boundaries(w.SO4).items():
        print(f"  {k:14s} {v:6.2f}")
    print("class boundaries, cycles (acid to pH 8.0 at 30 C):")
    for k, v in cycles_at_class_boundaries(w.SO4, w, 8.0, 30.0).items():
        print(f"  {k:14s} {v:6.2f}")
    for c in (3.0, 5.0, 6.0):
        for ph in (None, 8.0):
            r = concrete_sulfate_constraint(w, c, target_ph=ph)
            print(f"  {c:g} cycles, acid {'to pH '+str(ph) if ph else 'none':10s}: "
                  f"SO4 {r['so4_mg_l']:7.0f} mg/L  ACI {r['exposure']['aci_318_19']}"
                  f"  EN {r['exposure']['en_206']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
