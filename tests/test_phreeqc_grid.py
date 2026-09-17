"""The chemistry engine against STORED PHREEQC values on a 128-solution grid.

Pre-registered in docs/staged/phreeqc_benchmark_preregistration.md, committed
before PHREEQC was run. PHREEQC's output is stored under
data/reference/phreeqc_benchmark_20260917/, so CI needs no PHREEQC install:
these tests recompute the engine LIVE and compare it with the stored values.

THE REGISTERED VERDICT IS FAIL (staged defect 53). 95.7 % of 416 gated
comparisons are within tolerance, which clears the 95 % overall bar, but
calcite is within tolerance at only 89.1 % of its 128 points against a 90 %
per-mineral bar. Every failure is at I <= 0.1 and 45-55 C. The criterion test
is therefore `xfail(strict=True)`: when the engine is brought into agreement
it XPASSes and the suite goes red, which is the prompt to close defect 53.
Beside it, a non-xfail test pins the current shares so they cannot drift
quietly while the defect is open. No tolerance, share or grid point was
changed after the run.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phreeqc_grid_benchmark as bench  # noqa: E402

OUT = bench.OUT


@pytest.fixture(scope="module")
def grid():
    return json.loads((OUT / "grid.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rows(grid):
    return bench.compare(grid, bench.load_reference())


def test_the_grid_is_the_registered_grid(grid):
    assert len(grid) == 128
    assert [c for c in dict.fromkeys(p["composition"] for p in grid)] == [
        "ARAMCO_FIELD_VALIDATED", "DOE_SYN_MWW_NF_COC4",
        "DOE_SYN_MWW_NF_COC4_TABLE_2_3_2", "DOE_SYN_MWW_COC4"]
    assert sorted({p["cycles"] for p in grid}) == list(range(1, 9))
    assert sorted({p["T_C"] for p in grid}) == [25.0, 35.0, 45.0, 55.0]
    assert bench.compositions() == [c for c in dict.fromkeys(
        p["composition"] for p in grid)], (
        "the set of Water analyses passing validate_analysis has changed; the "
        "benchmark no longer covers what its pre-registration says it covers")


def test_the_tolerances_are_the_registered_ones():
    assert bench.tolerance(0.1) == 0.05
    assert bench.tolerance(0.1000001) == 0.10
    assert bench.tolerance(0.5) == 0.10
    assert bench.tolerance(0.5000001) is None
    assert bench.ION_COUNT_SCALE == {"calcite": 1.0, "gypsum": 1.0,
                                     "silica_am": 1.0, "hydroxyapatite": 4.0}


def test_the_reference_is_the_registered_binary_and_deck():
    prov = json.loads((OUT / "provenance.json").read_text(encoding="utf-8"))
    assert prov["returncode"] == 0
    assert prov["phreeqc_exe_sha256"] == bench.EXE_SHA256
    assert prov["phreeqc_dat_sha256"] == bench.DAT_SHA256
    deck = hashlib.sha256((OUT / "deck.pqi").read_bytes()).hexdigest()
    assert prov["deck_sha256"] == deck, "the stored deck is not the one that was run"


def test_the_stored_reference_reproduces_from_the_raw_output(grid):
    """reference.csv is derived, so re-derive it: totals, pH and temperature
    must round-trip, every point must be bracketed, and the interpolation must
    give the stored values."""
    fresh = bench.reference(grid, bench.read_selected())
    stored = bench.load_reference()
    assert all(r["bracketed"] for r in fresh)
    for r in fresh:
        s = stored[r["point"]]
        for col in ("si_calcite", "si_gypsum", "si_silica", "si_hap", "mu"):
            assert r[col] == pytest.approx(s[col], abs=1e-9)


@pytest.mark.xfail(strict=True, reason=(
    "staged defect 53: the engine fails the pre-registered PHREEQC criterion "
    "(calcite 89.1 % within tolerance against a 90 % per-mineral bar)"))
def test_engine_meets_the_preregistered_phreeqc_criterion(rows):
    v = bench.verdict(rows)
    assert v["share_within"] >= 0.95
    assert all(s >= 0.90 for s in v["share_by_mineral"].values())


def test_the_benchmark_result_has_not_drifted(rows):
    """Pins the registered FAIL so it cannot move quietly in either direction."""
    v = bench.verdict(rows)
    assert v["n_gated"] == 416
    assert v["verdict"] == "FAIL"
    assert v["share_within"] == pytest.approx(398 / 416, abs=1e-9)
    assert v["share_by_mineral"] == pytest.approx(
        {"calcite": 114 / 128, "gypsum": 124 / 128, "silica_am": 1.0,
         "hydroxyapatite": 1.0}, abs=1e-9)
    failing = [r for r in rows if r["gated"] and not r["within"]]
    assert all(r["T_C"] >= 45.0 and r["I"] <= 0.1 for r in failing), (
        "disagreement has spread beyond I <= 0.1 at 45-55 C")
    worst = max(abs(r["dSI"]) for r in rows if r["mineral"] in ("calcite", "gypsum"))
    assert worst == pytest.approx(0.0979, abs=0.002)


# ---------------------------------------------------------------------------
# Supplement: brucite saturation pH against PHREEQC + wateq4f.dat
# ---------------------------------------------------------------------------
# docs/staged/phreeqc_brucite_supplement_preregistration.md. The engine paired
# a hydroxide-form log K with the proton-form enthalpy (defect 57 as staged by
# the incumbent branch). PHREEQC confirmed it: 0 of 96 temperature shifts
# within 0.05 pH, median -0.62 at 45 C. Fixed, and re-scored against the SAME
# stored run: 96 of 96.
import phreeqc_brucite_benchmark as brucite  # noqa: E402


def test_brucite_enthalpy_is_the_hydroxide_form():
    assert ch_mod().BRUCITE_DH_HYDROXIDE_KCAL == pytest.approx(-27.1 + 2 * 13.362)


def ch_mod():
    return bench.ch


def test_brucite_temperature_dependence_matches_phreeqc():
    v = brucite.verdict(brucite.compare())
    assert v["n_gated"] == 96
    assert v["verdict"] == "PASS", v
    assert all(abs(d) < 0.02 for d in v["median_D_by_T"].values())


def test_the_brucite_check_is_not_vacuous(monkeypatch):
    """With the old proton-form enthalpy restored the same stored run fails."""
    monkeypatch.setattr(bench.ch, "BRUCITE_DH_HYDROXIDE_KCAL", -27.1)
    v = brucite.verdict(brucite.compare())
    assert v["share_within"] == 0.0 and v["confirms_suspected_defect"]
