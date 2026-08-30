"""
MIZAN :: counterflow wet cooling tower model
============================================
Poppe & Roegener heat-and-mass-transfer formulation, in the form given by
Kloppers & Kroeger (2005), "A critical investigation into the heat and mass
transfer analysis of counterflow wet-cooling towers", Int. J. Heat Mass
Transfer 48(3). Merkel is retained as the industry/acceptance-test
reference (CTI ATC-105, UNE-EN 13741).

Why Poppe and not Merkel alone: Merkel assumes the exit air is saturated
and neglects the evaporated water in the air-side mass balance, so it
CANNOT predict make-up water. Poppe integrates the air humidity ratio
explicitly, which yields the evaporation rate -- the quantity this product
actually optimises, and the quantity we validate against the measured
`q_w_lost` channel of the PSA dataset.

Salinity coupling
-----------------
The interface saturation humidity ratio is evaluated at the WATER ACTIVITY
of the circulating water, w_sw = f(a_w * pws(T_w)). At a_w = 1 this reduces
exactly to the textbook pure-water model. This single substitution is what
lets the same model price the water/energy trade-off of running the loop at
higher cycles of concentration.

State vector integrated against water temperature T_w:
    y = [w, h_a, Me, m_w]
"""
from __future__ import annotations

import math as _math

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

import psychro as ps

CPW = 4.186          # specific heat of liquid water [kJ/(kg.K)]


def lewis_factor(w, w_sw):
    """Bosnjakovic Lewis factor. Kloppers & Kroeger Eq. (5)."""
    r = (w_sw + 0.622) / (w + 0.622)
    r = np.clip(r, 1.0 + 1e-12, None)
    return 0.865 ** (2.0 / 3.0) * (r - 1.0) / np.log(r)


def vapour_enthalpy(T):
    """Enthalpy of saturated water vapour [kJ/kg] at T [degC]."""
    return 2501.6 + 1.868 * T


def _moist_enthalpy_general(T_a, w, p):
    """Air-stream enthalpy [kJ/kg dry air], valid on both sides of saturation.

    Below saturation this is the ordinary moist-air enthalpy. Above it the
    air is saturated and the excess humidity ratio is carried as suspended
    liquid (fog), which is how Poppe treats supersaturated tower air.
    """
    w_sa = ps.ws_scalar(T_a, p)
    if w > w_sa:
        return ps.h_scalar(T_a, w_sa) + (w - w_sa) * CPW * T_a
    return ps.h_scalar(T_a, w)


def _derivs(T_w, y, m_a, aw, p):
    """Poppe ODE right-hand side, d/dT_w of [w, T_a, Me, m_w].

    Two branches, per Kloppers & Kroeger (2005): the unsaturated set, and
    the supersaturated set used once the air stream has fogged. The state
    carries air DRY-BULB rather than enthalpy so the saturation test is
    direct and the branch switch is continuous in the state.
    """
    w, T_a, _Me, m_w = y

    # interface saturation is evaluated at the water activity of the
    # circulating water -- the salinity coupling
    w_sw = ps.ws_scalar(T_w, p, aw)
    h_asw = ps.h_scalar(T_w, w_sw)
    w_sa = ps.ws_scalar(T_a, p)
    h_v = vapour_enthalpy(T_w)

    supersaturated = w > w_sa
    if supersaturated:
        h_air = ps.h_scalar(T_a, w_sa) + (w - w_sa) * CPW * T_a
        drive = w_sw - w_sa
        Le_f = lewis_factor(w_sa, w_sw)
    else:
        h_air = ps.h_scalar(T_a, w)
        drive = w_sw - w
        Le_f = lewis_factor(w, w_sw)

    denom = ((h_asw - h_air)
             + (Le_f - 1.0) * ((h_asw - h_air) - drive * h_v)
             - drive * CPW * T_w)
    if abs(denom) < 1e-8:
        denom = 1e-8 if denom >= 0 else -1e-8

    ratio = m_w / m_a
    dw = CPW * ratio * drive / denom
    dh = CPW * ratio + CPW * T_w * dw          # energy balance incl. evaporation
    dMe = CPW / denom

    if supersaturated:                          # differentiate fogged enthalpy
        eps = 1e-5
        dh_dTa = (_moist_enthalpy_general(T_a + eps, w, p)
                  - _moist_enthalpy_general(T_a - eps, w, p)) / (2 * eps)
        dh_dw = (_moist_enthalpy_general(T_a, w + eps, p)
                 - _moist_enthalpy_general(T_a, w - eps, p)) / (2 * eps)
    else:
        dh_dTa = 1.006 + 1.86 * w
        dh_dw = 2501.0 + 1.86 * T_a

    dT_a = (dh - dh_dw * dw) / dh_dTa
    dmw = m_a * dw
    return [dw, dT_a, dMe, dmw]


def integrate_poppe(T_wo, T_wi, T_db, w_in, m_w_in, m_a, aw=1.0,
                    p=ps.P_ATM, n_steps=160):
    """Integrate the Poppe equations from the cold (air-inlet) end upward.

    Counterflow: air enters at the bottom, where the water leaves, so the
    air inlet state is the initial condition at T_w = T_wo.

    Fixed-step classical RK4 rather than an adaptive solver. Three reasons,
    in order of importance:

      1. Bounded, deterministic runtime. An adaptive solver collapses its
         step size where the saturated/supersaturated branch toggles, and
         its cost per call becomes unpredictable. A supervisory controller
         has a control interval to meet; it cannot call a routine whose
         worst case is unbounded.
      2. The integrand is smooth in T_w away from the branch switch, and
         the switch itself is a change of formula, not a stiff transient.
         160 steps over a range of at most ~20 K is roughly 0.1 K per step,
         far finer than the physics requires.
      3. Identical arithmetic on desktop and on the edge target, so the
         controller cannot disagree with the model it was validated as.
    """
    if not (T_wi > T_wo):
        return None
    h = (T_wi - T_wo) / n_steps
    y = [w_in, T_db, 0.0, m_w_in]
    T = T_wo
    for _ in range(n_steps):
        try:
            k1 = _derivs(T, y, m_a, aw, p)
            y2 = [y[i] + 0.5 * h * k1[i] for i in range(4)]
            k2 = _derivs(T + 0.5 * h, y2, m_a, aw, p)
            y3 = [y[i] + 0.5 * h * k2[i] for i in range(4)]
            k3 = _derivs(T + 0.5 * h, y3, m_a, aw, p)
            y4 = [y[i] + h * k3[i] for i in range(4)]
            k4 = _derivs(T + h, y4, m_a, aw, p)
            y = [y[i] + h / 6.0 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])
                 for i in range(4)]
        except (ValueError, OverflowError, ZeroDivisionError):
            return None
        T += h
        if not all(_math.isfinite(v) for v in y):
            return None
        if y[0] < 0.0 or y[0] > 1.0:          # humidity ratio left physics
            return None

    w_out, T_a_out, Me, m_w_top = y
    if Me <= 0.0 or not _math.isfinite(Me):
        return None
    return {
        "Me": float(Me),
        "w_out": float(w_out),
        "T_a_out": float(T_a_out),
        "h_a_out": _moist_enthalpy_general(float(T_a_out), float(w_out), p),
        "m_evap": float(m_a * (w_out - w_in)),
        "m_w_top": float(m_w_top),
        "fogged": bool(w_out > ps.ws_scalar(float(T_a_out), p)),
    }


def fill_merkel_number(m_w, m_a, c, n):
    """Fill thermal characteristic, Me = c * (m_w/m_a)^n.

    The standard two-parameter empirical form used in CTI/Merkel practice;
    c and n are the only quantities calibrated from data.
    """
    return c * (m_w / m_a) ** n


def solve_outlet_temperature(T_wi, T_db, rh, m_w, m_a, c, n,
                             aw=1.0, p=ps.P_ATM, n_scan=24):
    """Cold-water outlet temperature by matching the Merkel number demanded
    by the duty to the Merkel number the fill can supply (shooting method).

    The residual Me_demand(T_wo) - Me_fill is monotone decreasing in T_wo but
    is not defined over the whole interval (very low T_wo drives the air
    deep into fog and the integration can fail), so the bracket is found by
    a coarse scan rather than assumed at the endpoints.
    """
    w_in = float(ps.humidity_ratio_from_rh(T_db, rh, p))
    T_wb = float(ps.wetbulb(T_db, w_in, p))
    Me_avail = fill_merkel_number(m_w, m_a, c, n)

    lo, hi = T_wb + 0.05, T_wi - 0.02
    if hi <= lo:
        return float("nan"), None

    def residual(T_wo):
        """Me demanded minus Me available.

        Monotone DECREASING in T_wo: a colder target outlet demands more
        transfer units. Where the integration fails -- always at the cold
        end, where the air fogs hard -- we return a large POSITIVE value
        rather than NaN. That is both numerically necessary (a root finder
        cannot bracket across a NaN) and physically right: failure there
        means the duty is beyond what the tower can deliver, which is the
        same side of the root as "demand exceeds capacity".
        """
        r = integrate_poppe(T_wo, T_wi, T_db, w_in, m_w, m_a, aw, p)
        return 1.0e3 if r is None else r["Me"] - Me_avail

    # Walk DOWN from the hot end and take the FIRST sign change. That
    # matters: integration failure returns a large positive sentinel, so
    # the residual has a step discontinuity at the fogging boundary as well
    # as its true root. A root finder turned loose on the whole interval can
    # converge on the discontinuity instead of the physical root. Scanning
    # from the hot end and bracketing the first crossing always returns the
    # physical one.
    grid = np.linspace(hi, lo, n_scan)
    prev_T, prev_f = None, None
    for T in grid:
        f = residual(float(T))
        if prev_f is not None and prev_f * f <= 0:
            T_wo = brentq(residual, float(T), prev_T, xtol=1e-6, rtol=1e-10,
                          maxiter=100)
            info = integrate_poppe(T_wo, T_wi, T_db, w_in, m_w, m_a, aw, p)
            if info is None:
                return float("nan"), None
            info["T_wb"] = T_wb
            info["approach"] = T_wo - T_wb
            info["range"] = T_wi - T_wo
            info["Q"] = m_w * CPW * (T_wi - T_wo)
            info["Me_fill"] = float(Me_avail)
            return float(T_wo), info
        prev_T, prev_f = float(T), f
    return float("nan"), None


def air_mass_flow_from_fan(f_fan_pct, base_hz=50.0):
    """Air mass flow [kg/s] for the PSA pilot tower, from its fan-speed
    channel [%].

    The correlation published with the dataset is

        m_a = -0.0014 f^2 + 0.1743 f - 0.7251

    Its argument is fan frequency in HERTZ, not the percentage carried in
    the `w_fan` column, even though the dataset text calls f_fan a
    percentage. Two independent checks establish this:

      * Read as a percentage the quadratic turns over at f = 62.25 %, so
        air mass flow would FALL as the fan speeds up from 62 % to 100 %.
        No fan behaves that way.
      * Read as a percentage the published design point implies L/G = 2.55;
        read as hertz it gives L/G = 1.54, squarely in the normal range for
        a counterflow induced-draught tower.

    Getting this wrong costs about 1 K of holdout accuracy and injects a
    systematic warm bias, because it inflates air flow at low fan speeds --
    which is where most of the campaign-2 data sits.

    This is the PILOT tower's absolute air flow. It does not transfer to
    plant scale; the fill CHARACTERISTIC does. Plant models scale rated air
    flow by fan speed instead (see controller._thermal_solve).
    """
    f_hz = np.asarray(f_fan_pct, dtype=float) * base_hz / 100.0
    return -0.0014 * f_hz**2 + 0.1743 * f_hz - 0.7251


# Drift is quoted by manufacturers as a PERCENTAGE of circulating water
# flow. Modern high-efficiency eliminators are rated 0.0005 % to 0.001 %,
# i.e. 5e-6 to 1e-5 as a fraction. [C]
#
# This module previously defaulted to 0.0005 used as a FRACTION -- the
# modern rating with its percent sign dropped, and a hundred times too much
# drift. controller.py carried the identical error and was corrected first;
# this is the same constant, and the two must agree or the water balance
# means different things in the two places it is computed.
DRIFT_FRACTION = 1.0e-5        # 0.001 %, conservative end of the range [C]


def drift_loss(m_w, drift_fraction=DRIFT_FRACTION):
    """Drift (windage) loss [kg/s], as a fraction of circulating flow."""
    return drift_fraction * np.asarray(m_w, dtype=float)
