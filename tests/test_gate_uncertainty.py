"""The error model behind the water gates, and the reason V7's margin is void.

Gate V7 returned 15.01 % against a 15.00 % threshold. A 0.01-point margin is
meaningful only if the error is smaller than 0.01 points. It is not: the
interval is several percentage points wide, and these tests hold the error
model that says so to the data it was measured from.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
RESULTS = ROOT / "results"


@pytest.fixture(scope="module")
def gu():
    import gate_uncertainty as m
    return m


@pytest.fixture(scope="module")
def measured():
    """Recompute the per-campaign residual structure from the raw dataset.

    The point of recomputing rather than trusting the constants is that a
    hand-typed error model is the defect-12 shape: a number in a file that
    nobody can trace back to a measurement.
    """
    import warnings
    warnings.filterwarnings("ignore")
    import dataset as ds
    import calibrate as cal

    cfg = json.loads((RESULTS / "calibration.json").read_text())
    d = ds.derive(ds.load_all())
    _T, ev, ok = cal.predict(d, cfg["fill_c"], cfg["fill_n"])
    meas = d["m_evap_meas"].values
    m = ok & np.isfinite(ev) & (meas > 0)
    rel = (ev - meas) / meas * 100.0
    fan = d["w_fan"].values
    camp = d["campaign"].values

    out = {}
    for c in ("Exp1", "Exp2", "Exp3"):
        s = m & (camp == c)
        k, a = np.polyfit(fan[s], rel[s], 1)
        resid = rel[s] - (a + k * fan[s])
        out[c] = {"k": float(k), "a": float(a), "sd": float(resid.std()),
                  "n": int(s.sum())}
    return out


# ---------------------------------------------------------------------------
# the error model must trace to the data
# ---------------------------------------------------------------------------

def test_the_campaign_slopes_are_the_measured_ones(gu, measured):
    for c, got in measured.items():
        assert gu.CAMPAIGN_SLOPES[c] == pytest.approx(got["k"], abs=5e-4), c
        assert gu.CAMPAIGN_RESID_SD[c] == pytest.approx(got["sd"], abs=0.02), c


def test_the_slopes_disagree_in_sign_so_the_bias_cannot_be_corrected(measured):
    """If every campaign agreed on the sign, the fan dependence would be a
    physics error worth fixing. They do not, so it can only be propagated.
    This is the finding that makes an interval necessary rather than a
    correction."""
    ks = [v["k"] for v in measured.values()]
    assert min(ks) < 0 < max(ks), ks


def test_the_offset_varies_far_more_than_the_slope(measured):
    """The offset is what cancels in a ratio and the slope is what does not.
    The offset being the larger term is why a water SAVING is far better
    determined than an absolute water VOLUME -- and why WUE, m3/day and the
    side-stream break-even carry the full error while V5 and V7 do not."""
    a = np.array([v["a"] for v in measured.values()])
    k = np.array([v["k"] for v in measured.values()])
    assert a.std() > 5.0, a
    assert k.std() < 0.5, k


# ---------------------------------------------------------------------------
# the propagation
# ---------------------------------------------------------------------------

def test_no_fan_change_means_the_error_still_has_scatter_but_no_bias(gu):
    """With the fan unchanged the slope term vanishes and only the
    independent residual scatter remains, so the saving is unbiased."""
    rng = np.random.default_rng(1)
    s = gu.sample_saving(30.0, 27.0, 80.0, 80.0, rng, n=8000)
    point = 100.0 * (30.0 - 27.0) / 30.0
    assert np.median(s) == pytest.approx(point, abs=1.5)


def test_a_larger_fan_change_grows_the_non_cancelling_bias(gu):
    """Written after the first version of this test asserted the wrong thing.

    The INTERVAL WIDTH is dominated by each campaign's residual scatter,
    which is applied independently to the baseline and the optimised case and
    does not depend on the fan at all. So the total width is roughly flat in
    fan change, and asserting otherwise was simply false.

    What does grow with fan change is the part that cannot cancel: the spread
    of `k * delta_fan` across campaigns, because the campaigns disagree on k.
    That is the quantity the whole error model exists to carry, and it is
    what this test now pins.
    """
    ks = np.array(list(gu.CAMPAIGN_SLOPES.values()))
    prev = -1.0
    for d_fan in (0.0, 10.0, 24.0, 50.0):
        spread = (ks * d_fan).std()
        assert spread >= prev, (d_fan, spread)
        prev = spread
    # at the fan change the gates actually use, it is several points
    assert (ks * 24.0).std() > 2.0, (ks * 24.0).std()
    assert (ks * 0.0).std() == 0.0


def test_the_v7_margin_is_inside_its_own_error(gu):
    """THE RESULT. V7 cleared a 15 % threshold by 0.01 points. The
    probability that the true value clears it is near a coin toss, so the
    verdict carries no information and must never be quoted alone."""
    p = RESULTS / "gate_uncertainty.json"
    if not p.exists():
        pytest.skip("run scripts/gate_uncertainty.py first")
    g = {r["gate"]: r for r in json.loads(p.read_text())["gates"]}
    v7 = next(v for k, v in g.items() if k.startswith("V7"))

    assert v7["point_estimate_pct"] == pytest.approx(15.01, abs=0.05)
    assert v7["sd_pct"] > 2.0, (
        "if the interval were tight the margin would be meaningful and this "
        "test should be deleted")
    assert 0.2 < v7["p_exceeds_15"] < 0.8, (
        f"P(true >= 15 %) is {v7['p_exceeds_15']:.2f}; a threshold verdict "
        f"is only informative when this is near 0 or near 1")


def test_twenty_percent_is_not_distinguishable_from_fifteen(gu):
    """Answers the question directly: can this package tell a 15 % result
    from a 20 % one? It cannot, and the probability mass says so."""
    p = RESULTS / "gate_uncertainty.json"
    if not p.exists():
        pytest.skip("run scripts/gate_uncertainty.py first")
    g = {r["gate"]: r for r in json.loads(p.read_text())["gates"]}
    v7 = next(v for k, v in g.items() if k.startswith("V7"))
    assert v7["p_exceeds_20"] > 0.02, (
        "20 % is inside the error bar of the 15.01 % result, so 'improve it "
        "to 20 %' is not a measurable objective with this instrument")
    assert v7["ci95_high_pct"] > 20.0


def test_v5_interval_reaches_below_zero(gu):
    """The uncomfortable half. V5's 4.38 % is small enough relative to its
    error that the interval includes the optimiser using MORE water than the
    baseline. Reported because it is true."""
    p = RESULTS / "gate_uncertainty.json"
    if not p.exists():
        pytest.skip("run scripts/gate_uncertainty.py first")
    g = {r["gate"]: r for r in json.loads(p.read_text())["gates"]}
    v5 = next(v for k, v in g.items() if k.startswith("V5"))
    assert v5["ci95_low_pct"] < 0.0, v5["ci95_low_pct"]
    assert v5["p_exceeds_15"] < 0.10
