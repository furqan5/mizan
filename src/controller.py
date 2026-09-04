"""
MIZAN :: supervisory controller and economic optimisation
=========================================================
The product. A condenser-water loop has three supervisory handles that are
almost always set independently, by three different parties:

    fan speed        set by the BMS, on a fixed condenser-water setpoint
    blowdown         set by the water-treatment contractor, on a fixed
                     conductivity setpoint
    acid dose        set by the water-treatment contractor, on a fixed pH
                     setpoint

They are not independent. Raising cycles of concentration saves water but
raises scaling risk, which is usually answered by dosing more acid or by
giving up and blowing down harder. Lowering the condenser-water setpoint
saves chiller power but costs fan power and raises evaporation, which
concentrates the loop faster. Nobody optimises the three together, because
doing so requires the thermal model and the chemistry model to be solved as
one problem.

This module does that. It minimises total operating cost

    J = c_elec * (P_fan + P_chiller) + c_water * m_makeup
        + c_acid * m_acid + c_antiscalant * m_antiscalant

subject to the cooling duty being met, equipment limits, and mineral
saturation staying inside its limit AT CONDENSER SKIN TEMPERATURE -- not at
bulk temperature, which is where conventional practice evaluates it and
which systematically understates the risk.

The baseline it is compared against is not a straw man: it is fixed-setpoint
operation, which is what these plants actually run today.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
from scipy.optimize import brentq, minimize_scalar

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem
import psychro as ps
import tower as tw
import water_activity as wa

CPW = 4.186


class _TowerFailure(Exception):
    """The tower model could not solve at this point."""


# --- equipment models -----------------------------------------------------
def fan_power(m_a, m_a_rated, p_rated_kw):
    """Fan shaft power by the affinity law: power scales with the cube of
    air flow. The single largest lever the controller has on tower energy."""
    return p_rated_kw * (np.asarray(m_a, float) / m_a_rated) ** 3


def chiller_power(Q_evap_kw, T_cw_supply_c, T_chw_supply_c=7.0,
                  carnot_efficiency=0.55, approach_cond=4.0):
    """Chiller electrical power via a Carnot-referenced COP.

        COP = eta * T_evap / (T_cond - T_evap)

    Carnot-referenced rather than a fitted bi-quadratic because it is
    first-principles, needs one parameter instead of six, and cannot
    extrapolate into thermodynamically impossible territory -- which
    matters when an optimiser is free to push the condenser setpoint.

    `eta` is the fraction of Carnot actually achieved; 0.5-0.65 covers
    modern centrifugal machines. [A - to be calibrated per machine]
    """
    T_evap = T_chw_supply_c - 2.0 + 273.15
    T_cond = np.asarray(T_cw_supply_c, float) + approach_cond + 273.15
    cop = carnot_efficiency * T_evap / np.maximum(T_cond - T_evap, 1.0)
    return Q_evap_kw / cop, cop


# Drift is quoted by every manufacturer as a PERCENTAGE of circulating water
# flow. Modern high-efficiency eliminators are rated 0.0005 % to 0.001 % of
# circulating flow -- so as a fraction, 5e-6 to 1e-5. [C]
#
# This constant previously held 0.0005 used directly as a fraction, i.e.
# 0.05 % -- the modern rating with its percent sign silently dropped, and a
# hundred times too much drift. It is the same class of defect as the fan
# correlation read in percent instead of hertz.
#
# It does not move makeup water, and that is worth stating precisely rather
# than discovering later: with blowdown = evaporation/(C-1) - drift, the
# drift term cancels out of makeup = evaporation + drift + blowdown
# exactly, for as long as blowdown stays positive. What it did corrupt is
# the reported BLOWDOWN rate -- 27 % low at seven cycles -- which is the
# quantity a discharge permit is written against.
DRIFT_FRACTION = tw.DRIFT_FRACTION   # single definition, in tower.py


def water_balance(m_evap_kg_s, m_w_kg_s, cycles, drift_fraction=DRIFT_FRACTION):
    """Steady-state loop water balance.

        makeup = evaporation + drift + blowdown
        cycles = makeup / (blowdown + drift)

    Evaporation leaves the salts behind, so it does not appear in the
    cycles ratio; drift does, because drift carries salt out with it.
    """
    drift = drift_fraction * m_w_kg_s
    cycles = max(float(cycles), 1.0001)
    blowdown = m_evap_kg_s / (cycles - 1.0) - drift
    blowdown = max(blowdown, 0.0)
    makeup = m_evap_kg_s + drift + blowdown
    return {"makeup": makeup, "blowdown": blowdown, "drift": drift}


def acid_dose_for_ph(water, cycles, target_ph, T_c):
    """Sulphuric acid required to hold pH at target against the alkalinity
    carried in at `cycles`.

    Acid converts bicarbonate to CO2 and water. The dose is the bicarbonate
    that must be destroyed to move from the CO2-equilibrium pH the loop
    would otherwise reach down to the target, expressed as kg H2SO4 per
    kg of circulating makeup.
    """
    conc = water.concentrate(cycles)
    ph_free = chem.ph_atmospheric_equilibrium(conc, T_c)
    if target_ph >= ph_free:
        return 0.0, ph_free
    # bicarbonate remaining at the target pH, from the same equilibrium
    m_hco3_target = 10.0 ** (chem.log_k1_carbonic(T_c) + chem.log_kh_co2(T_c)
                             + np.log10(chem.P_CO2_ATM) + target_ph)
    m_hco3_now = conc.molality()["HCO3"]
    d_alk = max(m_hco3_now - m_hco3_target, 0.0)      # mol/kg to neutralise
    return d_alk * 98.079 / 2.0 * 1e-3, ph_free       # kg H2SO4 per kg water


# --- operating point ------------------------------------------------------
def evaluate_operating_point(fan_pct, cycles, target_ph, cond,
                             makeup_water, tariffs, fill_c, fill_n,
                             skin_delta_k=8.0):
    """Cost and constraint state of one supervisory decision.

    `cond` carries the ambient and duty conditions:
        T_db, rh, T_wi (condenser return), m_w, Q_evap_kw
    """
    m_a = float(tw.air_mass_flow_from_fan(fan_pct))
    if m_a <= 0.05:
        return None

    # circulating water chemistry sets the water activity seen by the tower
    conc = makeup_water.concentrate(cycles)
    aw = float(wa.water_activity_tds(conc.tds()))

    T_wo, info = tw.solve_outlet_temperature(
        cond["T_wi"], cond["T_db"], cond["rh"], cond["m_w"], m_a,
        fill_c, fill_n, aw=aw)
    if info is None:
        return None

    # energy
    p_fan = float(fan_power(m_a, cond["m_a_rated"], cond["p_fan_rated_kw"]))
    p_chill, cop = chiller_power_biquad(
        cond["Q_evap_kw"], T_wo, Q_ref_kw=nominal_capacity(cond))
    p_total = p_fan + float(p_chill)

    # water
    wb = water_balance(info["m_evap"], cond["m_w"], cycles)

    # chemistry, evaluated at the condenser SKIN temperature
    # Each mineral is evaluated where it is least soluble, not all at one
    # temperature. Calcite and gypsum are retrograde, so the hot tube skin
    # governs. Amorphous silica is PROGRADE -- more soluble hot -- so the
    # cold tower basin governs. Evaluating silica at the skin, as a single
    # evaluation point does, makes the model optimistic about the one
    # species with no effective inhibitor in general service.
    T_skin = cond["T_wi"] + skin_delta_k
    T_basin = T_wo
    acid_kg_per_kg, ph_free = acid_dose_for_ph(makeup_water, cycles,
                                               target_ph, T_skin)
    sat = chem.saturation_state_split(conc, T_skin, T_basin,
                                      pH_hot=target_ph, pH_cold=target_ph)
    limits = chem.OPERATING_LIMITS
    violations = {k: sat[k] - limits[k] for k in limits if sat[k] > limits[k]}

    # cost per hour
    m_acid = acid_kg_per_kg * wb["makeup"] * 3600.0          # kg/h
    cost = (tariffs["elec_per_kwh"] * p_total
            + tariffs["water_per_m3"] * wb["makeup"] * 3.6
            + tariffs["acid_per_kg"] * m_acid
            + tariffs["antiscalant_per_m3"] * wb["makeup"] * 3.6)

    return {
        "fan_pct": fan_pct, "cycles": cycles, "target_ph": target_ph,
        "m_a": m_a, "T_wo": T_wo, "approach": info["approach"],
        "aw": aw, "cop": float(cop),
        "P_fan_kW": p_fan, "P_chiller_kW": float(p_chill), "P_total_kW": p_total,
        "m_evap_kg_s": info["m_evap"],
        "makeup_m3_h": wb["makeup"] * 3.6, "blowdown_m3_h": wb["blowdown"] * 3.6,
        "acid_kg_h": m_acid, "ph_free": ph_free,
        "T_skin": T_skin,
        "SI_calcite": sat["SI_calcite"], "SI_gypsum": sat["SI_gypsum"],
        "SI_silica_am": sat["SI_silica_am"],
        "violations": violations, "feasible": len(violations) == 0,
        "cost_per_h": cost,
    }


# Counts how often the duty fixed point failed to converge. A run that
# reports results while this is non-zero is reporting unconverged numbers.
THERMAL_NONCONVERGED = {"calls": 0, "failed": 0}


def reset_thermal_log():
    THERMAL_NONCONVERGED.update({"calls": 0, "failed": 0})


def _thermal_solve(fan_pct, cycles, cond, makeup_water, fill_c, fill_n,
                   _cache={}, max_iter=40, tol=1e-5):
    """Tower + chiller solved as one consistent operating point.

    Two things must hold simultaneously and did not in the first version of
    this function:

    1. **Plant-scale air flow.** The fill law identified from the PSA pilot
       tower is a CHARACTERISTIC, Me = c (m_w/m_a)^n, and transfers to any
       geometry. The pilot's absolute air flow does not. Air flow here is
       the plant's own rated flow scaled by fan speed; using the pilot
       correlation gave L/G ~ 106 and a tower that barely cooled.

    2. **The condenser duty is not an input, it is a fixed point.** The
       tower rejects evaporator load PLUS compressor work. Compressor work
       depends on the cold-water temperature the tower achieves, which
       depends on the duty. So:

           T_wo -> P_chiller(T_wo) -> Q_cond -> range -> T_wi -> T_wo

       is iterated to convergence rather than assumed. Fixing the duty
       independently of the tower, as before, let the model reject a
       different amount of heat than the chiller actually produced.

    pH is absent from all of this -- it changes acid cost and the calcite
    constraint, not heat and mass transfer -- so the pH axis of the search
    is swept for free against this cached result.
    """
    # Keyed on the CONTENT of the operating condition, not id(cond).
    # id() is only unique among live objects: once a cond dict is released
    # CPython can hand the same address to the next one, and this cache
    # would then serve one ambient's solution to another. It has not been
    # observed to bite, which is exactly why it should not be left in.
    key = (round(float(fan_pct), 3), round(float(cycles), 4),
           tuple(sorted((k, float(v)) for k, v in cond.items()
                        if isinstance(v, (int, float)) and k != "T_wo_guess")))
    if key in _cache:
        return _cache[key]

    m_a = cond["m_a_rated"] * float(fan_pct) / 100.0
    if m_a <= 0.05:
        _cache[key] = None
        return None

    conc = makeup_water.concentrate(cycles)
    aw = float(wa.water_activity_tds(conc.tds()))
    m_w = cond["m_w"]

    # The map T_wo -> g(T_wo) is a monotone contraction with a ratio near
    # 0.5, so plain successive substitution needs about 26 iterations to
    # reach 1e-6 K. The original 6 iterations at 5e-3 K stopped it well
    # short, and because every grid point was seeded from ONE nearby solve,
    # the residual error was not random: points near the seed came out
    # accurate and points far from it did not. Evaporation, which is what
    # the water gate measures, moved 5.199 -> 5.396 kg/s (3.8 %) with the
    # seed alone -- larger than the margin by which that gate was failing.
    #
    # Aitken's delta-squared extrapolation removes it. Three plain steps
    # give x0, x1, x2; the geometric limit of a linearly convergent
    # sequence is then x2 - (dx1)^2 / (x2 - 2*x1 + x0), which lands on the
    # fixed point in about 9 tower solves instead of 26.
    def _step(T):
        p_chill, _cop = chiller_power_biquad(
            cond["Q_evap_kw"], T, Q_ref_kw=nominal_capacity(cond))
        Q = cond["Q_evap_kw"] + float(p_chill)
        T_in = T + Q / (m_w * CPW)
        T_next, inf = tw.solve_outlet_temperature(
            T_in, cond["T_db"], cond["rh"], m_w, m_a, fill_c, fill_n, aw=aw)
        return T_next, inf, T_in, Q

    THERMAL_NONCONVERGED["calls"] += 1

    # Two-stage solve of the duty fixed point.
    #
    # The original code took six plain substitution steps at 5e-3 K. The map
    # contracts at roughly 0.5 per step, so six steps leave it well short of
    # the fixed point -- and, worse, leave it short by an amount that depends
    # on the starting guess. Because gate_v5 seeds every grid point from one
    # nearby solve, points near the seed came out accurate and points far
    # from it did not. Evaporation moved 5.199 -> 5.396 kg/s (3.8 %) on the
    # seed alone. That is the quantity the water gate measures, and 3.8 % is
    # an order of magnitude larger than the margin the gate was failing by.
    #
    # Stage 1, the common path: Aitken delta-squared extrapolation of the
    # same substitution. A linearly convergent sequence has a geometric
    # limit, so three plain iterates x0,x1,x2 extrapolate to
    # x2 - (x2-x1)^2 / (x2-2*x1+x0). Converges in 7-10 tower solves.
    #
    # Stage 2, the fallback: Brent on r(T) = g(T) - T, which is monotone
    # decreasing and therefore bracketable. Guaranteed, but the bracket has
    # to be found by walking -- the tower model returns no solution at all
    # for inlet water far below the wet bulb -- so it is not the cheap path
    # and is used only where stage 1 fails to converge.
    def _rv(T):
        """r(T) = g(T) - T, or None where the tower has no solution."""
        T_next, inf, _T_in, _Q = _step(T)
        return None if inf is None else T_next - T

    T_wo = cond.get("T_wo_guess", cond["T_db"] - 4.0)
    converged = False
    hist = []
    for _ in range(max_iter):
        T_new, info, T_wi, Q_cond = _step(T_wo)
        if info is None:
            _cache[key] = None
            return None
        if abs(T_new - T_wo) < tol:
            T_wo, converged = T_new, True
            break
        hist.append(T_new)
        if len(hist) == 3:
            x0, x1, x2 = hist
            den = x2 - 2.0 * x1 + x0
            if abs(den) > 1e-12:
                x_ext = x2 - (x2 - x1) ** 2 / den
                if min(x0, x2) - 1.0 <= x_ext <= max(x0, x2) + 1.0:
                    T_new = x_ext
            hist = []
        T_wo = T_new

    if not converged:
        # walk outward from the last iterate to bracket the sign change,
        # then let Brent finish it
        lo = hi = None
        T = T_wo
        for _ in range(40):
            v = _rv(T)
            if v is not None and v > 0.0:
                lo = T
                break
            T -= 2.0
        if lo is not None:
            T = lo + 2.0
            for _ in range(40):
                v = _rv(T)
                if v is not None and v < 0.0:
                    hi = T
                    break
                T += 2.0
        if lo is not None and hi is not None:
            try:
                T_wo = float(brentq(lambda t: _rv(t) if _rv(t) is not None
                                    else 0.0, lo, hi, xtol=1e-8, maxiter=100))
                converged = True
            except (ValueError, RuntimeError):
                pass

    # final evaluation at the solution, so info / T_wi / Q_cond belong to
    # the T_wo actually reported
    T_check, info, T_wi, Q_cond = _step(T_wo)
    if info is None:
        _cache[key] = None
        return None
    if not converged or abs(T_check - T_wo) >= 1e-3:
        THERMAL_NONCONVERGED["failed"] += 1
    result = (m_a, aw, T_wo, info, conc, T_wi, Q_cond)

    _cache[key] = result
    return result


def _cost_at_ph(th, fan_pct, cycles, target_ph, cond, makeup_water, tariffs,
                skin_delta_k, corrosion_floor_si=None):
    """Complete an operating point given a cached thermal solution."""
    m_a, aw, T_wo, info, conc, T_wi, Q_cond = th
    p_fan = float(fan_power(m_a, cond["m_a_rated"], cond["p_fan_rated_kw"]))
    p_chill, cop = chiller_power_biquad(
        cond["Q_evap_kw"], T_wo, Q_ref_kw=nominal_capacity(cond))
    p_total = p_fan + float(p_chill)
    wb = water_balance(info["m_evap"], cond["m_w"], cycles)

    # Each mineral is evaluated where it is least soluble, not all at one
    # temperature. Calcite and gypsum are retrograde, so the hot tube skin
    # governs. Amorphous silica is PROGRADE -- more soluble hot -- so the
    # cold tower basin governs. Evaluating silica at the skin, as a single
    # evaluation point does, makes the model optimistic about the one
    # species with no effective inhibitor in general service.
    T_skin = T_wi + skin_delta_k
    T_basin = T_wo
    acid_kg_per_kg, ph_free = acid_dose_for_ph(makeup_water, cycles,
                                               target_ph, T_skin)
    sat = chem.saturation_state_split(conc, T_skin, T_basin,
                                      pH_hot=target_ph, pH_cold=target_ph)
    limits = chem.OPERATING_LIMITS
    violations = {k: sat[k] - limits[k] for k in limits if sat[k] > limits[k]}

    # --- CORROSION FLOOR -------------------------------------------------
    # Until 4 September 2026 this optimiser searched pH 7.0-9.0 against
    # saturation limits ONLY, with nothing stopping it driving the water
    # aggressive. That is not a conservative omission, it is the wrong sign of
    # error. Customer discovery found a plant chemist holding LSI at 0.8-1.0
    # DELIBERATELY, because a thin calcium-carbonate film IS the corrosion
    # defence, and a 1992 training syllabus lists "calcium carbonate protective
    # scale" as a corrosion-control method. An optimiser pushing toward LSI = 0
    # strips that film and corrodes the plant it was hired to protect.
    #
    # Saturation is therefore a BAND, not a ceiling. The floor is evaluated at
    # BULK temperature, because that is where LSI practice sits and where the
    # film has to survive; the ceiling stays at the SKIN, where scale forms.
    # Those being different evaluation points is the whole product.
    #
    # The floor is a violation exactly like a saturation breach, so no run can
    # quietly buy water by corroding the condenser.
    floor = CORROSION_FLOOR_SI if corrosion_floor_si is None else corrosion_floor_si
    if floor is not None:
        si_bulk = chem.saturation_state(conc, T_c=T_basin,
                                        pH=target_ph)["SI_calcite"]
        if si_bulk < floor:
            violations["SI_calcite_corrosion_floor"] = floor - si_bulk

    # The chiller model is an empirical correlation, and an empirical
    # correlation is only evidence inside the box it was fitted in. The
    # York YT curves are fitted over 15.56-35.00 degC entering condenser
    # water, and that window is not merely an artefact of the fit: it is
    # also the manufacturer's permitted entering-condenser-water range.
    # Below the floor, condenser head pressure collapses and oil return and
    # expansion-valve control fail; above the ceiling the machine is off its
    # rating envelope and trips on high head.
    #
    # This constraint exists because the optimiser found the hole. Given a
    # free hand it drove the fan to its lower bound in four of five Gulf
    # conditions, which puts entering condenser water at 36.5-40.5 degC --
    # outside the fitted range -- and then collected a large apparent water
    # saving from the extrapolation. A saving bought outside the validity
    # envelope of your own model is not a saving.
    # DEFECT 11, fixed 3 September 2026. The bi-quadratic has TWO validity
    # limits and only the temperature one was enforced. The capacity limit
    # binds FIRST, and lower, so the temperature guard above never sees it.
    #
    # `capft` is the machine's capacity as a function of temperature and it
    # falls as condenser water warms. Above about 32.5 degC this York YT cannot
    # make the 10 MW duty at all: q_avail drops below it and plr_raw climbs past
    # 1.0, reaching 1.15 by 35 degC. `chiller_power_biquad` then clamps plr to
    # 1.0 and evaluates the machine as merely full-loaded, so computed chiller
    # power FALLS as the condenser gets hotter. That is backwards, and it is
    # backwards in precisely the direction the optimiser pushes: its main energy
    # lever is fan speed, and lowering the fan raises T_wo. It was being paid to
    # go somewhere the machine cannot follow -- 4 of 5 Gulf conditions
    # infeasible, worst shortfall 1,216 kW of 10,000 kW.
    #
    # This is the same failure as the temperature guard above, one dimension
    # over, and it gets the same treatment: a hard feasibility constraint rather
    # than a clamp. CHILLER_RANGE_LOG already counted these as PLR_out and
    # nothing read it.
    #
    # Audited before the fix in src/chiller_feasibility_audit.py.
    t_lo, t_hi = CHILLER_TCWS_RANGE
    temp_ok = bool(t_lo <= T_wo <= t_hi)

    # DEFECT 16, fixed 4 September 2026. This read
    #     q_avail = cond["Q_evap_kw"] * capft_here
    # `capft_here` is normalised to ARI conditions -- 6.67 C chilled water,
    # 29.44 C ENTERING CONDENSER WATER -- so that line asserted the installed
    # machine is exactly the size of the load AT ARI. Nothing is ever selected
    # that way. A chiller is selected at its DESIGN entering-condenser
    # temperature, and for a Gulf plant on a cooling tower that is far above
    # 29.44 C. Selecting at ARI and then operating at 33-35 C guarantees a
    # shortfall on every hot day, which is exactly what was observed: after
    # defect 11 made the capacity limit binding, TWO OF FIVE design conditions
    # had no feasible operating point at all. Gulf plants demonstrably run on
    # those days, so the defect was in the sizing, not in the Gulf.
    #
    # The machine is now selected at the top of its own validated range,
    # CHILLER_TCWS_RANGE[1] = 35 C, so the capacity limit and the temperature
    # limit bind in the same place -- which is what a real selection does. The
    # resulting margin is 15.0 %, an ordinary number for this duty.
    # Audited in src/chiller_selection_audit.py.
    capft_ref = _biquad(CHILLER_CAPFT, 6.67, 29.44)
    capft_here = _biquad(CHILLER_CAPFT, cond.get("T_chws_c", 7.0), T_wo) / capft_ref
    q_nominal = nominal_capacity(cond)
    q_avail = q_nominal * capft_here
    plr_raw = cond["Q_evap_kw"] / max(q_avail, 1e-6)
    capacity_ok = bool(plr_raw <= CHILLER_PLR_RANGE[1])

    envelope_ok = temp_ok and capacity_ok

    m_acid = acid_kg_per_kg * wb["makeup"] * 3600.0
    cost = (tariffs["elec_per_kwh"] * p_total
            + tariffs["water_per_m3"] * wb["makeup"] * 3.6
            + tariffs["acid_per_kg"] * m_acid
            + tariffs["antiscalant_per_m3"] * wb["makeup"] * 3.6)

    return {
        "fan_pct": float(fan_pct), "cycles": float(cycles),
        "target_ph": float(target_ph), "m_a": m_a, "T_wo": T_wo,
        "approach": info["approach"], "aw": aw, "cop": float(cop),
        "P_fan_kW": p_fan, "P_chiller_kW": float(p_chill), "P_total_kW": p_total,
        "m_evap_kg_s": info["m_evap"],
        "makeup_m3_h": wb["makeup"] * 3.6, "blowdown_m3_h": wb["blowdown"] * 3.6,
        "acid_kg_h": m_acid, "ph_free": ph_free, "T_skin": T_skin,
        "T_wi": T_wi, "Q_cond_kW": Q_cond, "T_basin": T_basin,
        "SI_calcite": sat["SI_calcite"], "SI_gypsum": sat["SI_gypsum"],
        "SI_silica_am": sat["SI_silica_am"],
        # `violations` stays chemistry-only, because a pre-registered gate
        # counts skin-saturation violations by name and must keep counting
        # exactly that. The chiller envelope is a separate, additional
        # feasibility condition, reported separately.
        "violations": violations,
        "feasible_at_skin": len(violations) == 0,
        "chiller_envelope_ok": envelope_ok,
        "chiller_temp_ok": temp_ok, "chiller_capacity_ok": capacity_ok,
        "chiller_plr_raw": float(plr_raw), "chiller_q_avail_kW": float(q_avail),
        "feasible": len(violations) == 0 and envelope_ok,
        "cost_per_h": cost,
    }


def optimise(cond, makeup_water, tariffs, fill_c, fill_n,
             fan_grid=None, cycles_grid=None, ph_grid=None, skin_delta_k=8.0):
    """Least-cost supervisory setpoint subject to the skin-temperature
    saturation constraints.

    Grid search rather than a gradient method: the space is three
    dimensional and small, the objective is cheap once the thermal solve is
    memoised, and a grid returns a guaranteed-feasible answer plus the whole
    trade-off surface for the operator to inspect. In a supervisory loop a
    plant engineer has to sign off, determinism and inspectability are worth
    more than elegance.
    """
    fan_grid = np.arange(25, 101, 5.0) if fan_grid is None else fan_grid
    cycles_grid = np.arange(1.5, 12.01, 0.5) if cycles_grid is None else cycles_grid
    ph_grid = np.arange(7.0, 9.01, 0.25) if ph_grid is None else ph_grid

    best, n_eval = None, 0
    for f in fan_grid:
        for cy in cycles_grid:
            th = _thermal_solve(f, cy, cond, makeup_water, fill_c, fill_n)
            if th is None:
                continue
            for ph in ph_grid:
                r = _cost_at_ph(th, f, cy, ph, cond, makeup_water, tariffs,
                                skin_delta_k)
                n_eval += 1
                if r["feasible"] and (best is None
                                      or r["cost_per_h"] < best["cost_per_h"]):
                    best = r
    return best, n_eval


def baseline(cond, makeup_water, tariffs, fill_c, fill_n,
             fixed_cycles=4.0, fixed_ph=7.8, cw_setpoint_c=29.0,
             skin_delta_k=8.0, fan_grid=None):
    """Incumbent practice: fixed conductivity setpoint (fixed cycles), fixed
    pH setpoint, and the fan modulated to hold a fixed condenser-water
    supply temperature. The fan is not free here -- it is whatever is needed
    to hit the setpoint, which is exactly how a BMS runs it.
    """
    fan_grid = np.arange(25, 101, 2.5) if fan_grid is None else fan_grid
    chosen = None
    for f in fan_grid:
        th = _thermal_solve(f, fixed_cycles, cond, makeup_water, fill_c, fill_n)
        if th is None:
            continue
        r = _cost_at_ph(th, f, fixed_cycles, fixed_ph, cond, makeup_water,
                        tariffs, skin_delta_k)
        if r["T_wo"] <= cw_setpoint_c:      # setpoint reached
            chosen = r
            break
        chosen = r                           # else run flat out
    return chosen


# --- chiller power: bi-quadratic, replacing the Carnot-referenced model ---
#
# External review was blunt about this: "Real centrifugal chillers do not
# follow constant Carnot fractions at part-load or low-lift conditions due
# to aerodynamic surge limits and mechanical losses. Extrapolating chiller
# power savings using a static Carnot fraction at reduced condenser water
# temperatures will result in massive computational inaccuracies."
#
# That is precisely the regime the optimiser explores -- it pushes condenser
# water colder to buy compressor power -- so the error would land exactly
# where it matters most. The Carnot form was chosen for extrapolation
# safety; it turns out to be unsafe in the direction we care about.
#
# Replaced with the standard EnergyPlus / ASHRAE Chiller:Electric:EIR
# formulation:
#
#     CAPFT  = a1 + b1*Tchws + c1*Tchws^2 + d1*Tcws + e1*Tcws^2 + f1*Tchws*Tcws
#     EIRFT  = a2 + b2*Tchws + c2*Tchws^2 + d2*Tcws + e2*Tcws^2 + f2*Tchws*Tcws
#     EIRFPLR= a3 + b3*PLR + c3*PLR^2
#     P      = P_ref * CAPFT * EIRFT * EIRFPLR
#
# The coefficients below are a NAMED, PUBLISHED machine, not a generic set.
#
#   York YT, 1758 kW (500 TR) water-cooled centrifugal, R-123, inlet vanes,
#   reference COP 6.28 at the AHRI 550/590 rating point
#   (6.67 degC leaving chilled water, 29.44 degC entering condenser water).
#
# [C] EnergyPlus reference dataset `datasets/Chillers.idf`, object
#     "ElectricEIRChiller York YT 1758kW/6.28COP/Vanes" (NREL/EnergyPlus,
#     develop branch, lines 6001-6083). That file is the CoolTools curve
#     library, fitted to manufacturer selection data collected 1991-2001
#     and shipped unchanged with every EnergyPlus release.
#
# Why this machine, out of the 110 water-cooled centrifugals in that file:
#
#   1. Its reference point IS the AHRI rating point, so the normalisation
#      below is a 5.0 % / 0.5 % correction rather than a fudge, and the
#      reference COP is the machine's own instead of an assumption.
#   2. Its curves are fitted over 15.56-35.00 degC entering condenser
#      water. Gulf condenser water runs 32-35 degC; most of the library
#      stops at 26.11 degC and would be pure extrapolation here.
#   3. It is a vane-controlled centrifugal -- the workhorse of Gulf
#      district cooling -- not a high-COP VSD outlier.
#
# Effect of the swap: the previous untraced coefficients gave 2.62 % of
# chiller power per K of condenser water over 30->36 degC; this machine
# gives 2.36 %/K. The ensemble of every CoolTools centrifugal whose fit
# range reaches 32 degC spans 0.7-2.8 %/K, and constant-fraction Carnot
# gives 3.45 %/K. The change is therefore small, downward, and traceable.
#
# [C] REJECTED, and worth recording. The ASHRAE 90.1-2022 Normative
#     Appendix J curve sets (EnergyPlus `datasets/CodeCompliantEquipment.idf`,
#     PNNL, Sept 2022) are newer, are exactly unity at the AHRI point, and
#     state a validity range of 12.8-40 degC -- on paper the better source.
#     They are unusable here: they imply 0.4-0.5 %/K, i.e. a chiller that
#     loses 3 % of its COP going from 30 to 36 degC condenser water, where
#     ideal Carnot over the same lift loses 21 % and every named machine
#     loses 13-17 %. Those curves are fitted to reproduce rated full-load
#     and IPLV points, and the IPLV condenser schedule runs DOWNWARD from
#     29.44 degC as load falls, so above 30 degC they are unconstrained by
#     data despite the stated range. A stated validity range is not
#     evidence of a fitted range.

CHILLER_MACHINE = ("York YT 1758kW/6.28COP/Vanes, "
                   "EnergyPlus datasets/Chillers.idf (CoolTools)")
CHILLER_CAPFT = (0.7079149, -0.002006276, -0.002596043,
                 0.03005922, -0.001056423, 0.002045705)
CHILLER_EIRFT = (0.5605391, -0.01377994, 6.569542e-05,
                 0.01321951, 0.0002686074, -0.0005011451)
CHILLER_EIRFPLR = (0.1861223, 0.5482049, 0.2647377)
CHILLER_COP_REF = 6.28                 # machine reference COP, AHRI 550/590
CHILLER_TCHWS_RANGE = (4.44, 8.89)     # degC, fitted range of x
CHILLER_TCWS_RANGE = (15.56, 35.00)    # degC, fitted range of y
CHILLER_PLR_RANGE = (0.20, 1.06)

# Minimum calcium-carbonate saturation at BULK temperature. Below this the
# water is aggressive and strips the protective film -- see the corrosion
# floor in _cost_at_ph. 0.0 is the least defensible floor that is still a
# floor: it forbids driving the water into undersaturation without asserting
# the 0.8-1.0 an interviewed chemist actually holds, which is that plant's
# choice and not a universal constant. Sensitivity in
# src/corrosion_floor_audit.py. Set to None to disable, which is what the
# model did until 4 September 2026.
CORROSION_FLOOR_SI = 0.0

# Every evaluation outside the fitted box is counted rather than silently
# clipped, so a run can report how much of its answer was extrapolated
# instead of leaving the reader to assume none of it was.
CHILLER_RANGE_LOG = {"calls": 0, "T_chws_out": 0, "T_cws_out": 0,
                     "PLR_out": 0, "T_cws_min": None, "T_cws_max": None}


def selection_factor(T_chws_c=7.0, T_design_cws_c=None):
    """Installed nominal capacity as a multiple of the design load.

    A chiller is selected at its DESIGN entering-condenser temperature, not at
    the ARI rating point. Capacity falls as condenser water warms, so a machine
    whose nameplate equals the load at ARI cannot make that load anywhere
    hotter -- see defect 16 in _cost_at_ph.

    The design point used here is the top of the curve's own fitted range,
    CHILLER_TCWS_RANGE[1] = 35 C, so capacity and temperature validity end
    together. On this York YT that gives a factor of 1.1505, a 15.0 % margin.
    """
    T_design = CHILLER_TCWS_RANGE[1] if T_design_cws_c is None else T_design_cws_c
    ref = _biquad(CHILLER_CAPFT, 6.67, 29.44)
    capft_design = _biquad(CHILLER_CAPFT, T_chws_c, T_design) / ref
    return 1.0 / capft_design


def nominal_capacity(cond):
    """Installed nominal (ARI) capacity of the machine serving this load.

    Explicit `Q_nominal_kw` wins; otherwise it is derived by selecting at the
    design entering-condenser temperature. Defaulting to the LOAD -- which is
    what every call site did before defect 16 -- asserts a machine sized at ARI
    for a plant that never operates there.
    """
    q_nom = cond.get("Q_nominal_kw")
    if q_nom:
        return float(q_nom)
    return float(cond["Q_evap_kw"]) * selection_factor(cond.get("T_chws_c", 7.0))


def reset_chiller_range_log():
    CHILLER_RANGE_LOG.update({"calls": 0, "T_chws_out": 0, "T_cws_out": 0,
                              "PLR_out": 0, "T_cws_min": None,
                              "T_cws_max": None})


def _biquad(c, x, y):
    return c[0] + c[1]*x + c[2]*x*x + c[3]*y + c[4]*y*y + c[5]*x*y


def chiller_power_biquad(Q_evap_kw, T_cw_supply_c, T_chw_supply_c=7.0,
                         Q_ref_kw=None, cop_ref=CHILLER_COP_REF,
                         T_chws_ref=6.67, T_cws_ref=29.44):
    """Chiller electrical power, EnergyPlus Chiller:Electric:EIR form.

    Coefficients are those of a named machine (see above). They are
    NORMALISED to the AHRI rating point (6.67 degC leaving chilled water,
    29.44 degC entering condenser water) before use, because the published
    curves return 0.950 (CAPFT) and 0.995 (EIRFT) there rather than unity
    -- CoolTools fits were anchored to each machine's own calibration
    point, not to the rating point. Normalising preserves the curve SHAPE,
    which is how power varies with condenser temperature and is the only
    quantity the optimiser depends on, while anchoring the magnitude to the
    machine's stated reference COP of 6.28 (about 0.56 kW/ton).
    """
    Q_ref_kw = Q_evap_kw if Q_ref_kw is None else Q_ref_kw

    CHILLER_RANGE_LOG["calls"] += 1
    t_cws = float(T_cw_supply_c)
    lo, hi = CHILLER_RANGE_LOG["T_cws_min"], CHILLER_RANGE_LOG["T_cws_max"]
    CHILLER_RANGE_LOG["T_cws_min"] = t_cws if lo is None else min(lo, t_cws)
    CHILLER_RANGE_LOG["T_cws_max"] = t_cws if hi is None else max(hi, t_cws)
    if not (CHILLER_TCHWS_RANGE[0] <= T_chw_supply_c <= CHILLER_TCHWS_RANGE[1]):
        CHILLER_RANGE_LOG["T_chws_out"] += 1
    if not (CHILLER_TCWS_RANGE[0] <= t_cws <= CHILLER_TCWS_RANGE[1]):
        CHILLER_RANGE_LOG["T_cws_out"] += 1

    capft_ref = _biquad(CHILLER_CAPFT, T_chws_ref, T_cws_ref)
    eirft_ref = _biquad(CHILLER_EIRFT, T_chws_ref, T_cws_ref)
    capft = _biquad(CHILLER_CAPFT, T_chw_supply_c, T_cw_supply_c) / capft_ref
    eirft = _biquad(CHILLER_EIRFT, T_chw_supply_c, T_cw_supply_c) / eirft_ref
    capft = max(capft, 0.3)
    eirft = max(eirft, 0.3)

    q_avail = Q_ref_kw * capft
    plr_raw = Q_evap_kw / max(q_avail, 1e-6)
    if not (CHILLER_PLR_RANGE[0] <= plr_raw <= CHILLER_PLR_RANGE[1]):
        CHILLER_RANGE_LOG["PLR_out"] += 1
    plr = min(max(plr_raw, 0.1), 1.0)
    eirplr = (CHILLER_EIRFPLR[0] + CHILLER_EIRFPLR[1] * plr
              + CHILLER_EIRFPLR[2] * plr * plr)
    eirplr_ref = sum(CHILLER_EIRFPLR)
    eirplr = eirplr / eirplr_ref

    p_ref = Q_ref_kw / cop_ref
    power = p_ref * capft * eirft * eirplr
    return power, Q_evap_kw / max(power, 1e-6)


# --- TEMA / HEI minimum tube velocity ------------------------------------
#
# Also from review, and it is a hard bound on the whole coupling story:
# TEMA, HEI and the chiller makers enforce a minimum condenser tube water
# velocity of 0.9 m/s at design and an absolute floor of 0.5 m/s at deep
# part load, to prevent particulate settling. That is enforced regardless of
# scaling chemistry, so the optimiser CANNOT trade unlimited pump power for
# chemistry headroom -- there is a mechanical floor, and violating it voids
# warranties.
TUBE_VELOCITY_MIN_DESIGN = 0.9      # m/s [C - TEMA / HEI]
TUBE_VELOCITY_MIN_ABSOLUTE = 0.5    # m/s at deep part load [C]
