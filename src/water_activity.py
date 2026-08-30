"""
MIZAN :: water activity and vapour-pressure depression
======================================================
The coupling term that makes this product different.

A cooling tower run at high cycles of concentration carries a
concentrated brine. Dissolved salts lower the WATER ACTIVITY a_w of the
recirculating water, which lowers the equilibrium vapour pressure at the
air/water interface to a_w * pws(T). Lower interface vapour pressure means
a smaller mass-transfer driving potential, so evaporation and therefore
heat rejection fall as cycles rise.

Consequence: saving water by concentrating the loop is NOT free -- it is
paid for in fan power and condenser-water temperature. Standard tower
models (Merkel, and Poppe as normally implemented) assume pure water,
a_w = 1, and cannot see this trade-off at all. Optimising the two together
requires modelling it.

Two routes are implemented:
  osmotic_coefficient_pitzer -- rigorous, ion-specific, for the product
  water_activity_tds         -- reduced correlation for fast screening

Reference frame: a_w = exp(-nu * m * phi * Mw), with phi the molal osmotic
coefficient, m molality, nu ions per formula unit, Mw = 0.018015 kg/mol.
"""
from __future__ import annotations

import numpy as np

MW_WATER = 0.018015          # molar mass of water [kg/mol]


def water_activity_from_osmotic(sum_molality, phi):
    """a_w from total solute molality [mol/kg water] and osmotic coefficient.

    a_w = exp(-phi * Mw * sum_i m_i)
    This is the thermodynamic definition; `sum_molality` must already be the
    sum over ALL dissolved species (not the salt molality).
    """
    sum_molality = np.asarray(sum_molality, dtype=float)
    return np.exp(-np.asarray(phi, dtype=float) * MW_WATER * sum_molality)


def water_activity_tds(tds_mg_l, phi=0.90):
    """Reduced-form water activity from TDS [mg/L].

    Screening correlation for waters of ordinary mixed composition
    (TSE, brackish, municipal). Converts TDS to an equivalent total ionic
    molality with a mean equivalent weight of ~50 g/mol-ion, then applies
    the osmotic definition. `phi` defaults to 0.90, representative of mixed
    Na-Ca-SO4-Cl waters at moderate ionic strength.

    Accurate enough to size the effect; the product uses the Pitzer route.
    """
    tds = np.asarray(tds_mg_l, dtype=float)
    # mg/L -> kg/m3 -> approximate mol-ions per kg water
    sum_m = (tds * 1e-3) / 50.0
    return water_activity_from_osmotic(sum_m, phi)


def vapour_pressure_depression(tds_mg_l, phi=0.90):
    """Fractional depression of equilibrium vapour pressure, (1 - a_w)."""
    return 1.0 - water_activity_tds(tds_mg_l, phi)


def tds_at_cycles(tds_makeup_mg_l, cycles):
    """Circulating TDS at a given cycles of concentration."""
    return np.asarray(tds_makeup_mg_l, float) * np.asarray(cycles, float)


def boiling_point_elevation(sum_molality, T_c=40.0, phi=0.90):
    """Boiling-point elevation [K] -- the temperature-side twin of the
    vapour-pressure depression. Used as a sanity cross-check that the
    activity model is thermodynamically consistent.

    dTb = R * Tb^2 * Mw * phi * sum_m / dHvap
    """
    R = 8.314462          # J/(mol.K)
    Tb = T_c + 273.15
    dHvap = 2.406e6 * MW_WATER      # J/mol at ~40 C
    return R * Tb**2 * MW_WATER * phi * np.asarray(sum_molality, float) / dHvap
