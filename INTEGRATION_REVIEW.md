# Integration review — 20 Sep 2026

Base: upstream `267b99c17d9aeeb18c299590d4480c86c3adaf28`, including the solo-founder update.
Branch: `codex/robustness-integration-20260919`. Offline development only.

The historical defect register and failed gates remain historical evidence. This
review uses R identifiers to avoid colliding with numbers reserved by other work.

| Review item | Change | Verification |
|---|---|---|
| R1: equal-TDS water cache collision | Complete assay state in the thermal cache key | `review_tests/test_assay_cache_review.py`: cached and fresh B must agree after A; a formerly false-feasible case remains rejected |
| R2: invalid interlock input | Reject nonfinite/missing sensor or request values before observers; explicitly isolate acid; reject irregular scan timing | `review_tests/test_safety_admission_review.py`: malformed values, missed/repeated/backward scans, reset/proving sequence and shadow-mode invalid command |
| R3: missing optimizer result bypass | Attached layer returns explicit off command on infeasibility, exception or malformed result | Same test file; no-layer legacy behavior retained |
| R4: empty/invalid permit table | Reject unsupported/empty/nonfinite configurations instead of returning upper search bound | `review_tests/test_discharge_admission_review.py`; valid infeasibility still distinct from missing information |
| R5: infeasible chemistry search anchor | Raise `InfeasibleCeilingError` rather than presenting one cycle as feasible | `review_tests/test_sidestream_ceiling_review.py`; both prescribed and atmospheric pH paths |
| R6: inconsistent surface identity | New explicit heat-flux/film/deposit resistance network returns both surfaces | `review_tests/test_surface_temperatures_review.py`; legacy default and old results unchanged |
| R7: unregistered new artifacts | Register code/data/configuration before calculation; verify hashes and file sets; refuse overwriting or resealing | `review_tests/test_evidence_run.py`; injected input/output/source-set changes fail |
| R8: stale incumbent prose | Correct measured-water binding mineral, modeled money rows, LSI comparator and assay-vs-online-instrument cost interpretation | `docs/incumbent_gap.md`, source `results/incumbent_gap.json`; full consistency audit |

R6 supplies explicit alternatives, not a validated deposition or under-deposit
transport model. R7 applies to new wrapped runs; it does not retrofit provenance
onto every old artifact or prove physical correctness. R2/R3 are software acid
interlocks, not a qualified thermal fallback or independent hardware protection.

The old calibration/PHREEQC/PINN/safety failures are not declared repaired. No
registered numerical threshold was loosened and no protected historical test
was edited. Existing `tests/` and new `review_tests/` should run together:

```powershell
python -m pytest tests review_tests --basetemp <new-temporary-directory> -p no:cacheprovider
python src/audit.py
python scripts/evidence_run.py <new-registered-run-directory>
```

The companion `prototype/mizan_replay` adapter in the Startup Astra workspace
calls this core; it does not introduce a second thermal/chemistry engine. It
records a steady advisory replay, causal persistence forecasts and admission
faults. Full transient 96-step MPC remains unfinished, explicitly recorded in
the main workspace requirement ledger. Production deployment remains outside
the demonstrated evidence.
