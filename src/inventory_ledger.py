"""Conservative imposed-flux ledger; no chemistry, kinetics or live I/O.

See docs/inventory_ledger_scope.md for the registered numerical criteria and
scope. One state belongs to one chemically isolated circuit. Missing values
remain unknown; only an explicit complete zero vector means zero material.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numbers
from types import MappingProxyType
from typing import Mapping

SCHEMA_VERSION = "analytical-components-18-v1"
COMPONENTS = ("Ca", "Mg", "Na", "K", "Cl", "S(VI)", "C(inorganic)",
              "P(V)", "Si", "N(-III)", "N(III)", "N(V)", "Cu", "Fe",
              "Al", "Zn", "Ba", "S(-II)")
ELEMENT_OF = MappingProxyType({c: {"S(VI)": "S", "S(-II)": "S",
    "C(inorganic)": "C", "P(V)": "P", "N(-III)": "N", "N(III)": "N",
    "N(V)": "N"}.get(c, c) for c in COMPONENTS})
ELEMENTS = tuple(dict.fromkeys(ELEMENT_OF.values()))
WATER_ATOL_KG = 1e-9
ELEMENT_ATOL_MOL = 1e-10
BALANCE_RTOL = 1e-12


def explicit_zero_components() -> dict[str, float]:
    """Explicit caller declaration of a complete zero inventory or flux."""
    return {c: 0.0 for c in COMPONENTS}


def _number(value, name, *, signed=False, unknown=True):
    if value is None and unknown:
        return None
    if (isinstance(value, bool) or not isinstance(value, numbers.Real)
            or not math.isfinite(value)):
        raise ValueError(f"{name} must be a finite real number")
    if not signed and value < 0:
        raise ValueError(f"{name} cannot be negative")
    return float(value)


def _vector(values, name, *, signed=False):
    if not isinstance(values, Mapping):
        raise ValueError(f"{name} must be a component mapping")
    extra = set(values) - set(COMPONENTS)
    if extra:
        raise ValueError(f"unsupported {SCHEMA_VERSION} components: {sorted(extra)}")
    return MappingProxyType({c: _number(values.get(c), f"{name}.{c}", signed=signed)
                             for c in COMPONENTS})


def _name(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


@dataclass(frozen=True)
class SolidInventory:
    components_mol: Mapping[str, float | None]
    bound_water_kg: float | None

    def __post_init__(self):
        object.__setattr__(self, "components_mol", _vector(self.components_mol, "solid"))
        object.__setattr__(self, "bound_water_kg", _number(self.bound_water_kg, "bound_water_kg"))


@dataclass(frozen=True)
class Inventory:
    circuit_id: str
    solvent_kg: float | None
    dissolved_mol: Mapping[str, float | None]
    suspended: SolidInventory
    deposits: Mapping[str, SolidInventory]

    def __post_init__(self):
        _name(self.circuit_id, "circuit_id")
        mass = _number(self.solvent_kg, "solvent_kg")
        if mass == 0:
            raise ValueError("solvent_kg must be positive or unknown")
        object.__setattr__(self, "solvent_kg", mass)
        object.__setattr__(self, "dissolved_mol", _vector(self.dissolved_mol, "dissolved"))
        if not isinstance(self.suspended, SolidInventory) or not isinstance(self.deposits, Mapping):
            raise ValueError("explicit suspended and deposited inventory declarations are required")
        copied = {}
        for interface, solid in self.deposits.items():
            _name(interface, "interface")
            if not isinstance(solid, SolidInventory):
                raise ValueError("every deposit must be a SolidInventory")
            copied[interface] = solid
        object.__setattr__(self, "deposits", MappingProxyType(copied))

    def as_dict(self):
        return {"circuit_id": self.circuit_id, "solvent_kg": self.solvent_kg,
                "dissolved_mol": dict(self.dissolved_mol),
                "suspended": _solid_dict(self.suspended),
                "deposits": {k: _solid_dict(v) for k, v in self.deposits.items()}}


def _solid_dict(solid):
    return {"components_mol": dict(solid.components_mol), "bound_water_kg": solid.bound_water_kg}


@dataclass(frozen=True)
class StreamFlux:
    name: str
    direction: str                    # "in" or "out"
    compartment: str                  # liquid / suspended / deposit:<interface>
    components_mol_s: Mapping[str, float | None]
    water_kg_s: float | None          # solvent for liquid; bound water for solids
    kind: str                        # explicit source/endpoint classification
    acid_equivalents_eq_s: float | None = 0.0  # input diagnostic, not pH state

    def __post_init__(self):
        for value, label in ((self.name, "name"), (self.compartment, "compartment"), (self.kind, "kind")):
            _name(value, label)
        if self.direction not in ("in", "out"):
            raise ValueError("stream direction must be in or out")
        object.__setattr__(self, "components_mol_s", _vector(self.components_mol_s, self.name))
        object.__setattr__(self, "water_kg_s", _number(self.water_kg_s, "water_kg_s"))
        object.__setattr__(self, "acid_equivalents_eq_s",
                           _number(self.acid_equivalents_eq_s, "acid_equivalents_eq_s"))


@dataclass(frozen=True)
class PhaseTransfer:
    name: str
    component_rates: Mapping[str, Mapping[str, float | None]]
    water_rates: Mapping[str, float | None]

    def __post_init__(self):
        _name(self.name, "transfer name")
        if not isinstance(self.component_rates, Mapping) or not isinstance(self.water_rates, Mapping):
            raise ValueError("phase transfer requires explicit compartment mappings")
        if not self.component_rates or set(self.component_rates) != set(self.water_rates):
            raise ValueError("participating compartments need both water and component declarations")
        components, water = {}, {}
        for compartment, vector in self.component_rates.items():
            _name(compartment, "compartment")
            components[compartment] = _vector(vector, self.name, signed=True)
            water[compartment] = _number(self.water_rates[compartment], self.name, signed=True)
        object.__setattr__(self, "component_rates", MappingProxyType(components))
        object.__setattr__(self, "water_rates", MappingProxyType(water))


@dataclass(frozen=True)
class StepForcing:
    streams: tuple[StreamFlux, ...]
    transfers: tuple[PhaseTransfer, ...]
    evaporation_kg_s: float | None

    def __post_init__(self):
        streams, transfers = tuple(self.streams), tuple(self.transfers)
        if not all(isinstance(s, StreamFlux) for s in streams):
            raise ValueError("streams must contain StreamFlux objects")
        if not all(isinstance(t, PhaseTransfer) for t in transfers):
            raise ValueError("transfers must contain PhaseTransfer objects")
        names = [s.name for s in streams] + [t.name for t in transfers]
        if len(names) != len(set(names)):
            raise ValueError("stream and transfer names must be unique within a step")
        object.__setattr__(self, "streams", streams)
        object.__setattr__(self, "transfers", transfers)
        object.__setattr__(self, "evaporation_kg_s", _number(self.evaporation_kg_s, "evaporation_kg_s"))


@dataclass(frozen=True)
class StepResult:
    status: str
    state: Inventory
    ledger: Mapping | None
    reasons: tuple[str, ...]

    @property
    def advanced(self):
        return self.status == "OK"

    def as_dict(self):
        return {"status": self.status, "state": self.state.as_dict(),
                "ledger": _plain(self.ledger), "reasons": list(self.reasons)}


def _plain(value):
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    return value


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def elemental_totals(components):
    """Project known analytical component moles onto tracked elements."""
    vec = _vector(components, "element projection", signed=True)
    if any(value is None for value in vec.values()):
        return MappingProxyType({e: None for e in ELEMENTS})
    return MappingProxyType({e: math.fsum(vec[c] for c in COMPONENTS if ELEMENT_OF[c] == e)
                             for e in ELEMENTS})


def _compartments(state):
    out = {"liquid": (state.solvent_kg, state.dissolved_mol),
           "suspended": (state.suspended.bound_water_kg, state.suspended.components_mol)}
    out.update({f"deposit:{name}": (v.bound_water_kg, v.components_mol)
                for name, v in state.deposits.items()})
    return out


def _total_components(compartments):
    return {c: math.fsum(vec[c] for _, vec in compartments.values()) for c in COMPONENTS}


def _within(residual, absolute, *scale):
    return abs(residual) <= absolute + BALANCE_RTOL * max((abs(s) for s in scale), default=0.)


def advance_inventory(state: Inventory, forcing: StepForcing, dt_s: float) -> StepResult:
    """Integrate declared constant fluxes exactly, or leave the input unchanged.

    Structural/nonfinite misuse raises ValueError. Missing values yield
    UNKNOWN; unbalanced transfers, depleted inventories or failed numerical
    closure yield REJECTED. There is no clipping of a negative remainder.
    """
    if not isinstance(state, Inventory) or not isinstance(forcing, StepForcing):
        raise ValueError("Inventory and StepForcing objects are required")
    dt = _number(dt_s, "dt_s", unknown=False)
    if dt <= 0:
        raise ValueError("dt_s must be positive")
    compartments = _compartments(state)
    unknown = []
    for name, (water, components) in compartments.items():
        if water is None:
            unknown.append(f"{name}.water")
        unknown.extend(f"{name}.{c}" for c, v in components.items() if v is None)
    if forcing.evaporation_kg_s is None:
        unknown.append("evaporation_kg_s")
    for stream in forcing.streams:
        if stream.compartment not in compartments:
            return StepResult("REJECTED", state, None, (f"unknown compartment {stream.compartment}",))
        if stream.water_kg_s is None or stream.acid_equivalents_eq_s is None:
            unknown.append(f"stream.{stream.name}.water_or_acid_capacity")
        unknown.extend(f"stream.{stream.name}.{c}" for c, v in stream.components_mol_s.items() if v is None)
    for transfer in forcing.transfers:
        for name, vec in transfer.component_rates.items():
            if name not in compartments:
                return StepResult("REJECTED", state, None, (f"unknown compartment {name}",))
            if transfer.water_rates[name] is None:
                unknown.append(f"transfer.{transfer.name}.{name}.water")
            unknown.extend(f"transfer.{transfer.name}.{name}.{c}" for c, v in vec.items() if v is None)
    if unknown:
        return StepResult("UNKNOWN", state, None, tuple(unknown))
    try:
        return _advance_known(state, forcing, dt, compartments)
    except (OverflowError, ArithmeticError) as exc:
        return StepResult("REJECTED", state, None, (f"nonfinite integrated arithmetic: {type(exc).__name__}",))


def _advance_known(state, forcing, dt, compartments):
    changes = {name: {"water": [], **{c: [] for c in COMPONENTS}} for name in compartments}
    external = {c: [] for c in COMPONENTS}
    internal = {c: [] for c in COMPONENTS}
    external_water, internal_water, streams, phases = [], [], [], []
    gross = {e: [] for e in ELEMENTS}
    gross_water = []
    for stream in forcing.streams:
        sign = 1. if stream.direction == "in" else -1.
        amount = {c: stream.components_mol_s[c] * dt for c in COMPONENTS}
        water = stream.water_kg_s * dt
        acid = stream.acid_equivalents_eq_s * dt
        if not all(math.isfinite(v) for v in (*amount.values(), water, acid)):
            raise ArithmeticError("stream integration overflow")
        changes[stream.compartment]["water"].append(sign * water)
        external_water.append(sign * water)
        gross_water.append(water)
        for c, value in amount.items():
            changes[stream.compartment][c].append(sign * value)
            external[c].append(sign * value)
            gross[ELEMENT_OF[c]].append(value)
        streams.append(dict(name=stream.name, kind=stream.kind, direction=stream.direction,
                            compartment=stream.compartment, components_mol=amount,
                            water_kg=water, acid_equivalents_eq=acid))
    evap = forcing.evaporation_kg_s * dt
    if not math.isfinite(evap):
        raise ArithmeticError("evaporation integration overflow")
    changes["liquid"]["water"].append(-evap)
    external_water.append(-evap)
    gross_water.append(evap)
    for transfer in forcing.transfers:
        amounts = {name: {c: rate * dt for c, rate in vec.items()}
                   for name, vec in transfer.component_rates.items()}
        waters = {name: rate * dt for name, rate in transfer.water_rates.items()}
        values = [v for vec in amounts.values() for v in vec.values()] + list(waters.values())
        if not all(math.isfinite(v) for v in values):
            raise ArithmeticError("phase integration overflow")
        component_sum = {c: math.fsum(vec[c] for vec in amounts.values()) for c in COMPONENTS}
        element_sum = elemental_totals(component_sum)
        if not _within(math.fsum(waters.values()), WATER_ATOL_KG,
                       math.fsum(abs(v) for v in waters.values())):
            return StepResult("REJECTED", state, None, (f"transfer {transfer.name} does not conserve water",))
        for e, residual in element_sum.items():
            magnitude = math.fsum(abs(vec[c]) for vec in amounts.values()
                                  for c in COMPONENTS if ELEMENT_OF[c] == e)
            if not _within(residual, ELEMENT_ATOL_MOL, magnitude):
                return StepResult("REJECTED", state, None, (f"transfer {transfer.name} does not conserve {e}",))
        for name, vec in amounts.items():
            changes[name]["water"].append(waters[name])
            internal_water.append(waters[name])
            gross_water.append(abs(waters[name]))
            for c, value in vec.items():
                changes[name][c].append(value)
                internal[c].append(value)
                gross[ELEMENT_OF[c]].append(abs(value))
        phases.append(dict(name=transfer.name, components_mol=amounts, water_kg=waters))
    updated = {}
    for name, (water, vec) in compartments.items():
        next_water = math.fsum([water, *changes[name]["water"]])
        next_vector = {c: math.fsum([vec[c], *changes[name][c]]) for c in COMPONENTS}
        if not all(math.isfinite(v) for v in (next_water, *next_vector.values())):
            raise ArithmeticError("inventory integration overflow")
        if next_water < 0 or (name == "liquid" and next_water <= 0):
            return StepResult("REJECTED", state, None, (f"{name} water inventory would be depleted",))
        depleted = [c for c, v in next_vector.items() if v < 0]
        if depleted:
            return StepResult("REJECTED", state, None, (f"{name} components would be negative: {','.join(depleted)}",))
        updated[name] = (next_water, next_vector)
    start_c, end_c = _total_components(compartments), _total_components(updated)
    external_c = {c: math.fsum(v) for c, v in external.items()}
    internal_c = {c: math.fsum(v) for c, v in internal.items()}
    start_e, end_e, ext_e = map(elemental_totals, (start_c, end_c, external_c))
    element_residual = {e: math.fsum([end_e[e], -start_e[e], -ext_e[e]]) for e in ELEMENTS}
    start_water = math.fsum(water for water, _ in compartments.values())
    end_water = math.fsum(water for water, _ in updated.values())
    water_net = math.fsum(external_water)
    water_residual = math.fsum([end_water, -start_water, -water_net])
    if not _within(water_residual, WATER_ATOL_KG, start_water, end_water, math.fsum(gross_water)):
        return StepResult("REJECTED", state, None, ("total water numerical closure failed",))
    if any(not _within(element_residual[e], ELEMENT_ATOL_MOL, start_e[e], end_e[e],
                       math.fsum(gross[e])) for e in ELEMENTS):
        return StepResult("REJECTED", state, None, ("element numerical closure failed",))
    new_state = Inventory(state.circuit_id, updated["liquid"][0], updated["liquid"][1],
        SolidInventory(updated["suspended"][1], updated["suspended"][0]),
        {name: SolidInventory(updated[f"deposit:{name}"][1], updated[f"deposit:{name}"][0])
         for name in state.deposits})
    ledger = dict(schema_version=SCHEMA_VERSION, circuit_id=state.circuit_id, dt_s=dt,
        streams=streams, phase_transfers=phases, evaporation_kg=evap,
        start_total_water_kg=start_water, end_total_water_kg=end_water,
        external_net_water_kg=water_net, internal_net_water_kg=math.fsum(internal_water),
        water_residual_kg=water_residual, start_components_mol=start_c,
        end_components_mol=end_c, external_net_components_mol=external_c,
        internal_net_components_mol=internal_c, elemental_residual_mol=element_residual,
        component_residual_mol={c: math.fsum([end_c[c], -start_c[c], -external_c[c], -internal_c[c]])
                                for c in COMPONENTS},
        qualification="IMPOSED_FLUX_CONSERVATION_ONLY", live_write_enabled=False)
    return StepResult("OK", new_state, _freeze(ledger), ())


def solution_dose_stream(name, reagent_mol_s, components_per_mol,
                         active_molar_mass_kg_mol, active_mass_fraction,
                         acid_equivalents_per_mol):
    """Declare reagent components and carrier water once; all properties supplied.

    Carrier kg/s = reagent mol/s * active kg/mol * (1/x_active - 1).
    No reagent identity, purity, molar mass or chemical enthalpy is inferred.
    """
    rate = _number(reagent_mol_s, "reagent_mol_s")
    mass = _number(active_molar_mass_kg_mol, "active_molar_mass_kg_mol")
    fraction = _number(active_mass_fraction, "active_mass_fraction")
    equivalents = _number(acid_equivalents_per_mol, "acid_equivalents_per_mol")
    if mass == 0 or (fraction is not None and not 0 < fraction <= 1):
        raise ValueError("molar mass must be positive and active mass fraction in (0, 1]")
    composition = _vector(components_per_mol, "reagent composition")
    components = {c: None if rate is None or n is None else rate * n
                  for c, n in composition.items()}
    carrier = None if any(v is None for v in (rate, mass, fraction)) else rate * mass * (1/fraction-1)
    acid = None if rate is None or equivalents is None else rate * equivalents
    return StreamFlux(name, "in", "liquid", components, carrier, "dose", acid)
