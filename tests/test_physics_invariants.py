"""Physical laws that must hold whatever the parameters are.

These are not calibration checks -- the pre-registered gates do that. These
pin invariants that no fit, refactor or re-tune is ever allowed to break: the
second law, mass balance, monotonicity of saturation in concentration, and the
sign of every derivative that carries a physical meaning.

A model that violates one of these is wrong regardless of how well it scores.
"""
from __future__ import annotations

import numpy as np
import pytest

import chemistry as ch
import controller as ctl
import psychro as ps
import tower as tw


# ---------------------------------------------------------------------------
# Psychrometrics, against ASHRAE reference values
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("T_c, pws_pa", [
    (0.0, 611.2),        # triple point                     [C: ASHRAE Ch.1]
    (20.0, 2339.0),
    (30.0, 4247.0),
    (40.0, 7385.0),
])
def test_saturation_vapour_pressure_matches_ashrae(T_c, pws_pa):
    """The in-house psychrometrics exist because Python 3.14 has no CoolProp
    wheel. That makes an independent reference check mandatory, not optional."""
    assert ps.sat_vapour_pressure(T_c) == pytest.approx(pws_pa, rel=2e-3)


def test_temperature_ordering_dewpoint_wetbulb_drybulb():
    """T_dew <= T_wb <= T_db always, with equality only at saturation."""
    for T_db in (15.0, 25.0, 35.0, 45.0):
        for rh in (0.15, 0.40, 0.75, 0.99):
            W = ps.humidity_ratio_from_rh(T_db, rh)
            T_wb = ps.wetbulb(T_db, W)
            T_dp = ps.dewpoint(W)
            assert T_dp <= T_wb + 1e-6 <= T_db + 1e-6, (
                f"ordering violated at T_db={T_db}, rh={rh}: "
                f"dew {T_dp:.3f}, wb {T_wb:.3f}, db {T_db:.3f}")


def test_wetbulb_equals_drybulb_at_saturation():
    for T_db in (10.0, 25.0, 40.0):
        W = ps.humidity_ratio_from_rh(T_db, 1.0)
        assert ps.wetbulb(T_db, W) == pytest.approx(T_db, abs=0.05)


def test_humidity_ratio_round_trips_through_relative_humidity():
    for T_c in (12.0, 28.0, 44.0):
        for rh in (0.2, 0.5, 0.9):
            W = ps.humidity_ratio_from_rh(T_c, rh)
            assert ps.relative_humidity(T_c, W) == pytest.approx(rh, rel=1e-6)


# ---------------------------------------------------------------------------
# Tower: the second law, and monotonicity in the actuator
# ---------------------------------------------------------------------------
def test_outlet_water_never_falls_below_the_wet_bulb():
    """A counterflow evaporative tower cannot cool water below the ambient wet
    bulb. This is the second law expressed in the one place the integrator
    could silently break it."""
    for T_db, rh in ((25.0, 0.5), (35.0, 0.3), (45.0, 0.2)):
        T_wb = ps.wetbulb_from_rh(T_db, rh)
        for m_a in (200.0, 300.0, 400.0):
            out = tw.solve_outlet_temperature(
                T_wi=T_wb + 12.0, T_db=T_db, rh=rh,
                m_w=478.0, m_a=m_a, c=1.35, n=-0.55)
            T_wo = out[0] if isinstance(out, (tuple, list)) else out
            if T_wo is None or not np.isfinite(T_wo):
                continue
            assert T_wo >= T_wb - 1e-3, (
                f"outlet {T_wo:.3f} C is below the wet bulb {T_wb:.3f} C")
            assert T_wo <= T_wb + 12.0 + 1e-6, (
                "a cooling tower must not heat the water")


def test_more_air_cools_the_water_further():
    """Monotonicity in the actuator. If this inverts, the optimiser will walk
    the wrong way -- and it is exactly what defect 1 caused."""
    T_db, rh = 35.0, 0.35
    temps = []
    for m_a in (150.0, 250.0, 350.0, 450.0):
        out = tw.solve_outlet_temperature(
            T_wi=ps.wetbulb_from_rh(T_db, rh) + 12.0, T_db=T_db, rh=rh,
            m_w=478.0, m_a=m_a, c=1.35, n=-0.55)
        T_wo = out[0] if isinstance(out, (tuple, list)) else out
        if T_wo is not None and np.isfinite(T_wo):
            temps.append(T_wo)
    assert len(temps) >= 3
    assert all(b < a + 1e-9 for a, b in zip(temps, temps[1:])), (
        f"outlet temperature must fall as air flow rises, got {temps}")


# ---------------------------------------------------------------------------
# Water balance
# ---------------------------------------------------------------------------
def test_water_balance_closes():
    """makeup = evaporation + drift + blowdown, exactly."""
    for m_evap in (3.0, 5.2, 9.4):
        for cycles in (2.0, 4.0, 6.0, 7.0):
            wb = ctl.water_balance(m_evap, 478.0, cycles)
            assert wb["makeup"] == pytest.approx(
                m_evap + wb["drift"] + wb["blowdown"], rel=1e-12), (
                "the water balance must close identically")
            assert wb["blowdown"] >= 0.0
            assert wb["drift"] > 0.0


def test_makeup_follows_the_cycles_arithmetic():
    """makeup = evaporation x C/(C-1) is arithmetic, not a model. It is the
    reason the 15 % water gate was unreachable: 7 cycles gives 12.50 %, 8
    gives 14.29 %, and 15 % needs 8.5 -- while gypsum saturates at 7."""
    m_evap = 5.2
    for cycles in (2.0, 3.5, 6.0, 7.0, 8.5):
        wb = ctl.water_balance(m_evap, 478.0, cycles)
        expected = m_evap * cycles / (cycles - 1.0)
        assert wb["makeup"] == pytest.approx(expected, rel=1e-9)


def test_the_water_gate_threshold_was_arithmetically_unreachable():
    """Documents the V5 finding as an invariant rather than a narrative: no
    control strategy of any kind reaches a 15 % makeup reduction from a
    baseline of 4 cycles without exceeding 8.5 cycles."""
    def reduction(c_from, c_to):
        return 100.0 * (1.0 - (c_to / (c_to - 1.0)) / (c_from / (c_from - 1.0)))
    assert reduction(4.0, 7.0) == pytest.approx(12.50, abs=0.01)
    assert reduction(4.0, 8.0) == pytest.approx(14.29, abs=0.01)
    assert reduction(4.0, 8.5) >= 15.0 - 0.35
    assert reduction(4.0, 7.0) < 15.0, (
        "the gypsum wall at 7 cycles sits below the 15 % criterion; the "
        "pre-registration was mis-specified, not merely missed")


# ---------------------------------------------------------------------------
# Chemistry: monotonicity in concentration
# ---------------------------------------------------------------------------
def _concentrate(w, c):
    ions = ("Ca", "Mg", "Na", "K", "HCO3", "SO4", "Cl", "NO3", "TDS")
    return ch.Water(**{**w.__dict__,
                       **{k: getattr(w, k) * c for k in ions}})


def test_saturation_rises_monotonically_with_cycles(aramco):
    """Concentrating a water can only make it more saturated. If any index
    falls with cycles, the speciation has a sign error."""
    prev = None
    for c in (2.0, 3.0, 4.0, 5.0, 6.0, 7.0):
        ss = ch.saturation_state(_concentrate(aramco, c), 40.0, pH=8.0)
        if prev is not None:
            for key in ("SI_calcite", "SI_gypsum"):
                assert ss[key] > prev[key] - 1e-9, (
                    f"{key} fell from {prev[key]:.5f} to {ss[key]:.5f} between "
                    f"cycles {c-1} and {c}")
        prev = ss


def test_max_cycles_tightens_as_the_limit_tightens(aramco):
    loose = ch.max_cycles(aramco, 40.0,
                          limits={"SI_calcite": 1.5, "SI_gypsum": 0.5,
                                  "SI_silica_am": 0.0})
    tight = ch.max_cycles(aramco, 40.0,
                          limits={"SI_calcite": 0.0, "SI_gypsum": -0.3,
                                  "SI_silica_am": 0.0})
    assert tight < loose, (
        "a stricter saturation limit must permit fewer cycles")


def test_gypsum_is_not_ph_sensitive(aramco):
    """EPRI: calcium sulphate scale 'is not pH sensitive as is calcium
    carbonate scale'. This is why the acid lever cannot buy cycles against
    gypsum, and therefore why the water gate is unreachable."""
    conc = _concentrate(aramco, 6.0)
    si = [ch.saturation_state(conc, 40.0, pH=p)["SI_gypsum"]
          for p in (7.0, 7.5, 8.0, 8.5, 9.0)]
    assert max(si) - min(si) < 0.02, (
        f"SI_gypsum moved {max(si) - min(si):.4f} across pH 7-9; it must be "
        "essentially pH-insensitive")

    si_cal = [ch.saturation_state(conc, 40.0, pH=p)["SI_calcite"]
              for p in (7.0, 9.0)]
    assert si_cal[1] - si_cal[0] > 1.0, (
        "calcite MUST be strongly pH-sensitive -- if it is not, the "
        "comparison above is vacuous")


# ---------------------------------------------------------------------------
# Chiller and fan
# ---------------------------------------------------------------------------
def _nameplate(q_design_kw: float) -> float:
    """The nameplate the production path uses. Every call site in
    controller.py passes `Q_ref_kw=nominal_capacity(cond)`; calling without it
    is a different machine (see the trap test below)."""
    return q_design_kw * ctl.selection_factor(7.0)


def test_chiller_power_rises_with_condenser_water_temperature():
    """The whole reason cooling the condenser is worth fan power. If this sign
    inverts, the optimiser will heat the condenser to save energy.

    Scored on the PRODUCTION path -- a fixed nameplate, as every call site in
    controller.py uses."""
    q = 5000.0
    p = [ctl.chiller_power_biquad(q, T, Q_ref_kw=_nameplate(q))[0]
         for T in np.arange(20.0, 35.01, 1.0)]
    assert all(b > a for a, b in zip(p, p[1:])), (
        f"chiller power must rise monotonically with entering condenser water "
        f"across the whole fitted envelope, got {p}")


def test_chiller_cop_falls_monotonically_with_condenser_water():
    q = 5000.0
    cop = [ctl.chiller_power_biquad(q, T, Q_ref_kw=_nameplate(q))[1]
           for T in np.arange(20.0, 35.01, 1.0)]
    assert all(b < a for a, b in zip(cop, cop[1:])), (
        f"COP must fall as lift rises; got {cop}")


def test_chiller_sensitivity_is_in_the_range_named_machines_show():
    """HANDOFF records 2.36 %/K over 30-36 C for the York YT curves, against
    ~21 % over the span for Carnot and 0.4-0.5 %/K for the ASHRAE 90.1
    Appendix J curves that were REJECTED because they are unconstrained by
    data above 30 C. A drift out of this band means a curve set was swapped."""
    q, lo, hi = 5000.0, 30.0, 35.0
    ref = _nameplate(q)
    p_lo = ctl.chiller_power_biquad(q, lo, Q_ref_kw=ref)[0]
    p_hi = ctl.chiller_power_biquad(q, hi, Q_ref_kw=ref)[0]
    per_k = 100.0 * (p_hi / p_lo - 1.0) / (hi - lo)
    assert 1.5 <= per_k <= 4.0, (
        f"chiller sensitivity is {per_k:.2f} %/K; below ~1.5 means the "
        "Appendix J curves have crept back in, above ~4 means Carnot has")


def test_the_plr_clamp_trap_still_behaves_exactly_as_the_audit_recorded():
    """NOT a defect -- a documented trap, and this pins it so it cannot change
    silently.

    `src/chiller_feasibility_audit.py` records: 'chiller_power_biquad clamps
    plr_raw to 1.0 when the machine cannot make the duty, so computed power
    FALLS with rising condenser temperature above ~32.5 C. The optimiser's
    main lever (fan speed down -> T_cws up) drives it into that region, where
    the chiller cost that should offset the fan saving is under-computed.'

    That happens only when the nameplate is set equal to the load, which is
    what `Q_ref_kw=None` does. No controller.py call site does that -- all
    three pass `nominal_capacity(cond)` -- and defect 11's capacity guard
    rejects the region anyway. `fouling_energy.py` uses the degenerate mode
    deliberately, as a cross-check confined to below the turnover.

    If this test ever fails, the default changed. Check every call site."""
    p = [ctl.chiller_power_biquad(5000.0, T)[0] for T in (30.0, 32.0, 34.0)]
    assert p[2] < p[1], (
        "the degenerate Q_ref_kw=None mode is documented to turn over above "
        "~32.5 C; it no longer does, so the default has changed and every "
        "call site needs re-checking")


def test_the_capacity_guard_rejects_the_clamped_region():
    """Defect 11's fix is what makes the trap above harmless in production:
    once plr_raw exceeds the machine's declared range the point is refused."""
    q = 5000.0
    ref = _nameplate(q)
    ctl.reset_chiller_range_log()
    # Push the machine well past its capacity by starving the nameplate.
    ctl.chiller_power_biquad(q, 34.0, Q_ref_kw=q * 0.5)
    assert ctl.CHILLER_RANGE_LOG["PLR_out"] >= 1, (
        "a part-load ratio outside the declared range must be counted so the "
        "optimiser can reject the point (defect 11)")

    ctl.reset_chiller_range_log()
    ctl.chiller_power_biquad(q, 30.0, Q_ref_kw=ref)
    assert ctl.CHILLER_RANGE_LOG["PLR_out"] == 0, (
        "a normal production point must not be flagged")


def test_fan_power_follows_the_cube_law():
    """Fan power scales as the cube of air flow. This is what makes the
    trade-off convex and gives the optimiser an interior optimum at all."""
    rated, p_rated = 400.0, 110.0
    for ratio in (0.5, 0.75, 1.0):
        p = ctl.fan_power(rated * ratio, rated, p_rated)
        assert p == pytest.approx(p_rated * ratio**3, rel=1e-6)


def test_chiller_validity_envelope_rejects_rather_than_extrapolates():
    """Defect 9 in force: outside the fitted entering-condenser-water window
    the point must be refused, not silently evaluated."""
    lo, hi = ctl.CHILLER_TCWS_RANGE
    ctl.reset_chiller_range_log()
    ctl.chiller_power_biquad(5000.0, hi + 5.0)
    log = ctl.CHILLER_RANGE_LOG
    assert log["T_cws_out"] >= 1, (
        "evaluating outside the fitted condenser-water range must be counted; "
        "silent extrapolation is what booked a false 20.41 % water saving")


# ---------------------------------------------------------------------------
# Aggregation: the mean-of-ratios defect
# ---------------------------------------------------------------------------
def test_ratio_of_totals_differs_from_mean_of_ratios_when_load_correlates():
    """Defect 20's class. A percentage aggregated as a mean of ratios gives a
    light January hour the same vote as a heavy August hour. Where the
    percentage saving correlates with load -- and here it does, negatively for
    energy and positively for water -- the two disagree, and only the ratio of
    totals is the number a plant banks."""
    hours = np.array([4380.0, 4380.0])
    base = np.array([680.0, 1490.0])           # kW: light winter, heavy summer
    opt = np.array([610.0, 1460.0])

    mean_of_ratios = float(np.sum((hours / hours.sum())
                                  * (100.0 * (base - opt) / base)))
    ratio_of_totals = float(100.0 * (np.sum(hours * base) - np.sum(hours * opt))
                            / np.sum(hours * base))

    assert abs(mean_of_ratios - ratio_of_totals) > 1.0, (
        "this fixture must actually exhibit the divergence, or the test is "
        "vacuous")
    assert ratio_of_totals < mean_of_ratios, (
        "when the larger saving sits on the lighter load, the mean of ratios "
        "FLATTERS the result -- that is the defect")
