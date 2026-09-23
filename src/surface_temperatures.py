"""Explicit surfaces for a steady, prescribed-heat-flux resistance network.

Heat travels from metal through a deposit and a convective film into coolant.
The fluid-facing deposit surface and the metal underneath it are different
temperatures. This module does not replace the legacy chemistry defaults.

Constitutive basis: Modelica.Thermal.HeatTransfer.Components.Convection,
Q_flow = h*A*(solid.T-fluid.T), and Fourier resistance across a passive layer.
https://build.openmodelica.org/Documentation/Modelica.Thermal.HeatTransfer.Components.Convection.html
https://doc.comsol.com/6.4/doc/com.comsol.help.heat/heat_ug_ht_features.09.103.html
"""
from __future__ import annotations

import math


def steady_surface_temperatures(bulk_temperature_c, heat_flux_w_m2,
                                film_coefficient_w_m2k,
                                fouling_resistance_m2k_w=0.0):
    """Return both surfaces; all resistances use the same area basis.

    Only nonnegative heat flux from metal toward the coolant is admitted.
    Heat flux and film coefficient are prescribed, not re-solved as fouling
    changes. No deposition kinetics, pore-water chemistry or under-deposit
    mass transport is represented. Using the hotter metal temperature with
    bulk-ion chemistry is a separate hypothesis, not this module's result.
    """
    inputs = {
        "bulk_temperature_c": bulk_temperature_c,
        "heat_flux_w_m2": heat_flux_w_m2,
        "film_coefficient_w_m2k": film_coefficient_w_m2k,
        "fouling_resistance_m2k_w": fouling_resistance_m2k_w,
    }
    for name, value in inputs.items():
        if isinstance(value, bool):
            raise ValueError(f"{name} must be a finite number, not a boolean")
        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a finite number") from exc
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        inputs[name] = value

    bulk = inputs["bulk_temperature_c"]
    flux = inputs["heat_flux_w_m2"]
    film = inputs["film_coefficient_w_m2k"]
    resistance = inputs["fouling_resistance_m2k_w"]
    if bulk < -273.15:
        raise ValueError("bulk_temperature_c cannot be below absolute zero")
    if flux < 0:
        raise ValueError("heat_flux_w_m2 must be nonnegative toward the coolant")
    if film <= 0:
        raise ValueError("film_coefficient_w_m2k must be positive")
    if resistance < 0:
        raise ValueError("fouling_resistance_m2k_w must be nonnegative")

    film_delta = flux / film
    deposit_delta = flux * resistance
    surface = bulk + film_delta
    metal = surface + deposit_delta
    if not all(math.isfinite(x) for x in
               (film_delta, deposit_delta, surface, metal)):
        raise ValueError("surface-temperature calculation overflowed")
    return {
        **inputs,
        "fluid_facing_deposit_c": surface,
        "metal_under_deposit_c": metal,
        "film_delta_k": film_delta,
        "deposit_delta_k": deposit_delta,
        "model_scope": "steady_1d_prescribed_heat_flux",
        "under_deposit_chemistry_modelled": False,
        "deposition_kinetics_modelled": False,
        "assumptions": [
            "Steady one-dimensional heat flow from metal through deposit to coolant.",
            "No heat source or storage inside the deposit or convective film.",
            "Prescribed heat flux and film coefficient on one common area basis.",
            "Fouling does not independently change heat flux, area or film coefficient here.",
            "Fluid-facing temperature does not resolve pore-water or under-deposit transport.",
        ],
    }
