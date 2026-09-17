"""Concrete-basin sulfate exposure: published thresholds, reported not imposed.

Thresholds and their verification are documented in src/concrete.py. These
tests pin the class boundaries as transcribed, the cycles helper, the acid's
sulfate contribution, and the rule that the constraint binds only on a
declared basin.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import chemistry as chem      # noqa: E402
import concrete as cc         # noqa: E402
import controller as ctl      # noqa: E402

FIELD = chem.ARAMCO_FIELD_VALIDATED


@pytest.mark.parametrize("so4,aci", [(0.0, "S0"), (149.9, "S0"), (150.0, "S1"),
                                     (1499.9, "S1"), (1500.0, "S2"),
                                     (10000.0, "S2"), (10000.1, "S3")])
def test_aci_318_19_boundaries_as_transcribed(so4, aci):
    assert cc.concrete_sulfate_exposure(so4)["aci_318_19"] == aci


@pytest.mark.parametrize("so4,en", [(199.9, None), (200.0, "XA1"), (600.0, "XA1"),
                                    (600.1, "XA2"), (3000.0, "XA2"),
                                    (3000.1, "XA3"), (6000.0, "XA3"),
                                    (6000.1, "beyond XA3")])
def test_en_206_boundaries_as_transcribed(so4, en):
    assert cc.concrete_sulfate_exposure(so4)["en_206"] == en


def test_cycles_at_boundaries_without_acid_is_a_ratio():
    b = cc.cycles_at_class_boundaries(300.0)
    assert b["ACI S2"] == pytest.approx(5.0)
    assert b["EN XA2"] == pytest.approx(2.0)
    assert b["EN XA3"] == pytest.approx(10.0)
    assert b["ACI S1"] < 1.0          # the makeup itself is already past it


def test_the_field_water_makeup_is_already_S1_and_XA1():
    e = cc.concrete_sulfate_exposure(FIELD.SO4)
    assert (e["aci_318_19"], e["en_206"]) == ("S1", "XA1")


def test_acid_sulfate_is_the_engines_dose_one_sulfate_per_diprotic_acid():
    C, ph = 5.0, 8.0
    kg, _ = ctl.acid_dose_for_ph(FIELD, C, ph, 30.0)
    add = cc.acid_sulfate_mg_l(FIELD, C, ph, 30.0)
    assert add == pytest.approx(kg * 96.06 / 98.079 * 1e6, rel=1e-12)
    # mol SO4 per kg = half the equivalents of alkalinity destroyed
    d_alk_eq = kg / (98.079e-3 / 2.0)
    assert add == pytest.approx(d_alk_eq / 2.0 * 96060.0, rel=1e-9)


def test_acid_moves_every_boundary_to_fewer_cycles():
    plain = cc.cycles_at_class_boundaries(FIELD.SO4)
    dosed = cc.cycles_at_class_boundaries(FIELD.SO4, FIELD, 8.0, 30.0)
    for k in ("ACI S2", "ACI S3", "EN XA2", "EN XA3"):
        assert dosed[k] < plain[k], k
    assert 3.5 < dosed["ACI S2"] < 4.5


def test_undeclared_basin_is_inactive_not_satisfied():
    r = cc.concrete_sulfate_constraint(FIELD, 6.0)
    assert r["active"] is False and r["binds"] is None
    assert "not satisfied" in r["status"]
    assert r["exposure"]["aci_318_19"] == "S2"      # still reported


def test_a_non_concrete_basin_is_not_applicable():
    r = cc.concrete_sulfate_constraint(FIELD, 6.0, basin_material="FRP")
    assert r["active"] is False and "not applicable" in r["status"]


def test_declared_concrete_binds_on_its_cement():
    ii = cc.concrete_sulfate_constraint(FIELD, 5.0, "concrete",
                                        "ASTM_C150_TYPE_II", 8.0, 30.0)
    assert ii["active"] and ii["binds"] is True
    assert ii["max_cycles"] == pytest.approx(
        cc.cycles_at_class_boundaries(FIELD.SO4, FIELD, 8.0, 30.0)["ACI S2"])
    v = cc.concrete_sulfate_constraint(FIELD, 5.0, "concrete",
                                       "ASTM_C150_TYPE_V", 8.0, 30.0)
    assert v["active"] and v["binds"] is False
    nodecl = cc.concrete_sulfate_constraint(FIELD, 5.0, "concrete", None)
    assert nodecl["active"] is False and nodecl["binds"] is None
