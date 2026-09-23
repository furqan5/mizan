"""Protocol fixed before execution, 21 Sep 2026.

Numerical balances: 1e-10 relative and 1e-7 kJ for extensive updates/HX;
tower mass 1e-8 relative+1e-9 kg/s and energy 1e-5 relative+1e-6 kW.
Synthetic fixtures are software cases, not measured or calibrated plants.
Test faults must reject, preserve state, or expose the specified legacy
difference. No field accuracy, MPC optimality or economic gate is claimed.
"""
import math

import pytest

import controller
import thermal_dynamics as td


def water():
    return td.ConstantCpFluid('synthetic water', 4.0, 0., 100., 'test fixture, constant cp')


def test_mixing_tracks_extensive_energy_and_variable_mass():
    node = td.EnergyNode('CW', 'basin', 100., 100.*4.*30., water())
    # Ten kilograms added at 10 C, five removed at 30 C, plus 100 kJ heat.
    step = td.advance_energy(node, [td.EnthalpyStream('makeup', 1., 40.),
                                   td.EnthalpyStream('drain', -.5, 120.)], 10., 10.)
    assert step.state.solution_mass_kg == 105.
    assert step.state.enthalpy_kj == 11900.
    assert step.state.temperature_c == pytest.approx(11900./420.)
    assert step.energy_residual_kj == pytest.approx(0., abs=1e-7)
    assert node.solution_mass_kg == 100.
    assert node.temperature_c == 30.


def test_equal_temperature_mass_removal_does_not_cool_remaining_liquid():
    node = td.EnergyNode('CW', 'basin', 100., 12000., water())
    step = td.advance_energy(node, [td.EnthalpyStream('drain', -1., 120.)], 0., 10.)
    assert step.state.temperature_c == 30.
    assert step.state.enthalpy_kj == 10800.


@pytest.mark.parametrize('dt,heat,streams', [
    (0., 0., []), (-1., 0., []), (1., math.nan, []),
    (100., 0., [td.EnthalpyStream('empty', -1., 120.)]),
    (1., 1e8, []), (1., 0., [td.EnthalpyStream('bad', 1., math.inf)]),
    (1., 0., [td.EnthalpyStream('same', 1., 1.), td.EnthalpyStream('same', 1., 1.)]),
])
def test_invalid_energy_step_cannot_advance(dt, heat, streams):
    node = td.EnergyNode('CW', 'basin', 100., 12000., water())
    with pytest.raises(td.ThermalDomainError):
        td.advance_energy(node, streams, heat, dt)
    assert node.enthalpy_kj == 12000.


@pytest.mark.parametrize('effectiveness', [0., .25, .8, 1.])
@pytest.mark.parametrize('temperatures', [(20., 40.), (40., 20.), (30., 30.)])
def test_hx_heat_closes_for_unequal_capacity_and_reversed_temperature(effectiveness, temperatures):
    glycol = td.ConstantCpFluid('test glycol', 3.0, 0., 100., 'synthetic')
    tp, ts = temperatures
    r = td.heat_exchanger_pass(tp, ts, 10., 5., water(), glycol, effectiveness)
    primary_gain = 10.*4.*(r.primary_out_c-tp)
    secondary_gain = 5.*3.*(r.secondary_out_c-ts)
    assert primary_gain == pytest.approx(-secondary_gain, abs=1e-7)
    assert primary_gain == pytest.approx(effectiveness*15.*(ts-tp), abs=1e-7)
    assert min(temperatures) <= r.primary_out_c <= max(temperatures)
    assert min(temperatures) <= r.secondary_out_c <= max(temperatures)


def test_no_heat_transfer_at_explicit_zero_effectiveness():
    r = td.heat_exchanger_pass(20., 40., 10., 5., water(), water(), 0.)
    assert (r.primary_out_c, r.secondary_out_c, r.heat_secondary_to_primary_kw) == (20., 40., 0.)


def test_capacity_overflow_does_not_become_a_zero_temperature():
    node = td.EnergyNode('CW', 'invalid', 1e308, 1e308, water())
    with pytest.raises(td.ThermalDomainError, match='finite'):
        _ = node.temperature_c


def test_property_enthalpy_overflow_is_rejected():
    fluid = td.ConstantCpFluid('overflow fixture', 1e308, 0., 100., 'synthetic')
    with pytest.raises(td.ThermalDomainError, match='finite'):
        fluid.enthalpy_kj_kg(20.)


def test_hx_capacity_overflow_is_rejected():
    with pytest.raises(td.ThermalDomainError, match='finite'):
        td.heat_exchanger_pass(20., 40., 1e308, 1e308, water(), water(), .8)


@pytest.mark.parametrize('effectiveness,flow', [(None, 5.), (1.01, 5.), (-.01, 5.), (.8, 0.)])
def test_hx_unknown_or_unphysical_data_rejected(effectiveness, flow):
    with pytest.raises(td.ThermalDomainError):
        td.heat_exchanger_pass(20., 40., flow, 5., water(), water(), effectiveness)


@pytest.mark.parametrize('plr', [.2, .6, 1., 1.03, 1.06])
def test_chiller_matches_independent_rating_point_polynomial(plr):
    nominal = 1000.
    r = td.chiller_pass(plr*nominal, 29.44, 6.67, nominal, enabled=True)
    a, b, c = controller.CHILLER_EIRFPLR
    expected = nominal/controller.CHILLER_COP_REF*(a+b*plr+c*plr**2)/(a+b+c)
    assert r.electricity_kw == pytest.approx(expected, rel=1e-12)
    assert r.condenser_kw-r.evaporator_kw == pytest.approx(r.electricity_kw)


def test_strict_chiller_exposes_legacy_above_unity_power_clamp():
    legacy, _ = controller.chiller_power_biquad(1060., 29.44, 6.67, Q_ref_kw=1000.)
    strict = td.chiller_pass(1060., 29.44, 6.67, 1000., enabled=True)
    assert strict.electricity_kw > legacy
    at_unity, _ = controller.chiller_power_biquad(1000., 29.44, 6.67, Q_ref_kw=1000.)
    assert legacy == at_unity  # Preserve the historical behaviour explicitly.


@pytest.mark.parametrize('q,tcw,tchw', [
    (0., 29.44, 6.67), (199., 29.44, 6.67), (1061., 29.44, 6.67),
    (500., 15., 7.), (500., 36., 7.), (500., 29., 22.), (math.nan, 29., 7.),
])
def test_chiller_never_silently_clips_outside_supported_domain(q, tcw, tchw):
    with pytest.raises(td.ThermalDomainError):
        td.chiller_pass(q, tcw, tchw, 1000., enabled=True)


def test_chiller_off_is_explicit_and_has_no_claimed_cop():
    r = td.chiller_pass(0., 30., 22., 1000., enabled=False)
    assert (r.evaporator_kw, r.electricity_kw, r.condenser_kw, r.cop) == (0., 0., 0., None)
    with pytest.raises(td.ThermalDomainError):
        td.chiller_pass(1., 30., 22., 1000., enabled=False)


@pytest.mark.parametrize('rh,aw', [(.3, 1.), (.6, .99), (.85, 1.)])
def test_poppe_hot_flow_and_air_liquid_energy_agree(rh, aw):
    r = td.tower_pass(38., 25., rh, 101325., 100., 75., 1., .6, aw)
    assert r.cold_liquid_kg_s+r.evaporation_kg_s == pytest.approx(100., rel=1e-8, abs=1e-9)
    assert r.evaporation_kg_s > 0
    assert r.cold_out_c < 38.
    assert r.liquid_enthalpy_loss_kw == pytest.approx(r.air_enthalpy_gain_kw, rel=1e-5, abs=1e-6)
    # Nominal cp*m_cold*DeltaT alone omits hot-side enthalpy of evaporated mass.
    nominal_sensible = td.tower.CPW*r.cold_liquid_kg_s*(38.-r.cold_out_c)
    assert r.liquid_enthalpy_loss_kw-nominal_sensible == pytest.approx(td.tower.CPW*r.evaporation_kg_s*38., rel=2e-6)


def test_faulted_air_energy_is_detected(monkeypatch):
    original = td.tower.solve_outlet_temperature
    def faulty(*args, **kwargs):
        t, info = original(*args, **kwargs)
        return t, dict(info, h_a_out=info['h_a_out']+10.)
    monkeypatch.setattr(td.tower, 'solve_outlet_temperature', faulty)
    with pytest.raises(td.ThermalDomainError, match='energy closure'):
        td.tower_pass(38., 25., .3, 101325., 100., 75., 1., .6, 1.)


def test_failed_tower_never_becomes_zero_heat(monkeypatch):
    monkeypatch.setattr(td.tower, 'solve_outlet_temperature', lambda *a, **k: (math.nan, None))
    with pytest.raises(td.ThermalDomainError, match='no converged'):
        td.tower_pass(38., 25., .3, 101325., 100., 75., 1., .6, 1.)


@pytest.mark.parametrize('rh,pressure,air', [(-.1, 101325., 75.), (1.1, 101325., 75.),
                                           (.3, 0., 75.), (.3, 101325., 0.)])
def test_tower_invalid_boundary_rejected(rh, pressure, air):
    with pytest.raises(td.ThermalDomainError):
        td.tower_pass(38., 25., rh, pressure, 100., air, 1., .6, 1.)


@pytest.mark.parametrize('rh', [.3, .6, .85])
def test_conservative_poppe_numerical_refinement(rh):
    # Registered in tower.py before execution: <=0.01 K and <=0.1% evaporation.
    coarse_t, coarse = td.tower.solve_outlet_temperature(
        38., 25., rh, 100., 75., 1., .6, conservative_energy=True, n_steps=160)
    fine_t, fine = td.tower.solve_outlet_temperature(
        38., 25., rh, 100., 75., 1., .6, conservative_energy=True, n_steps=320)
    assert coarse is not None and fine is not None
    assert abs(coarse_t-fine_t) <= .01
    assert abs(coarse['m_evap']/fine['m_evap']-1.) <= .001


def test_original_fog_energy_failure_is_reproduced_without_rewriting_old_path():
    t, info = td.tower.solve_outlet_temperature(38., 25., .85, 100., 75., 1., .6)
    humidity = td.psychro.humidity_ratio_from_rh(25., .85, 101325.)
    air_gain = 75.*(info['h_a_out']-td.psychro.h_scalar(25., humidity))
    liquid_loss = td.tower.CPW*(info['m_w_top']*38.-100.*t)
    assert abs(liquid_loss-air_gain) > 1e-6+1e-5*abs(liquid_loss)


@pytest.mark.parametrize('fault', ['mass', 'fill'])
def test_inconsistent_tower_internal_closure_rejected(monkeypatch, fault):
    original = td.tower.solve_outlet_temperature
    def faulty(*args, **kwargs):
        t, info = original(*args, **kwargs)
        if fault == 'mass':
            return t, dict(info, m_w_top=info['m_w_top']+1.)
        return t, dict(info, Me=info['Me']+1.)
    monkeypatch.setattr(td.tower, 'solve_outlet_temperature', faulty)
    with pytest.raises(td.ThermalDomainError, match='closure'):
        td.tower_pass(38., 25., .3, 101325., 100., 75., 1., .6, 1.)
