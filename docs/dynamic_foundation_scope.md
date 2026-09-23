# Dynamic foundation, 21–22 Sep 2026

[J] These components extend the reviewed core toward the accepted dynamic
controller. They do not implement the complete coupled rollout or optimizer.

- [V] `inventory_ledger.py` advances explicitly supplied water, dissolved,
  suspended and deposited component fluxes, including hydration water. It
  preserves missing information and rejects unbalanced/depleting transfers.
  See `inventory_ledger_scope.md` for the 18-component basis and H/O, charge,
  alkalinity, kinetics and reaction-enthalpy exclusions.
- [V] `thermal_dynamics.py` supplies constant-flux extensive energy updates,
  isolated epsilon-based heat exchange, a strict canonical chiller wrapper
  and a tower pass specified by hot liquid flow. Fluid properties and their
  domain are explicit inputs, with no field qualification inferred.
- [V] `solution_mass_bridge.py` connects an identified aqueous reference row
  to solution mass using density times volume. It requires solvent equality
  and explicit property identity; it rejects unexplained reaction-water or
  separated-phase mass. See its scope and retained failure record.
- [V] `control_timeline.py` provides immutable 96-by-10 prediction inputs,
  900-second cells, at-most-300-second first releases and load resampling
  preserving interval energy. Actual records require exact requested-window
  coverage. Its proposals always require fresh independent activation checks.

[V] Canonical changes are opt-in. `chiller_power_biquad(strict_domain=True)`
uses raw PLR through the declared 1.06 maximum and rejects extrapolation;
the default retains legacy clipping. `solve_outlet_temperature` adds
`conservative_energy=True` and a numerical `n_steps` parameter, retaining
the historical defaults. The new tower integration imposes the Poppe water
and enthalpy invariants at every RK stage, inverts the existing moist/fog
enthalpy law and reuses the canonical transfer derivatives.

[V] The first new tower energy test failed at 85% RH by 1.8373 kW.
`review_runs/20260921/thermal_tests_initial.log` retains it. The tolerance
was unchanged. The conservative path passed the same case and the registered
160/320-step comparisons. These numerical tests do not repair or rescore
the historical evaporation/heat-rejection validation failures.

[V] Verification is recorded in new `review_runs/20260921` logs. The first
complete historical-plus-review run passed 500 tests with four expected
failures before the separate mass/timing additions and three overflow tests.
The existing audit passed 71 assertions, retaining its scientific FAIL rows.
Run the final four component test modules together to verify the current
foundation. Synthetic numerical success is separate from physical accuracy,
decision feasibility and hardware/permit/material qualification.

[J] Next integration requirements: reconcile actual circuit/thermal-node
inventories; carry alkalinity and supported reaction/gas terms; speciate local
temperature from conserved totals; accumulate only actual elapsed flows;
implement the robust 96-step planner and independent first-move checker.
Required unsupported constraints remain UNKNOWN. No device-write interface
or automatic promotion to live control is included here.

[V/J] Reference for the chiller formulation: EnergyPlus
[plant equipment](https://bigladdersoftware.com/epx/docs/26-1/input-output-reference/group-plant-equipment.html).
PLR above one requires machine/curve support. The inherited York archetype
does not qualify a warm-water FWS chiller or an actual installation.
