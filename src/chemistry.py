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
    # DEFECT 29. Phosphate. The molar mass and charge are those of the fully
    # deprotonated orthophosphate ion, because that is the reference form the
    # association constants below are written from. At cooling-tower pH the
    # ion is almost entirely HPO4(2-) and H2PO4(-), so the CHARGE CARRIED for
    # ionic-strength and charge-balance purposes is not -3: see
    # phosphate_mean_charge().
    "PO4":  (94.971, -3),
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
    PO4: float = 0.0
    pH: float = 7.8
    TDS: float = None

    def molality(self):
        return {s: getattr(self, s) * 1e-3 / SPECIES[s][0] for s in SPECIES}

    def _charge(self, s):
        """Charge borne by component `s` at this water's pH.

        Every component but phosphate carries its formal charge, which is
        also the charge of its dominant form across the whole operating pH
        band. Phosphate does not: PO4(3-) is a vanishing fraction below pH 12
        and using -3 would overstate both the ionic strength and the anion
        sum. See phosphate_mean_charge().
        """
        if s == "PO4":
            return phosphate_mean_charge(self.pH)
        return SPECIES[s][1]

    def ionic_strength(self):
        m = self.molality()
        return 0.5 * sum(m[s] * self._charge(s) ** 2 for s in SPECIES)

    def tds(self):
        if self.TDS is not None:
            return self.TDS
        return sum(getattr(self, s) for s in SPECIES)

    def charge_balance_pct(self):
        """Percent charge imbalance -- a data-quality check on any analysis."""
        m = self.molality()
        z = {s: self._charge(s) for s in SPECIES}
        cat = sum(m[s] * z[s] for s in SPECIES if z[s] > 0)
        an = sum(-m[s] * z[s] for s in SPECIES if z[s] < 0)
        return 100.0 * (cat - an) / (0.5 * (cat + an)) if (cat + an) else 0.0

    def concentrate(self, cycles):
        """This water concentrated to `cycles` cycles of concentration."""
        kw = {s: getattr(self, s) * cycles for s in SPECIES}
        return Water(name=f"{self.name} x{cycles:g}", pH=self.pH,
                     TDS=(self.TDS * cycles if self.TDS is not None else None),
                     **kw)

    def pitzer_required(self):
        return self.ionic_strength() > 0.5


# ---------------------------------------------------------------------------
# Analysis validation -- refuse a bad input rather than absorbing it
# ---------------------------------------------------------------------------
# Six of this package's defects were caught because a first-principles model,
# or a check written against it, refused a bad input. Until 10 September 2026
# the water analysis itself was the one input nothing checked: `ARAMCO_
# RECLAIMED` fails TDS closure by +22.7 % and carries SiO2 = 0.0 for a species
# the source analysis never reported. Both flowed silently into every result.
#
# These are OBJECTIVE tests. Neither needs an outside authority and neither
# identifies which number is wrong -- they establish only that an analysis is
# or is not self-consistent.

ANALYSIS_TOLERANCES = {
    "charge_balance_pct": 5.0,    # laboratory practice accepts +/- 5 %
    "tds_closure_pct": 10.0,      # ions may not exceed the stated TDS
    "ionic_strength_max": 0.5,    # Davies validity; above this Pitzer is needed
}

# Measured Saudi makeup silica. Al-Mutaz & Al-Anezi (2004), King Saud
# University / Riyadh Water Treatment Project, Salbukh field. [C]
# Recorded in HANDOFF.md as the value at which the model computes 4.4-4.9 max
# cycles against an industry empirical band of 3.5-5.0.
GULF_SILICA_MG_L = 26.8


class AnalysisRejected(ValueError):
    """A water analysis failed a self-consistency test it must pass."""


def validate_analysis(water, tolerances=None, silica_declared=False,
                      phosphate_declared=False):
    """Objective self-consistency checks on a water analysis.

    Returns a dict of {check: (passed, detail)}. Nothing here decides which
    reported number is wrong -- an analysis that fails is simply one this
    model should not be run on without a declared reason.
    """
    tol = dict(ANALYSIS_TOLERANCES if tolerances is None else tolerances)
    ions = sum(getattr(water, s) for s in SPECIES)
    tds = water.tds()
    cb = water.charge_balance_pct()
    closure = 100.0 * (ions - tds) / tds if tds else 0.0
    I = water.ionic_strength()

    checks = {
        "charge_balance": (
            abs(cb) <= tol["charge_balance_pct"],
            f"{cb:+.2f} % against a +/-{tol['charge_balance_pct']:.0f} % tolerance"),
        "tds_closure": (
            closure <= tol["tds_closure_pct"],
            f"ions sum to {ions:.0f} mg/L against a stated TDS of {tds:.0f} "
            f"({closure:+.1f} %); a water cannot contain more ions than its "
            f"own TDS"),
        "davies_applicable": (
            I <= tol["ionic_strength_max"],
            f"ionic strength {I:.3f} mol/kg against a Davies limit of "
            f"{tol['ionic_strength_max']:.1f}"),
        "silica_declared": (
            bool(silica_declared) or water.SiO2 > 0.0,
            f"SiO2 = {water.SiO2:.1f} mg/L. Zero is indistinguishable from "
            f"UNMEASURED unless declared. Amorphous silica binds at the cold "
            f"basin and is not pH-sensitive, so acid cannot buy cycles "
            f"against it: carrying it as zero can move the ceiling by more "
            f"than six cycles"),
        # DEFECT 29, and the same trap as silica one species over. An
        # unmeasured zero is not a measurement of zero. Phosphate is the
        # second-ranked scale in the only full-scale study of this
        # application and it is retrograde, so it binds at the tube skin
        # where the heat transfer is.
        "phosphate_declared": (
            bool(phosphate_declared) or water.PO4 > 0.0,
            f"PO4 = {water.PO4:.1f} mg/L. Zero is indistinguishable from "
            f"UNMEASURED. Tertiary treated municipal wastewater carries "
            f"7-10 mg/L, and the US DOE study of this exact application "
            f"found hydroxyapatite as the ONLY crystalline phase on its "
            f"heated surface while LSI read negative"),
    }
    return checks


def require_valid_analysis(water, tolerances=None, silica_declared=False,
                           phosphate_declared=False):
    """As `validate_analysis`, but raises. Use at a product boundary."""
    checks = validate_analysis(water, tolerances, silica_declared,
                               phosphate_declared)
    bad = {k: d for k, (ok, d) in checks.items() if not ok}
    if bad:
        raise AnalysisRejected(
            f"water analysis '{water.name}' failed "
            + "; ".join(f"{k}: {d}" for k, d in bad.items()))
    return checks


# ---------------------------------------------------------------------------
# Aqueous ion association -- DEFECT 24
# ---------------------------------------------------------------------------
# Until 10 September 2026 this module applied Davies activity coefficients to
# TOTAL calcium and sulfate and never solved aqueous complexation. Benchmarked
# against PHREEQC 3.9.0 on the USGS worked example of a solution held AT gypsum
# saturation, it returned SI_gypsum = +0.2046 where the published value is
# 0.000: it called a saturated solution supersaturated.
#
# The cause is physical, not numerical. That example carries 0.01508 mol/kgw
# total calcium, of which only 0.01046 is the free Ca(2+) ion -- 0.004627 is
# the NEUTRAL CaSO4 ion pair, about 31 % of the calcium, and a neutral species
# contributes nothing to the ion activity product. Matching a mineral's logK is
# not the same as reproducing its speciation.
#
# Association constants are the phreeqc.dat values, transcribed rather than
# linked, for the same reason every other constant in this file is: an edge
# controller must ship without a third-party scientific runtime. [C phreeqc.dat]
#
#   name       log K(25 C)   dH (kcal/mol)   charge
ASSOCIATION = {
    "CaSO4":  (2.250, 1.325, 0, {"Ca": 1, "SO4": 1}),
    "CaHCO3": (1.106, 2.690, 1, {"Ca": 1, "HCO3": 1}),
    "CaCO3":  (3.224, 3.545, 0, {"Ca": 1, "CO3": 1}),
    "MgSO4":  (2.370, 4.550, 0, {"Mg": 1, "SO4": 1}),
    "MgHCO3": (1.070, 0.790, 1, {"Mg": 1, "HCO3": 1}),
    "MgCO3":  (2.980, 2.713, 0, {"Mg": 1, "CO3": 1}),
    "NaSO4":  (0.700, 1.120, -1, {"Na": 1, "SO4": 1}),
    "NaHCO3": (-0.25, 0.000, 0, {"Na": 1, "HCO3": 1}),
    "NaCO3":  (1.270, 8.910, -1, {"Na": 1, "CO3": 1}),
    "KSO4":   (0.850, 2.250, -1, {"K": 1, "SO4": 1}),
}

_FREE_CHARGE = {"Ca": 2, "Mg": 2, "Na": 1, "K": 1,
                "HCO3": -1, "CO3": -2, "SO4": -2, "Cl": -1, "NO3": -1,
                "PO4": -3}

SPECIATION_MAX_ITER = 200
SPECIATION_TOL = 1e-12


def _assoc_log_k(name, T_c):
    """van 't Hoff from the phreeqc.dat 25 C constant and enthalpy."""
    log_k25, dh_kcal, _z, _comp = ASSOCIATION[name]
    return _vant_hoff(log_k25, dh_kcal, T_c)



# ---------------------------------------------------------------------------
# Phosphate -- DEFECT 29
# ---------------------------------------------------------------------------
# Until 10 September 2026 this model had no phosphate species at all, while
# phosphate is MEASURED in the water the product is aimed at and is a named
# scale former in exactly this application.
#
# The evidence that forced it, none of it ours:
#
#   * Vidic, Dzombak & Landis (2012), "Use of Treated Municipal Wastewater as
#     Power Plant Cooling System Makeup Water", US DOE/NETL final technical
#     report, Cooperative Agreement DE-NT0006550 (415 pp). This is the
#     definitive study of the application. Its weekly analyte list is four
#     anions -- Cl, PO4, NO3, SO4 -- and four cations -- Ca, Mg, Fe, Cu.
#     SILICA IS NOT MEASURED ANYWHERE IN THE REPORT; the word does not appear
#     once. Phosphate is 9.98 / 7.16 / 8.46 mg/L in its three waters, and the
#     synthetic recipe built to reproduce the scaling carries PO4 at 0.48 mM
#     and no silica. [C 10.2172/1063876 Tables 2.3.1, 2.3.2]
#
#   * The same report, section 4.2.5, on a HEATED surface at four cycles:
#     "Hydroxyapatite (Ca5(PO4)3(OH)) was the only crystalline material
#     identified by XRD analysis in the deposits formed on the heater."
#     Not calcite. Not gypsum. Not silica. [C ibid. p. 4-19]
#
#   * The same report, section 3.2.4, having computed LSI, RSI and PSI --
#     "widely used to estimate the scaling potential of calcium carbonate" --
#     concludes: "Water quality analysis suggests that calcium phosphate is
#     the primary mineral scale when pH of the recirculating water is
#     adjusted at 7.8". [C ibid. p. 3-28]
#
#   * Veolia Water Handbook ch. 25 names calcium phosphate among the
#     retrograde species that "supersaturate in the higher-temperature water
#     adjacent to the heat transfer surface". Already cited in
#     docs/chemistry_evidence.md 3.1. [C]
#
# Association constants are the phreeqc.dat values, transcribed not linked,
# for the reason every other constant here is. Their internal consistency is
# checkable without the database: the successive differences reproduce the
# textbook dissociation constants of phosphoric acid,
#   21.721 - 19.553 = 2.168 = pKa1 (2.15)
#   19.553 - 12.346 = 7.207 = pKa2 (7.20)
#                     12.346 = pKa3 (12.35)
# and that identity is asserted in tests/test_reference_benchmarks.py.
#
#   name          log K(25 C)  dH kcal/mol   charge   composition
PHOSPHATE_ASSOCIATION = {
    "HPO4":     (12.346, -3.530, -2, {"PO4": 1, "H": 1}),
    "H2PO4":    (19.553, -4.520, -1, {"PO4": 1, "H": 2}),
    "H3PO4":    (21.721, -2.030,  0, {"PO4": 1, "H": 3}),
    "CaPO4":    ( 6.459,  3.100, -1, {"Ca": 1, "PO4": 1}),
    "CaHPO4":   (15.085, -0.230,  0, {"Ca": 1, "PO4": 1, "H": 1}),
    "CaH2PO4":  (20.961, -1.120,  1, {"Ca": 1, "PO4": 1, "H": 2}),
    "MgPO4":    ( 6.589,  3.100, -1, {"Mg": 1, "PO4": 1}),
    "MgHPO4":   (15.216, -0.230,  0, {"Mg": 1, "PO4": 1, "H": 1}),
    "MgH2PO4":  (21.066, -1.120,  1, {"Mg": 1, "PO4": 1, "H": 2}),
}
# The Ca/Mg entries are cumulative from PO4(3-): phreeqc.dat writes them from
# HPO4(2-) and H2PO4(-), so e.g. CaHPO4 = 12.346 + 2.739 = 15.085 and
# MgH2PO4 = 19.553 + 1.513 = 21.066. Enthalpies add the same way.

PHOSPHATE_PKA = (2.148, 7.198, 12.346)   # H3PO4 -> H2PO4- -> HPO4-2 -> PO4-3


def phosphate_mean_charge(pH):
    """Charge-weighted mean charge on total phosphate at `pH`.

    Concentration-basis (activity coefficients omitted), which is the same
    convention a laboratory uses when it reports an anion sum. At pH 7.8 this
    is about -1.80; at pH 6.7 about -1.24. Using the formal -3 would overstate
    the anion sum by two thirds and would fail an otherwise sound analysis on
    charge balance.
    """
    pk1, pk2, pk3 = PHOSPHATE_PKA
    h = 10.0 ** (-pH)
    # relative abundances, referenced to PO4(3-) = 1
    r_po4 = 1.0
    r_hpo4 = 10.0 ** pk3 * h
    r_h2po4 = 10.0 ** (pk3 + pk2) * h * h
    r_h3po4 = 10.0 ** (pk3 + pk2 + pk1) * h * h * h
    tot = r_po4 + r_hpo4 + r_h2po4 + r_h3po4
    return -(3.0 * r_po4 + 2.0 * r_hpo4 + 1.0 * r_h2po4) / tot


def log_k_tricalcium_phosphate(T_c):
    """Ca3(PO4)2 = 3Ca+2 + 2PO4-3.

    beta-tricalcium phosphate (whitlockite), log Ksp = -28.92 at 25 C, dH
    -20.0 kcal/mol. Strongly RETROGRADE: like calcite it is least soluble at
    the hot tube skin, which is where the DOE study found it. [U] -- the
    constant is a literature consensus value, not a phreeqc.dat transcription,
    and is flagged as such wherever it is used.
    """
    return _vant_hoff(-28.92, -20.0, T_c)


def log_k_hydroxyapatite(T_c):
    """Ca5(PO4)3OH + 4H+ = 5Ca+2 + 3HPO4-2 + H2O.

    phreeqc.dat: log_k -3.421, dH -36.155 kcal/mol. Hydroxyapatite is the
    thermodynamically stable calcium phosphate and therefore the LEAST
    soluble; amorphous calcium phosphate and whitlockite form first because
    hydroxyapatite nucleates slowly. The DOE study saw both -- hydroxyapatite
    by XRD, with a Ca:P ratio of 1.54 against the 1.67 of pure
    hydroxyapatite, "indicated that amorphous calcium phosphate ... may also
    exist in the deposits". [C phreeqc.dat]
    """
    return _vant_hoff(-3.421, -36.155, T_c)


def _phosphate_distribution(po4_total, a_H, ca_free, mg_free, g, T_c):
    """Solve the phosphate sub-system analytically at fixed Ca, Mg and pH.

    Every phosphate species is first order in free PO4(3-), so the mass
    balance is linear and needs no iteration:  total = p * (1 + sum(coeff)).
    Returns (free_PO4, {species: molality}).
    """
    if po4_total <= 0.0:
        return 0.0, {n: 0.0 for n in PHOSPHATE_ASSOCIATION}
    parents = {"Ca": ca_free, "Mg": mg_free}
    coeff = {}
    for name, (lk25, dh, z_c, comp) in PHOSPHATE_ASSOCIATION.items():
        k = 10.0 ** _vant_hoff(lk25, dh, T_c)
        # activity of everything except the free PO4(3-) itself
        term = k * g[3] / g[abs(z_c)]
        for ion, n in comp.items():
            if ion == "PO4":
                continue
            if ion == "H":
                term *= a_H ** n
            else:
                term *= (parents[ion] * g[2]) ** n
        coeff[name] = term
    p = po4_total / (1.0 + sum(coeff.values()))
    return p, {n: coeff[n] * p for n in coeff}


PHOSPHATE_CHARGE = {n: v[2] for n, v in PHOSPHATE_ASSOCIATION.items()}


def speciate(water, T_c, pH=None):
    """Solve aqueous ion association and return FREE-ion molalities.

    Returns a dict with:
        free       free-ion molality per component, mol/kg
        complexes  molality of each ion pair, mol/kg
        gamma      activity coefficient by absolute charge
        I          ionic strength computed on the SPECIATED solution
        iterations, converged

    Fixed-point iteration with damping. The ionic strength is recomputed from
    the speciated distribution each sweep, because complexation lowers it --
    a neutral pair contributes nothing and a 1-charged pair contributes a
    quarter of what its 2-charged parents did.
    """
    pH = water.pH if pH is None else pH
    m = water.molality()
    a_H = 10.0 ** (-pH)
    log_k2 = log_k2_carbonic(T_c)

    total = {s: m.get(s, 0.0) for s in ("Ca", "Mg", "Na", "K", "SO4",
                                        "HCO3", "Cl", "NO3", "PO4")}
    # Carbonate is not an analysis input: it is set by HCO3 and pH.
    free = dict(total)
    free["CO3"] = 0.0
    cx = {name: 0.0 for name in ASSOCIATION}
    # DEFECT 29: phosphate species, solved analytically each sweep.
    px = {name: 0.0 for name in PHOSPHATE_ASSOCIATION}

    converged = False
    it = 0
    for it in range(1, SPECIATION_MAX_ITER + 1):
        # ionic strength on the speciated distribution
        I = 0.5 * sum(free.get(s, 0.0) * z * z
                      for s, z in _FREE_CHARGE.items())
        I += 0.5 * sum(cx[n] * ASSOCIATION[n][2] ** 2 for n in ASSOCIATION)
        I += 0.5 * sum(px[n] * PHOSPHATE_CHARGE[n] ** 2
                       for n in PHOSPHATE_ASSOCIATION)
        I = max(I, 1e-12)
        g = {z: davies_gamma(z, I, T_c) for z in (1, 2, 3)}
        g[0] = 1.0

        # phosphate, at this sweep's free Ca and Mg
        free["PO4"], px = _phosphate_distribution(
            total.get("PO4", 0.0), a_H, free.get("Ca", 0.0),
            free.get("Mg", 0.0), g, T_c)

        # carbonate from the free bicarbonate at this pH
        free["CO3"] = (free["HCO3"] * g[1] * 10.0 ** log_k2 / a_H) / g[2]

        new_cx = {}
        for name, (_lk25, _dh, z_c, comp) in ASSOCIATION.items():
            k = 10.0 ** _assoc_log_k(name, T_c)
            prod = 1.0
            for ion, n in comp.items():
                prod *= (free.get(ion, 0.0) * g[abs(_FREE_CHARGE[ion])]) ** n
            new_cx[name] = k * prod / g[abs(z_c)]

        # mass balance: free = total - what is tied up in pairs
        new_free = dict(free)
        worst = 0.0
        for s in ("Ca", "Mg", "Na", "K", "SO4", "HCO3"):
            bound = sum(new_cx[n] * ASSOCIATION[n][3].get(s, 0)
                        for n in ASSOCIATION)
            bound += sum(px[n] * PHOSPHATE_ASSOCIATION[n][3].get(s, 0)
                         for n in PHOSPHATE_ASSOCIATION)
            target = max(total.get(s, 0.0) - bound, 1e-30)
            worst = max(worst, abs(target - free.get(s, 0.0)))
            new_free[s] = 0.5 * free.get(s, 0.0) + 0.5 * target   # damped
        free, cx = new_free, new_cx
        if worst < SPECIATION_TOL:
            converged = True
            break

    I = 0.5 * sum(free.get(s, 0.0) * z * z for s, z in _FREE_CHARGE.items())
    I += 0.5 * sum(cx[n] * ASSOCIATION[n][2] ** 2 for n in ASSOCIATION)
    I += 0.5 * sum(px[n] * PHOSPHATE_CHARGE[n] ** 2
                   for n in PHOSPHATE_ASSOCIATION)
    g = {z: davies_gamma(z, max(I, 1e-12), T_c) for z in (1, 2, 3)}
    g[0] = 1.0
    return {"free": free, "complexes": cx, "phosphate": px, "gamma": g,
            "I": max(I, 1e-12), "iterations": it, "converged": converged}


def saturation_state(water, T_c, pH=None):
    """Saturation indices at temperature `T_c`.

    SI = log10(IAP / Ksp). SI > 0 supersaturated (scale can form).
    """
    pH = water.pH if pH is None else pH
    m = water.molality()

    # DEFECT 24 FIXED 10 Sep 2026. These were TOTAL molalities, which counts
    # ion pairs as if they were free ions and inflates every index. They are
    # now the FREE-ion molalities from the association solver, and the ionic
    # strength is the speciated one. See speciate() above and
    # tests/test_reference_benchmarks.py.
    sp = speciate(water, T_c, pH)
    free, I = sp["free"], sp["I"]
    g1, g2 = sp["gamma"][1], sp["gamma"][2]

    a_H = 10.0 ** (-pH)
    a_HCO3 = free["HCO3"] * g1
    a_CO3 = free["CO3"] * g2
    a_Ca = free["Ca"] * g2
    a_SO4 = free["SO4"] * g2

    # DEFECT 29. Phosphate. Two calcium phosphates are reported because they
    # answer two different questions. Hydroxyapatite is the stable phase and
    # so the earliest possible warning; whitlockite/beta-TCP is the phase the
    # published inhibitor-limit table is written against, and is what a
    # constraint can actually be set on. SI_hydroxyapatite >= SI_tcp always,
    # asserted in tests/test_physics_invariants.py.
    a_PO4 = free.get("PO4", 0.0) * sp["gamma"][3]
    a_HPO4 = sp["phosphate"]["HPO4"] * g2

    return {
        "T_C": T_c,
        "pH": pH,
        "ionic_strength": I,
        "SI_calcite": math.log10(max(a_Ca * a_CO3, 1e-30)) - log_k_calcite(T_c),
        "SI_gypsum": math.log10(max(a_Ca * a_SO4, 1e-30)) - log_k_gypsum(T_c),
        "SI_silica_am": math.log10(max(m["SiO2"], 1e-30)) - log_k_silica_am(T_c),
        "SI_tcp": (3.0 * math.log10(max(a_Ca, 1e-30))
                   + 2.0 * math.log10(max(a_PO4, 1e-30))
                   - log_k_tricalcium_phosphate(T_c)),
        "SI_hydroxyapatite": (5.0 * math.log10(max(a_Ca, 1e-30))
                              + 3.0 * math.log10(max(a_HPO4, 1e-30))
                              + 4.0 * pH - log_k_hydroxyapatite(T_c)),
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
# DEFECT 29 AND WHY PHOSPHATE IS NOT IN THAT DICT.
#
# It was, briefly, at SI_tcp <= 3.0, and the model immediately falsified the
# choice: the ceiling on the field water collapsed to 1.0 cycle, meaning the
# water could not be concentrated at all. The Aramco pilot ran that same TSE
# at 3.5 cycles with, in its own words, the "condenser surface clean without
# mineral deposit formation". A limit that contradicts the one field
# observation the package has is wrong, and the limit is what was wrong.
#
# The physics behind it is standard and is the reason phosphate is special.
# Calcium phosphate is enormously supersaturated in almost every natural and
# treated water and does not deposit, because it is KINETICALLY inhibited --
# the same reason phosphate persists in seawater and in blood. Published
# inhibited limits show it directly: calcite tolerates SR 135-150 before
# deposition, tricalcium phosphate tolerates SR 1500-2500, an order of
# magnitude more, and SR 125,000 under a stressed programme.
#
# So on this water SI_tcp runs 3.28 at three cycles to 4.40 at seven, and the
# published band runs 3.18 to 5.10. THE ENTIRE OPERATING RANGE OF INTEREST
# LIES INSIDE THE BAND WHERE THE ANSWER DEPENDS ON THE INHIBITOR PROGRAMME.
# Phosphate therefore does not select a ceiling. It selects a REQUIREMENT:
# this water needs a phosphate-capable programme, and what the ceiling is
# depends on whether one is dosed. Reporting that is honest; inventing a
# threshold inside the band to make phosphate bind would be fitting.
#
# The DOE study brackets it experimentally, which is why it is worth trusting:
#   * bench heated surface, synthetic MWW_NF at four cycles, NO inhibitor,
#     SI_tcp +3.3 to +4.0 -> hydroxyapatite deposited, the only crystalline
#     phase found by XRD.
#   * pilot towers B and C, 5 ppm polymaleic acid at pH 7.8 -> orthophosphate
#     stayed at 2.0-3.5x makeup, i.e. it did NOT precipitate.
# Same mineral, same saturation range, opposite outcome, decided by the
# inhibitor. [C 10.2172/1063876 sections 3.2.4 and 4.2.5]
PHOSPHATE_SCREEN = {
    "uninhibited": 0.0,          # thermodynamic saturation
    "typical_inhibited": 3.18,   # IWC-11-77 SR 1500
    "stressed_inhibited": 5.10,  # IWC-11-77 SR 125,000
}


PHOSPHATE_PROGRAMME = {
    # A DECLARED site input, not a physical constant. Which one applies is a
    # fact about the inhibitor programme the plant actually doses, and it is
    # the second thing a site survey has to return after the water analysis.
    #
    #   None       phosphate is screened and reported, and binds nothing.
    #              The honest default for an uncharacterised site.
    #   "standard" SR 1500, the bottom of the published typical inhibited
    #              band. IWC-11-77 Table 7.
    #   "stressed" SR 125,000, the published stressed limit -- a formulation
    #              designed for extreme conditions. Never assume it.
    #
    # The DOE study brackets both ends experimentally: no inhibitor and
    # SI_tcp +3.3 to +4.0 deposited hydroxyapatite; 5 ppm polymaleic acid at
    # pH 7.8 and the same saturation did not precipitate at all.
    # [C 10.2172/1063876 sections 3.2.4 and 4.2.5; IWC-11-77 Table 7]
    "standard": PHOSPHATE_SCREEN["typical_inhibited"],   # 3.18
    "stressed": PHOSPHATE_SCREEN["stressed_inhibited"],  # 5.10
}


def temperature_floor_for_silica(makeup, cycles, si_limit=0.0,
                                 lo=1.0, hi=95.0):
    """Minimum water temperature at which amorphous silica stays at or below
    `si_limit` at `cycles` cycles of concentration.

    THE CHEMICAL FREE-COOLING FLOOR.

    Every other constraint in this package is a CEILING on temperature:
    calcite and calcium phosphate are retrograde, so they get worse as the
    water gets hotter and the danger is a hot tube skin. Amorphous silica is
    prograde and inverts that entirely -- it gets worse as the water gets
    COLDER, so it imposes a FLOOR, and the danger is a cold tower basin.

    That matters far more in a liquid-cooled data centre than in a chiller
    plant, because the single biggest energy lever there is free cooling, and
    free cooling means deliberately driving the facility water as cold as the
    wet bulb allows. A thermal-only economizer will do exactly that, and on a
    silica-bearing water it walks straight into precipitation -- at the tower
    basin and on the CDU plate, neither of which any thermal model looks at.

    Returns the floor in degrees Celsius. Returns `lo` when the water is
    below the limit even at the coldest temperature considered, i.e. there is
    no floor and free cooling is chemically unbounded.

    Silica saturation in this model is independent of pH below about pH 9, so
    unlike every other limit here this floor cannot be bought with acid. It
    is a hard thermal boundary or it is nothing.
    """
    conc = makeup.concentrate(cycles)
    m_si = conc.molality()["SiO2"]
    if m_si <= 0.0:
        return float(lo)

    def si(T_c):
        return math.log10(max(m_si, 1e-30)) - log_k_silica_am(T_c) - si_limit

    if si(lo) <= 0.0:
        return float(lo)          # already safe at the coldest point
    if si(hi) > 0.0:
        return float(hi)          # no temperature in range is safe
    return float(brentq(si, lo, hi, xtol=1e-4))


def limits_for_programme(programme=None, base=None):
    """Operating limits, with calcium phosphate promoted to a binding limit
    only when a treatment programme is DECLARED.

    Undeclared means phosphate binds nothing -- which is the honest state for
    a site nobody has surveyed, and is why `phosphate_screen()` exists to
    report the requirement separately.
    """
    limits = dict(OPERATING_LIMITS if base is None else base)
    if programme is None:
        return limits
    if programme not in PHOSPHATE_PROGRAMME:
        raise ValueError(
            f"unknown phosphate programme {programme!r}; expected None or one "
            f"of {tuple(PHOSPHATE_PROGRAMME)}")
    limits["SI_tcp"] = PHOSPHATE_PROGRAMME[programme]
    return limits


def phosphate_screen(water, T_c, pH=None):
    """Screen a water for calcium phosphate risk. Returns (verdict, SI_tcp).

    Not a ceiling -- a requirement on the treatment programme. See the note
    above OPERATING_LIMITS for why phosphate cannot bind a ceiling on the
    evidence available. [U] on the SI/SR mapping: a saturation ratio is only
    comparable to our index if it was computed against the same Ksp, and the
    source does not state its constant.
    """
    si = saturation_state(water, T_c, pH)["SI_tcp"]
    if si <= PHOSPHATE_SCREEN["uninhibited"]:
        v = "undersaturated: no phosphate programme needed"
    elif si <= PHOSPHATE_SCREEN["typical_inhibited"]:
        v = "supersaturated but within the range a standard programme holds"
    elif si <= PHOSPHATE_SCREEN["stressed_inhibited"]:
        v = ("PHOSPHATE PROGRAMME REQUIRED: above the published typical "
             "inhibited limit, below the stressed limit. The ceiling here is "
             "set by the inhibitor, not by the water. Site data needed.")
    else:
        v = ("PHOSPHATE UNCONTROLLABLE: above the published stressed limit, "
             "where more chemical does not help.")
    return v, si


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
    # Calcium phosphate is retrograde -- the DOE study found hydroxyapatite
    # on a HEATER, not in the basin -- so it is evaluated at the tube skin
    # alongside calcite. dH is -20 kcal/mol for beta-TCP and -36.155 for
    # hydroxyapatite, both strongly negative for dissolution as written.
    "SI_tcp": "hot",
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
    # This function takes (T_c, water) -- reversed from every other function
    # in this module, which take (water, T_c). Five call sites use it
    # correctly, so the signature is left alone rather than churned; but a
    # swapped call previously died with a bare TypeError deep inside
    # _vant_hoff. Refuse it by name instead.
    if isinstance(T_c, Water) or not isinstance(water, Water):
        raise TypeError(
            "ph_saturation_brucite takes (T_c, water) -- note the order is "
            "reversed from the rest of this module, which takes (water, T_c)")
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


# ---------------------------------------------------------------------------
# The analysis the controller actually runs on -- 10 September 2026
# ---------------------------------------------------------------------------
# `ARAMCO_RECLAIMED` above transcribes Table 1 of Badruzzaman et al. (2022)
# faithfully and is kept unchanged. But that table is NOT an analysis of any
# water, and this is provable from the table itself:
#
#   Its columns are "Raw Groundwater | Reclaimed Min | Ave | Max", and the
#   MAX column's ions sum to 3557 mg/L against its own stated TDS of 1800 --
#   nearly double. No sample can do that. The Min/Ave/Max columns are
#   INDEPENDENT PER-ION MARGINALS over a monitoring campaign: the highest
#   sodium ever seen beside the highest sulfate ever seen, from different
#   days. The Raw Groundwater column, which IS a sample, closes cleanly
#   (charge +3.9 %, TDS -1.2 %), so the laboratory method is sound.
#
#   Treating the "Ave" column as a water is therefore a category error, not a
#   transcription error, and no single-ion correction can repair it. That is
#   the true content of defect 17.
#
# The SAME PILOT was reported as one coherent analysis in the trade press:
# Badruzzaman, Abdul, Al-Malki, Al-Wohaib, Samad and Jutail, "Use of Treated
# Sewage Effluent as Cooling Tower Makeup Water - A Pilot Study", Water
# Technology, January 2021. Saudi Aramco, Abqaiq. [C]
#
#   TDS 1500, Ca 106, Mg 41, Na 310, Cl 528, SO4 300, HCO3 105,
#   TOC 5, phosphate 8.  Potassium and nitrate are not given there and are
#   carried over from the 2022 table [A].
#
# It closes on both objective tests (charge -1.2 %, TDS -4.5 %) and it is the
# operating engineers' own account of the water they actually ran.
#
# THE PILOT ALSO GIVES A HARD VALIDATION TARGET, which no model here was
# fitted to:
#     groundwater at COC 2.0  ->  "severe scaling on the condenser surfaces"
#     TSE        at COC 3.5  ->  "condenser surface was clean without mineral
#                                 deposit formation"
#     reported LSI 0 to 0.5
#
# SILICA IS STILL UNMEASURED, and this is now the single open input.
# **Neither Aramco publication reports silica at all** -- the 2022 paper
# mentions it once, as the compound class "magnesium silicates", and the 2021
# field article not at all. The value below is therefore an ASSUMPTION carried
# from a DIFFERENT WATER TYPE: Al-Mutaz & Al-Anezi (2004), King Saud
# University / Riyadh Water Treatment Project, whose own text puts brackish
# water generally in the range 20-60 mg/L. It was already used at 26.8 mg/L
# elsewhere in this package before being declared here.
#
# WHY THE IMPORT IS NEVERTHELESS DEFENSIBLE, and it is a mechanism rather than
# a hope: dissolved silica does not decrease significantly through primary or
# secondary sewage treatment -- it passes through essentially unchanged. [C]
# So the silica in a treated sewage effluent is approximately the silica of the
# municipal supply that became the sewage, and Al-Mutaz & Al-Anezi measured
# exactly that supply for Riyadh. The two waters are linked by the treatment
# train, not merely by geography.
#
# That makes 26.8 mg/L a reasoned estimate rather than an arbitrary borrowing.
# It is still not a measurement of THIS water, and the mechanism carries its
# own caveat: Eastern Province municipal supply is partly desalinated seawater,
# which is very low in silica, so a blended supply could sit well below 26.8.
# The published brackish range is 20-60 mg/L and the industry fouling threshold
# is 120-180 mg/L, so the plausible band is wide and entirely below the
# threshold -- which is why the CEILING, not the fouling risk, is what moves.
#
# It is also the BINDING MINERAL, so the ceiling rests on it. One silica assay
# on a real plant's makeup water is the highest-value measurement in the
# project.
ARAMCO_FIELD_VALIDATED = balance_sodium(Water(
    name="Aramco TSE, Water Technology 2021 field analysis + assumed Gulf silica",
    Na=310.0, K=25.0, Ca=106.0, Mg=41.0,
    Cl=528.0, SO4=300.0, HCO3=105.0, NO3=12.0,
    SiO2=GULF_SILICA_MG_L,
    # DEFECT 29. Phosphate is MEASURED in this water -- 8 mg/L in the 2021
    # field account, 8.15 mg/L in the 2022 table. It is carried here for the
    # same reason silica is not: an unmeasured zero is not a measurement.
    # The distinction matters and is the whole point of defect 29 -- silica
    # is an ASSUMPTION imported from a different water, phosphate is a
    # measurement of THIS one.
    PO4=8.0,
    pH=7.4, TDS=1500.0,
))

# The same water with silica at zero, for the sensitivity the ceiling rests on.
ARAMCO_FIELD_NO_SILICA = balance_sodium(Water(
    name="Aramco TSE, Water Technology 2021 field analysis, silica omitted",
    Na=310.0, K=25.0, Ca=106.0, Mg=41.0,
    Cl=528.0, SO4=300.0, HCO3=105.0, NO3=12.0,
    SiO2=0.0, PO4=8.0, pH=7.4, TDS=1500.0,
))


# ---------------------------------------------------------------------------
# US DOE / NETL reference waters -- DEFECT 29 benchmark
# ---------------------------------------------------------------------------
# Vidic, Dzombak & Landis (2012), DE-NT0006550, Table 2.3.1. Three treated
# municipal wastewaters from the Franklin Township Municipal Sanitary
# Authority, Murrysville PA, each an average of weekly samples over a summer.
# Transcribed verbatim. Na and K were NOT measured, so they are carried as
# zero and these waters are NOT charge-balanced -- they are used only as a
# saturation benchmark, never as a controller input, and
# require_valid_analysis() will correctly refuse them.
#
# Alkalinity is reported as mg/L CaCO3 and converted to HCO3 by 61.017/50.04.
# SiO2 is carried as zero because THE REPORT NEVER MEASURES IT; that is the
# honest transcription and the reason the silica_declared check exists.

DOE_MWW = Water(
    name="DOE secondary treated MWW (FTMSA)",
    Ca=33.3, Mg=6.55, Na=0.0, K=0.0,
    HCO3=123.0 * 61.017 / 50.04, SO4=67.0, Cl=199.0,
    NO3=9.62 * 62.004 / 14.007,        # reported as NO3-N
    SiO2=0.0, PO4=9.98, pH=7.16, TDS=644.0)

DOE_MWW_NF = Water(
    name="DOE nitrified-filtered MWW (FTMSA)",
    Ca=46.7, Mg=11.1, Na=0.0, K=0.0,
    HCO3=25.1 * 61.017 / 50.04, SO4=57.8, Cl=212.0,
    NO3=12.1 * 62.004 / 14.007,
    SiO2=0.0, PO4=7.16, pH=6.65, TDS=362.0)

DOE_MWW_NFG = Water(
    name="DOE nitrified-filtered-GAC MWW (FTMSA)",
    Ca=39.8, Mg=8.44, Na=0.0, K=0.0,
    HCO3=44.2 * 61.017 / 50.04, SO4=59.5, Cl=162.0,
    NO3=11.8 * 62.004 / 14.007,
    SiO2=0.0, PO4=8.46, pH=7.94, TDS=439.0)

# CORRECTED 11 Sep 2026, and the correction was earned by an external agent.
#
# There are TWO synthetic MWW_NF recipes in this report and they are not the
# same water. Table 2.3.2 (p. 2-14) is the general recipe used for the
# chapter 2/3 bench work. Table 4.2.1 (p. 4-13) is the one that governs
# CHAPTER 4 -- the batch tests, the bench recirculating tests and the heated
# surface study, which is to say the experiment that produced the
# hydroxyapatite XRD result this package benchmarks against.
#
# They differ where it matters most:
#
#              Table 2.3.2      Table 4.2.1 (chapter 4)
#   Na             8.60 mM          9.80 mM
#   HCO3           0.40 mM          1.60 mM    <-- FOUR TIMES the alkalinity
#
# Using the wrong one understates carbonate saturation on the very water the
# benchmark claims calcite is undersaturated in. That would have made the
# benchmark easier to pass for the wrong reason, which is the failure mode
# this whole register exists to prevent.
#
# NO3 is printed "as N", so 1.20 mM N is 1.20 mM NO3 and the mass conversion
# is unchanged. [C 10.2172/1063876 Table 4.2.1, PDF p. 101]
DOE_SYN_MWW_NF_COC4 = Water(
    name="DOE SynMWW_NF at CoC4 (Table 4.2.1, chapter 4)",
    Ca=4.00 * 40.078, Mg=1.60 * 24.305, Na=9.80 * 22.990, K=0.48 * 39.098,
    HCO3=1.60 * 61.017, SO4=3.50 * 96.06, Cl=11.2 * 35.453,
    NO3=1.20 * 62.004, SiO2=0.0, PO4=0.48 * 94.971, pH=7.2)

# The chapter 2/3 general recipe, retained so the two can be compared and so
# nobody re-imports it into a chapter 4 benchmark by accident.
DOE_SYN_MWW_NF_COC4_TABLE_2_3_2 = Water(
    name="DOE SynMWW_NF at CoC4 (Table 2.3.2, general)",
    Ca=4.00 * 40.078, Mg=1.60 * 24.305, Na=8.60 * 22.990, K=0.48 * 39.098,
    HCO3=0.40 * 61.017, SO4=3.50 * 96.06, Cl=11.2 * 35.453,
    NO3=1.20 * 62.004, SiO2=0.0, PO4=0.48 * 94.971, pH=7.2)

DOE_SYN_MWW_COC4 = Water(
    name="DOE SynMWW at CoC4 (Table 2.3.2)",
    Ca=4.00 * 40.078, Mg=1.60 * 24.305, Na=13.0 * 22.990, K=0.48 * 39.098,
    HCO3=6.00 * 61.017, SO4=3.50 * 96.06, Cl=11.2 * 35.453,
    NO3=0.0, SiO2=0.0, PO4=0.48 * 94.971, pH=8.8)


# ---------------------------------------------------------------------------
# THE MEASURED SAUDI TSE ANALYSIS -- found 11 September 2026
# ---------------------------------------------------------------------------
# AlMajnouni, A.D. and Jaffer, A.E. (Saudi Aramco, P&CSD/PED, Dhahran),
# "Effective Monitoring of Non-Chromate Chemical Treatment Programs for
# Refinery Cooling Systems Using Sewage Water as Make-Up", NACE International
# Annual Conference, Paper No. 577. Table 1, "TYPICAL SECONDARY TREATED
# SEWAGE EFFLUENT MAKE-UP ANALYSIS", Riyadh Refinery Cooling Tower No. 1.
#
# THIS IS THE ASSAY THE PACKAGE SPENT A MONTH LOOKING FOR. It is Saudi, it is
# treated sewage effluent, it is COOLING TOWER MAKEUP rather than blowdown or
# circulating water, it is the operator's own laboratory, and it reports
# SILICA AND PHOSPHATE alongside the full major-ion set.
#
#   SiO2 = 18 mg/L, MEASURED.
#
# Every silica-dependent result in this package until now rested on 26.8 mg/L
# imported from Al-Mutaz & Al-Anezi's Riyadh BRACKISH GROUNDWATER -- a
# different water entirely. That import is now superseded for any question
# about Saudi TSE.
#
# WHAT DOES NOT TRANSFER. This is Riyadh Refinery and the NACE paper is from
# the 1990s. Badruzzaman et al. (2022) is Dhahran, twenty-odd years later, and
# reports TOTAL PHOSPHATE AT 8.0 mg/L against this water's 1.0 -- an eightfold
# difference between two Saudi TSE sources. Phosphate is a treatment-plant
# property, not a regional constant, and neither number may be used for the
# other site.
#
# WHAT THE MODEL CANNOT HOLD. The analysis carries ammonia 16 mg/L and
# nitrite 31 mg/L. `SPECIES` has neither, so they are dropped, and the charge
# balance below is computed without them. Including ammonium as NH4+ would
# move it from -5.25 % to roughly -2 %. The omission is recorded rather than
# patched, because inventing a species to improve a balance is how defect 17
# started.
ARAMCO_RIYADH_REFINERY_TSE = Water(
    name="Aramco Riyadh Refinery secondary TSE makeup (NACE Paper 577 Table 1)",
    Ca=80.0, Mg=11.0, Na=222.0, K=15.0,
    HCO3=140.0 * 61.017 / 50.04,   # alkalinity 140 as CaCO3, converted
    SO4=326.0, Cl=216.0, NO3=3.0,
    SiO2=18.0,                     # MEASURED, not assumed
    PO4=1.0,                       # total phosphate; orthophosphate 0.6
    pH=7.44, TDS=1050.0,
)

# The operator's own numbers, for scoring the engine against something it did
# not produce. All from the same paper.
ARAMCO_RIYADH_FIELD_FACTS = {
    "cycles_range": (1.6, 4.0),
    "cycles_average": 2.9,
    "recommended_limit_cycles": 4.0,
    "recommended_max_pH": 8.0,
    "LSI": 1.4,
    "RSI": 5.1,
    "calcite_saturation_ratio": 9.0,   # they call this "more indicative"
    "acid_policy": "increase cycles WITHOUT the addition of sulfuric acid",
    "quote_on_indices":
        "The Langelier and Ryznar indices for this water 1.4 and 5.1 "
        "respectively. The calcite saturation, which is more indicative of "
        "the calcium carbonate scaling potential is 9.0.",
}


# ---------------------------------------------------------------------------
# WHAT THIS MODEL DOES NOT COMPUTE -- DEFECT 35, resolved
# ---------------------------------------------------------------------------
# Defect 35 was opened because the engine returns 6.56 cycles on the Aramco
# Riyadh Refinery water at pH 8.0 while the operator concludes "the cycles of
# concentration should be limited to 4 at a maximum pH of 8.0". Being 64 %
# more permissive than the plant operator is the direction that scales a
# condenser, so it was registered rather than explained away.
#
# It resolves as a CATEGORY DIFFERENCE, and the paper supplies the evidence.
#
# Work backwards from their number. At 4 cycles and pH 8.0 this engine puts
# that water at a calcite saturation ratio of 42.5, i.e. SI 1.63. So Aramco's
# practical tolerance is SI 1.6-1.7. The PUBLISHED INHIBITED BAND for calcite
# is SR 135-150, i.e. SI 2.13-2.18 (IWC-11-77 Table 7). **Aramco operate about
# three times more conservatively than the inhibitor chemistry alone requires**,
# and this module's SI_calcite <= 2.0 already sits below the published band.
#
# The paper says why, and none of the reasons is calcium carbonate:
#
#   "process leaks consisting of amines and hydrocarbons prevented an increase
#    in cycles of concentration DUE TO INCREASED TURBIDITY. Hence, increased
#    blowdown was mandatory."
#
#   "Corrosion rates can be reduced by increasing the cycles of concentrations
#    or increasing the pH above 8" -- corrosion as a competing objective
#
# and they ran without sulfuric acid by design, which caps the pH lever.
#
# SO THE MODEL IS NOT WRONG AND NEITHER ARE THEY. It computes a SCALING
# ceiling. They set an OPERATING ceiling, which is the minimum over scaling,
# fouling, turbidity, corrosion, biological control and whatever the process
# is leaking that week. A scaling ceiling is an upper bound on an operating
# ceiling and must never be quoted as one.
#
# The correct fix is therefore to RELABEL THE OUTPUT, not to move the limit.
# Moving SI_calcite to 1.7 to match one plant would be fitting a
# thermodynamic constant to one site's housekeeping.
CONSTRAINTS_NOT_MODELLED = (
    "particulate fouling and turbidity -- the constraint that actually "
    "stopped the Aramco pilot, caused by process leaks rather than chemistry",
    "biological fouling and biocide demand",
    "corrosion rate, beyond the single calcite corrosion floor this model "
    "carries; no metallurgy, no galvanic couple, no pitting",
    "inhibitor programme performance, which sets how much supersaturation is "
    "actually tolerable and varies by vendor and formulation",
    "suspended solids and their effect on heat-transfer surfaces",
    "process contamination -- amines, hydrocarbons, oil, ammonia",
)


def scaling_ceiling_caveat(ceiling_cycles):
    """The sentence that must travel with every ceiling this engine reports.

    Returns prose rather than a number on purpose: the caveat is the finding,
    and a caller that wants only the number should not be able to get it
    without this.
    """
    return (
        f"{ceiling_cycles:.2f} cycles is a SCALING ceiling, computed from "
        f"mineral saturation alone. The operating ceiling is the minimum over "
        f"scaling and {len(CONSTRAINTS_NOT_MODELLED)} other constraints this "
        f"model does not compute. On the one water where a plant operator has "
        f"published both, the operator's limit was 39 % lower than the "
        f"scaling ceiling and the binding constraint was turbidity from "
        f"process leaks, not carbonate. Treat this as an upper bound.")
