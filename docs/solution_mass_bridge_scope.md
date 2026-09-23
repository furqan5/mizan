# PHREEQC solution-mass bridge: admission contract

Registered 21 Sep 2026 before the first execution of the new bridge tests. [V] denotes a documented interface fact; [E] a dimensional derivation; [J] an implementation requirement. This bridge does not constitute a coupled chemical/thermal simulation or field validation.

[V] PHREEQC reports `TOT("water")` as solvent mass in kg, `RHO` as aqueous-solution density in kg/L, and `SOLN_VOL` as solution volume in L. `TOTMOLE` is an amount in mol, while ordinary component `TOT` values are mol/kg water. Source: [USGS PHREEQC Basic functions](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-61.htm).

[E] From the same reference solution row:

```text
M_solution [kg] = RHO [kg/L] * SOLN_VOL [L]
w_water [kg solvent/kg solution] = TOT("water") [kg] / M_solution [kg]
flow_solution [kg/s] = flow_solvent [kg/s] / w_water
flow_solvent [kg/s] = flow_solution [kg/s] * w_water
```

[J] The row and expected state must carry matching circuit, state, reference-row, temperature, pressure, database SHA-256, composition SHA-256 and property-model identity. The identity is an adapter provenance assertion, not a substitute for a verified PHREEQC input/output manifest. Never join a density from one row to a volume or water mass from another. Explicit `aqueous_only=True` excludes separated suspended/deposited/gas phases. Their masses and enthalpies require separate phase records.

[J] The caller must supply the current `thermal_dynamics.ConstantCpFluid` object. Its exact name, cp, validity interval, property-basis text and 0 °C enthalpy reference are fingerprinted by `constant_cp_property_id`; that fingerprint must match both state identities. The bridge checks temperature inside that interval. It does not infer cp, qualify a declared cp value, estimate acid dilution heat, or infer reaction/phase enthalpy from SI. Missing properties return `UNKNOWN`.

[V/J] PHREEQC may change solvent-water mass through H/O reaction balances and mineral hydration; see [USGS gypsum example](https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-64.htm). The present 18-component ledger does not contain a complete H/O reaction ledger. Therefore, a reference solvent mass different from the expected inventory beyond numerical tolerance is `REJECTED`. It must not be disguised as makeup or silently overwrite the inventory. Active reaction coupling needs an independently reconciled chemical-water and energy ledger.

## Numerical checks fixed before tests

| Quantity | Criterion [J] |
|---|---|
| Identity strings and fingerprints | exact match |
| Temperature match | absolute difference <= `1e-8 K` |
| Pressure match | absolute difference <= `1e-3 Pa` |
| Reference versus expected solvent | absolute difference <= `1e-9 kg + 1e-12 * max(reference, expected)` |
| Density, volume, solvent and solution mass | finite and strictly positive |
| Water mass fraction | finite and `0 < w_water <= 1`, with no clipping |
| Mass and flow formula fixtures | `1e-12` relative and `1e-12` absolute comparison |
| Signed flow conversions | finite input and output; zero and either sign supported |
| Missing required values or identity | `UNKNOWN`; no admitted bridge |
| Identity mismatch, reaction-water mismatch or unsupported phase basis | `REJECTED`; no admitted bridge |

[J] Tests are synthetic software fixtures. They will cover density/volume-derived mass, reciprocal signed flow conversions, absent and mismatched identities, missing property model, mismatched property fingerprint, temperature outside its declared property interval, water-fraction violation, nonfinite data, solvent changes, mixed-phase exclusion, immutable records and arithmetic overflow. No historical result or tolerance is revised.

## API

`admit_solution_mass(row, expected_identity, expected_solvent_kg, fluid)` returns an immutable `BridgeResult`. Only `status == 'OK'` supplies `bridge`; the other statuses supply reasons and no bridge. `bridge.solution_flow_from_solvent(kg_s)` and `bridge.solvent_flow_from_solution(kg_s)` convert the declared flow basis. Validation does not mutate either reference or expected inventory.

Execution results will be appended after the registered first test run.

## Execution record: 22 Sep 2026

[V] First execution reported **57 passed and 10 failed in 1.54 s** (tool output `321283`, exit 1). The 10 failures reproduced an alternate-construction path: callers could instantiate the immutable output dataclass with inconsistent mass/fraction/residual values or incomplete/out-of-domain identity. Immutability alone did not validate those values.

[J/V] `SolutionMassBridge.__post_init__` now checks complete identity, the derived ratio and residual equations, registered solvent tolerance, exact property fingerprint and the supplied temperature's property domain. Derived values must equal their recomputed expressions; they are not separate measured quantities to round independently. The factory and direct construction obey the same numerical state invariants.

[V] Second execution reported **67 passed in 0.90 s** (output `d0722b`, exit 0). Registered numerical criteria were not changed. Both runs used this command from the isolated integration repository:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPATH="C:\Users\Nouman\Desktop\Furqan's Docs\Startup Astra\.runtime_packages"
& 'C:\Users\Nouman\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest review_tests/test_solution_mass_bridge.py -o addopts='' -q -p no:cacheprovider
```

[V] These results are retained in the tool transcript; no previous source artifact or run log was overwritten. The tests include missing fields, source/state/property mismatches, reaction-water changes, explicit separated-phase rejection, signed reciprocal flows, finite-input overflow and direct-constructor invariants. They establish software behavior on synthetic cases. Actual PHREEQC output parsing, a qualified cp correlation, chemistry-induced water/energy changes and full coupled conservation still require separate validation.
