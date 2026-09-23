"""Synthetic cases; criteria registered before execution in bridge scope."""
from dataclasses import FrozenInstanceError, replace
import json
import math
import pytest

from thermal_dynamics import ConstantCpFluid
from solution_mass_bridge import (
    ReferenceIdentity, SolutionMassRow, BridgeInputError, admit_solution_mass,
    constant_cp_property_id, WATER_ATOL_KG, WATER_RTOL,
    TEMPERATURE_ATOL_K, PRESSURE_ATOL_PA,
)


def fluid():
    return ConstantCpFluid("synthetic aqueous fluid", 4., 0., 100.,
                           "explicit test fixture; not site-qualified")


def identity():
    return ReferenceIdentity("CW", "state-0042", "simulation1/solution1/step0",
                             30., 101325., "a"*64, "b"*64,
                             constant_cp_property_id(fluid()))


def row():
    # Synthetic same-row property fixture: total solution mass = 1.2 kg.
    return SolutionMassRow(identity(), 1., 1.02, 1.2/1.02, True)


def admitted():
    result = admit_solution_mass(row(), identity(), 1., fluid())
    assert result.status == "OK", result.reasons
    return result.bridge


def test_registered_criteria_are_unchanged():
    assert (WATER_ATOL_KG, WATER_RTOL) == (1e-9, 1e-12)
    assert TEMPERATURE_ATOL_K == 1e-8 and PRESSURE_ATOL_PA == 1e-3


def test_same_row_density_times_volume_defines_mass_and_fraction():
    bridge = admitted()
    assert bridge.solution_mass_kg == pytest.approx(1.2, rel=1e-12, abs=1e-12)
    assert bridge.water_fraction == pytest.approx(1./1.2, rel=1e-12, abs=1e-12)
    assert bridge.reference_solvent_kg == bridge.expected_solvent_kg == 1.
    assert bridge.solvent_residual_kg == 0.
    assert bridge.fluid == fluid()
    result = admit_solution_mass(row(), identity(), 1., fluid())
    json.dumps(result.as_dict(), allow_nan=False)


@pytest.mark.parametrize("flow", [0., 1., -1., 123.4, -123.4, 1e-9])
def test_signed_flow_conversion_is_reciprocal(flow):
    bridge = admitted()
    solution = bridge.solution_flow_from_solvent(flow)
    assert solution == pytest.approx(flow*1.2, rel=1e-12, abs=1e-12)
    assert bridge.solvent_flow_from_solution(solution) == pytest.approx(flow, rel=1e-12, abs=1e-12)


def test_missing_reference_or_expected_identity_is_unknown():
    for reference, expected in ((None, identity()), (row(), None)):
        result = admit_solution_mass(reference, expected, 1., fluid())
        assert result.status == "UNKNOWN" and result.bridge is None


@pytest.mark.parametrize("field", ["circuit_id", "state_id", "reference_row_id", "T_c", "P_pa",
                                    "database_sha256", "composition_sha256", "property_model_id"])
def test_every_missing_identity_field_is_unknown(field):
    missing = replace(identity(), **{field: None})
    result = admit_solution_mass(replace(row(), identity=missing), identity(), 1., fluid())
    assert result.status == "UNKNOWN" and result.bridge is None
    assert f"reference.{field}" in result.reasons


@pytest.mark.parametrize("field", ["solvent_kg", "density_kg_l", "volume_l", "aqueous_only"])
def test_missing_reference_mass_fields_are_unknown(field):
    result = admit_solution_mass(replace(row(), **{field: None}), identity(), 1., fluid())
    assert result.status == "UNKNOWN" and result.bridge is None and field in result.reasons


def test_missing_expected_inventory_or_property_model_is_unknown():
    for expected_mass, properties in ((None, fluid()), (1., None)):
        result = admit_solution_mass(row(), identity(), expected_mass, properties)
        assert result.status == "UNKNOWN" and result.bridge is None


@pytest.mark.parametrize("field,value", [
    ("circuit_id", "TCS"), ("state_id", "state-0041"),
    ("reference_row_id", "simulation2/solution1/step0"),
    ("database_sha256", "c"*64), ("composition_sha256", "d"*64),
    ("property_model_id", "e"*64), ("T_c", 30.000001), ("P_pa", 101326.),
])
def test_every_identity_mismatch_rejects_without_cross_row_join(field, value):
    expected = replace(identity(), **{field: value})
    result = admit_solution_mass(row(), expected, 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None
    assert any("identity mismatch" in reason for reason in result.reasons)


def test_property_fingerprint_cannot_be_reused_with_different_cp():
    result = admit_solution_mass(row(), identity(), 1., replace(fluid(), cp_kj_kg_solution_k=3.))
    assert result.status == "REJECTED" and result.bridge is None
    assert "supplied fluid differs from declared property identity" in result.reasons


@pytest.mark.parametrize("field,value", [
    ("name", "different fluid"), ("property_basis", "different source"),
    ("min_temperature_c", -10.), ("max_temperature_c", 90.),
])
def test_property_fingerprint_includes_name_source_and_validity_interval(field, value):
    assert constant_cp_property_id(replace(fluid(), **{field: value})) != constant_cp_property_id(fluid())


def test_matched_reference_outside_declared_property_interval_is_rejected():
    ident = replace(identity(), T_c=101.)
    result = admit_solution_mass(replace(row(), identity=ident), ident, 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None
    assert any("out-of-range" in reason for reason in result.reasons)


def test_solution_cannot_weigh_less_than_its_solvent_and_is_not_clipped():
    reference = replace(row(), density_kg_l=.9, volume_l=1.)
    result = admit_solution_mass(reference, identity(), 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None
    assert reference.density_kg_l == .9 and reference.volume_l == 1.


def test_pure_water_fraction_one_is_allowed_when_explicitly_declared():
    result = admit_solution_mass(replace(row(), density_kg_l=1., volume_l=1.), identity(), 1., fluid())
    assert result.status == "OK" and result.bridge.water_fraction == 1.


@pytest.mark.parametrize("changed_mass", [.99, 1.01])
def test_chemical_water_change_cannot_overwrite_the_expected_inventory(changed_mass):
    reference = replace(row(), solvent_kg=changed_mass)
    result = admit_solution_mass(reference, identity(), 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None
    assert any("reconcile reaction water" in reason for reason in result.reasons)
    assert reference.solvent_kg == changed_mass


def test_subtolerance_residual_is_recorded_without_normalizing_either_mass():
    reference = replace(row(), solvent_kg=1.+1e-10)
    result = admit_solution_mass(reference, identity(), 1., fluid())
    assert result.status == "OK"
    assert result.bridge.reference_solvent_kg == reference.solvent_kg
    assert result.bridge.expected_solvent_kg == 1.
    assert result.bridge.solvent_residual_kg == reference.solvent_kg-1.


def test_explicit_separated_phase_content_is_rejected():
    result = admit_solution_mass(replace(row(), aqueous_only=False), identity(), 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None
    assert any("separated phases" in reason for reason in result.reasons)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, 0., -1., True])
def test_invalid_density_does_not_enter_the_reference_record(bad):
    with pytest.raises(BridgeInputError):
        replace(row(), density_kg_l=bad)


@pytest.mark.parametrize("bad", [math.nan, math.inf, None, True])
def test_nonfinite_or_missing_conversion_flow_is_rejected(bad):
    bridge = admitted()
    with pytest.raises(BridgeInputError):
        bridge.solution_flow_from_solvent(bad)
    with pytest.raises(BridgeInputError):
        bridge.solvent_flow_from_solution(bad)


def test_solution_mass_overflow_has_no_admitted_bridge():
    result = admit_solution_mass(replace(row(), density_kg_l=1e308, volume_l=1e308), identity(), 1., fluid())
    assert result.status == "REJECTED" and result.bridge is None


def test_flow_conversion_overflow_is_rejected():
    # water fraction 1e-6; multiplying a finite input by 1e6 exceeds float64.
    result = admit_solution_mass(replace(row(), density_kg_l=1., volume_l=1e6), identity(), 1., fluid())
    assert result.status == "OK"
    with pytest.raises(BridgeInputError):
        result.bridge.solution_flow_from_solvent(1e308)


def test_reference_expected_and_admitted_records_are_immutable():
    reference, expected = row(), identity()
    result = admit_solution_mass(reference, expected, 1., fluid())
    with pytest.raises(FrozenInstanceError):
        reference.volume_l = 999.
    with pytest.raises(FrozenInstanceError):
        expected.circuit_id = "other"
    with pytest.raises(FrozenInstanceError):
        result.bridge.water_fraction = 1.
    with pytest.raises(FrozenInstanceError):
        result.status = "REJECTED"


def test_malformed_identity_hash_is_not_a_valid_provenance_record():
    with pytest.raises(BridgeInputError, match="SHA-256"):
        replace(identity(), database_sha256="phreeqc.dat")


def test_unsupported_property_type_is_rejected_without_defaulting():
    result = admit_solution_mass(row(), identity(), 1., {"cp": 4.})
    assert result.status == "REJECTED" and result.bridge is None


@pytest.mark.parametrize("change", [
    {"water_fraction": .5}, {"solution_mass_kg": 9.},
    {"solvent_residual_kg": .5}, {"expected_solvent_kg": .99},
    {"reference_solvent_kg": 1.1},
])
def test_direct_construction_cannot_bypass_mass_and_residual_invariants(change):
    with pytest.raises(BridgeInputError):
        replace(admitted(), **change)


@pytest.mark.parametrize("change", [{"state_id": None}, {"T_c": None}, {"T_c": 101.},
                                    {"P_pa": None}, {"composition_sha256": None}])
def test_direct_construction_cannot_bypass_identity_and_property_domain(change):
    with pytest.raises(BridgeInputError):
        replace(admitted(), identity=replace(identity(), **change))
