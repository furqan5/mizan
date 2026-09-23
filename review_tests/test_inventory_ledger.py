"""Synthetic conservation fixtures registered in inventory_ledger_scope.md."""
import dataclasses
import json
import math
import pytest

from inventory_ledger import (
    COMPONENTS, ELEMENTS, WATER_ATOL_KG, ELEMENT_ATOL_MOL, BALANCE_RTOL,
    Inventory, SolidInventory, StreamFlux, PhaseTransfer, StepForcing,
    advance_inventory, explicit_zero_components, elemental_totals,
    solution_dose_stream,
)


def vec(**entries):
    result = explicit_zero_components()
    result.update(entries)
    return result


def solid(**entries):
    return SolidInventory(vec(**entries), 0.)


def state(circuit="tower", water=100., **entries):
    return Inventory(circuit, water, vec(**entries), solid(), {"wall": solid()})


def forcing(streams=(), transfers=(), evap=0.):
    return StepForcing(tuple(streams), tuple(transfers), evap)


def check_ok(result):
    assert result.status == "OK", result.reasons
    assert result.advanced
    assert abs(result.ledger["water_residual_kg"]) <= WATER_ATOL_KG
    assert all(abs(x) <= ELEMENT_ATOL_MOL for x in result.ledger["elemental_residual_mol"].values())
    assert result.ledger["live_write_enabled"] is False
    json.dumps(result.as_dict(), allow_nan=False)


def test_schema_and_registered_tolerances():
    assert len(COMPONENTS) == 18 and len(ELEMENTS) == 15
    assert WATER_ATOL_KG == 1e-9
    assert ELEMENT_ATOL_MOL == 1e-10
    assert BALANCE_RTOL == 1e-12


def test_pure_water_dilution_preserves_ions_and_halves_concentration():
    initial = state(Cl=20.)
    stream = StreamFlux("makeup", "in", "liquid", vec(), 10., "makeup")
    result = advance_inventory(initial, forcing((stream,)), 10.)
    check_ok(result)
    assert result.state.solvent_kg == 200.
    assert result.state.dissolved_mol["Cl"] == 20.
    assert result.state.dissolved_mol["Cl"]/result.state.solvent_kg == .1
    assert result.ledger["streams"][0]["water_kg"] == 100.


def test_evaporation_concentrates_without_exporting_components():
    result = advance_inventory(state(Cl=20.), forcing(evap=5.), 10.)
    check_ok(result)
    assert result.state.solvent_kg == 50.
    assert result.state.dissolved_mol["Cl"] == 20.
    assert result.ledger["evaporation_kg"] == 50.
    assert all(v == 0. for v in result.ledger["external_net_components_mol"].values())


def test_declared_outflow_keeps_each_integrated_stream_in_the_ledger():
    stream = StreamFlux("measured-blowdown", "out", "liquid", vec(Cl=.2), 1., "blowdown")
    result = advance_inventory(state(Cl=20.), forcing((stream,)), 10.)
    check_ok(result)
    assert result.state.solvent_kg == 90.
    assert result.state.dissolved_mol["Cl"] == 18.
    assert result.ledger["streams"][0]["components_mol"]["Cl"] == 2.
    assert result.ledger["external_net_components_mol"]["Cl"] == -2.


def test_sulfuric_acid_fixture_adds_sulfate_carrier_and_capacity_once():
    # Chosen synthetic property fixture: 0.098 kg/mol, 50% active by mass.
    # It does not represent a verified commercial acid product.
    acid = solution_dose_stream("acid", 2., vec(**{"S(VI)": 1.}), .098, .5, 2.)
    result = advance_inventory(state(), forcing((acid,)), 10.)
    check_ok(result)
    assert result.state.dissolved_mol["S(VI)"] == 20.
    assert result.state.solvent_kg == pytest.approx(101.96, abs=1e-10)
    assert result.ledger["streams"][0]["acid_equivalents_eq"] == 40.
    assert result.ledger["streams"][0]["water_kg"] == pytest.approx(1.96, abs=1e-10)


def hydration_transfer(reverse=False):
    # CaSO4·2H2O fixture with deliberately specified 0.018 kg/mol water.
    sign = -1. if reverse else 1.
    removal = vec(Ca=-sign, **{"S(VI)": -sign})
    addition = vec(Ca=sign, **{"S(VI)": sign})
    return PhaseTransfer("reverse" if reverse else "precipitation",
                         {"liquid": removal, "suspended": addition},
                         {"liquid": -.036*sign, "suspended": .036*sign})


def test_declared_hydration_and_redissolution_return_the_original_state():
    initial = state(Ca=10., **{"S(VI)": 10.})
    precip = advance_inventory(initial, forcing(transfers=(hydration_transfer(),)), 5.)
    check_ok(precip)
    assert precip.state.solvent_kg == pytest.approx(99.82, abs=1e-10)
    assert precip.state.suspended.bound_water_kg == pytest.approx(.18, abs=1e-10)
    assert precip.state.suspended.components_mol["Ca"] == 5.
    assert precip.state.dissolved_mol["Ca"] == 5.
    dissolve = advance_inventory(precip.state, forcing(transfers=(hydration_transfer(True),)), 5.)
    check_ok(dissolve)
    assert dissolve.state.solvent_kg == pytest.approx(initial.solvent_kg, abs=1e-10)
    assert dissolve.state.dissolved_mol == initial.dissolved_mol
    assert dissolve.state.suspended.bound_water_kg == 0.


def test_suspension_to_wall_transfers_both_solid_elements_and_bound_water():
    initial = Inventory("tower", 100., vec(), SolidInventory(vec(Ca=5.), .18), {"wall": solid()})
    transfer = PhaseTransfer("deposition", {"suspended": vec(Ca=-.5), "deposit:wall": vec(Ca=.5)},
                             {"suspended": -.018, "deposit:wall": .018})
    result = advance_inventory(initial, forcing(transfers=(transfer,)), 10.)
    check_ok(result)
    assert result.state.suspended.components_mol["Ca"] == 0.
    assert result.state.deposits["wall"].components_mol["Ca"] == 5.
    assert result.state.deposits["wall"].bound_water_kg == pytest.approx(.18, abs=1e-10)


@pytest.mark.parametrize("source,destination,element", [
    ("N(-III)", "N(V)", "N"), ("S(-II)", "S(VI)", "S"),
])
def test_redox_rows_cancel_only_after_element_projection(source, destination, element):
    transfer = PhaseTransfer("declared-redox", {"liquid": vec(**{source: -.5, destination: .5})},
                             {"liquid": 0.})
    result = advance_inventory(state(**{source: 10.}), forcing(transfers=(transfer,)), 4.)
    check_ok(result)
    assert result.state.dissolved_mol[source] == 8.
    assert result.state.dissolved_mol[destination] == 2.
    assert result.ledger["internal_net_components_mol"][source] == -2.
    assert result.ledger["internal_net_components_mol"][destination] == 2.
    assert result.ledger["elemental_residual_mol"][element] == 0.


def test_unbalanced_internal_component_transfer_is_rejected():
    transfer = PhaseTransfer("unbalanced", {"liquid": vec(Ca=-1.), "suspended": vec(Ca=.9)},
                             {"liquid": 0., "suspended": 0.})
    initial = state(Ca=5.)
    result = advance_inventory(initial, forcing(transfers=(transfer,)), 1.)
    assert result.status == "REJECTED" and result.state is initial and result.ledger is None
    assert "does not conserve Ca" in result.reasons[0]


def test_unbalanced_hydration_water_is_rejected():
    transfer = PhaseTransfer("water-from-nowhere", {"liquid": vec(), "suspended": vec()},
                             {"liquid": -.1, "suspended": .2})
    result = advance_inventory(state(), forcing(transfers=(transfer,)), 1.)
    assert result.status == "REJECTED" and "conserve water" in result.reasons[0]


@pytest.mark.parametrize("stream", [
    StreamFlux("excess-water", "out", "liquid", vec(), 101., "withdrawal"),
    StreamFlux("all-solvent", "out", "liquid", vec(), 100., "withdrawal"),
    StreamFlux("trace-negative", "out", "liquid", vec(Ca=1e-15), 0., "removal"),
])
def test_impossible_withdrawal_is_rejected_without_clipping_or_mutating(stream):
    initial = state()
    result = advance_inventory(initial, forcing((stream,)), 1.)
    assert result.status == "REJECTED"
    assert result.state is initial and result.ledger is None and not result.advanced


@pytest.mark.parametrize("component", COMPONENTS)
def test_every_omitted_initial_component_is_unknown_not_zero(component):
    missing = vec()
    del missing[component]
    initial = Inventory("tower", 100., missing, solid(), {})
    result = advance_inventory(initial, forcing(), 1.)
    assert result.status == "UNKNOWN" and result.state is initial and result.ledger is None
    assert f"liquid.{component}" in result.reasons
    assert initial.dissolved_mol[component] is None


def test_missing_stream_component_and_particulate_assay_are_unknown():
    stream = StreamFlux("partial-assay", "in", "liquid", {"Cl": 1.}, 1., "makeup")
    assert advance_inventory(state(), forcing((stream,)), 1.).status == "UNKNOWN"
    partial_solids = SolidInventory({}, 0.)
    initial = Inventory("tower", 100., vec(), partial_solids, {})
    assert advance_inventory(initial, forcing(), 1.).status == "UNKNOWN"


def test_unknown_carrier_fraction_does_not_turn_into_zero_carrier():
    stream = solution_dose_stream("acid", 1., vec(**{"S(VI)": 1.}), .098, None, 2.)
    assert stream.water_kg_s is None
    assert advance_inventory(state(), forcing((stream,)), 1.).status == "UNKNOWN"


def test_missing_evaporation_and_internal_component_are_unknown():
    assert advance_inventory(state(), forcing(evap=None), 1.).status == "UNKNOWN"
    transfer = PhaseTransfer("partial", {"liquid": {"Cl": -1.}, "suspended": {"Cl": 1.}},
                             {"liquid": 0., "suspended": 0.})
    assert advance_inventory(state(Cl=2.), forcing(transfers=(transfer,)), 1.).status == "UNKNOWN"


def test_explicit_zero_inputs_allow_an_unchanged_known_state():
    initial = state()
    result = advance_inventory(initial, forcing(), 1.)
    check_ok(result)
    assert result.state.as_dict() == initial.as_dict()


def test_isolated_closed_loop_has_no_ion_transfer_from_tower():
    tower, closed = state("tower", Cl=50.), state("closed", Cl=.01)
    closed_before = closed.as_dict()
    tower_result = advance_inventory(tower, forcing(evap=1.), 10.)
    closed_result = advance_inventory(closed, forcing(), 10.)
    check_ok(tower_result)
    check_ok(closed_result)
    assert tower_result.state.solvent_kg == 90.
    assert closed_result.state.as_dict() == closed_before
    assert closed.as_dict() == closed_before


def test_state_flux_and_returned_ledger_are_deeply_immutable():
    raw = vec(Cl=2.)
    deposits = {"wall": solid()}
    initial = Inventory("tower", 100., raw, solid(), deposits)
    raw["Cl"] = 999.
    deposits.clear()
    assert initial.dissolved_mol["Cl"] == 2. and "wall" in initial.deposits
    with pytest.raises(TypeError):
        initial.dissolved_mol["Cl"] = 1.
    with pytest.raises(dataclasses.FrozenInstanceError):
        initial.solvent_kg = 50.
    result = advance_inventory(initial, forcing(), 1.)
    with pytest.raises(TypeError):
        result.ledger["end_components_mol"]["Cl"] = 9.


def test_dissolved_and_particulate_discharge_are_separate_but_both_count():
    initial = Inventory("tower", 100., vec(**{"P(V)": 5.}), solid(**{"P(V)": 2.}), {})
    streams = (StreamFlux("dissolved-P", "out", "liquid", vec(**{"P(V)": .1}), .2, "blowdown"),
               StreamFlux("particulate-P", "out", "suspended", vec(**{"P(V)": .05}), 0., "blowdown"))
    result = advance_inventory(initial, forcing(streams), 10.)
    check_ok(result)
    assert result.ledger["external_net_components_mol"]["P(V)"] == pytest.approx(-1.5, abs=1e-10)
    assert result.state.suspended.components_mol["P(V)"] == 1.5


def test_repeated_constant_flux_steps_match_direct_integration():
    initial = state(Ca=10., Cl=20.)
    streams = (StreamFlux("in", "in", "liquid", vec(Ca=.03, Cl=.04), 1., "makeup"),
               StreamFlux("out", "out", "liquid", vec(Ca=.01, Cl=.02), .2, "blowdown"))
    imposed = forcing(streams, evap=.5)
    current = initial
    for _ in range(100):
        result = advance_inventory(current, imposed, .25)
        check_ok(result)
        current = result.state
    direct = advance_inventory(initial, imposed, 25.)
    check_ok(direct)
    assert current.solvent_kg == pytest.approx(direct.state.solvent_kg, abs=1e-10)
    assert current.dissolved_mol["Ca"] == pytest.approx(direct.state.dissolved_mol["Ca"], abs=1e-10)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1., True])
def test_invalid_scalar_inputs_are_rejected_at_construction(bad):
    with pytest.raises(ValueError):
        state(water=bad)


def test_integrated_overflow_rejects_without_exposing_infinity():
    initial = state()
    stream = StreamFlux("huge", "in", "liquid", vec(), 1e308, "test")
    result = advance_inventory(initial, forcing((stream,)), 10.)
    assert result.status == "REJECTED" and result.ledger is None and result.state is initial


def test_unknown_compartment_cannot_create_a_new_cross_loop_path():
    stream = StreamFlux("invalid-route", "out", "other-loop", vec(), 1., "test")
    result = advance_inventory(state(), forcing((stream,)), 1.)
    assert result.status == "REJECTED" and "unknown compartment" in result.reasons[0]


def test_element_projection_keeps_nitrogen_and_sulfur_totals():
    result = elemental_totals(vec(**{"N(-III)": 1., "N(III)": 2., "N(V)": 3., "S(VI)": 4., "S(-II)": 5.}))
    assert result["N"] == 6. and result["S"] == 9.
    assert all(x is None for x in elemental_totals({"N(V)": 3.}).values())


def test_invalid_internal_creation_cannot_hide_behind_a_second_transfer():
    creation = PhaseTransfer("creation", {"liquid": vec(Ca=1.)}, {"liquid": 0.})
    destruction = PhaseTransfer("destruction", {"liquid": vec(Ca=-1.)}, {"liquid": 0.})
    result = advance_inventory(state(Ca=5.), forcing(transfers=(creation, destruction)), 1.)
    assert result.status == "REJECTED" and "creation" in result.reasons[0]


def test_internal_global_balance_cannot_borrow_nonexistent_suspended_material():
    transfer = PhaseTransfer("empty-suspension", {"suspended": vec(Ca=-1.),
                                                "deposit:wall": vec(Ca=1.)},
                             {"suspended": 0., "deposit:wall": 0.})
    initial = state(Ca=10.)
    result = advance_inventory(initial, forcing(transfers=(transfer,)), 1.)
    assert result.status == "REJECTED" and result.state is initial
    assert "suspended" in result.reasons[0]


def test_cleaning_removes_deposited_elements_and_bound_water_as_external_stream():
    initial = Inventory("tower", 100., vec(), solid(), {"wall": SolidInventory(vec(Ca=5.), .2)})
    removal = StreamFlux("cleaning", "out", "deposit:wall", vec(Ca=1.), .04, "cleaning")
    result = advance_inventory(initial, forcing((removal,)), 5.)
    check_ok(result)
    assert result.state.solvent_kg == 100.
    assert result.state.deposits["wall"].bound_water_kg == 0.
    assert result.ledger["external_net_water_kg"] == -.2
    assert result.ledger["external_net_components_mol"]["Ca"] == -5.


def test_unknown_initial_water_stays_unknown():
    initial = Inventory("tower", None, vec(), solid(), {})
    result = advance_inventory(initial, forcing(), 1.)
    assert result.status == "UNKNOWN" and result.state is initial
    assert "liquid.water" in result.reasons


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1., True])
def test_invalid_component_and_unsigned_stream_cannot_enter_state(bad):
    with pytest.raises(ValueError):
        state(Ca=bad)
    with pytest.raises(ValueError):
        StreamFlux("invalid", "in", "liquid", vec(), bad, "makeup")


@pytest.mark.parametrize("fraction", [0., -1., 1.1, math.nan, math.inf])
def test_invalid_acid_fraction_is_rejected_without_inventing_carrier(fraction):
    with pytest.raises(ValueError):
        solution_dose_stream("acid", 1., vec(**{"S(VI)": 1.}), .098, fraction, 2.)


def test_pure_reagent_has_explicit_zero_carrier_not_missing_carrier():
    reagent = solution_dose_stream("acid", 1., vec(**{"S(VI)": 1.}), .098, 1., 2.)
    assert reagent.water_kg_s == 0.
    result = advance_inventory(state(), forcing((reagent,)), 1.)
    check_ok(result)
    assert result.state.solvent_kg == 100.


def test_unsupported_component_requires_schema_revision():
    unsupported = vec()
    unsupported["Sr"] = .1
    with pytest.raises(ValueError, match="unsupported analytical-components-18-v1"):
        Inventory("tower", 100., unsupported, solid(), {})
