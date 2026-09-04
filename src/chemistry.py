"""
MIZAN :: cooling-water hydrochemistry
=====================================
Ion-association speciation and mineral saturation for recirculating cooling
water. Every equilibrium constant is taken directly from the USGS PHREEQC
`phreeqc.dat` thermodynamic database. That choice is deliberate: it makes
this engine checkable against PHREEQC, the accepted reference
implementation, rather than against a correlation of our own devising.

Why not the Langelier index, as the industry does
-------------------------------------------------
LSI is a single-mineral (calcite), low-ionic-strength index built for
potable water. Gulf cooling loops running treated sewage effluent at high
cycles are neither: ionic strength is an order of magnitude higher, and the
binding constraint is frequently gypsum or amorphous silica, which LSI
cannot represent at all. `langelier_index` is implemented only so the two
can be compared quantitatively.

Why skin temperature, not bulk
------------------------------
Precipitation occurs at the hottest wetted surface -- the condenser tube
wall -- which runs several kelvin above bulk water temperature. Calcite and
gypsum both become LESS soluble as temperature rises, so an index computed
at bulk temperature systematically understates risk at the surface where
scale actually forms. `saturation_state` takes an explicit temperature so
one water can be evaluated at both.

Units: input concentrations in mg/L, converted internally to molality.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq

T_K0 = 273.15

# molar mass [g/mol], charge
SPECIES = {
    "Ca":   (40.078,  2),
    "Mg":   (24.305,  2),
    "Na":   (22.990,  1),
    "K":    (39.098,  1),
    "HCO3": (61.017, -1),
    "SO4":  (96.06,  -2),
    "Cl":   (35.453, -1),
    "NO3":  (62.004, -1),
    "SiO2": (60.084,  0),
}


def log_k_calcite(T_c):
    """CaCO3 = Ca+2 + CO3-2 (Plummer & Busenberg, as in phreeqc.dat)."""
    T = T_c + T_K0
    return -171.9065 - 0.077993 * T + 2839.319 / T + 71.595 * math.log10(T)


def log_k2_carbonic(T_c):
    """HCO3- = H+ + CO3-2 (phreeqc.dat analytical expression)."""
    T = T_c + T_K0
    return (-107.8871 - 0.03252849 * T + 5151.79 / T
            + 38.92561 * math.log10(T) - 563713.9 / T ** 2)


def _vant_hoff(log_k25, delta_h_kcal, T_c):
    """van't Hoff extrapolation from 25 degC; delta_h in kcal/mol."""
    R = 8.314462
    T = T_c + T_K0
    return log_k25 - (delta_h_kcal * 4184.0) / (2.302585 * R) * (1.0 / T - 1.0 / 298.15)


def log_k_gypsum(T_c):
    """CaSO4:2H2O = Ca+2 + SO4-2 + 2H2O (phreeqc.dat analytical expression).

    DEFECT 15, fixed 4 September 2026. This was
        _vant_hoff(-4.58, -0.109, T_c)
    A single-enthalpy van't Hoff is MONOTONIC BY CONSTRUCTION, and the comment
    at MINERAL_EVAL_POINT below has always said gypsum has a "maximum near
    35-40 C". That form cannot produce a maximum anywhere. Measured: strictly
    decreasing over 10-80 C, moving only 0.0105 log units across 25->70 C,
    while activity coefficients moved the full SI ~10x that in the SAME
    direction. Gypsum therefore looked LESS saturated at the hot skin than in
    the bulk -- the opposite of the mechanism this product is built on, and the
    reason the hottest condition returned the most permissive wall (defect 14).

    No new source was needed. phreeqc.dat, already cited above for calcite and
    for carbonic K2 in exactly this analytic form, supplies one for gypsum:
        Gypsum  -analytic  68.2401  0.0  -3221.51  -25.0627
    Calcite had been given this treatment from the start; gypsum had not.
    Anchored to the same log_k25 (agrees to 0.0009), it has an interior maximum
    near 23 C and 10.8x the temperature response.

    Scored against pre-registered predictions in src/gypsum_logk_upgrade.py.
    """
    T = T_c + T_K0
    return 68.2401 - 3221.51 / T - 25.0627 * math.log10(T)


def log_k_silica_am(T_c):
    """SiO2(a) + 2H2O = H4SiO4. phreeqc.dat log_k -2.71, dH +3.59 kcal.

    Positive enthalpy: amorphous silica gets MORE soluble on heating, the
    opposite of calcite and gypsum. That sign difference is why the binding
    scaling constraint can switch mineral as duty or season changes -- and
    why a single fixed conductivity setpoint cannot be correct year round.
    """
    return _vant_hoff(-2.71, 3.59, T_c)


def debye_huckel_A(T_c):
    """Debye-Huckel A parameter for water [kg^0.5 mol^-0.5]."""
    T = T_c + T_K0
    eps = 87.74 - 0.4008 * T_c + 9.398e-4 * T_c ** 2 - 1.410e-6 * T_c ** 3
    return 1.82483e6 / (eps * T) ** 1.5


def davies_gamma(z, I, T_c=25.0):
    """Davies activity coefficient. Valid to I ~ 0.5 mol/kg; beyond that a
    Pitzer treatment is required, flagged by Water.pitzer_required()."""
    A = debye_huckel_A(T_c)
    s = math.sqrt(I)
    return 10.0 ** (-A * z ** 2 * (s / (1.0 + s) - 0.3 * I))


@dataclass
class Water:
    """A cooling water. Concentrations in mg/L."""
    name: str = "water"
    Ca: float = 0.0
    Mg: float = 0.0
    Na: float = 0.0
    K: float = 0.0
    HCO3: float = 0.0
    SO4: float = 0.0
    Cl: float = 0.0
    NO3: float = 0.0
    SiO2: float = 0.0
    pH: float = 7.8
    TDS: float = None

    def molality(self):
        return {s: getattr(self, s) * 1e-3 / SPECIES[s][0] for s in SPECIES}

    def ionic_strength(self):
        m = self.molality()
        return 0.5 * sum(m[s] * SPECIES[s][1] ** 2 for s in SPECIES)

    def tds(self):
        if self.TDS is not None:
            return self.TDS
        return sum(getattr(self, s) for s in SPECIES)

    def charge_balance_pct(self):
        """Percent charge imbalance -- a data-quality check on any analysis."""
        m = self.molality()
        cat = sum(m[s] * SPECIES[s][1] for s in SPECIES if SPECIES[s][1] > 0)
        an = sum(-m[s] * SPECIES[s][1] for s in SPECIES if SPECIES[s][1] < 0)
        return 100.0 * (cat - an) / (0.5 * (cat + an)) if (cat + an) else 0.0

    def concentrate(self, cycles):
        """This water concentrated to `cycles` cycles of concentration."""
        kw = {s: getattr(self, s) * cycles for s in SPECIES}
        return Water(name=f"{self.name} x{cycles:g}", pH=self.pH,
                     TDS=(self.TDS * cycles if self.TDS is not None else None),
                     **kw)

    def pitzer_required(self):
        return self.ionic_strength() > 0.5


def saturation_state(water, T_c, pH=None):
    """Saturation indices at temperature `T_c`.

    SI = log10(IAP / Ksp). SI > 0 supersaturated (scale can form).
    """
    pH = water.pH if pH is None else pH
    m = water.molality()
    I = water.ionic_strength()
    g1 = davies_gamma(1, I, T_c)
    g2 = davies_gamma(2, I, T_c)

    a_H = 10.0 ** (-pH)
    a_HCO3 = m["HCO3"] * g1
    a_CO3 = a_HCO3 * 10.0 ** log_k2_carbonic(T_c) / a_H
    a_Ca = m["Ca"] * g2
    a_SO4 = m["SO4"] * g2

    return {
        "T_C": T_c,
        "pH": pH,
        "ionic_strength": I,
        "SI_calcite": math.log10(max(a_Ca * a_CO3, 1e-30)) - log_k_calcite(T_c),
        "SI_gypsum": math.log10(max(a_Ca * a_SO4, 1e-30)) - log_k_gypsum(T_c),
        "SI_silica_am": math.log10(max(m["SiO2"], 1e-30)) - log_k_silica_am(T_c),
        "pitzer_required": water.pitzer_required(),
    }


def langelier_index(water, T_c, pH=None):
    """Langelier Saturation Index -- the incumbent industry practice.

    Included ONLY as the comparison baseline; single-mineral and
    low-ionic-strength by construction.
    """
    pH = water.pH if pH is None else pH
    tds = max(water.tds(), 1.0)
    ca_hardness = water.Ca * 2.497          # as mg/L CaCO3
    alk = water.HCO3 * 0.8202               # as mg/L CaCO3
    A = (math.log10(tds) - 1.0) / 10.0
    B = -13.12 * math.log10(T_c + T_K0) + 34.55
    C = math.log10(max(ca_hardness, 1e-6)) - 0.4
    D = math.log10(max(alk, 1e-6))
    return pH - ((9.3 + A + B) - (C + D))


DEFAULT_LIMITS = {"SI_calcite": 0.5, "SI_gypsum": 0.0, "SI_silica_am": 0.0}


def max_cycles(makeup, T_eval, limits=None, pH=None, lo=1.0, hi=30.0, tol=1e-3):
    """Highest cycles of concentration keeping every mineral within limit at
    `T_eval`. This is the number the controller acts on."""
    limits = DEFAULT_LIMITS if limits is None else limits

    def margin(cy):
        s = saturation_state(makeup.concentrate(cy), T_eval, pH=pH)
        return min(limits[k] - s[k] for k in limits)

    if margin(lo) < 0:
        return float(lo)
    if margin(hi) > 0:
        return float(hi)
    return float(brentq(margin, lo, hi, xtol=tol))


def binding_mineral(makeup, cycles, T_eval, limits=None, pH=None):
    """Which mineral is closest to its limit at this operating point."""
    limits = DEFAULT_LIMITS if limits is None else limits
    s = saturation_state(makeup.concentrate(cycles), T_eval, pH=pH)
    return min(limits, key=lambda k: limits[k] - s[k])


# --- pH closure and analysis conditioning ---------------------------------
def log_kh_co2(T_c):
    """Henry constant for CO2, [CO2(aq)]/pCO2. phreeqc.dat CO2(g) log_k -1.468,
    delta_h -4.776 kcal."""
    return _vant_hoff(-1.468, -4.776, T_c)


def log_k1_carbonic(T_c):
    """CO2(aq) + H2O = H+ + HCO3- (phreeqc.dat analytical expression)."""
    T = T_c + T_K0
    return (-356.3094 - 0.06091964 * T + 21834.37 / T
            + 126.8339 * math.log10(T) - 1684915.0 / T ** 2)


P_CO2_ATM = 10.0 ** -3.4        # atmospheric partial pressure of CO2 [atm]


def ph_atmospheric_equilibrium(water, T_c, p_co2=P_CO2_ATM):
    """pH of a recirculating cooling water in equilibrium with air.

    A cooling tower is an intensive air stripper: the recirculating water
    is driven toward equilibrium with atmospheric CO2, which strips carbonic
    acid and RAISES pH as alkalinity concentrates. Holding pH constant while
    concentrating -- the naive assumption -- understates calcite
    supersaturation at high cycles and is the reason bench calculations
    disagree with operating plants.

        [H+] = K1 * KH * pCO2 / [HCO3-]
    """
    m_hco3 = max(water.molality()["HCO3"], 1e-12)
    log_h = log_k1_carbonic(T_c) + log_kh_co2(T_c) + math.log10(p_co2) \
        - math.log10(m_hco3)
    return -log_h


def balance_chloride(water):
    """Close a published analysis on charge balance by adjusting chloride.

    Standard practice when a reported analysis omits or misreports an ion:
    chloride is conservative, analytically robust and usually the largest
    unreported anion, so it carries the closure. The adjustment is reported
    so the assumption stays visible.
    """
    m = water.molality()
    cat = sum(m[s] * SPECIES[s][1] for s in SPECIES if SPECIES[s][1] > 0)
    an = sum(-m[s] * SPECIES[s][1] for s in SPECIES
             if SPECIES[s][1] < 0 and s != "Cl")
    m_cl_needed = max(cat - an, 0.0)
    out = Water(**{**water.__dict__})
    out.Cl = m_cl_needed * SPECIES["Cl"][0] * 1e3
    out.name = water.name + " (Cl-balanced)"
    return out


# Operating saturation limits.
#
# These are NOT pure thermodynamic limits. Calcite and gypsum precipitation
# is kinetically inhibited by antiscalant, so plants routinely run them
# supersaturated; the allowance below reflects normal phosphonate/polymer
# programmes. Amorphous silica has no effective inhibitor in general
# service, so its limit stays at thermodynamic saturation -- which is why
# silica, invisible to LSI, is usually the true ceiling on TSE at high
# cycles.
OPERATING_LIMITS = {
    "SI_calcite": 2.0,       # SR 100
    "SI_gypsum": 0.3,        # SR 2.0
    "SI_silica_am": 0.0,     # SR 1.0
}

# Published inhibitor limits, IWC-11-77 Table 7 ("Treated Limits
# Comparison"), converted from saturation ratio to log10 saturation index.
# The paper's framing matters: "Scale inhibitors have upper limits and are
# not effective above saturation level driving force, regardless of the
# inhibitor dosage." There is a ceiling that more chemical cannot buy.
#
#   species    typical SR      -> SI        stressed SR -> SI
#   calcite    135-150            2.13-2.18   200-225      2.30-2.35
#   gypsum     2.5-4.0            0.40-0.60   4.0+         >=0.60
#   silica     1.2                0.08        2.5          0.40
#
# Our defaults above sit BELOW the published typical band for all three --
# deliberately, as first-deployment margin on an uncharacterised site.
# Once a site's inhibitor programme is characterised, these are the cited
# values to move to. Never exceed the stressed column without
# inhibitor-specific vendor data.
CHARACTERISED_LIMITS = {
    "SI_calcite": 2.15,      # standard phosphonate programme
    "SI_gypsum": 0.40,       # bottom of the published typical band
    "SI_silica_am": 0.08,    # SR 1.2, standard programme
}

# Silica is the weakest link and deserves its own note. Dispersants barely
# work on it -- published evidence puts the achievable gain at roughly
# 150-200 to 180-220 ppm, "often an undetectable increase". Polymerisation
# inhibitors do better. Silica deposits need hydrofluoric acid or mechanical
# removal. Only raise SI_silica_am to 0.40 where a named polymerisation
# inhibitor is actually dosed.
SILICA_INHIBITED_LIMIT = 0.40


def max_cycles_atm(makeup, T_eval, limits=None, lo=1.0, hi=30.0, tol=1e-3):
    """Max cycles with pH resolved by atmospheric CO2 equilibrium at each
    trial concentration, rather than held at the makeup value."""
    limits = OPERATING_LIMITS if limits is None else limits

    def margin(cy):
        w = makeup.concentrate(cy)
        pH = ph_atmospheric_equilibrium(w, T_eval)
        s = saturation_state(w, T_eval, pH=pH)
        return min(limits[k] - s[k] for k in limits)

    if margin(lo) < 0:
        return float(lo)
    if margin(hi) > 0:
        return float(hi)
    return float(brentq(margin, lo, hi, xtol=tol))


def binding_mineral_atm(makeup, cycles, T_eval, limits=None):
    limits = OPERATING_LIMITS if limits is None else limits
    w = makeup.concentrate(cycles)
    s = saturation_state(w, T_eval, pH=ph_atmospheric_equilibrium(w, T_eval))
    return min(limits, key=lambda k: limits[k] - s[k])


# --- per-mineral evaluation point ----------------------------------------
#
# A single evaluation temperature is WRONG, and wrong in a dangerous
# direction. Solubility-temperature sign differs by mineral:
#
#   calcite, magnesium silicate  retrograde  -> least soluble HOT
#                                            -> evaluate at the tube skin
#   gypsum                       maximum near 35-40 C, weakly retrograde
#                                            above it -> evaluate at skin,
#                                            but the benefit is small
#   amorphous silica             PROGRADE (more soluble hot)
#                                            -> least soluble COLD
#                                            -> evaluate at the tower basin
#
# Evaluating silica at the hot skin makes the model OPTIMISTIC about the one
# species with no effective inhibitor in general service. Reference: Berce
# et al. (2021), Processes 9(11) 1356; Demadis (2003) on silica normal vs
# magnesium silicate inverse solubility.
MINERAL_EVAL_POINT = {
    "SI_calcite": "hot",
    "SI_gypsum": "hot",
    "SI_silica_am": "cold",
}


def wall_bulk_delta_t(heat_flux_w_m2, velocity_m_s=2.0, tube_id_m=0.0176,
                      T_bulk_c=30.0):
    """Wall-to-bulk temperature rise [K], dT = q'' / h_i.

    Replaces a fixed +8 K assumption with the quantity the controller can
    actually compute from duty and geometry. Film coefficient from
    Dittus-Boelter (Nu = 0.023 Re^0.8 Pr^0.4, fluid being heated).

    External review narrowed the credible heat-flux band for shell-and-tube
    condensers to 20-30 kW/m2, against the 15.8-47.3 kW/m2 originally taken
    from a general water-handbook range. At 2 m/s (h = 8186 W/m2K) that
    gives a clean-surface skin rise of 2.4-3.7 K, so the "3.8 K typical"
    used earlier sits at the top of the corrected clean range. Values near
    8 K now correspond only to a FOULED surface, whose deposit face runs
    hotter than clean metal, or to velocities near the TEMA minimum.

    The film coefficient itself and the q''/h_i derivation were both
    confirmed correct by that review.
    """
    rho, mu, k, cp = 995.7, 7.97e-4, 0.615, 4178.0
    Re = rho * velocity_m_s * tube_id_m / mu
    Pr = cp * mu / k
    Nu = 0.023 * Re ** 0.8 * Pr ** 0.4
    h_i = Nu * k / tube_id_m
    return heat_flux_w_m2 / h_i, h_i


def saturation_state_split(water, T_hot, T_cold, pH_hot=None, pH_cold=None):
    """Saturation indices with each mineral evaluated where it is least
    soluble: retrograde species at the hot skin, prograde species at the
    coldest point in the loop."""
    hot = saturation_state(water, T_hot, pH=pH_hot)
    cold = saturation_state(water, T_cold, pH=pH_cold)
    out = {"T_hot": T_hot, "T_cold": T_cold}
    for k, where in MINERAL_EVAL_POINT.items():
        out[k] = hot[k] if where == "hot" else cold[k]
        out[k + "_at"] = where
    out["ionic_strength"] = hot["ionic_strength"]
    out["pitzer_required"] = hot["pitzer_required"]
    return out


def max_cycles_split(makeup, T_hot, T_cold, limits=None, lo=1.0, hi=30.0,
                     tol=1e-3):
    """Max cycles with per-mineral evaluation points and pH resolved by
    atmospheric CO2 equilibrium at each point."""
    limits = OPERATING_LIMITS if limits is None else limits

    def margin(cy):
        w = makeup.concentrate(cy)
        s = saturation_state_split(
            w, T_hot, T_cold,
            pH_hot=ph_atmospheric_equilibrium(w, T_hot),
            pH_cold=ph_atmospheric_equilibrium(w, T_cold))
        return min(limits[k] - s[k] for k in limits)

    if margin(lo) < 0:
        return float(lo)
    if margin(hi) > 0:
        return float(hi)
    return float(brentq(margin, lo, hi, xtol=tol))


def binding_mineral_split(makeup, cycles, T_hot, T_cold, limits=None):
    limits = OPERATING_LIMITS if limits is None else limits
    w = makeup.concentrate(cycles)
    s = saturation_state_split(
        w, T_hot, T_cold,
        pH_hot=ph_atmospheric_equilibrium(w, T_hot),
        pH_cold=ph_atmospheric_equilibrium(w, T_cold))
    return min(limits, key=lambda k: limits[k] - s[k])


# --- measured Saudi waters, Badruzzaman et al. 2022 -----------------------
#
# Badruzzaman, M., Anazi, J.R., Al-Wohaib, F.A., Al-Malki, A.A., Jutail, F.
# (2022) "Municipal reclaimed water as makeup water for cooling systems:
# Water efficiency, biohazards, and reliability", Water Resources and
# Industry 28:100188. Open access, CC BY-NC-ND.
# Authors: Saudi Aramco Environmental Protection; Process & Control Systems;
# Community Services -- Dhahran, Saudi Arabia.
#
# A 4.2 MW cooling tower at a Saudi oil and gas facility, run on treated
# municipal wastewater effluent. This replaces the third-party analysis we
# previously had to close on charge balance with an invented chloride: it is
# measured, Saudi, and from an operating tower on the makeup water our
# product targets.
#
# Two features matter for the model:
#   sulfate 566 mg/L -- roughly double the value we had been using, which
#     pushes GYPSUM saturation much earlier;
#   bicarbonate 70 mg/L (alkalinity 57 as CaCO3) -- markedly lower than we
#     assumed, which reduces calcite risk and the acid needed to manage it.
# Together those move the binding constraint decisively away from calcite,
# which is exactly the regime where the Langelier index is blind.
#
# Silica is NOT reported in the source. It is left at zero rather than
# invented; the silica constraint is therefore inactive on this water and
# the model reports that honestly rather than guessing.

ARAMCO_RECLAIMED = Water(
    name="Aramco reclaimed (Badruzzaman 2022, average)",
    Na=379.0, K=25.0, Ca=94.0, Mg=41.0,
    Cl=565.0, SO4=566.0, HCO3=70.0, NO3=12.0,
    SiO2=0.0,          # not reported in the source -- not invented
    pH=7.4, TDS=1500.0,
)

ARAMCO_GROUNDWATER = Water(
    name="Aramco raw groundwater (Badruzzaman 2022)",
    Na=680.0, K=41.0, Ca=233.0, Mg=97.0,
    Cl=1170.0, SO4=558.0, HCO3=226.0,
    SiO2=0.0,
    pH=7.82, TDS=3040.0,
)


def balance_sodium(water):
    """Close an analysis on charge balance by adjusting sodium.

    Companion to balance_chloride, for analyses carrying an ANION excess.
    Sodium is the conventional balancing cation: conservative, analytically
    robust, and usually the largest monovalent cation present.

    Needed for the Badruzzaman reclaimed-water column, which is reported as
    an independent Min/Ave/Max per ion across a sampling campaign. Averaging
    each ion separately does not preserve electroneutrality, so the average
    column carries a ~14 % anion excess even though each individual sample
    would have balanced. That is an artefact of how the table is published,
    not an error in the measurements, and closing it on sodium is the
    standard remedy.
    """
    m = water.molality()
    cat = sum(m[s] * SPECIES[s][1] for s in SPECIES
              if SPECIES[s][1] > 0 and s != "Na")
    an = sum(-m[s] * SPECIES[s][1] for s in SPECIES if SPECIES[s][1] < 0)
    out = Water(**{**water.__dict__})
    out.Na = max(an - cat, 0.0) * SPECIES["Na"][0] * 1e3
    out.name = water.name + " (Na-balanced)"
    return out


# --- magnesium silicate ---------------------------------------------------
#
# Gap identified in external review: magnesium silicate scales form on the
# HOT heat-transfer surface and can bind before amorphous silica does. Our
# model evaluated amorphous silica at the cold basin and nothing at all for
# Mg-silicate, so a real failure mode was invisible.
#
# Modelled as sepiolite, the standard PHREEQC proxy for magnesium silicate
# scaling. From phreeqc.dat:
#
#   Sepiolite  Mg2Si3O7.5OH:3H2O + 4 H+ + 0.5 H2O = 2 Mg+2 + 3 H4SiO4
#              log_k 15.760,  delta_h -10.7 kcal
#
# The negative reaction enthalpy means K falls as temperature rises, so
# sepiolite is RETROGRADE -- less soluble hot -- and therefore governs at
# the condenser tube skin, opposite to amorphous silica. That is precisely
# why a single evaluation temperature cannot work: on the same water,
# silica binds cold and magnesium silicate binds hot.

def log_k_sepiolite(T_c):
    """Sepiolite dissolution constant. phreeqc.dat log_k 15.760, dH -10.7 kcal."""
    return _vant_hoff(15.760, -10.7, T_c)


def si_sepiolite(water, T_c, pH):
    """Saturation index for magnesium silicate, as sepiolite.

    SI = 2 log a(Mg) + 3 log m(H4SiO4) + 4 pH - log K

    Dissolved silica is carried as the neutral species H4SiO4, so its
    activity coefficient is taken as unity, consistent with how the
    amorphous-silica index is computed elsewhere in this module.
    """
    m = water.molality()
    if m["Mg"] <= 0 or m["SiO2"] <= 0:
        return float("-inf")        # constraint inactive, not violated
    I = water.ionic_strength()
    a_mg = m["Mg"] * davies_gamma(2, I, T_c)
    return (2.0 * math.log10(a_mg) + 3.0 * math.log10(m["SiO2"])
            + 4.0 * pH - log_k_sepiolite(T_c))


# --- total dissolved solids, a regulatory rather than chemical limit ------
#
# Also raised in review: municipal discharge caps on blowdown TDS can bind
# before any scaling limit does. Where a cap applies, the cycles limit is
# min(chemistry, regulation), and on low-cap sites the chemistry headroom is
# irrelevant. Modelled explicitly so the controller cannot recommend an
# operating point that is chemically safe and legally prohibited.
# RESOLVED against the primary regulation. Royal Commission Environmental
# Regulations RCER-2015, Volume I (Royal Commission for Jubail and Yanbu),
# which is the binding instrument for the Jubail and Yanbu industrial
# cities. Three separate tables apply to three different discharge routes,
# and they do not agree with each other: [C]
#
#   Table 3B  discharge to the CENTRAL WASTEWATER TREATMENT FACILITIES
#             TDS 2,000 mg/L (Jubail) / 2,500 mg/L (Yanbu);
#             chloride 1,000 / 400; sulfate 800 / 400; temperature 60 / 50 C
#
#   Table 3C  DIRECT DISCHARGE TO COASTAL WATERS, explicitly including
#             discharge to the seawater cooling return
#             NO TDS LIMIT. Under PHYSICAL the table lists only floating
#             particles and temperature.
#
#   Table 3D  discharge to an IRRIGATION SYSTEM
#             TDS 2,000 mg/L maximum, 1,750 mg/L monthly average
#
# The conclusion is that a TDS cap is not a property of the cooling loop at
# all. It is a property of WHERE THE BLOWDOWN GOES.
#
# That resolves the contradiction that stopped this constraint being used.
# On 1,500 mg/L reclaimed makeup, a 2,000 mg/L cap implies a ceiling of
# 1.33 cycles -- which would forbid evaporative cooling on reclaimed water
# outright, and plants demonstrably run 3.5-5.0. They are therefore not
# discharging tower blowdown to the sewer. A coastal industrial plant
# discharging to the seawater cooling return has no TDS limit to satisfy,
# and that is exactly the case where observed practice sits.
#
# So the cap is a site configuration item, defaulting to none, and the
# controller reports which route it assumed rather than silently picking.
DISCHARGE_TDS_CAPS = {
    "coastal_outfall": None,        # RCER-2015 Table 3C: no TDS limit  [C]
    "jubail_sewer": 2000.0,         # RCER-2015 Table 3B, Jubail        [C]
    "yanbu_sewer": 2500.0,          # RCER-2015 Table 3B, Yanbu         [C]
    "irrigation_reuse": 2000.0,     # RCER-2015 Table 3D                [C]
    "none": None,
}

# Chloride and sulfate are capped alongside TDS on the sewer route, and on
# a concentrated loop they bind before TDS does. Carried so the constraint
# can be evaluated ion-by-ion rather than on a bulk surrogate -- which is
# the same argument this whole package makes about saturation.
DISCHARGE_ION_CAPS = {                                    # mg/L      [C]
    "jubail_sewer": {"Cl": 1000.0, "SO4": 800.0},
    "yanbu_sewer": {"Cl": 400.0, "SO4": 400.0},
    "irrigation_reuse": {"Cl": 1000.0, "SO4": 600.0},
    "coastal_outfall": {},
    "none": {},
}


def max_cycles_tds(makeup, cap_mg_L):
    """Cycles at which circulating TDS reaches a discharge cap."""
    if cap_mg_L is None:
        return float("inf")
    t = makeup.tds()
    return float("inf") if t <= 0 else cap_mg_L / t


# NOTE: sepiolite is deliberately NOT registered in MINERAL_EVAL_POINT.
# It was added as a magnesium-silicate proxy and then rejected on review as
# the wrong phase for a real-time controller -- crystalline silicates are
# kinetically inhibited over a condenser residence time, so the index
# chronically over-predicts. Magnesium silicate is handled instead by the
# empirical Mg x SiO2 product rule and the brucite saturation-pH criterion
# above. si_sepiolite() is retained only for comparison and diagnostics.


# --- operating limits for the two newly added constraints -----------------
#
# Both are added to the model as MECHANISM, with their thresholds marked
# unverified, because in each case the naive value contradicts observed
# practice and we will not ship a number that we can already see is wrong.
#
# MAGNESIUM SILICATE. Sepiolite comes out supersaturated at every cycle
# count on Aramco reclaimed water -- SI +1.56 at 3 cycles rising to +3.50
# at 8. Taken literally that would forbid operation everywhere, which is
# plainly false: plants run 4-5 cycles on this water without catastrophic
# magnesium silicate fouling. The resolution is that sepiolite precipitation
# is strongly kinetically inhibited, and practical cooling-water control
# uses an empirical Mg x SiO2 product rather than a thermodynamic index.
# We therefore have the driving force but not the threshold.
#
# [VERIFY] the operating limit for magnesium silicate: either a defensible
# sepiolite SI allowance, or the empirical Mg x SiO2 product limit and the
# temperature it is evaluated at.
SEPIOLITE_SI_LIMIT = None      # deliberately unset -- see above

# DISCHARGE TDS CAP -- resolved, see DISCHARGE_TDS_CAPS above. The earlier
# reasoning was right for the wrong reason: the assumed 3,000 mg/L was not
# merely unverified, it was the wrong KIND of number. The regulation caps
# TDS on two discharge routes and not on the third, and the third is the one
# a coastal Gulf industrial plant uses. The default therefore stays unset,
# now on evidence rather than on doubt.
DISCHARGE_TDS_CAP_DEFAULT = None
DISCHARGE_ROUTE_DEFAULT = "coastal_outfall"   # RCER-2015 Table 3C  [C]


# --- magnesium silicate, corrected -----------------------------------------
#
# External review established that sepiolite is the WRONG proxy for a
# real-time controller. Crystalline magnesium silicates (sepiolite, talc,
# chrysotile, forsterite) are thermodynamic end-states whose crystallisation
# is heavily kinetically inhibited, requiring ageing far beyond the ~3 s a
# parcel of water spends crossing the condenser skin. What actually forms
# first is a poorly ordered AMORPHOUS magnesium silicate with a far higher
# solubility product; crystalline phases appear only as that precipitate
# ages. Using sepiolite therefore chronically over-predicts scaling, which
# is exactly what our own run showed (SI +1.56 to +3.50, forbidding
# operation everywhere).
#
# Industry does not use a thermodynamic index for this mineral at all. It
# uses an empirical product of magnesium and silica. The rule is
# pH-dependent, and the published thresholds are:
#
#     pH < 7.5   product   Mg x SiO2  <=  35 000   (most cited)
#                          40 000 (permissive), 25 000 (utility standard),
#                          20 000 (total assurance)
#     pH > 7.5   sum       Mg + SiO2  <=  17 000
#
# The sum rule is a documented anomaly -- adding concentrations contradicts
# mass action -- and on ordinary cooling water it is numerically
# non-binding, so it is implemented but flagged rather than trusted.
#
# UNIT AMBIGUITY, and it matters as much as the fan-correlation units did.
# Sources describe the magnesium term as "magnesium hardness expressed as
# ppm CaCO3", but the two conventions give very different answers:
#
#     Mg as CaCO3 : limit reached at ~2.8 cycles  -- BELOW observed practice
#     Mg as Mg2+  : limit reached at ~5.6 cycles  -- matches observed practice
#
# Since plants demonstrably operate at 3.5-5.0 cycles on this water, the
# Mg-as-Mg2+ convention is the one consistent with reality. Both are
# implemented; the model reports both and flags the discrepancy rather than
# silently picking one.

MG_SILICA_LIMITS = {
    "permissive": 40_000.0,
    "standard": 35_000.0,      # most cited
    "utility": 25_000.0,
    "assurance": 20_000.0,
}
MG_SILICA_SUM_LIMIT_ALKALINE = 17_000.0    # pH > 7.5, documented anomaly
MG_TO_CACO3 = 100.0869 / 24.305            # 4.118


def mg_silica_product(water, mg_basis="Mg"):
    """Empirical magnesium-silica product [ppm^2].

    mg_basis "Mg"    -> magnesium as ppm Mg2+ (matches observed practice)
    mg_basis "CaCO3" -> magnesium hardness as ppm CaCO3 (as literally worded
                        in several sources, but see the unit note above)
    """
    mg = water.Mg * (MG_TO_CACO3 if mg_basis == "CaCO3" else 1.0)
    return mg * water.SiO2


def mg_silica_sum(water, mg_basis="Mg"):
    """Empirical magnesium + silica sum [ppm], used above pH 7.5."""
    mg = water.Mg * (MG_TO_CACO3 if mg_basis == "CaCO3" else 1.0)
    return mg + water.SiO2


def max_cycles_mg_silicate(makeup, limit=35_000.0, mg_basis="Mg"):
    """Cycles at which the magnesium-silica product reaches its limit.

    Both Mg and SiO2 concentrate linearly, so the product grows as N^2 and
    the limit has a closed form.
    """
    p1 = mg_silica_product(makeup, mg_basis)
    if p1 <= 0:
        return float("inf")
    return math.sqrt(limit / p1)


def ph_saturation_brucite(T_c, water):
    """Saturation pH for Mg(OH)2 (brucite) at temperature T_c.

    The mechanism behind magnesium silicate scaling is two-step: brucite
    precipitates first, then reacts with dissolved and colloidal silica in
    the boundary layer to form the dense silicate scale. Brucite's
    saturation pH is RETROGRADE -- it falls as temperature rises -- so
    deposition cannot occur while bulk pH stays below the saturation pH
    evaluated at the hottest surface in the system.

    Mg(OH)2 = Mg+2 + 2 OH-,  phreeqc.dat log_k -11.18, delta_h -27.1 kcal.
    """
    log_k = _vant_hoff(-11.18, -27.1, T_c)
    m = water.molality()
    if m["Mg"] <= 0:
        return float("inf")
    I = water.ionic_strength()
    a_mg = m["Mg"] * davies_gamma(2, I, T_c)
    # log K = log a_Mg + 2 log a_OH  ->  pOH = (log K - log a_Mg) / 2
    log_a_oh = (log_k - math.log10(a_mg)) / 2.0
    pOH = -log_a_oh
    kw = _vant_hoff(-14.0, 13.362, T_c)          # water dissociation
    return -kw - pOH
