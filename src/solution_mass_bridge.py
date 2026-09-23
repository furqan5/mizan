"""Admit a same-row PHREEQC solution mass into the explicit thermal basis.

No species/atomic-mass reconstruction, inferred heat capacity, reaction-water
correction, phase-mass subtraction, kinetic model or live I/O is performed.
Registered scope/tolerances: docs/solution_mass_bridge_scope.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from numbers import Real
import re

from thermal_dynamics import ConstantCpFluid

WATER_ATOL_KG = 1e-9
WATER_RTOL = 1e-12
TEMPERATURE_ATOL_K = 1e-8
PRESSURE_ATOL_PA = 1e-3


class BridgeInputError(ValueError):
    """Malformed, unsupported or nonfinite mass/property input."""


def _number(value, name, *, positive=False, optional=True):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise BridgeInputError(f"{name} must be a finite real number")
    if positive and value <= 0:
        raise BridgeInputError(f"{name} must be strictly positive")
    return float(value)


def _text(value, name, *, digest=False):
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BridgeInputError(f"{name} must be a nonempty string or None")
    if digest:
        if re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
            raise BridgeInputError(f"{name} must be a SHA-256 digest")
        return value.lower()
    return value


@dataclass(frozen=True)
class ReferenceIdentity:
    circuit_id: str | None
    state_id: str | None
    reference_row_id: str | None
    T_c: float | None
    P_pa: float | None
    database_sha256: str | None
    composition_sha256: str | None
    property_model_id: str | None

    def __post_init__(self):
        for name in ("circuit_id", "state_id", "reference_row_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name in ("database_sha256", "composition_sha256", "property_model_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name, digest=True))
        temperature = _number(self.T_c, "T_c")
        if temperature is not None and temperature <= -273.15:
            raise BridgeInputError("temperature must exceed absolute zero")
        object.__setattr__(self, "T_c", temperature)
        object.__setattr__(self, "P_pa", _number(self.P_pa, "P_pa", positive=True))


@dataclass(frozen=True)
class SolutionMassRow:
    identity: ReferenceIdentity
    solvent_kg: float | None
    density_kg_l: float | None
    volume_l: float | None
    aqueous_only: bool | None

    def __post_init__(self):
        if not isinstance(self.identity, ReferenceIdentity):
            raise BridgeInputError("reference identity must be explicitly declared")
        for name in ("solvent_kg", "density_kg_l", "volume_l"):
            object.__setattr__(self, name, _number(getattr(self, name), name, positive=True))
        if self.aqueous_only is not None and type(self.aqueous_only) is not bool:
            raise BridgeInputError("aqueous_only must be Boolean or unknown")


def constant_cp_property_id(fluid: ConstantCpFluid) -> str:
    """Fingerprint the declared constant-cp model, including enthalpy reference."""
    if type(fluid) is not ConstantCpFluid:
        raise BridgeInputError("only an explicit ConstantCpFluid is supported")
    record = {"model": "constant-cp-solution-v1", "enthalpy_reference_c": 0.,
              "name": _text(fluid.name, "fluid.name"),
              "cp_kj_kg_solution_k": _number(fluid.cp_kj_kg_solution_k, "cp", positive=True, optional=False),
              "min_temperature_c": _number(fluid.min_temperature_c, "Tmin", optional=False),
              "max_temperature_c": _number(fluid.max_temperature_c, "Tmax", optional=False),
              "property_basis": _text(fluid.property_basis, "fluid.property_basis")}
    if record["name"] is None or record["property_basis"] is None:
        raise BridgeInputError("fluid name and property basis are required")
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SolutionMassBridge:
    identity: ReferenceIdentity
    reference_solvent_kg: float
    expected_solvent_kg: float
    solution_mass_kg: float
    water_fraction: float
    solvent_residual_kg: float
    fluid: ConstantCpFluid
    qualification: str = "DECLARED_AQUEOUS_MASS_AND_CONSTANT_CP_ONLY"

    def __post_init__(self):
        if (not isinstance(self.identity, ReferenceIdentity)
                or any(value is None for value in asdict(self.identity).values())):
            raise BridgeInputError("admitted bridge requires a complete reference identity")
        for name in ("reference_solvent_kg", "expected_solvent_kg", "solution_mass_kg", "water_fraction"):
            _number(getattr(self, name), name, positive=True, optional=False)
        _number(self.solvent_residual_kg, "solvent_residual_kg", optional=False)
        if self.water_fraction > 1:
            raise BridgeInputError("water fraction cannot exceed one")
        # These are derived outputs, not independently measured inputs. The
        # factory computes the same expressions; direct construction must
        # not introduce a second, inconsistent mass or residual definition.
        if self.water_fraction != self.reference_solvent_kg / self.solution_mass_kg:
            raise BridgeInputError("water fraction disagrees with declared solution/solvent masses")
        residual = self.reference_solvent_kg - self.expected_solvent_kg
        if self.solvent_residual_kg != residual:
            raise BridgeInputError("solvent residual disagrees with reference minus expected mass")
        if abs(residual) > WATER_ATOL_KG + WATER_RTOL * max(self.reference_solvent_kg, self.expected_solvent_kg):
            raise BridgeInputError("reaction-water mismatch exceeds the registered tolerance")
        if constant_cp_property_id(self.fluid) != self.identity.property_model_id:
            raise BridgeInputError("fluid does not match admitted property identity")
        try:
            enthalpy = self.fluid.enthalpy_kj_kg(self.identity.T_c)
        except (TypeError, ValueError) as exc:
            raise BridgeInputError("admitted temperature is outside the property domain") from exc
        if not math.isfinite(enthalpy):
            raise BridgeInputError("declared constant-cp enthalpy is nonfinite")

    def solution_flow_from_solvent(self, solvent_kg_s):
        """Signed kg solution/s from signed kg solvent/s; no phase stream added."""
        value = _number(solvent_kg_s, "solvent flow", optional=False) / self.water_fraction
        return _number(value, "converted solution flow", optional=False)

    def solvent_flow_from_solution(self, solution_kg_s):
        """Signed kg solvent/s from signed kg solution/s."""
        value = _number(solution_kg_s, "solution flow", optional=False) * self.water_fraction
        return _number(value, "converted solvent flow", optional=False)


@dataclass(frozen=True)
class BridgeResult:
    status: str
    bridge: SolutionMassBridge | None
    reasons: tuple[str, ...]

    def as_dict(self):
        return {"status": self.status,
                "bridge": asdict(self.bridge) if self.bridge is not None else None,
                "reasons": list(self.reasons)}


def admit_solution_mass(row: SolutionMassRow | None,
                        expected_identity: ReferenceIdentity | None,
                        expected_solvent_kg: float | None,
                        fluid: ConstantCpFluid | None) -> BridgeResult:
    """Require a complete matching same-row mass/property contract.

    UNKNOWN and REJECTED supply no bridge. No reference number or inventory
    is normalized, clipped, substituted or overwritten to obtain admission.
    """
    if row is None or expected_identity is None:
        return BridgeResult("UNKNOWN", None, ("reference row or expected identity missing",))
    if not isinstance(row, SolutionMassRow) or not isinstance(expected_identity, ReferenceIdentity):
        raise BridgeInputError("explicit SolutionMassRow and ReferenceIdentity required")
    expected_mass = _number(expected_solvent_kg, "expected_solvent_kg", positive=True)
    missing = []
    for prefix, identity in (("reference", row.identity), ("expected", expected_identity)):
        missing.extend(f"{prefix}.{name}" for name, value in asdict(identity).items() if value is None)
    missing.extend(name for name in ("solvent_kg", "density_kg_l", "volume_l", "aqueous_only")
                   if getattr(row, name) is None)
    if expected_mass is None:
        missing.append("expected_solvent_kg")
    if fluid is None:
        missing.append("constant_cp_property_model")
    if missing:
        return BridgeResult("UNKNOWN", None, tuple(missing))
    mismatches = []
    for name in ("circuit_id", "state_id", "reference_row_id", "database_sha256",
                 "composition_sha256", "property_model_id"):
        if getattr(row.identity, name) != getattr(expected_identity, name):
            mismatches.append(f"identity mismatch: {name}")
    if abs(row.identity.T_c - expected_identity.T_c) > TEMPERATURE_ATOL_K:
        mismatches.append("identity mismatch: temperature")
    if abs(row.identity.P_pa - expected_identity.P_pa) > PRESSURE_ATOL_PA:
        mismatches.append("identity mismatch: pressure")
    if not row.aqueous_only:
        mismatches.append("separated phases cannot be included in solution mass")
    try:
        fingerprint = constant_cp_property_id(fluid)
        if fingerprint != expected_identity.property_model_id:
            mismatches.append("supplied fluid differs from declared property identity")
        # Check BOTH the reference and the inventory state's temperature.
        for temperature in (row.identity.T_c, expected_identity.T_c):
            if not math.isfinite(fluid.enthalpy_kj_kg(temperature)):
                mismatches.append("nonfinite declared constant-cp enthalpy")
    except (TypeError, ValueError) as exc:
        mismatches.append(f"unsupported or out-of-range property model: {exc}")
    solvent_residual = row.solvent_kg - expected_mass
    if abs(solvent_residual) > WATER_ATOL_KG + WATER_RTOL * max(row.solvent_kg, expected_mass):
        mismatches.append("reference solvent changed: reconcile reaction water before coupling")
    solution_mass = row.density_kg_l * row.volume_l
    if not math.isfinite(solution_mass) or solution_mass <= 0:
        mismatches.append("nonfinite or nonpositive density-volume solution mass")
        fraction = None
    else:
        fraction = row.solvent_kg / solution_mass
        if not math.isfinite(fraction) or not 0 < fraction <= 1:
            mismatches.append("water fraction outside (0, 1]; no clipping permitted")
    if mismatches:
        return BridgeResult("REJECTED", None, tuple(mismatches))
    bridge = SolutionMassBridge(row.identity, row.solvent_kg, expected_mass,
                                solution_mass, fraction, solvent_residual, fluid)
    return BridgeResult("OK", bridge, ())
