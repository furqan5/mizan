"""The incumbent-gap harness, checked against results the repository already
holds, and its registered verdicts, checked against its own recorded numbers.

Pre-registration: docs/staged/incumbent_gap_preregistration.md. The harness
is suspected first: bulk vs skin temperature, the LSI sign, CaCO3 vs ion
basis, and Mg basis and SiO2 vs Si in the rule of thumb.
"""
from __future__ import annotations

import json
import math

import pytest

import chemistry as ch
import incumbent_gap as ig
import sidestream as ss
from conftest import RESULTS, ROOT


@pytest.fixture(scope="module")
def gap():
    p = RESULTS / "incumbent_gap.json"
    assert p.exists(), "run python src/incumbent_gap.py"
    return json.loads(p.read_text(encoding="utf-8"))


def test_the_study_points_at_a_committed_preregistration(gap):
    assert gap["preregistration"] == ig.PREREG
    text = (ROOT / ig.PREREG).read_text(encoding="utf-8")
    for h in ("**H1.**", "**H2.**", "**H3 (adversarial).**", "**H4 (harness",
              "**H4b.**"):
        assert h in text


def test_harness_reproduces_the_calcite_only_gypsum_wall(aramco):
    """Mirror of test_acid_dosing_walks_a_calcite_only_controller_into_the_
    gypsum_wall, computed through this harness's own root finder."""
    full = ch.OPERATING_LIMITS
    cal = {"SI_calcite": full["SI_calcite"]}
    lo_full = ig.single_point_ceiling(aramco, 40.0, 7.5, full)
    lo_cal = ig.single_point_ceiling(aramco, 40.0, 7.5, cal)
    assert lo_cal - lo_full > 5.0
    assert lo_full == pytest.approx(ch.max_cycles(aramco, 40.0, limits=full, pH=7.5),
                                    abs=0.01)
    hi_full = ig.single_point_ceiling(aramco, 40.0, 8.5, full)
    hi_cal = ig.single_point_ceiling(aramco, 40.0, 8.5, cal)
    assert hi_full == pytest.approx(hi_cal, abs=0.01)


def test_harness_reproduces_the_cycle_ceiling_report():
    """The report computes the Riyadh ceiling at 45/32 C, pH 8.25, with the
    diurnal margin applied, bound by calcite. M must be that number when
    neither brucite nor Davies binds."""
    w = ch.ARAMCO_RIYADH_REFINERY_TSE
    lim = ch.limits_with_diurnal_margin(32.0, 5.0)
    product, binding = ss.ceiling_with(w, 45.0, 32.0, limits=lim, pH=8.25)
    m = ig.mizan_ceiling(w, 45.0, 32.0, pH=8.25, report=False)
    assert m["cycles"] == pytest.approx(product, abs=1e-6)
    assert m["binding"] == binding == "SI_calcite"
    assert m["cycles"] == pytest.approx(4.52, abs=0.02)


def test_lsi_converts_ions_to_caco3_exactly_once():
    w = ch.ARAMCO_FIELD_VALIDATED.concentrate(3.0)
    T, pH = 38.0, 7.8
    A = (math.log10(w.tds()) - 1.0) / 10.0
    B = -13.12 * math.log10(T + 273.15) + 34.55
    C = math.log10(w.Ca * 100.0869 / 40.078) - 0.4
    D = math.log10(w.HCO3 * 50.04 / 61.017)
    assert ch.langelier_index(w, T, pH) == pytest.approx(pH - (9.3 + A + B - C - D),
                                                         abs=2e-3)


def test_lsi_is_positive_for_scale_and_rises_with_cycles():
    w = ch.ARAMCO_FIELD_VALIDATED
    lsi = [ch.langelier_index(w.concentrate(c), 37.0, 7.8) for c in (1, 3, 6, 10)]
    assert lsi == sorted(lsi) and lsi[-1] > 0
    c1 = ig.p1_lsi_ceiling(w, 37.0, 7.8)
    assert ch.langelier_index(w.concentrate(c1), 37.0, 7.8) == pytest.approx(
        ig.LSI_MAX, abs=5e-3)


def test_rule_of_thumb_basis_is_stated_not_guessed():
    w = ch.ARAMCO_FIELD_VALIDATED
    caco3 = ig.mg_silica_rule_cycles(w, 20_000.0, "CaCO3")
    ion = ig.mg_silica_rule_cycles(w, 20_000.0, "Mg")
    assert caco3 == pytest.approx(math.sqrt(20_000.0 / (w.Mg * 100.0869 / 24.305
                                                        * w.SiO2)), rel=1e-4)
    assert ion == pytest.approx(math.sqrt(20_000.0 / (w.Mg * w.SiO2)), rel=1e-6)
    # SiO2 is carried as SiO2, not as Si: 100 mg/L of SiO2 at 26.8 in makeup
    assert ig.silica_rule_cycles(w, 100.0) == pytest.approx(100.0 / 26.8, rel=1e-6)


def test_silica_binds_at_the_basin_and_the_incumbent_reads_bulk():
    w = ch.ARAMCO_FIELD_VALIDATED
    base = ig.mizan_ceiling(w, 45.0, 31.5, pH=7.8, report=False)
    hotter_skin = ig.mizan_ceiling(w, 50.0, 31.5, pH=7.8, report=False)
    colder_basin = ig.mizan_ceiling(w, 45.0, 28.5, pH=7.8, report=False)
    assert base["binding"] == "SI_silica_am"
    assert hotter_skin["cycles"] == pytest.approx(base["cycles"], abs=2e-3)
    assert colder_basin["cycles"] < base["cycles"] - 0.1
    # P1 reads one bulk temperature and nothing else
    assert ig.p1_lsi_ceiling(w, 37.0) != pytest.approx(ig.p1_lsi_ceiling(w, 32.0),
                                                       abs=0.05)


def test_h4_grid_maxima_recompute_from_the_recorded_conditions(gap):
    cond = gap["conditions"][0]
    for key, water in (("H4_review_input", ch.balance_sodium(ch.ARAMCO_RECLAIMED)),
                       ("H4b_field_water", ch.ARAMCO_FIELD_VALIDATED)):
        row = gap[key]["rows"][0]
        for pol in ("P1", "M", "calcite_only", "bulk_only"):
            assert ig.grid_max(pol, water, cond) == row[pol], (key, pol)


def test_each_registered_verdict_is_recorded_as_computed(gap):
    """Re-derive every verdict from the recorded numbers with the registered
    thresholds, then pin the verdicts this study returned so a rerun that
    flips one fails loudly instead of quietly."""
    strict = {k: gap["waters"][k] for k in gap["strict_panel"]}
    n = len(strict)
    s1 = sum(abs(r["summary"]["median_gap_acid"]["P1"]) >= 1.0
             for r in strict.values()) / n
    s3 = sum(abs(r["summary"]["median_gap_acid"]["P3"]) <= 0.5
             for r in strict.values()) / n
    silica = [r for r in strict.values() if r["summary"]["class"] == "silica-bound"]
    h2 = (None if not silica else
          all(pc["acid"]["gap"]["P1"] >= 0.5 for r in silica
              for pc in r["per_condition"]))
    v = gap["verdicts"]
    assert v["H1"]["verdict"] == ("HOLDS" if s1 >= 0.5 else "FAILS")
    assert v["H3"]["verdict"] == ("HOLDS" if s3 >= 0.5 else "FAILS")
    assert v["H2"]["verdict"] == ("NOT TESTABLE" if h2 is None else
                                  "HOLDS" if h2 else "FAILS")
    for key, tag in (("H4_review_input", "H4"), ("H4b_field_water", "H4b")):
        same = all(r["P1"] == r["M"] for r in gap[key]["rows"])
        assert v[tag]["verdict"] == ("HOLDS" if same else "FAILS")

    assert gap["strict_panel"] == ["ARAMCO_FIELD_VALIDATED"]
    assert {k: v[k]["verdict"] for k in v} == {
        "H1": "HOLDS", "H2": "HOLDS", "H3": "FAILS", "H4": "HOLDS",
        "H4b": "FAILS"}


def test_registered_verdicts_do_not_rest_on_the_brucite_constant(gap):
    """Staged defect 57: brucite's saturation pH carries a proton-form
    enthalpy on a hydroxide-form log K. It binds M only in the unscored
    no-acid regime; in the scored acid regime it must bind nowhere."""
    for r in gap["waters"].values():
        for pc in r["per_condition"]:
            assert pc["acid"]["M"]["binding"] != "brucite_mg_silicate"
            assert pc["acid"]["M"]["brucite_cycles"] >= ig.HI - 1e-6
