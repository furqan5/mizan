"""
FURQAN / MIZAN :: the discharge ceiling, which is not the scaling ceiling.

WHAT THIS ADDS, AND WHY IT WAS A HOLE.

Every ceiling in this package until now has been a SATURATION limit: how far
can the water be concentrated before a mineral comes out of solution. That is
a physics question and the engine answers it well.

It is not the only ceiling. Blowdown has to go somewhere, and where it goes
has a permit. A controller that recommends six cycles on a water whose
blowdown breaches its discharge consent at two has not optimised anything --
it has written the operator a fine.

Before this module the model could do exactly that.

THE JURISDICTION MODELLED

Royal Commission Environmental Regulations 2015 (RCER-2015), Volume I,
Kingdom of Saudi Arabia, Royal Commission for Jubail and Yanbu. This governs
Jubail and Yanbu Industrial Cities -- which includes Hadeed and the Marafiq
service area whose tariffs this package's economics are built on. It does NOT
govern Dhahran, which is where the Aramco pilot that supplies our makeup
analysis was run. That distinction matters and is enforced below rather than
assumed.

THE TWO ROUTES, AND WHY THE CHOICE IS THE WHOLE POINT

RCER 3.6.4: blowdown "shall be designated as variance stream if it is in
compliance with standards provided in Table 3C before dilution with the
non-contact cooling water flow."

    Table 3C   direct discharge to coastal waters, as a variance stream.
               The cheap route. Tight on nutrients and metals.
    Table 3B   pretreatment standard at the point of discharge to the
               central wastewater treatment facility. The route taken when
               3C cannot be met. Tight on TDS and chloride.

So the operator faces a genuine either/or, and which limit binds depends on
which route is taken. A plant that cannot meet 3C is not forbidden to operate
-- it pays to send blowdown to the IWTP instead, and then a DIFFERENT
parameter caps its cycles.

THE FINDING THAT MADE THIS URGENT

RCER 3.6.3 prohibits sulphuric acid as a scaling inhibitor and REQUIRES
polyphosphonates. Table 3C caps total phosphorus at 1 mg/L monthly average
and 2 mg/L maximum. The regulation mandates dosing a phosphorus-bearing
inhibitor into a water whose phosphorus discharge it then limits to 1 mg/L.
That tension is real, it is in the same document, and it is not resolved
here -- it is reported.
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import chemistry as chem            # noqa: E402


# Mass conversions between what a lab reports and what a regulation limits.
P_PER_PO4 = 30.974 / 94.971        # total phosphorus as P, from PO4
N_PER_NO3 = 14.007 / 62.004        # nitrogen as N, from NO3


# ---------------------------------------------------------------------------
# RCER-2015 Table 3C -- direct discharge to coastal waters (variance stream)
# ---------------------------------------------------------------------------
# Transcribed from RCER-2015 Volume I, Table 3C, pp. 63-64. Only the
# parameters this model can actually compute from a water analysis are
# carried; the metals, organics and biological limits are real and are listed
# in NOT_MODELLED below so their absence is declared rather than silent.
#
# Two columns: an absolute maximum and a monthly average. The monthly average
# is the operative one for continuous operation.
RCER_TABLE_3C = {
    "P_as_P":  {"max": 2.0,  "monthly_avg": 1.0,  "unit": "mg/L"},
    "NO3":     {"max": 10.0, "monthly_avg": 1.0,  "unit": "mg/L"},
    "pH":      {"min": 6.0,  "max": 9.0,          "unit": "pH units"},
}

# ---------------------------------------------------------------------------
# RCER-2015 Table 3B -- pretreatment to the central wastewater facility
# ---------------------------------------------------------------------------
# Transcribed from RCER-2015 Volume I, Table 3B, p. 61. Jubail column.
RCER_TABLE_3B_JUBAIL = {
    "TDS": {"max": 2000.0, "unit": "mg/L"},
    "Cl":  {"max": 1000.0, "unit": "mg/L"},
}

NOT_MODELLED = (
    "Table 3C also limits aluminium, ammonia, arsenic, barium, BOD5, cadmium, "
    "COD, chlorinated hydrocarbons, residual chlorine, chromium, cobalt, "
    "copper, cyanide, fluoride, iron, lead, manganese, molybdenum, mercury, "
    "nickel, oil and grease, dissolved oxygen, PAH, phenols, salinity, "
    "selenium, sulfide, TKN, TOC, vanadium, zinc, total suspended solids, "
    "turbidity, temperature differential and total coliform. NONE of those "
    "are computable from a major-ion analysis, so none is checked here. A "
    "pass from this module is a pass on the parameters it can see and is not "
    "a compliance statement."
)

JURISDICTION_NOTE = (
    "RCER-2015 governs Jubail and Yanbu Industrial Cities. It does NOT govern "
    "Dhahran, where the Aramco pilot supplying this package's makeup analysis "
    "was run. Applying these limits to that water answers the question 'what "
    "if this water were used in Jubail', which is a legitimate question and a "
    "different one from 'what did Aramco have to comply with'."
)


def _concentration_at(makeup, cycles, species):
    """Blowdown concentration of `species` at `cycles`, in mg/L.

    Blowdown carries the circulating concentration, which is the makeup
    concentration times the cycles of concentration. This holds for
    conservative species -- ones that are neither precipitated nor volatile.
    Phosphate is NOT strictly conservative if calcium phosphate deposits, so
    this is the CONSERVATIVE-TRACER estimate and it is an upper bound on what
    leaves in solution. Said plainly because an upper bound on discharge is
    the safe direction for a permit and the unsafe direction for a sales
    number.
    """
    return getattr(makeup, species) * cycles


def blowdown_quality(makeup, cycles):
    """Everything this model can compute about the blowdown at `cycles`."""
    po4 = _concentration_at(makeup, cycles, "PO4")
    return {
        "cycles": float(cycles),
        "P_as_P": po4 * P_PER_PO4,
        "PO4": po4,
        "NO3": _concentration_at(makeup, cycles, "NO3"),
        "Cl": _concentration_at(makeup, cycles, "Cl"),
        "TDS": makeup.tds() * cycles,
    }


def max_cycles_for_discharge(makeup, table=None, basis="monthly_avg",
                             lo=1.0, hi=30.0):
    """Highest cycles at which the blowdown still meets every limit we can
    compute. Returns (cycles, binding_parameter).

    Returns `lo` and the offending parameter when the MAKEUP ALONE already
    breaches, which is not a hypothetical: treated sewage effluent carrying
    8 mg/L of phosphate is at 2.6 mg/L as P before it is concentrated at all,
    against a Table 3C monthly average of 1.0.
    """
    table = RCER_TABLE_3C if table is None else table

    def worst(cy):
        q = blowdown_quality(makeup, cy)
        out = []
        for param, lim in table.items():
            if param == "pH":
                continue                      # not a function of cycles here
            cap = lim.get(basis, lim.get("max"))
            if cap is None or param not in q:
                continue
            out.append((q[param] - cap, param))
        return max(out) if out else (-math.inf, None)

    if worst(lo)[0] > 0:
        return float(lo), worst(lo)[1]
    if worst(hi)[0] <= 0:
        return float(hi), None

    a, b = lo, hi
    for _ in range(60):
        m = 0.5 * (a + b)
        if worst(m)[0] > 0:
            b = m
        else:
            a = m
    return float(a), worst(b)[1]


def binding_ceiling(makeup, T_hot, T_cold, pH=8.25, table=None,
                    basis="monthly_avg", limits=None):
    """The ceiling that actually binds: scaling or discharge, whichever is
    lower. This is the number a controller may use.

    Reporting only the scaling ceiling was the hole this module closes.
    """
    import sidestream as ss
    chem_c, chem_m = ss.ceiling_with(makeup, T_hot, T_cold, limits=limits,
                                     pH=pH)
    disc_c, disc_p = max_cycles_for_discharge(makeup, table, basis)
    if disc_c < chem_c:
        return {"cycles": disc_c, "binding": "DISCHARGE",
                "parameter": disc_p, "scaling_cycles": chem_c,
                "scaling_mineral": chem_m, "discharge_cycles": disc_c,
                "jurisdiction": JURISDICTION_NOTE, "caveat": NOT_MODELLED}
    return {"cycles": chem_c, "binding": "SCALING",
            "parameter": chem_m, "scaling_cycles": chem_c,
            "scaling_mineral": chem_m, "discharge_cycles": disc_c,
            "jurisdiction": JURISDICTION_NOTE, "caveat": NOT_MODELLED}
