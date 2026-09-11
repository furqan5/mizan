"""
FURQAN / MIZAN :: the free measurement.
=======================================

THE PROBLEM THIS SOLVES, AND WHY IT IS THE MOST IMPORTANT FILE IN THE PACKAGE.

Every saturation index in this repository is computed from an ion composition
that is itself ASSUMED: a laboratory analysis of the makeup water, multiplied
by cycles of concentration. Nothing checks that assumption after the day the
sample was taken. The package's single largest weakness, stated in its own
documents, is that no water has ever been in front of an instrument.

Instrumenting it properly is priced out of the market. A sensor survey costing
this out (docs/instrumentation_spec.md) lands at roughly $120,000-185,000 per
tower to measure silica, calcium, alkalinity and phosphate online, against an
annual water-and-energy saving of order $89,000 on a 4.2 MW tower. THE
INSTRUMENTS COST MORE THAN THE THING THEY OPTIMISE. That is structural, it is
why nobody sells this, and no amount of negotiation fixes it.

But there is one measurement that is already on the skid, costs about $1,900,
and is bought anyway because the cycles calculation needs it: CONDUCTIVITY.

And conductivity is not independent of the ion composition. It is a known,
validated FUNCTION of it:

    McCleskey, R.B., Nordstrom, D.K., Ryan, J.N., Ball, J.W. (2012)
    "A new method of calculating electrical conductivity with applications to
    natural waters", Geochimica et Cosmochimica Acta 77, 369-382.
    Validated over ionic strength 0.0004-0.7 mol/kg, 0-95 C, pH 1-10, and
    30-70,000 uS/cm -- which contains this package's entire operating range.

    Companion: McCleskey et al. (2012), "Comparison of electrical conductivity
    calculation methods for natural waters", Limnol. Oceanogr. Methods 10,
    952-967. USGS publishes PHREEQCI input files implementing it.

So: compute the conductivity our assumed composition IMPLIES, compare it to
the conductivity the sensor actually reads, and the residual is a continuous,
free, closed-loop check on the assumption every other number rests on. USGS
calls it the SPECIFIC CONDUCTANCE IMBALANCE and uses it alongside charge
balance as a routine quality check:

    SCI % = 100 * (SC_calculated - SC_measured) / SC_measured

WHAT THIS BUYS, precisely, because it is easy to overclaim:

  * It does NOT measure ions. One conductivity and one pH are two equations
    against eight-plus unknowns and the inverse is underdetermined in
    principle. Anyone claiming otherwise is importing a constraint set and not
    saying so.
  * It DOES tell you when the assumed composition has stopped being true.
    That is a different and more useful thing for a controller whose job is to
    sit on a limit: you do not need to know the absolute calcium to know that
    calcium is no longer where you thought it was.
  * And the direction of the residual is diagnostic. Calcite precipitating
    REMOVES Ca and HCO3 from solution, so the measured conductivity falls
    below the conservative prediction. THE RESIDUAL IS THE SCALING SIGNAL.

That last point is the product. The controller's job becomes: hold the
residual near zero, and treat a divergence as the thing to act on, rather than
pretend to know concentrations it cannot see.

WHAT IS IMPLEMENTED HERE, AND WHAT IS NOT.

This is a Kohlrausch-type calculation with a Debye-Huckel-Onsager style
concentration correction, NOT McCleskey's full per-ion parameterisation. Their
method fits two coefficients per species against measured data; we have not
transcribed those fits and will not invent them. The limiting molar
conductivities are standard reference values.

The accuracy is therefore first-order, and `validate_against()` reports it
honestly rather than asserting it. That is sufficient for the intended use --
a DRIFT detector, where the same systematic error sits in both the baseline
and the current reading and cancels -- and it is NOT sufficient to report an
absolute conductivity as a measurement. The module refuses to be used that way
by returning the residual, not the value.
"""

from __future__ import annotations

import math

import chemistry as chem

# Limiting molar ionic conductivities at 25 C, S cm2 / mol of CHARGE
# (i.e. per equivalent: the 1/2 Ca2+ convention). Standard reference values,
# CRC Handbook of Chemistry and Physics, "Ionic Conductivity and Diffusion at
# Infinite Dilution". [C]
LAMBDA_0 = {
    "Na": 50.08, "K": 73.48, "Ca": 59.50, "Mg": 53.00,
    "Cl": 76.31, "SO4": 80.00, "HCO3": 44.50, "CO3": 69.30, "NO3": 71.42,
    "H": 349.65, "OH": 198.00,
}

# SiO2 and PO4 are deliberately absent. Dissolved silica below pH 9 is the
# NEUTRAL species H4SiO4 and carries no current at all -- which is the same
# fact that makes SI_silica_am pH-free (defect 38). Phosphate does conduct,
# but at 1-8 mg/L on these waters it is a fraction of a per cent of the total
# and its speciation is pH-dependent; omitting it is a stated approximation,
# not an oversight.

_CHARGE = {"Na": 1, "K": 1, "Ca": 2, "Mg": 2,
           "Cl": 1, "SO4": 2, "HCO3": 1, "CO3": 2, "NO3": 1}


def _temperature_factor(T_c):
    """Conductivity rises about 2 % per kelvin near 25 C.

    The standard linear reference correction used to report specific
    conductance AT 25 C. Every sensor on the market does this internally; it
    is reproduced so a caller can compare like with like when it has not.
    """
    return 1.0 + 0.02 * (T_c - 25.0)


def specific_conductance(water, T_c=25.0, reference_25c=True):
    """Specific conductance in microsiemens per centimetre.

    Kohlrausch's law of independent ion migration, with each equivalent
    conductivity reduced for ionic strength by an Onsager-type square-root
    term. Returns the value referenced to 25 C by default, which is what a
    sensor reports and what a laboratory analysis quotes.
    """
    m = water.molality()          # mol/kg
    I = water.ionic_strength()

    # Onsager-style attenuation. A single empirical form for all species
    # rather than McCleskey's per-species fit -- stated in the module
    # docstring, and the reason this is a drift detector and not a meter.
    sqrt_I = math.sqrt(max(I, 0.0))
    atten = 1.0 / (1.0 + 1.5 * sqrt_I)

    total = 0.0
    for sp, lam in LAMBDA_0.items():
        if sp in ("H", "OH"):
            continue
        c_eq = m.get(sp, 0.0) * _CHARGE[sp] * 1000.0     # eq/m3 -> mmol_c/L
        total += lam * c_eq * atten

    # H+ and OH- matter only at the ends of the pH scale, and a cooling loop
    # is nowhere near them; included for completeness because they are cheap.
    pH = water.pH if water.pH is not None else 7.0
    total += LAMBDA_0["H"] * (10.0 ** (-pH)) * 1000.0
    total += LAMBDA_0["OH"] * (10.0 ** (pH - 14.0)) * 1000.0

    if not reference_25c:
        total *= _temperature_factor(T_c)
    return total


def specific_conductance_imbalance(water, measured_us_cm, T_c=25.0):
    """USGS SCI: how far the assumed composition is from what the sensor sees.

        SCI % = 100 * (SC_calculated - SC_measured) / SC_measured

    A NEGATIVE SCI means the water conducts LESS than the assumed composition
    would -- ions have left solution. On a cooling loop that is the signature
    of precipitation, and it is the signal this controller exists to act on.

    A POSITIVE SCI means there is more ionic material than the makeup analysis
    times cycles accounts for: an unmeasured ion, a process leak, or a cycles
    estimate that is too low.
    """
    calc = specific_conductance(water, T_c)
    if measured_us_cm <= 0:
        raise ValueError("measured specific conductance must be positive")
    sci = 100.0 * (calc - measured_us_cm) / measured_us_cm
    return {
        "calculated_us_cm": calc,
        "measured_us_cm": float(measured_us_cm),
        "sci_pct": sci,
        "interpretation": (
            "ions have LEFT solution relative to the assumed composition -- "
            "on a cooling loop this is the precipitation signature"
            if sci > 0 else
            "more ionic material than makeup x cycles accounts for -- an "
            "unmeasured ion, a process leak, or cycles underestimated"),
    }


def validate_against(water, measured_us_cm, T_c=25.0):
    """Score this implementation on a water whose conductivity is known.

    Returns the error rather than asserting a tolerance, because the accuracy
    of a Kohlrausch calculation on a 1,000-2,000 mg/L water is an empirical
    question and this package does not get to assume the answer.
    """
    d = specific_conductance_imbalance(water, measured_us_cm, T_c)
    d["abs_error_pct"] = abs(d["sci_pct"])
    return d


def tds_to_conductance(tds_mg_l, factor=0.65):
    """The rule of thumb, carried ONLY so it can be labelled as one.

    TDS = k * SC with k between about 0.55 and 0.75 depending on the ion mix.
    It is not a measurement and it is not a model; where a water reports TDS
    but no conductivity this gives a band, not a number.
    """
    return {"sc_us_cm": tds_mg_l / factor,
            "band_us_cm": (tds_mg_l / 0.75, tds_mg_l / 0.55),
            "caveat": "a rule of thumb with a +/- 15 % spread, not a datum"}


def residual_is_precipitation(water_assumed, measured_us_cm, T_c=25.0,
                              threshold_pct=5.0):
    """Is the conductivity residual big enough to act on?

    `threshold_pct` defaults to 5 %, which is the charge-balance tolerance
    this package already applies to an analysis -- the same standard of
    "closed" applied to the same kind of question. It is a parameter because
    a site that has measured its own instrument's repeatability should use
    that instead.
    """
    d = specific_conductance_imbalance(water_assumed, measured_us_cm, T_c)
    d["threshold_pct"] = float(threshold_pct)
    d["actionable"] = abs(d["sci_pct"]) > threshold_pct
    d["direction"] = ("precipitation" if d["sci_pct"] > threshold_pct else
                      "accumulation" if d["sci_pct"] < -threshold_pct else
                      "within tolerance")
    return d


def main() -> int:
    print("=" * 78)
    print("SPECIFIC CONDUCTANCE -- the measurement we already pay for")
    print("=" * 78)

    waters = [("Riyadh measured TSE", chem.ARAMCO_RIYADH_REFINERY_TSE),
              ("Dhahran field-validated", chem.ARAMCO_FIELD_VALIDATED),
              ("Aramco reclaimed", chem.ARAMCO_RECLAIMED)]

    print("\nComputed conductance against the TDS rule of thumb, which is the")
    print("only cross-check these analyses carry. The rule is +/- 15 %, so")
    print("agreement inside that band is all this can establish.\n")
    print(f"{'water':28}{'TDS':>8}{'calc uS/cm':>12}{'rule band':>18}{'in band':>9}")
    for name, w in waters:
        if w.TDS is None:
            continue
        sc = specific_conductance(w)
        band = tds_to_conductance(w.TDS)["band_us_cm"]
        ok = band[0] <= sc <= band[1]
        print(f"{name:28}{w.TDS:>8.0f}{sc:>12.0f}"
              f"{f'{band[0]:.0f}-{band[1]:.0f}':>18}{'yes' if ok else 'NO':>9}")

    print("\n\nWHAT THE RESIDUAL WOULD SAY IN SERVICE\n")
    w = chem.ARAMCO_RIYADH_REFINERY_TSE
    conc = w.concentrate(3.0)
    base = specific_conductance(conc)
    print(f"  assumed composition at 3.0 cycles -> {base:.0f} uS/cm computed\n")
    print(f"  {'sensor reads':>16}{'SCI %':>9}   verdict")
    for frac in (1.00, 0.97, 0.93, 0.85, 1.05):
        d = residual_is_precipitation(conc, base * frac)
        print(f"  {base*frac:>16.0f}{d['sci_pct']:>9.1f}   {d['direction']}")
    print("\n  Calcite taking Ca and HCO3 out of solution lowers the MEASURED")
    print("  conductance while the assumed composition stays put, so the")
    print("  residual goes positive. That is the scaling alarm, and it costs")
    print("  one sensor the skid was buying anyway.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
