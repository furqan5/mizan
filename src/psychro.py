"""
MIZAN :: psychrometrics
=======================
Self-contained moist-air property library, ASHRAE Handbook of Fundamentals
(2017) Ch.1 formulation. Implemented in-house rather than taken from a
library so that every constant is auditable and the whole thermal core can
be shipped on an edge controller with no third-party runtime.

Validated in tests/test_psychro.py against ASHRAE published table values.

Sign / unit convention
----------------------
T      dry-bulb temperature            [degC]
Twb    thermodynamic wet-bulb          [degC]
p      total (barometric) pressure     [Pa]
W      humidity ratio          [kg water / kg dry air]
h      specific enthalpy       [kJ / kg dry air]
pws    saturation vapour pressure      [Pa]
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

# --- constants ------------------------------------------------------------
P_ATM = 101_325.0          # standard atmosphere                      [Pa]
R_DA = 287.042             # gas constant, dry air              [J/(kg.K)]
R_W = 461.524              # gas constant, water vapour         [J/(kg.K)]
MW_RATIO = R_DA / R_W      # 0.621945, ASHRAE Eq. (22)                 [-]
T0 = 273.15                # 0 degC in kelvin                          [K]


def sat_vapour_pressure(T):
    """Saturation vapour pressure over liquid water / ice [Pa].

    ASHRAE Fundamentals 2017 Eq. (5) for -100..0 degC (over ice) and
    Eq. (6) for 0..200 degC (over liquid water). Hyland & Wexler basis.
    """
    T = np.asarray(T, dtype=float)
    Tk = T + T0
    ice = T < 0.0

    # Eq. (5) -- over ice
    ln_ice = (-5.6745359e3 / Tk + 6.3925247 - 9.677843e-3 * Tk
              + 6.2215701e-7 * Tk**2 + 2.0747825e-9 * Tk**3
              - 9.484024e-13 * Tk**4 + 4.1635019 * np.log(Tk))
    # Eq. (6) -- over liquid water
    ln_liq = (-5.8002206e3 / Tk + 1.3914993 - 4.8640239e-2 * Tk
              + 4.1764768e-5 * Tk**2 - 1.4452093e-8 * Tk**3
              + 6.5459673 * np.log(Tk))

    return np.exp(np.where(ice, ln_ice, ln_liq))


def humidity_ratio_from_vp(pv, p=P_ATM):
    """Humidity ratio from vapour partial pressure. ASHRAE Eq. (20)."""
    pv = np.asarray(pv, dtype=float)
    return MW_RATIO * pv / (p - pv)


def vapour_pressure_from_W(W, p=P_ATM):
    """Inverse of humidity_ratio_from_vp. ASHRAE Eq. (20) rearranged."""
    W = np.asarray(W, dtype=float)
    return p * W / (MW_RATIO + W)


def sat_humidity_ratio(T, p=P_ATM, aw=1.0):
    """Saturation humidity ratio at temperature `T`.

    `aw` is the WATER ACTIVITY of the liquid phase (1.0 for pure water).
    Dissolved salts depress the equilibrium vapour pressure to aw * pws;
    this is the single hook through which cooling-tower water chemistry
    couples back into the thermal model. See mizan.water_activity.
    """
    return humidity_ratio_from_vp(aw * sat_vapour_pressure(T), p)


def enthalpy(T, W):
    """Moist-air specific enthalpy [kJ/kg dry air]. ASHRAE Eq. (30)."""
    T = np.asarray(T, dtype=float)
    W = np.asarray(W, dtype=float)
    return 1.006 * T + W * (2501.0 + 1.860 * T)


def humidity_ratio_from_wetbulb(T, Twb, p=P_ATM):
    """Humidity ratio from dry-bulb and thermodynamic wet-bulb.

    ASHRAE Eq. (33) above freezing, Eq. (34) below.
    """
    T = np.asarray(T, dtype=float)
    Twb = np.asarray(Twb, dtype=float)
    Wsw = sat_humidity_ratio(Twb, p)
    above = ((2501.0 - 2.326 * Twb) * Wsw - 1.006 * (T - Twb)) / \
            (2501.0 + 1.86 * T - 4.186 * Twb)
    below = ((2830.0 - 0.24 * Twb) * Wsw - 1.006 * (T - Twb)) / \
            (2830.0 + 1.86 * T - 2.1 * Twb)
    return np.maximum(np.where(Twb >= 0.0, above, below), 0.0)


def relative_humidity(T, W, p=P_ATM):
    """Relative humidity [0..1] from dry-bulb and humidity ratio."""
    return vapour_pressure_from_W(W, p) / sat_vapour_pressure(T)


def humidity_ratio_from_rh(T, rh, p=P_ATM):
    """Humidity ratio from dry-bulb and relative humidity [0..1]."""
    return humidity_ratio_from_vp(np.asarray(rh, float) * sat_vapour_pressure(T), p)


def _wetbulb_scalar(T, W, p):
    if W <= 0.0:
        lo = -100.0
    else:
        lo = -100.0
    f = lambda twb: humidity_ratio_from_wetbulb(T, twb, p) - W
    # wet-bulb is bounded above by dry-bulb
    hi = float(T)
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:                      # saturated / numerically degenerate
        return hi
    return brentq(f, lo, hi, xtol=1e-8, rtol=1e-12, maxiter=200)


def wetbulb(T, W, p=P_ATM):
    """Thermodynamic wet-bulb from dry-bulb and humidity ratio [degC].

    Inverts ASHRAE Eq. (33)/(34) by bracketed root find; robust because the
    residual is monotone in Twb over (-100 degC, T].
    """
    Ta = np.atleast_1d(np.asarray(T, dtype=float))
    Wa = np.atleast_1d(np.asarray(W, dtype=float))
    Ta, Wa = np.broadcast_arrays(Ta, Wa)
    out = np.array([_wetbulb_scalar(t, w, p) for t, w in zip(Ta.ravel(), Wa.ravel())])
    out = out.reshape(Ta.shape)
    return out if out.size > 1 else float(out.ravel()[0])


def wetbulb_from_rh(T, rh, p=P_ATM):
    """Convenience: thermodynamic wet-bulb from dry-bulb and RH [0..1]."""
    return wetbulb(T, humidity_ratio_from_rh(T, rh, p), p)


def dewpoint(W, p=P_ATM):
    """Dew-point temperature [degC] from humidity ratio."""
    pv = np.atleast_1d(vapour_pressure_from_W(W, p))
    out = np.array([brentq(lambda t: sat_vapour_pressure(t) - v, -100.0, 200.0,
                           xtol=1e-8, rtol=1e-12) for v in pv])
    return out if out.size > 1 else float(out[0])


def moist_air_density(T, W, p=P_ATM):
    """Moist-air density [kg moist air / m3]. ASHRAE Eq. (26) inverted."""
    T = np.asarray(T, dtype=float)
    W = np.asarray(W, dtype=float)
    v = R_DA * (T + T0) * (1.0 + 1.607858 * W) / p      # m3 / kg dry air
    return (1.0 + W) / v


def water_enthalpy(T):
    """Specific enthalpy of saturated liquid water [kJ/kg], ref 0 degC."""
    return 4.186 * np.asarray(T, dtype=float)


def latent_heat_vaporisation(T):
    """Latent heat of vaporisation of water [kJ/kg]."""
    return 2501.0 - 2.326 * np.asarray(T, dtype=float)


# --- fast scalar kernels (hot path inside ODE integration) ----------------
import math as _math


def pws_scalar(T):
    """Scalar saturation vapour pressure [Pa]; ASHRAE Eq. (6), T > 0 degC.

    Pure-Python twin of sat_vapour_pressure, ~40x faster on scalars. Used
    only inside the tower ODE right-hand side, where it is called on the
    order of 1e5 times per solve. Agreement with the array version is
    asserted in tests/test_psychro.py.
    """
    Tk = T + 273.15
    if T < 0.0:
        return _math.exp(-5.6745359e3 / Tk + 6.3925247 - 9.677843e-3 * Tk
                         + 6.2215701e-7 * Tk**2 + 2.0747825e-9 * Tk**3
                         - 9.484024e-13 * Tk**4 + 4.1635019 * _math.log(Tk))
    return _math.exp(-5.8002206e3 / Tk + 1.3914993 - 4.8640239e-2 * Tk
                     + 4.1764768e-5 * Tk**2 - 1.4452093e-8 * Tk**3
                     + 6.5459673 * _math.log(Tk))


def ws_scalar(T, p=P_ATM, aw=1.0):
    """Scalar saturation humidity ratio, with liquid-phase water activity."""
    pv = aw * pws_scalar(T)
    return MW_RATIO * pv / (p - pv)


def h_scalar(T, w):
    """Scalar moist-air enthalpy [kJ/kg dry air]."""
    return 1.006 * T + w * (2501.0 + 1.860 * T)
