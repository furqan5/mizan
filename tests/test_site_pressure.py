"""DEFECT 79 -- the Almería tower was calibrated at sea-level pressure.

`calibrate.predict` called `tower.solve_outlet_temperature` without `p`, so
all 147 rows were solved at 101,325 Pa for a tower that stands at 497 m. The
fill law is now re-fitted, and V1/V2 re-scored, at the site pressure, as
pre-registered in docs/staged/almeria_site_pressure_preregistration.md.

These tests hold the pressure, the wiring, and the stored rescore to that
plan, and re-derive the fill law from the source so the artefact cannot go
stale behind them (the defect-74 shape).
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "wct_pilot_plant_dataset" / "data"
PREREG = ROOT / "docs" / "staged" / "almeria_site_pressure_preregistration.md"

import calibrate  # noqa: E402
import psychro as ps  # noqa: E402


def _cal():
    return json.loads((ROOT / "results" / "calibration.json").read_text())


def test_the_site_pressure_is_the_registered_standard_atmosphere():
    assert calibrate.PSA_ELEVATION_M == 497.0
    want = 101325.0 * (1.0 - 2.25577e-5 * 497.0) ** 5.2559
    assert calibrate.PSA_PRESSURE_PA == pytest.approx(want, abs=1e-9)
    assert calibrate.PSA_PRESSURE_PA == pytest.approx(95495.2, abs=0.1)


def test_the_almeria_functions_default_to_the_site_pressure():
    for fn in (calibrate.demanded_merkel, calibrate.predict):
        assert inspect.signature(fn).parameters["p"].default \
            == calibrate.PSA_PRESSURE_PA, fn.__name__
    # and nowhere else: the plant models are not at Almería
    assert ps.P_ATM == 101325.0


# psychro functions take p as their third positional argument; the tower
# functions take it far down the list, so only the keyword is accepted there.
_PSYCHRO = {"humidity_ratio_from_rh", "wetbulb", "wetbulb_from_rh"}
_TOWER = {"integrate_poppe", "solve_outlet_temperature"}


@pytest.mark.parametrize("module", ["calibrate.py", "fill_law.py",
                                    "uncertainty.py"])
def test_every_almeria_tower_and_psychrometric_call_passes_a_pressure(module):
    """The defect was a missing argument. Each call site in the Almería
    modules must now carry one, or the default comes back silently."""
    tree = ast.parse((ROOT / "src" / module).read_text(encoding="utf-8"))
    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        has_kw = any(k.arg == "p" for k in node.keywords)
        if name in _TOWER and not has_kw:
            missing.append(f"{name} at line {node.lineno}")
        if name in _PSYCHRO and not (has_kw or len(node.args) >= 3):
            missing.append(f"{name} at line {node.lineno}")
    assert not missing, f"{module}: called without a pressure: {missing}"


def test_the_stored_rescore_matches_its_preregistration():
    cal = _cal()
    sp = cal["site_pressure"]
    assert sp["p_Pa"] == pytest.approx(calibrate.PSA_PRESSURE_PA, abs=1e-9)
    assert sp["elevation_m"] == 497.0
    assert sp["preregistration"] == \
        "docs/staged/almeria_site_pressure_preregistration.md"
    # the plan has not been edited since the run that cites it
    assert sp["preregistration_sha256"] == \
        hashlib.sha256(PREREG.read_bytes()).hexdigest()
    # thresholds and split unchanged
    assert cal["thresholds"] == {"V1_Tout_MAE_K": 1.0, "V1_Tout_MAE_target_K": 0.5,
                                 "V1_Q_MAPE_pct": 6.0, "V2_evap_MAPE_pct": 8.0}
    assert cal["TRAIN"]["n_points"] == 115 and cal["HOLDOUT"]["n_points"] == 32
    ho = cal["HOLDOUT"]
    assert cal["verdict"] == {"V1_Tout": ho["Tout_MAE_K"] <= 1.0,
                              "V1_Q": ho["Q_MAPE_pct"] <= 6.0,
                              "V2_evap": ho["evap_MAPE_pct"] <= 8.0}
    # the result of the single registered run, 21 Oct 2026
    assert cal["fill_c"] == pytest.approx(1.1728994129484793, abs=1e-9)
    assert cal["fill_n"] == pytest.approx(-0.595079013563148, abs=1e-9)
    assert ho["Tout_MAE_K"] == pytest.approx(0.5418186077426027, abs=1e-6)
    assert ho["Q_MAPE_pct"] == pytest.approx(6.085182953996518, abs=1e-4)
    assert ho["evap_MAPE_pct"] == pytest.approx(10.015609656408465, abs=1e-4)


def test_the_superseded_sea_level_result_is_kept_out_of_the_live_artefact():
    """The audit reads every float in calibration.json as a live figure, so a
    sea-level copy there would stop it catching documents that quote 6.27 %
    and 10.80 % as current. The reference lives in a file of its own."""
    ref = json.loads((ROOT / "results"
                      / "calibration_sea_level_reference.json").read_text())
    assert ref["p_Pa"] == 101325.0 and "NOT_A_GATE" in ref
    assert ref["HOLDOUT"]["Tout_MAE_K"] == pytest.approx(0.5996496645121069, abs=1e-6)
    assert ref["HOLDOUT"]["Q_MAPE_pct"] == pytest.approx(6.269479706945836, abs=1e-4)
    assert ref["HOLDOUT"]["evap_MAPE_pct"] == pytest.approx(10.800079300774595, abs=1e-4)
    text = (ROOT / "results" / "calibration.json").read_text()
    for stale in ("1.2400648", "0.5996496", "6.269479", "10.800079"):
        assert stale not in text, stale


def test_the_fill_law_re_derives_from_the_source():
    """Re-fit from the data and the code that exists now. About a second."""
    pytest.importorskip("netCDF4")
    if not (DATA / "Exp2.nc").exists():
        pytest.skip("Almería dataset not present")
    import dataset as ds
    train, _ = ds.split_holdout(ds.derive(ds.load_all()),
                                calibrate.TRAIN_CAMPAIGNS,
                                calibrate.TEST_CAMPAIGNS)
    Me, LG, _, ok = calibrate.demanded_merkel(train)
    c, n, _ = calibrate.fit_fill_law(Me, LG, ok)
    cal = _cal()
    assert c == pytest.approx(cal["fill_c"], abs=1e-9)
    assert n == pytest.approx(cal["fill_n"], abs=1e-9)
