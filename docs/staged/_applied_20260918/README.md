# Applied 18 September 2026

These are the defect rows and stale-number lists that six branches staged on
17 September 2026 rather than editing shared documents, and they have all been
applied to `docs/defect_register.md`, `HANDOFF.md`, `docs/handoff_external.md`,
`README.md`, the deck markdown and the rest of `docs/`.

They are **archived rather than deleted**, for three reasons:

1. Each one records *how* a defect was found and what was measured before it was
   fixed, at more length than a register row carries.
2. The doc-update lists are the provenance of individual replacements — file,
   line, old value, new value — and the register records the supersession but
   not which line in which document each figure sat on.
3. Two of them also record decisions that were deliberately *not* taken
   (`safety-interlocks_defects.md` on the fail-safe default;
   `cdu-side_defects.md` on the chilled-water framing), and those decisions are
   still open.

Nothing in the repository reads these files. The pre-registrations are a
different matter and stay in `docs/staged/`: they are cited by `src/calibrate.py`,
`src/incumbent_gap.py`, `src/cdu_joint_policy.py`, `src/safety.py`,
`scripts/phreeqc_grid_benchmark.py` and others, and
`results/cdu_joint_policy_20260917/registration.json` records the SHA-256 of one
of them against its path. Moving a pre-registration would break the record it
exists to be.

**The register is the source of truth.** Where one of these files disagrees with
`docs/defect_register.md`, the register wins, because the register was written
against `results/` after all six branches were merged.
