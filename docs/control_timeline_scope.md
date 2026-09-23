# Control timeline scope and preregistration

21 Sep 2026. [J] This protocol is recorded before the first execution of `review_tests/test_control_timeline.py`. Synthetic values are software fixtures, not machine limits or measured forecasts.

## Scope

[J] `src/control_timeline.py` supplies immutable timing/data contracts for the dual-domain specification §§4, 15 and 15a. It is not an optimizer, thermal integrator, PLC writer or safety certification. A horizon is 96 cells of 900 s anchored at activation. Only the first command is proposed for at most 300 s. Command limits, slew rates and allowed feedback age are mandatory caller inputs; this module provides no machine defaults.

[J] API: `ActivationHorizon`, `PredictionPlan`, `IssuedLoadInterval`, `resample_load`, `AppliedControlInterval`, `validate_actual_intervals`, `CapabilityMask`, `ChannelLimits`, and `propose_first_move`. All datetimes must have a valid timezone and are normalized to UTC before arithmetic. Numeric values reject booleans, NaN and infinity. Forecast load is nonnegative, piecewise constant and in kW. Source intervals must form an unambiguous contiguous coverage of the requested horizon; extra contiguous padding may extend outside it.

[E] For a target cell j, `E_j=sum(P_i*overlap_seconds(i,j)/3600)` kWh and `mean_j=E_j/(900/3600)` kW. Source minima/maxima consider every source interval intersecting that cell, including short spikes. They do not reconstruct sub-source-interval peaks. The reported source energy is clipped to the horizon, not the entire padded input series. Forecast issuance and availability must precede the caller's explicit as-of time, which cannot be after activation.

[J] Recorded applied intervals are a distinct type with unique event IDs and a recording timestamp at or after the interval end. Their validation rejects predictions, overlaps, gaps, future records and missing requested-time coverage. Actual records must match requested start/end exactly; unlike forecast padding, extra actual coverage is rejected so summing returned durations cannot overcount the requested interval. The caller may explicitly split real records while retaining provenance. This module does not turn predictions into measured records or implement a persistent compliance ledger. The caller remains responsible for trustworthy evidence and idempotent durable accounting.

[J] `propose_first_move` returns only the physically enabled channel values; auxiliary CoC/lift never become writes. The fan-Hz and CW-setpoint authority modes cannot both be enabled. Disabled plan columns are masked values with no write authority, not assertions that the plant's corresponding state is zero. Feedback and limits must exist for every enabled actuator. Each target must lie in its explicit range and be reachable from supplied actual feedback over `expires_at-activation_at`, at most 300 s. No 900 s slew allowance and no assumed pre-activation motion are credited. The preparation check enforces caller-supplied feedback freshness, but the proposal **always requires a fresh activation check** for local mode, measurements, thermal/chemistry/permit constraints and lease. This module cannot prove those conditions.

## Fixed acceptance cases

[J] Before execution, register these cases and criteria:

1. Horizon has exactly 97 UTC boundaries, 96 cells and ten canonical named channels. Plan construction freezes caller-owned nested lists and rejects wrong shapes, nonfinite/bool values, malformed datetimes and future issuance.
2. A 24-hour piecewise-constant load that crosses activation-grid boundaries preserves clipped energy to absolute 1e-9 kWh plus relative 1e-12; a short spike survives in per-cell extrema. A hand-calculated first-cell example independently checks interval weights.
3. Load input gaps, overlaps, empty coverage, negative/nonfinite/bool power, future issue/availability, reversed intervals and naive time are rejected. Different timezone representations of the same instants give identical energy.
4. Actual intervals are immutable and type-distinct, total only elapsed recorded time, and reject duplicate IDs, gaps, overlaps, future recordings, reversed intervals or predictions. No predicted 900 s interval enters a 300 s record.
5. A 300 s first lease is accepted; zero/negative, >300 s, late preparation and naive/malformed expiry are rejected. A shorter lease shortens reachable slew. Boundary targets pass; targets requiring the 900 s forecast allowance fail.
6. Enabling fan Hz and CW-setpoint simultaneously, enabling auxiliary/unknown channels, missing enabled feedback/bounds, stale/future feedback, invalid machine bounds/rates and out-of-range targets all reject. Inputs are unchanged after success or failure.
7. Proposal activity is half-open `[activation, expiration)` and requires activation revalidation. Only masked physical commands are returned; CoC/lift and disabled channels are absent.

[J] Run only the bounded review test file first, with bytecode and pytest cache disabled. Record actual results below without retroactively relaxing thresholds. A failure remains visible along with its correction. Broader integration and machine qualification belong to the parent task.

## Execution record

[V] Original preregistration SHA-256: `D6847B2044BD64B52ED49B25CF29C696364EB37B3D01F12023FD7E765DEB81FE`; original test SHA-256: `EB7DA9E726225CF6542E875C9184CEE4A324FF711CEB9EE99E3DA19796C81CEE`. The files were written on 21 Sep; execution resumed on 22 Sep 2026.

[V] First shell invocation (`C:\Python314\python.exe -B -m pytest ...`) stopped before collection because pytest was absent from that interpreter's default path. No packages were installed. Using the existing workspace `.runtime_packages` via `PYTHONPATH`, the first functional run exited 0 with all 90 cases passing. This was not a failed model or changed threshold.

[J] Review addendum, registered before the next test execution: verify that direct construction of proposal/result records also freezes caller-owned containers and rejects malformed proposal chronology; reject numeric overflow with `TimelineError`, while preserving representable large finite arithmetic. This closes construction/finite-value validation gaps in the existing scope. Existing acceptance thresholds remain unchanged. No field or control-authority claim is added.

[V] The canonical-runtime run after that addendum passed **93 tests in 0.27 s** on 22 Sep 2026, with exit code 0.

[J] Parent review addendum, before the next execution: reject actual-record padding at either requested endpoint. This prevents summing complete returned intervals from overcounting the requested actual-time window. Add two boundary cases; retain the energy/time thresholds and forecast-padding behavior unchanged.

[V] Final bounded run: **95 passed in 0.22 s**, exit code 0, on **22 Sep 2026**, Python **3.12.14** from the bundled canonical runtime. Invocation: `python -m pytest review_tests/test_control_timeline.py -o addopts='' -q -p no:cacheprovider`, with the existing workspace `.runtime_packages` on `PYTHONPATH` and `PYTHONDONTWRITEBYTECODE=1`. No installation, field validation or full-core rerun was performed by this subtask.

[V] Frozen implementation SHA-256: `77D6E699B5F588B057488DEF3EC386D4A59B43A8805CA812B4631013672FF152`. Final test SHA-256: `3E231A7F5A7E7563CC00A79E28B9AD181A228B75E4E6A13A19DEC2531147881E`. The implementation and tests are frozen for parent integration. All commanded limits remain explicit caller inputs, and every returned proposal still requires independent fresh activation admission.
