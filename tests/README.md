# The regression suite

**Added 7 September 2026.** Run it with `python -m pytest` from the repository
root. It takes about three seconds.

```
48 passed, 1 xfailed
```

## Why it exists

Before this, `.pytest_cache/v/cache/nodeids` was `[]` — pytest had run and
collected **zero tests** — and there was exactly one `assert` in the whole
`src/` tree.

That is not the same as untested. The pre-registered gates (V1–V6, P1–P4) are
genuinely good integration tests: thresholds fixed and printed before fitting,
failures reported rather than rescored. But they are slow, they need the full
pipeline, and they score a *number* rather than pinning a *mechanism*.

Every one of the twenty-two defects in `docs/defect_register.md` was found by
manual re-derivation. Nothing in the repository prevented any of them from
coming back. And the two most expensive — the fan correlation read in the wrong
unit (defect 1) and the drift eliminator rating with its percent sign dropped
(defect 7) — are the **same defect class, found days apart**. A constant wrong
by a factor of 100 produces plots that look entirely reasonable.

## What is in it

| file | what it pins |
|---|---|
| `test_defect_regressions.py` | one test per named defect, so none can silently return |
| `test_physics_invariants.py` | laws no fit or refactor may break — the second law, mass balance, monotonicity, and the sign of every physically meaningful derivative |
| `test_artefact_consistency.py` | pre-registration integrity, and agreement between documents and artefacts |

## The three rules it follows

**1. A guard that cannot fail is not a guard.** Several tests are paired with a
companion that proves the check is capable of failing — `test_defect_01_
percent_reading_would_be_caught` shows the wrong unit really does produce a
non-monotonic curve, and `test_ratio_of_totals_differs_from_mean_of_ratios`
asserts its own fixture actually exhibits the divergence. The same discipline
was applied to the new audit check: it was verified by injecting a wrong count
and confirming the audit failed.

**2. Test the production path, then pin the trap separately.**
`chiller_power_biquad` produces a physically impossible curve when called
without a nameplate — COP *rises* above 32 °C, because `Q_ref_kw=None` sets the
machine's capacity equal to the load and PLR is then clamped at 1.0. This is
**not a defect**: `src/chiller_feasibility_audit.py` already documented it, all
three `controller.py` call sites pass `Q_ref_kw=nominal_capacity(cond)`, and
defect 11's capacity guard rejects the region anyway. So the suite scores the
production path *and* pins the degenerate behaviour, so that if the default
ever changes, `test_the_plr_clamp_trap_still_behaves_exactly_as_the_audit_
recorded` fails and sends you to re-check every call site.

**3. An open defect is a failing test, not a missing one.** Defect 17 — the
makeup water that fails charge balance by −14.3 % and whose ions sum to
1752 mg/L against a stated TDS of 1500 — has a real test, marked `xfail` with
`xfail_strict = true`. When someone fixes the water analysis the suite goes red
with XPASS. That is the prompt to close the defect in the register. A fixed
fault left marked open is its own kind of staleness.

## What it deliberately does not do

It does not re-run the controller. `run_controller.py` takes about 25 minutes
because the duty fixed point is solved to convergence rather than truncated,
and that is the right trade for the number being correct — but it is the wrong
trade for a suite you should run before every commit. The gates remain the
integration test; this is the unit and invariant layer beneath them.

It also does not test the MATLAB twin, the Simulink model, or the Modelica leg.
The twin is scored against the Python core by `matlab/mizan_verify.m` with its
own gates in advance, and agreement is 1.4e-5 K.
