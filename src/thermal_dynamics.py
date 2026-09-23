"""Thermal components for the conserved-inventory dynamic integration.

[J] Protocol registered 21 Sep 2026 before execution: algebraic water-mass
closure <= 1e-8 relative + 1e-9 kg/s; Poppe air/liquid energy closure <= 1e-5
relative + 1e-6 kW. Constant-flux node energy closure <= 1e-10 relative +
1e-7 kJ. Fill-characteristic closure <= 1e-6 relative + 1e-8 (registered
before its new fault/convergence tests). Rejected inputs never produce an advanced state. These are numerical
checks, not field-accuracy thresholds. At most 20 tower mass iterations.

[E] Fluid properties are an explicitly supplied constant-cp approximation:
h = cp*T, referenced to 0 degC. Stream mass is kg SOLUTION, not kg solvent.
The inventory integrator must provide solution mass including solutes before
these components are connected. Evaporation leaves the liquid as pure water.
No phase-change latent heat is charged twice: a tower's total liquid enthalpy
loss already equals its moist-air enthalpy gain, including transferred mass.

[V] Reuses tower.solve_outlet_temperature and controller.chiller_power_biquad.
The former integrates from the cold end: m_w is cold liquid flow, and
info['m_w_top'] is hot liquid flow. This adapter solves that mass boundary.
The canonical Poppe cp remains CPW; saline/glycol cp corrections, dynamic fill
holdup, natural draft/off-fan behaviour and two-phase loops are not assessed.
The HX is a quasi-steady epsilon relation from system specification section 5;
epsilon and actual fluid properties require site calibration/qualification.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Iterable

import controller
import psychro
import tower


class ThermalDomainError(ValueError):
    """The requested calculation lacks a supported physical/numerical domain."""


def _finite(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ThermalDomainError(f'{name}: finite numeric value required')
    return float(value)


def _positive(value, name):
    value = _finite(value, name)
    if value <= 0:
        raise ThermalDomainError(f'{name}: must be positive')
    return value


def _close(residual, scale, atol, rtol):
    return abs(residual) <= atol + rtol * abs(scale)


@dataclass(frozen=True)
class ConstantCpFluid:
    name: str
    cp_kj_kg_solution_k: float
    min_temperature_c: float
    max_temperature_c: float
    property_basis: str

    def __post_init__(self):
        _positive(self.cp_kj_kg_solution_k, 'cp')
        _finite(self.min_temperature_c, 'minimum temperature')
        _finite(self.max_temperature_c, 'maximum temperature')
        if not self.name or not self.property_basis:
            raise ThermalDomainError('Fluid name and property basis are required')
        if self.min_temperature_c >= self.max_temperature_c:
            raise ThermalDomainError('Invalid fluid temperature interval')
        if self.min_temperature_c <= -273.15:
            raise ThermalDomainError('Fluid interval reaches absolute zero')

    def enthalpy_kj_kg(self, temperature_c):
        temperature_c = _finite(temperature_c, 'temperature')
        if not self.min_temperature_c <= temperature_c <= self.max_temperature_c:
            raise ThermalDomainError('Temperature outside declared fluid-property interval')
        return _finite(self.cp_kj_kg_solution_k * temperature_c, 'specific enthalpy')


@dataclass(frozen=True)
class EnergyNode:
    circuit_id: str
    node_id: str
    solution_mass_kg: float
    enthalpy_kj: float
    fluid: ConstantCpFluid

    @property
    def temperature_c(self):
        mass = _positive(self.solution_mass_kg, 'node solution mass')
        capacity = _positive(mass * self.fluid.cp_kj_kg_solution_k, 'node thermal capacity')
        value = _finite(self.enthalpy_kj, 'node enthalpy') / capacity
        self.fluid.enthalpy_kj_kg(value)
        return value


@dataclass(frozen=True)
class EnthalpyStream:
    """Signed constant mass/enthalpy flow into a node; negative mass is outflow.

    Enthalpy includes the stream's actual phase. This also permits explicitly
    specified solid/hydration/reagent streams; their properties are not guessed.
    """
    name: str
    mass_kg_s: float
    specific_enthalpy_kj_kg: float


@dataclass(frozen=True)
class EnergyStep:
    state: EnergyNode
    external_mass_kg: float
    stream_energy_kj: float
    heat_energy_kj: float
    energy_residual_kj: float


def advance_energy(node: EnergyNode, streams: Iterable[EnthalpyStream],
                   net_heat_kw: float, dt_s: float) -> EnergyStep:
    """Exact extensive update for supplied CONSTANT fluxes, not an ODE solver.

    Caller reevaluates temperature-dependent fluxes in its integration stages.
    No implicit well-mixed outlet assumption or automatic mass makeup occurs.
    """
    node.temperature_c
    dt_s = _positive(dt_s, 'duration')
    net_heat_kw = _finite(net_heat_kw, 'net heat')
    streams = tuple(streams)
    if any(not s.name for s in streams) or len({s.name for s in streams}) != len(streams):
        raise ThermalDomainError('Each stream needs a unique nonempty name')
    mass_rate = math.fsum(_finite(s.mass_kg_s, s.name) for s in streams)
    energy_rate = math.fsum(_finite(s.mass_kg_s, s.name) *
                           _finite(s.specific_enthalpy_kj_kg, s.name) for s in streams)
    delta_mass, stream_energy, heat_energy = mass_rate*dt_s, energy_rate*dt_s, net_heat_kw*dt_s
    final_mass = node.solution_mass_kg + delta_mass
    final_h = math.fsum((node.enthalpy_kj, stream_energy, heat_energy))
    final = EnergyNode(node.circuit_id, node.node_id, final_mass, final_h, node.fluid)
    final.temperature_c  # rejects depletion and excursions; never clips them
    residual = (final_h-node.enthalpy_kj) - math.fsum((stream_energy, heat_energy))
    if not _close(residual, max(abs(final_h), abs(node.enthalpy_kj)), 1e-7, 1e-10):
        raise ThermalDomainError('Node enthalpy closure failed')
    return EnergyStep(final, delta_mass, stream_energy, heat_energy, residual)


@dataclass(frozen=True)
class HeatExchangerPass:
    heat_secondary_to_primary_kw: float
    primary_out_c: float
    secondary_out_c: float
    energy_residual_kw: float


def heat_exchanger_pass(primary_in_c, secondary_in_c, primary_flow_kg_s,
                        secondary_flow_kg_s, primary_fluid: ConstantCpFluid,
                        secondary_fluid: ConstantCpFluid, effectiveness):
    """Two isolated fluid streams: heat transfer, no ion or liquid crossover."""
    primary_fluid.enthalpy_kj_kg(primary_in_c)
    secondary_fluid.enthalpy_kj_kg(secondary_in_c)
    cp = _positive(_positive(primary_flow_kg_s, 'primary flow') * primary_fluid.cp_kj_kg_solution_k, 'primary capacity rate')
    cs = _positive(_positive(secondary_flow_kg_s, 'secondary flow') * secondary_fluid.cp_kj_kg_solution_k, 'secondary capacity rate')
    effectiveness = _finite(effectiveness, 'effectiveness')
    if not 0 <= effectiveness <= 1:
        raise ThermalDomainError('Effectiveness must be between zero and one')
    q = _finite(effectiveness * min(cp, cs) * (secondary_in_c-primary_in_c), 'HX heat transfer')
    tp, ts = primary_in_c+q/cp, secondary_in_c-q/cs
    primary_fluid.enthalpy_kj_kg(tp)
    secondary_fluid.enthalpy_kj_kg(ts)
    residual = cp*(tp-primary_in_c)+cs*(ts-secondary_in_c)
    if not _close(residual, q, 1e-7, 1e-10):
        raise ThermalDomainError('Heat exchanger energy closure failed')
    return HeatExchangerPass(q, tp, ts, residual)


@dataclass(frozen=True)
class ChillerPass:
    evaporator_kw: float
    electricity_kw: float
    condenser_kw: float
    cop: float | None
    machine_basis: str


def chiller_pass(evaporator_kw, condenser_in_c, chilled_out_c, nominal_kw,
                 *, enabled: bool):
    """Canonical fitted machine, explicit off mode; no low-load cycling model."""
    evaporator_kw = _finite(evaporator_kw, 'evaporator heat')
    _positive(nominal_kw, 'installed nominal capacity')
    _finite(condenser_in_c, 'condenser inlet')
    _finite(chilled_out_c, 'chilled outlet')
    if type(enabled) is not bool:
        raise ThermalDomainError('Chiller enabled must be an explicit Boolean')
    if not enabled:
        if evaporator_kw != 0:
            raise ThermalDomainError('Disabled chiller cannot supply cooling')
        return ChillerPass(0., 0., 0., None, controller.CHILLER_MACHINE)
    try:
        power, cop = controller.chiller_power_biquad(
            evaporator_kw, condenser_in_c, chilled_out_c,
            Q_ref_kw=nominal_kw, strict_domain=True)
    except (ValueError, TypeError) as exc:
        raise ThermalDomainError(str(exc)) from exc
    return ChillerPass(evaporator_kw, power, evaporator_kw+power, cop,
                       controller.CHILLER_MACHINE)


@dataclass(frozen=True)
class TowerPass:
    cold_out_c: float
    hot_liquid_kg_s: float
    cold_liquid_kg_s: float
    evaporation_kg_s: float
    liquid_enthalpy_loss_kw: float
    air_enthalpy_gain_kw: float
    mass_residual_kg_s: float
    energy_residual_kw: float
    mass_iterations: int
    fogged: bool
    qualification: str = 'Canonical constant-water-cp Poppe; not field-qualified'


def tower_pass(hot_in_c, dry_bulb_c, relative_humidity, pressure_pa,
               hot_liquid_kg_s, dry_air_kg_s, fill_c, fill_n, water_activity):
    """Prescribe HOT flow and reconcile the core's COLD-flow argument.

    Fixed-point failure or an unphysical mass balance rejects the component.
    The returned air enthalpy gain is a whole control-volume flux, including
    evaporated water. Do not add E*h_fg to it. Liquid enthalpies use tower.CPW.
    """
    hot_in_c = _finite(hot_in_c, 'hot inlet')
    dry_bulb_c = _finite(dry_bulb_c, 'dry bulb')
    if min(hot_in_c, dry_bulb_c) <= -273.15:
        raise ThermalDomainError('Temperature at or below absolute zero')
    rh = _finite(relative_humidity, 'relative humidity')
    pressure_pa = _positive(pressure_pa, 'absolute pressure')
    hot_flow = _positive(hot_liquid_kg_s, 'hot liquid flow')
    air_flow = _positive(dry_air_kg_s, 'dry-air flow')
    fill_c = _positive(fill_c, 'fill c')
    fill_n = _finite(fill_n, 'fill n')
    aw = _finite(water_activity, 'water activity')
    if not 0 <= rh <= 1 or not 0 < aw <= 1:
        raise ThermalDomainError('Invalid humidity or water activity')
    cold_flow = hot_flow
    for iteration in range(1, 21):
        cold_t, info = tower.solve_outlet_temperature(
            hot_in_c, dry_bulb_c, rh, cold_flow, air_flow, fill_c, fill_n,
            aw=aw, p=pressure_pa, conservative_energy=True)
        if info is None or not math.isfinite(cold_t):
            raise ThermalDomainError('Canonical tower has no converged cooling solution')
        evap = _finite(info['m_evap'], 'tower evaporation')
        if not 0 <= evap < hot_flow:
            raise ThermalDomainError('Evaporation outside supported wet-tower mass domain')
        if not _close(info['Me']-info['Me_fill'], info['Me_fill'], 1e-8, 1e-6):
            raise ThermalDomainError('Tower fill-characteristic closure failed')
        if not _close(info['m_w_top']-cold_flow-evap, hot_flow, 1e-9, 1e-8):
            raise ThermalDomainError('Tower internal water-mass closure failed')
        mass_residual = info['m_w_top']-hot_flow
        if _close(mass_residual, hot_flow, 1e-9, 1e-8):
            break
        cold_flow = hot_flow-evap
    else:
        raise ThermalDomainError('Tower hot/cold mass iteration did not converge')
    humidity = float(psychro.humidity_ratio_from_rh(dry_bulb_c, rh, pressure_pa))
    air_gain = air_flow*(info['h_a_out']-psychro.h_scalar(dry_bulb_c, humidity))
    liquid_loss = tower.CPW*(hot_flow*hot_in_c-cold_flow*cold_t)
    energy_residual = liquid_loss-air_gain
    if not _close(energy_residual, max(abs(air_gain), abs(liquid_loss)), 1e-6, 1e-5):
        raise ThermalDomainError(f'Poppe energy closure failed: {energy_residual} kW')
    return TowerPass(cold_t, hot_flow, cold_flow, evap, liquid_loss, air_gain,
                     hot_flow-cold_flow-evap, energy_residual, iteration, info['fogged'])
