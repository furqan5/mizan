"""Independent resistance-network checks; legacy chemistry remains unchanged."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from surface_temperatures import steady_surface_temperatures


def test_surfaces_are_distinct_and_both_elements_carry_the_prescribed_flux():
    r = steady_surface_temperatures(30.0, 10_000.0, 2_000.0, 0.001)
    assert r["fluid_facing_deposit_c"] == 35.0
    assert r["metal_under_deposit_c"] == 45.0
    assert 2_000.0 * (r["fluid_facing_deposit_c"] - 30.0) == 10_000.0
    assert (r["metal_under_deposit_c"] - r["fluid_facing_deposit_c"]) / 0.001 == 10_000.0
    assert r["under_deposit_chemistry_modelled"] is False
    assert r["deposition_kinetics_modelled"] is False


def test_zero_deposit_resistance_coincides_with_clean_metal_surface():
    r = steady_surface_temperatures(30.0, 10_000.0, 2_000.0, 0.0)
    assert r["metal_under_deposit_c"] == r["fluid_facing_deposit_c"] == 35.0
    assert r["deposit_delta_k"] == 0.0


def test_zero_duty_does_not_create_a_temperature_difference():
    r = steady_surface_temperatures(30.0, 0.0, 2_000.0, 0.001)
    assert r["metal_under_deposit_c"] == r["fluid_facing_deposit_c"] == 30.0


@pytest.mark.parametrize("field", ["bulk_temperature_c", "heat_flux_w_m2",
                                    "film_coefficient_w_m2k", "fouling_resistance_m2k_w"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_inputs_are_refused(field, value):
    params = dict(bulk_temperature_c=30.0, heat_flux_w_m2=10_000.0,
                  film_coefficient_w_m2k=2_000.0, fouling_resistance_m2k_w=0.001)
    params[field] = value
    with pytest.raises(ValueError, match="finite"):
        steady_surface_temperatures(**params)


@pytest.mark.parametrize("params", [
    (30.0, -1.0, 2_000.0, 0.001),
    (30.0, 10_000.0, -1.0, 0.001),
    (30.0, 10_000.0, 0.0, 0.001),
    (30.0, 10_000.0, 2_000.0, -0.001),
    (-274.0, 10_000.0, 2_000.0, 0.001),
])
def test_nonphysical_resistances_duty_or_absolute_temperature_are_refused(params):
    with pytest.raises(ValueError):
        steady_surface_temperatures(*params)


def test_finite_inputs_that_overflow_do_not_produce_a_surface():
    with pytest.raises(ValueError, match="overflowed"):
        steady_surface_temperatures(30.0, 1e308, 1e-308, 1.0)
