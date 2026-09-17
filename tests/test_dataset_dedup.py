"""DEFECT 51 (staged) -- the Almería calibration data counted 18 rows twice.

The published netCDF files concatenate to 165 rows, of which 147 are
distinct across the seven measured channels. All 17 rows of Exp3.nc are
copies of Exp1 rows 0-16 (the dataset README describes Exp3 as a DIFFERENT
full-factorial campaign), and Exp1 row 16 is also Exp2 row 113. Scored as
loaded, the 50-row V1/V2 holdout was 33 distinct rows, one of which the fill
law had been trained on.

These tests hold the loader and the split so the duplicates cannot re-enter,
and pin the re-score to the pre-registration in
docs/staged/almeria_dedup_preregistration.md.
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "extracted" / "wct_pilot_plant_dataset" / "data"

pytest.importorskip("netCDF4")
if not (DATA / "Exp1.nc").exists():
    pytest.skip("Almería dataset not present", allow_module_level=True)

import dataset as ds  # noqa: E402


@pytest.fixture(scope="module")
def raw():
    return ds.load_all(deduplicate=False)


@pytest.fixture(scope="module")
def distinct():
    return ds.load_all()


def _keys(df):
    return [tuple(r) for r in df[list(ds.MEASURED_CHANNELS)].itertuples(
        index=False, name=None)]


def test_the_published_files_really_do_repeat_rows(raw):
    """Guards the guard: if the upstream files are ever corrected, the counts
    below stop being true and this says so rather than passing vacuously."""
    assert len(raw) == 165
    assert len(set(_keys(raw))) == 147
    exp1 = set(_keys(raw[raw.campaign == "Exp1"]))
    exp3 = _keys(raw[raw.campaign == "Exp3"])
    assert len(exp3) == 17 and all(k in exp1 for k in exp3), (
        "Exp3.nc is no longer a copy of Exp1 rows; re-examine defect 51")


def test_the_loader_returns_each_measurement_once(distinct):
    keys = _keys(distinct)
    assert len(keys) == len(set(keys)), "a duplicated measurement re-entered"
    assert len(distinct) == 147
    # nothing is dropped silently: membership records every campaign
    assert (distinct.campaigns.str.contains("Exp3")).sum() == 17
    assert ds.in_campaigns(distinct, ["Exp3"]).sum() == 17
    assert (distinct.campaign == "Exp3").sum() == 0, (
        "Exp3 has no measurement of its own")


def test_the_split_cannot_hold_out_a_training_row(distinct):
    train, test = ds.split_holdout(distinct, ["Exp2"], ["Exp1", "Exp3"])
    assert len(train) == 115, "the training campaign must be all of Exp2"
    assert len(test) == 32
    assert not set(_keys(train)) & set(_keys(test)), "train/holdout leakage"


def test_the_leak_guard_is_not_vacuous(raw):
    """Filtering on the campaign LABEL, as calibrate.py did before the fix,
    must still show the leak -- otherwise the test above proves nothing."""
    train = raw[raw.campaign == "Exp2"]
    test = raw[raw.campaign.isin(["Exp1", "Exp3"])]
    assert len(test) == 50
    assert len(set(_keys(train)) & set(_keys(test))) == 1


def test_calibrate_scores_the_leak_free_split():
    src = (ROOT / "src" / "calibrate.py").read_text(encoding="utf-8")
    assert "ds.split_holdout(" in src
    assert "campaign.isin(" not in src, (
        "calibrate.py filters on the campaign label again, which re-admits "
        "the duplicated and leaked rows")


def test_the_rescore_matches_its_preregistration():
    """Pre-registered: training unchanged so the fill law must not move;
    holdout 32; thresholds unchanged; the diagnostic is labelled as one."""
    cal = json.loads((ROOT / "results" / "calibration.json").read_text())
    assert cal["thresholds"] == {"V1_Tout_MAE_K": 1.0, "V1_Tout_MAE_target_K": 0.5,
                                 "V1_Q_MAPE_pct": 6.0, "V2_evap_MAPE_pct": 8.0}
    assert cal["fill_c"] == pytest.approx(1.2400648125849212, abs=1e-12)
    assert cal["fill_n"] == pytest.approx(-0.5013981003349164, abs=1e-12)
    assert cal["TRAIN"]["n_points"] == 115
    assert cal["HOLDOUT"]["n_points"] == 32
    assert cal["data"]["duplicate_rows_removed"] == 18
    assert cal["data"]["holdout_rows_removed_because_in_training"] == 1
    assert "diagnostic_leave_one_campaign_out_NOT_A_GATE" in cal
    ho = cal["HOLDOUT"]
    assert cal["verdict"] == {
        "V1_Tout": ho["Tout_MAE_K"] <= 1.0,
        "V1_Q": ho["Q_MAPE_pct"] <= 6.0,
        "V2_evap": ho["evap_MAPE_pct"] <= 8.0,
    }, "a verdict disagrees with its own number"
