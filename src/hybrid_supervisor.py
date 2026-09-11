"""
FURQAN / MIZAN :: coupled supervisory control of tower + CDU + trim chiller.

THE FINDING THIS MODULE EXISTS TO ENFORCE.

A thermal-only economizer drives the facility water as cold as the wet bulb
allows, because every kelvin of colder supply is compressor work avoided.
On a silica-bearing makeup water that is precisely the wrong direction.

    Amorphous silica is PROGRADE. It is least soluble COLD.

So free cooling -- the single largest energy lever in a liquid-cooled data
centre -- pushes the facility water toward silica precipitation, at the tower
basin and on the CDU plate. Measured on the validated Aramco TSE analysis:

    cycles   minimum safe facility-water temperature
      4                  20.7 C
      5                  31.8 C
      6                  41.4 C

Every cycle of concentration won -- which is water saved -- costs about ten
kelvin of free-cooling headroom. That coupling is real, it is large, and no
thermal optimiser in the literature can see it: of fourteen data-centre
thermal-control papers surveyed, eleven mention water and none model
chemistry. It cannot be bought back with acid either, because silica
saturation is pH-independent below about pH 9. It is a hard thermal boundary.

WHAT THE SUPERVISOR DOES ABOUT IT.

    1. Compute the chemical floor from the water and the cycles.
    2. Refuse to cool below it -- by slowing the tower fan, which also saves
       fan power and evaporation, so the constraint is not purely a cost.
    3. Pay for the warmer supply on the CDU side instead, by raising the
       secondary flow enough to hold the cold-plate return at its limit.
       That costs pump power CUBICALLY, which is why the trade has to be
       computed rather than guessed.

`compare_blind_vs_bounded()` runs both policies side by side and reports what
the thermal-only one would have done to the plate.
"""

from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import chemistry as chem                    # noqa: E402
import controller as ctl                    # noqa: E402
import psychro as ps                        # noqa: E402
import tower as tw                          # noqa: E402
from models import cdu_model as cdu         # noqa: E402

CPW_KJ_KGK = tw.CPW


def solve_free_cooling(T_db, rh, m_w_pri, q_total_kw, fan_pct,
                       m_a_rated, fill_c, fill_n, aw=1.0,
                       max_iter=60, tol=1e-5):
    """Tower alone, no compressor: the facility water loop closed on itself.

    The tower outlet IS the facility supply, and the return is the supply
    plus the loop rise, so the two are coupled and have to be solved
    together -- the same fixed point the Mizan core solves for a condenser,
    with the chiller removed.
    """
    m_a = tw.air_mass_flow_from_fan(fan_pct) * m_a_rated / \
        tw.air_mass_flow_from_fan(100.0)
    if m_a <= 0.05:
        return None
    rise = q_total_kw / (m_w_pri * CPW_KJ_KGK)

    # SECANT, not damped substitution. The old form was
    #     T_wo <- 0.5*T_wo + 0.5*f(T_wo + rise)
    # which halves the error each sweep, so reaching a 1e-5 K tolerance from a
    # 5 K initial error takes about twenty tower solves -- and a tower solve is
    # a 24-point scan plus a Brent solve over a Poppe integration, so one call
    # to this function cost roughly eighteen seconds. That is why the
    # four-region study never finished.
    #
    # The residual g(T) = f(T + rise) - T is smooth and monotone, so a secant
    # root-find converges in four or five evaluations instead of twenty. The
    # damped iteration is kept as a fallback for the rare case where the
    # secant step leaves the physical range.
    def _resid(T):
        T_new, info = tw.solve_outlet_temperature(
            T + rise, T_db, rh, m_w_pri, m_a, fill_c, fill_n, aw=aw)
        if info is None or not math.isfinite(T_new):
            return None, None
        return T_new - T, (T_new, info)

    t0 = T_db - 4.0
    t1 = t0 + 1.0
    g0, s0 = _resid(t0)
    if g0 is None:
        return None
    g1, s1 = _resid(t1)
    if g1 is None:
        return None
    T_wo, info = s1[0], s1[1]
    ok = False
    for _ in range(max_iter):
        if abs(g1) < tol:
            ok = True
            break
        denom = (g1 - g0)
        if abs(denom) < 1e-14:
            break
        t2 = t1 - g1 * (t1 - t0) / denom
        if not math.isfinite(t2) or not (T_db - 40.0 < t2 < T_db + 60.0):
            break
        g2, s2 = _resid(t2)
        if g2 is None:
            break
        t0, g0 = t1, g1
        t1, g1 = t2, g2
        T_wo, info = s2[0], s2[1]
    if not ok:
        # fallback: the original damped substitution, from the best secant point
        for _ in range(max_iter):
            T_new, info2 = tw.solve_outlet_temperature(
                T_wo + rise, T_db, rh, m_w_pri, m_a, fill_c, fill_n, aw=aw)
            if info2 is None or not math.isfinite(T_new):
                return None
            info = info2
            if abs(T_new - T_wo) < tol:
                T_wo = T_new
                ok = True
                break
            T_wo = 0.5 * T_wo + 0.5 * T_new
    if not ok:
        return None

    info["T_fws"] = float(T_wo)
    info["T_fwr"] = float(T_wo + rise)
    info["m_a"] = float(m_a)
    info["fan_pct"] = float(fan_pct)
    info["P_fan_kW"] = float(ctl.fan_power(m_a, m_a_rated, 110.0))
    return info


_FAN_CURVE_CACHE = {}
_FAN_ANSWER_CACHE = {}


def fan_for_target_fws(target_c, T_db, rh, m_w_pri, q_total_kw,
                       m_a_rated, fill_c, fill_n, aw=1.0,
                       fan_lo=15.0, fan_hi=100.0):
    """Slowest fan that still meets `target_c`, i.e. the least fan power and
    the least evaporation consistent with the chemical floor.

    Colder outlet needs more air, so the outlet falls monotonically with fan
    speed and a bisection is well posed. Returns (fan_pct, state) or None.
    """
    # PERFORMANCE, and it is not a detail. The original form ran 30 bisection
    # steps, each a full tower solve of up to 60 sweeps with a 24-point scan
    # and a Brent solve inside. Across a 24-hour, two-policy, four-region
    # study that is of order 1e5 tower solves and the script never finished.
    #
    # The map fan -> T_fws is monotone and smooth, so it is built ONCE per
    # thermal condition on a coarse grid, cached, and inverted by
    # interpolation; only the refinement touches the solver again. Same
    # answer to the same tolerance, roughly an order of magnitude fewer
    # solves, and the cache pays again every time a second policy asks about
    # the same hour.
    key = (round(T_db, 3), round(rh, 4), round(m_w_pri, 3),
           round(q_total_kw, 2), round(m_a_rated, 3),
           round(fill_c, 6), round(fill_n, 6), round(aw, 6),
           round(fan_lo, 2), round(fan_hi, 2))
    ans_key = (key, round(float(target_c), 3))
    if ans_key in _FAN_ANSWER_CACHE:
        return _FAN_ANSWER_CACHE[ans_key]

    curve = _FAN_CURVE_CACHE.get(key)
    if curve is None:
        pts = []
        n = 9
        for i in range(n):
            f = fan_lo + (fan_hi - fan_lo) * i / (n - 1)
            st = solve_free_cooling(T_db, rh, m_w_pri, q_total_kw, f,
                                    m_a_rated, fill_c, fill_n, aw)
            if st is not None:
                pts.append((f, st["T_fws"], st))
        curve = pts
        if len(_FAN_CURVE_CACHE) > 4096:
            _FAN_CURVE_CACHE.clear()
        _FAN_CURVE_CACHE[key] = curve
    if not curve:
        return None

    hi = curve[-1][2]
    if hi["T_fws"] > target_c:
        _FAN_ANSWER_CACHE[ans_key] = (fan_hi, hi)
        return fan_hi, hi                      # cannot get colder even flat out

    # bracket on the cached curve: the coldest point at or below target, and
    # the warmest point above it
    lo_pct = fan_lo
    hi_pct, best = curve[-1][0], curve[-1][2]
    for f, t, st in curve:
        if t <= target_c and f <= hi_pct:
            hi_pct, best = f, st
        if t > target_c and f > lo_pct:
            lo_pct = f

    # Five refinements halve a 10.6-point grid spacing to about 0.33 points of
    # fan speed, which is finer than any tower is actually controlled to.
    for _ in range(5):                          # refine inside the bracket
        if hi_pct - lo_pct < 0.4:
            break
        mid = 0.5 * (lo_pct + hi_pct)
        st = solve_free_cooling(T_db, rh, m_w_pri, q_total_kw, mid,
                                m_a_rated, fill_c, fill_n, aw)
        if st is None:
            lo_pct = mid
            continue
        if st["T_fws"] > target_c:
            lo_pct = mid
        else:
            hi_pct, best = mid, st
    out = (float(hi_pct), best)
    if len(_FAN_ANSWER_CACHE) > 8192:
        _FAN_ANSWER_CACHE.clear()
    _FAN_ANSWER_CACHE[ans_key] = out
    return out


def required_secondary_flow(unit: cdu.CDUSubsystem, t_fws_c):
    """Secondary mass flow needed to hold the cold-plate return at its limit.

    T_ret = T_fws + approach + Q/(m*cp) <= limit, so
        m >= Q / (cp * (limit - T_fws - approach)).
    Returns None when the supply is already so warm that no flow can satisfy
    the limit -- which is the real ceiling on how far the chemical floor can
    be allowed to push the supply.
    """
    headroom = unit.return_limit_c - t_fws_c - unit.approach_k
    if headroom <= 0:
        return None
    return unit.q_it_kw * 1000.0 / (unit.cp_sec * headroom)


def water_balance_for(state, cycles, makeup_water):
    """Makeup, blowdown and drift for a tower evaporating `state['m_evap']`."""
    wb = ctl.water_balance(state["m_evap"], state["m_w"] if "m_w" in state
                           else state.get("m_w_pri", 0.0), cycles)
    return wb


def evaluate(T_db, rh, q_it_kw, makeup, cycles, tariffs, unit,
             m_w_pri, m_a_rated, fill_c, fill_n,
             enforce_chemical_floor=True, ph=8.25,
             p_pump_pri_kw=None, limits=None):
    """One operating point of the coupled plant, under one policy.

    `enforce_chemical_floor=False` is the thermal-only economizer: it takes
    the coldest facility water the tower can make. That is the baseline this
    product exists to beat, and it is what every optimiser in the surveyed
    literature would do.
    """
    limits = chem.OPERATING_LIMITS if limits is None else limits
    floor = chem.temperature_floor_for_silica(makeup, cycles)

    # start from the coldest the tower can make at full fan
    q_guess = q_it_kw * 1.03
    full = solve_free_cooling(T_db, rh, m_w_pri, q_guess, 100.0,
                              m_a_rated, fill_c, fill_n)
    if full is None:
        return None

    if enforce_chemical_floor and full["T_fws"] < floor:
        got = fan_for_target_fws(floor, T_db, rh, m_w_pri, q_guess,
                                 m_a_rated, fill_c, fill_n)
        if got is None:
            return None
        fan_pct, state = got
        bounded_by_chemistry = True
    else:
        fan_pct, state = 100.0, full
        bounded_by_chemistry = False

    t_fws = state["T_fws"]

    # CDU hydraulic compensation: hold the cold-plate return at its limit by
    # raising secondary flow, and pay for it cubically.
    m_req = required_secondary_flow(unit, t_fws)
    if m_req is None:
        return None
    m_sec = max(unit.m_dot_sec_nom_kg_s, m_req)
    unit_here = cdu.CDUSubsystem(
        q_it_kw=unit.q_it_kw, m_dot_sec_kg_s=m_sec,
        m_dot_sec_nom_kg_s=unit.m_dot_sec_nom_kg_s,
        p_pump_sec_nom_kw=unit.p_pump_sec_nom_kw,
        approach_k=unit.approach_k, cp_sec=unit.cp_sec, cp_pri=unit.cp_pri,
        primary_film_fraction=unit.primary_film_fraction,
        return_limit_c=unit.return_limit_c)
    cdu_state = unit_here.solve(t_fws, m_dot_pri_kg_s=m_w_pri)
    scaling = unit_here.scaling_state(cdu_state, makeup, cycles, ph,
                                      limits=limits)

    # power and water
    p_pump_pri = (0.015 * q_it_kw if p_pump_pri_kw is None
                  else float(p_pump_pri_kw))     # [A archetype]
    p_fan = state["P_fan_kW"]
    p_pump_sec = unit_here.pump_power_kw()
    p_total_facility = p_fan + p_pump_pri + p_pump_sec
    pue = (q_it_kw + p_total_facility) / q_it_kw

    wb = ctl.water_balance(state["m_evap"], m_w_pri, cycles)
    makeup_m3_h = wb["makeup"] * 3.6
    wue_l_per_kwh = makeup_m3_h * 1000.0 / q_it_kw

    cost_h = (tariffs["elec_per_kwh"] * (q_it_kw + p_total_facility)
              + ctl._water_cost_per_h(wb, tariffs)
              + tariffs["antiscalant_per_m3"] * makeup_m3_h)

    return {
        "policy": ("chemically_bounded" if enforce_chemical_floor
                   else "blind_free_cooling"),
        "bounded_by_chemistry": bounded_by_chemistry,
        "chemical_floor_c": float(floor),
        "cycles": float(cycles),
        "fan_pct": float(fan_pct),
        "T_db": float(T_db), "rh": float(rh),
        "T_wb": float(state.get("T_wb", float("nan"))),
        "T_fws_c": float(t_fws),
        "T_fwr_c": cdu_state["t_fwr_c"],
        "T_sec_supply_c": cdu_state["t_sec_supply_c"],
        "T_sec_return_c": cdu_state["t_sec_return_c"],
        "T_wall_primary_c": cdu_state["t_wall_primary_c"],
        "return_ok": cdu_state["return_ok"],
        "return_margin_k": cdu_state["return_margin_k"],
        "m_dot_sec_kg_s": float(m_sec),
        "m_dot_sec_nom_kg_s": float(unit.m_dot_sec_nom_kg_s),
        "secondary_flow_ratio": float(m_sec / unit.m_dot_sec_nom_kg_s),
        "P_fan_kW": float(p_fan),
        "P_pump_pri_kW": float(p_pump_pri),
        "P_pump_sec_kW": float(p_pump_sec),
        "P_facility_kW": float(p_total_facility),
        "P_it_kW": float(q_it_kw),
        "PUE": float(pue),
        "m_evap_kg_s": float(state["m_evap"]),
        "makeup_m3_h": float(makeup_m3_h),
        "blowdown_m3_h": float(wb["blowdown"] * 3.6),
        "WUE_L_per_kWh": float(wue_l_per_kwh),
        "cost_per_h": float(cost_h),
        "SI": scaling["SI"],
        "violations": scaling["violations"],
        "zero_scaling": scaling["zero_scaling"],
        "max_SI_over_limit": scaling["max_SI_over_limit"],
    }


def compare_blind_vs_bounded(**kw):
    """The deliverable: what a thermal-only economizer does to the plate, and
    what it costs to stop it."""
    blind = evaluate(enforce_chemical_floor=False, **kw)
    bounded = evaluate(enforce_chemical_floor=True, **kw)
    if blind is None or bounded is None:
        return {"blind": blind, "bounded": bounded, "delta": None}

    def pct(a, b):
        return 100.0 * (a - b) / a if a else float("nan")

    return {
        "blind": blind,
        "bounded": bounded,
        "delta": {
            "T_fws_raised_k": bounded["T_fws_c"] - blind["T_fws_c"],
            "fan_pct_change": bounded["fan_pct"] - blind["fan_pct"],
            "secondary_flow_ratio": (bounded["secondary_flow_ratio"]
                                     / max(blind["secondary_flow_ratio"], 1e-9)),
            "P_fan_saved_kW": blind["P_fan_kW"] - bounded["P_fan_kW"],
            "P_pump_sec_added_kW": (bounded["P_pump_sec_kW"]
                                    - blind["P_pump_sec_kW"]),
            "P_facility_delta_kW": (bounded["P_facility_kW"]
                                    - blind["P_facility_kW"]),
            "PUE_delta": bounded["PUE"] - blind["PUE"],
            "water_saved_pct": pct(blind["makeup_m3_h"], bounded["makeup_m3_h"]),
            "WUE_delta": bounded["WUE_L_per_kWh"] - blind["WUE_L_per_kWh"],
            "cost_delta_per_h": bounded["cost_per_h"] - blind["cost_per_h"],
            "blind_violated_silica": bool(
                "SI_silica_am" in blind["violations"]),
            "blind_SI_silica": blind["SI"].get("SI_silica_am"),
            "bounded_SI_silica": bounded["SI"].get("SI_silica_am"),
        },
    }


# ---------------------------------------------------------------------------
# THE ENERGY CLAIM -- how much free cooling the chemistry forbids
# ---------------------------------------------------------------------------
# This package has been honest that condenser-water energy optimisation is
# prior art: seven published optimisers, savings of 8-25 %, none with any
# water chemistry. That has been treated as a weakness. It is not.
#
# Every economizer in that literature drives the facility water as cold as the
# tower can make it, because colder water is compressor work avoided. On a
# silica-bearing makeup that is not merely suboptimal, it is FORBIDDEN below
# the amorphous-silica floor -- and on real weather the floor binds for most
# of the year.
#
# Counted on Dhahran TMYx 2011-2025, 8,760 hours, with the economizer taking
# T_fws = T_wetbulb + tower approach:
#
#     cycles   floor      hours below the floor      fraction of the year
#       4      20.7 C          2,632 h                    30.0 %
#       5      31.8 C          8,053 h                    91.9 %
#       6      41.4 C          8,760 h                   100.0 %
#
#     (4 K tower approach; 3 K and 5 K give 35/96/100 and 25/87/100)
#
# So a chemistry-blind optimiser running this water at five cycles claims
# free cooling it cannot have for NINE TENTHS OF THE YEAR, and at six cycles
# for all of it. The published 8-25 % savings are not wrong about their own
# water -- they are inapplicable to this one, and nothing in those papers
# would reveal that, because none of them carries a chemistry state.
#
# THAT IS THE ENERGY PITCH, and it is stronger than competing on percentages:
# not "we save more energy" but "the savings you were quoted are unavailable
# on the water you actually have, and here is the fraction of the year".
#
# The measured cost of obeying the floor, 9 MW case at five cycles:
# PUE 1.047 -> 1.150, fan -100 kW against secondary pump +1,028 kW. The
# correct supervisory response is to lower cycles rather than pay that, which
# is a decision neither an energy-only nor a water-only optimiser can reach.


def free_cooling_hours_forbidden(makeup, cycles, tower_approach_k=4.0,
                                 tmy_path=None):
    """Hours per year an economizer would go below the chemical floor.

    Returns the count and the fraction, plus the floor itself, so the caller
    cannot quote the fraction without the temperature it came from.
    """
    import numpy as np
    import pathlib
    import chemistry as chem

    p = pathlib.Path(tmy_path or (pathlib.Path(__file__).resolve().parent.parent
                                  / "results" / "tmy_hourly.npy"))
    if not p.exists():
        return None
    h = np.load(p)
    t_wb = h[:, 5]
    floor = chem.temperature_floor_for_silica(makeup, float(cycles))
    t_fws = t_wb + float(tower_approach_k)
    below = int((t_fws < floor).sum())
    return {
        "cycles": float(cycles),
        "floor_c": float(floor),
        "tower_approach_k": float(tower_approach_k),
        "hours_total": int(t_wb.size),
        "hours_below_floor": below,
        "fraction_of_year": below / float(t_wb.size),
        "note": ("hours in which a thermal-only economizer would drive the "
                 "facility water below the amorphous-silica floor, i.e. free "
                 "cooling the surveyed literature counts and this water "
                 "forbids"),
    }
