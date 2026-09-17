"""Regression tests for the weather-input defects 60, 61 and 62.

60  the envelope split classified whole wet-bulb bins by their centroid, so a
    bin with a 21.38 C centroid and 266 hours above 21.9 C was booked as
    validated. The split must be hour by hour.
61  `tmy.py` read the EPW time-zone field (+3) as the station elevation.
62  the EPW hour convention: hour h holds the observation at local (h-1):00.
    Investigated; nothing was shifted. These tests pin the convention so a
    future consumer cannot silently assume h:00.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "src"))

import annual                                                   # noqa: E402
import tmy                                                      # noqa: E402

LIMIT = annual.ALMERIA_WB_MAX_C


# ---------------------------------------------------------------------------
# Defect 60
# ---------------------------------------------------------------------------
def test_defect_60_bins_never_straddle_the_envelope_edge():
    """The failure case in miniature: eight equal-hour bins over a year whose
    fifth bin has a centroid below the limit and a tail above it."""
    rng = np.random.default_rng(60)
    t_wb = np.concatenate([rng.uniform(5.0, 21.9, 5209),
                           rng.uniform(21.9001, 34.0, 3551)])
    rng.shuffle(t_wb)

    # the OLD rule, reproduced, does misclassify on this data
    old = np.array_split(np.argsort(t_wb), 8)
    straddling = [b for b in old
                  if t_wb[b].mean() <= LIMIT and (t_wb[b] > LIMIT).any()]
    assert straddling, "fixture no longer reproduces the defect-60 shape"

    bins = annual.envelope_bins(t_wb, 8, LIMIT)
    assert len(bins) == 8
    allidx = np.sort(np.concatenate(bins))
    assert np.array_equal(allidx, np.arange(t_wb.size)), "hours lost or doubled"
    for b in bins:
        above = t_wb[b] > LIMIT
        assert above.all() or not above.any(), "a bin straddles the edge"
    inside = sum(b.size for b in bins if (t_wb[b] <= LIMIT).all())
    assert inside == int((t_wb <= LIMIT).sum())


def test_defect_60_one_sided_years_are_handled():
    assert len(annual.envelope_bins(np.full(100, 10.0), 8)) == 8
    assert len(annual.envelope_bins(np.full(100, 30.0), 8)) == 8
    # a year with a handful of hot hours still gets its own bin
    t = np.concatenate([np.full(8755, 15.0), np.full(5, 25.0)])
    bins = annual.envelope_bins(t, 8)
    assert sum(1 for b in bins if (t[b] > LIMIT).all()) == 1


def test_defect_60_the_artefact_split_is_hour_by_hour():
    """The published split must equal the weather file's own hour counts."""
    hp, ap = RESULTS / "tmy_hourly.npy", RESULTS / "annual_dhahran.json"
    if not (hp.exists() and ap.exists()):
        pytest.skip("annual study not generated")
    h = np.load(hp)
    d = json.loads(ap.read_text(encoding="utf-8"))
    assert d.get("input_hourly_sha256") == annual.hourly_sha256(h), (
        "annual_dhahran.json was not computed from the current tmy_hourly.npy")
    above = int((h[:, 5] > LIMIT).sum())
    assert d["by_envelope"]["extrapolated"]["hours"] == above
    assert d["by_envelope"]["inside"]["hours"] == h.shape[0] - above
    assert d["hours_above_almeria"] == above
    for b in d["bins"]:
        assert b["pct_hours_above_almeria"] in (0.0, 100.0), (
            f"bin {b['bin']} is mixed: {b['pct_hours_above_almeria']:.1f} % "
            "of its hours are above the envelope")
        assert b["inside_validated_envelope"] == (b["pct_hours_above_almeria"] == 0.0)
    tp = RESULTS / "tmy_dhahran.json"
    if tp.exists():
        assert json.loads(tp.read_text())["hours_above_almeria"] == above


# ---------------------------------------------------------------------------
# Defect 61
# ---------------------------------------------------------------------------
def test_defect_61_elevation_is_the_tenth_location_field():
    header = ["LOCATION,Dhahran-Abdulaziz.AB,SH,SAU,SRC-TMYx,404160,"
              "26.26500,50.15200,3.0,25.6"]
    loc = tmy.parse_location(header)
    assert loc["timezone_h"] == 3.0
    assert loc["elevation_m"] == 25.6
    assert loc["wmo"] == "404160"
    with pytest.raises(ValueError):
        tmy.parse_location(["LOCATION,a,b,c,d,e,1.0,2.0,3.0"])


def test_defect_61_the_artefact_records_the_true_elevation():
    tp = RESULTS / "tmy_dhahran.json"
    if not tp.exists():
        pytest.skip("tmy_dhahran.json not generated")
    t = json.loads(tp.read_text())
    assert t["elevation_m"] == pytest.approx(25.6)
    assert t["timezone_h"] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Defect 62 (investigated; convention pinned)
# ---------------------------------------------------------------------------
def test_defect_62_epw_hour_maps_to_the_previous_clock_hour():
    assert tmy.epw_hour_to_local_hour(1) == 0
    assert tmy.epw_hour_to_local_hour(24) == 23
    assert np.array_equal(tmy.epw_hour_to_local_hour(np.arange(1, 25)),
                          np.arange(24))
    for bad in (0, 25):
        with pytest.raises(ValueError):
            tmy.epw_hour_to_local_hour(bad)


def test_defect_62_diurnal_row_index_is_the_local_clock_hour():
    """`diurnal.py` labels row t of the chosen day as hour t and calls
    t < 6 or t >= 21 night. That is right only if the day's rows are EPW
    hours 1..24 in order, i.e. t = h - 1 = local clock hour."""
    hp = RESULTS / "tmy_hourly.npy"
    if not hp.exists():
        pytest.skip("tmy_hourly.npy not generated")
    import diurnal
    h = np.load(hp)
    idx, _ = diurnal.pick_summer_day(h)
    assert np.array_equal(h[idx, 2].astype(int), np.arange(1, 25))
    assert np.array_equal(tmy.epw_hour_to_local_hour(h[idx, 2].astype(int)),
                          np.arange(24))
    assert len({(int(h[i, 0]), int(h[i, 1])) for i in idx}) == 1, (
        "hour 24 must belong to the same calendar day (local 23:00)")
    tp = RESULTS / "tmy_dhahran.json"
    if tp.exists():
        assert "(h-1):00" in json.loads(tp.read_text())["hour_convention"]
