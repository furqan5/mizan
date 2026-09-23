# Inventory ledger: development scope and registered checks

Registered on 21 Sep 2026 before this module's first test execution. [J] Implementation choices and numerical criteria below are development requirements, not field validation. Source contract: the workspace `docs/MIZAN_Dual_Domain_System_Specification.md`, sections 4, 4a and 5.

## Contract

[J] One immutable `Inventory` represents one chemically isolated circuit: solvent water in kg; 18 dissolved analytical component inventories in mol; suspended component inventories and bound water; and independently identified deposited inventories and bound water. The schema is `Ca, Mg, Na, K, Cl, S(VI), C(inorganic), P(V), Si, N(-III), N(III), N(V), Cu, Fe, Al, Zn, Ba, S(-II)`. Missing fields or `None` are unknown; an explicit zero is a known zero. `explicit_zero_components()` is an intentional caller declaration, not an assay-completion algorithm.

[E] Constant imposed fluxes integrate as `inventory_end = inventory_start + dt * net_rate`. Each external stream records its direction, circuit compartment, complete component-rate vector (mol/s), and solvent or bound-water rate (kg/s). Evaporation removes solvent only. Its use for a volatile component requires a separate gas-removal stream. Every stream is integrated independently and retained in the returned ledger. Dose streams carry their components and solvent carrier once. The acid-equivalent metadata is an integrated input diagnostic, not an inferred pH or alkalinity state.

[J] Outgoing component rates must be supplied, measured, or computed by a separate transport integrator. This primitive does **not** treat a frozen initial `q*n/M` as an exact continuously mixed withdrawal solution. Caller time-step convergence and its changing outlet composition remain independent obligations. Constant rates imply affine inventory trajectories, so nonnegative start and end inventories bound the entire interval; zero solvent inventory is rejected because subsequent concentration is undefined.

[E] Internal `PhaseTransfer` terms provide signed, complete component vectors and signed water rates by participating compartment. They represent declared precipitation, redissolution, suspension/deposition, detachment or redox transfers. They do not infer a rate from SI. Transfers must cancel in total water and after the 18-component projection onto 15 tracked elemental totals. Sulfur oxidation rows project onto S; the three nitrogen oxidation rows project onto N. Component-wise internal sums may be nonzero during redox and are reported explicitly.

[J] H/O atom balance, electron balance, charge/alkalinity balance, phase identity, reaction enthalpy, chemical kinetics, volume/density conversion, corrosion mechanisms, fouling resistance and permit compliance are outside this primitive. A declared vector passing the tracked-element check is not a complete chemical-reaction validation. The model includes no ion transfer across an isolated heat exchanger; separate circuit calls have no shared mutable inventory. Cross-circuit material transfer requires explicit paired external streams in a higher-level topology ledger.

## Numerical criteria fixed before tests

| Check | Registered criterion [J] |
|---|---|
| Total water closure | absolute residual <= `1e-9 kg + 1e-12 * max(start, end, gross transferred water)` |
| Each tracked elemental closure | absolute residual <= `1e-10 mol + 1e-12 * max(start, end, gross transferred component moles)` |
| Internal transfer water balance | same water criterion applied to step-integrated internal terms |
| Internal elemental balance | same elemental criterion applied to step-integrated internal terms |
| Inventory bounds | no negative component/bound-water value; solvent strictly positive; no clipping or deletion of a negative remainder |
| Missing information | `UNKNOWN`, unchanged input state, no released integrated ledger |
| Impossible or unbalanced step | `REJECTED`, unchanged input state, explicit reason, no released integrated ledger |
| Reference fixture comparisons | `1e-10` absolute for mol and kg values below 1,000; `1e-12` relative for large-value cases |

[J] Tests will cover dilution, pure evaporation, declared withdrawal, sulfuric-acid sulfate/carrier/acid-equivalent input, hydration precipitation and reverse dissolution, suspended-to-deposit transfer, N and S redox projection, rejection of unbalanced transfer and excessive withdrawal, unknown schema, immutable caller inputs, isolation between circuits, and arithmetic closure over sequential steps. Inputs are synthetic fixtures unless explicitly stated; no calibration dataset or historical gate is rescored.

## API and failure handling

`advance_inventory(state, forcing, dt_s)` returns `StepResult(status, state, ledger, reasons)`. `OK` alone means that the declared flux integration and numerical closure passed. `UNKNOWN` or `REJECTED` retains the exact input state and supplies no accepted ledger. Structural misuse, nonfinite numbers and negative unsigned input quantities raise `ValueError` at construction/admission. A consumer must check status before advancing its simulation clock or combining the state with a thermal prediction.

No test results are claimed in this preregistration section. Execution evidence is added after the first run below.

## Execution record: 21 Sep 2026

[V] First execution: 47 passed in 0.71 s, exit code 0, tool output chunk `d226d9`. An adversarial review added checks for creation hidden by a cancelling second transfer, withdrawal of nonexistent suspended material, cleaning removal of deposit water, unknown initial water, invalid component and unsigned stream inputs, invalid acid purity, explicit neat reagent, and unsupported added constituents. Second execution: **62 passed in 0.28 s**, exit code 0, chunk `70822d`. No numerical criterion was changed between runs. These are synthetic numerical/software tests, not measured plant validation.

Exact process, from the isolated integration repository:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH="C:\Users\Nouman\Desktop\Furqan's Docs\Startup Astra\.runtime_packages"
& 'C:\Users\Nouman\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest review_tests/test_inventory_ledger.py -o addopts='' -q -p no:cacheprovider
```

[V] Output was captured by the tool transcript; no historical run log was overwritten and no additional run-log file was created. This change owns only the new module, its new review tests, and this scope document. `PYTHONDONTWRITEBYTECODE` and the disabled pytest cache avoid incidental source-tree bytecode/cache writes.

## Integration example and independent handoff

```python
from inventory_ledger import (
    Inventory, SolidInventory, StreamFlux, StepForcing,
    explicit_zero_components, advance_inventory,
)

# Synthetic complete declaration, not a replacement for a measured assay.
ions = explicit_zero_components()
ions['Cl'] = 2.0  # mol
initial = Inventory('CW', 100.0, ions,
    SolidInventory(explicit_zero_components(), 0.0), {})
makeup = StreamFlux('makeup', 'in', 'liquid',
    explicit_zero_components(), 1.0, 'makeup')
result = advance_inventory(initial, StepForcing((makeup,), (), 0.1), 10.0)
if result.status != 'OK':
    raise RuntimeError(result.reasons)  # do not advance coupled thermal time
next_inventory = result.state
serializable_record = result.as_dict()
```

[J] Before joining this ledger to energy, independently verify each circuit's topology; assay/component mapping; outgoing dissolved and particulate rates; reagent composition, molar mass, purity and acid capacity; phase stoichiometry including bound water; and any gas exchange. The registered `OK` status verifies the declared inventory arithmetic only. Summing the atomic masses of the 18 analytical components does not reconstruct complete solution mass: H/O/speciation and a qualified water-mass fraction/property model remain necessary for the thermal bridge. A full coupled solver must also demonstrate time-step convergence as concentration-dependent transport and heat fluxes change.
