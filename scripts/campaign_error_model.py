"""
MIZAN :: the per-campaign evaporation error model behind the water-gate bars
============================================================================
`src/gate_uncertainty.CAMPAIGN_FITS` and `scripts/gate_uncertainty.py`'s
`CAMPAIGN_SLOPES` / `CAMPAIGN_RESID_SD` were typed constants with no generator
(defect 74's shape). This is the generator.

For each campaign, on its distinct rows (campaign MEMBERSHIP, so the one row
Exp1 and Exp2 share counts in both, as it always did), the published fill law
predicts evaporation and the relative error is regressed on fan speed:

    rel[%] = 100 (predicted - measured) / measured = a + k * w_fan[%]

with the residual sd taken about that line (population sd, ddof 0).

The method was fixed by reproducing the stored constants on the sea-level law
at 101,325 Pa before it was run on the site-pressure law
(docs/staged/plant_scale_site_pressure_preregistration.md, section 5). That
reproduction is repeated here every run and the script refuses to write if it
fails, so the constants cannot drift from their method again.

Run:  python scripts/campaign_error_model.py
Writes: results/campaign_error_model.json
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
RESULTS = ROOT / "results"

import calibrate as cb  # noqa: E402
import dataset as ds  # noqa: E402

CAMPAIGNS = ("Exp1", "Exp2")       # defect 70: Exp3 repeats Exp1 rows 0-16

# The constants as they stood before defect 79's law reached them, and the
# precision they were printed at. The reproduction check is held to that.
SEA_LEVEL_STORED = {
    "Exp1": {"n": 33, "offset_pct": -0.52, "slope_pct_per_fanpct": -0.2002,
             "residual_sd_pp": 6.27},
    "Exp2": {"n": 115, "offset_pct": 9.06, "slope_pct_per_fanpct": -0.3660,
             "residual_sd_pp": 11.63},
}


def fits(c, n, p):
    df = ds.derive(ds.load_all())
    _t, evap, ok = cb.predict(df, c, n, p=p)
    meas = df["m_evap_meas"].values
    rel = 100.0 * (evap - meas) / meas
    out = {}
    for camp in CAMPAIGNS:
        g = (ds.in_campaigns(df, [camp]).values & ok & np.isfinite(rel)
             & (meas > 0))
        x, y = df["w_fan"].values[g], rel[g]
        k, a = np.polyfit(x, y, 1)
        r = y - (a + k * x)
        out[camp] = {"n": int(g.sum()), "offset_pct": float(a),
                     "slope_pct_per_fanpct": float(k),
                     "residual_sd_pp": float(r.std(ddof=0))}
    return out


def reproduces(got, want):
    for camp, w in want.items():
        g = got[camp]
        if g["n"] != w["n"]:
            return False
        if round(g["offset_pct"], 2) != w["offset_pct"]:
            return False
        if round(g["slope_pct_per_fanpct"], 4) != w["slope_pct_per_fanpct"]:
            return False
        if round(g["residual_sd_pp"], 2) != w["residual_sd_pp"]:
            return False
    return True


def main() -> int:
    ref = json.loads((RESULTS / "calibration_sea_level_reference.json")
                     .read_text(encoding="utf-8"))
    sea = fits(ref["fill_c"], ref["fill_n"], ref["p_Pa"])
    ok = reproduces(sea, SEA_LEVEL_STORED)
    print("sea-level law at 101,325 Pa, reproduction of the stored constants:")
    for camp, f in sea.items():
        print(f"   {camp}  n {f['n']:3d}  a {f['offset_pct']:+7.2f} %  "
              f"k {f['slope_pct_per_fanpct']:+.4f} %/fan%  "
              f"sd {f['residual_sd_pp']:6.2f} pp")
    print("   REPRODUCED" if ok else "   NOT REPRODUCED")
    if not ok:
        print("refusing to write: the method no longer reproduces its own "
              "stored constants")
        return 1

    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    p = cal["site_pressure"]["p_Pa"]
    cur = fits(cal["fill_c"], cal["fill_n"], p)
    print(f"\ncurrent law c {cal['fill_c']:.4f}, n {cal['fill_n']:.4f}, "
          f"at {p:,.0f} Pa:")
    for camp, f in cur.items():
        print(f"   {camp}  n {f['n']:3d}  a {f['offset_pct']:+7.2f} %  "
              f"k {f['slope_pct_per_fanpct']:+.4f} %/fan%  "
              f"sd {f['residual_sd_pp']:6.2f} pp")
    (RESULTS / "campaign_error_model.json").write_text(json.dumps({
        "method": "rel = 100 (pred - meas)/meas on each campaign's distinct "
                  "rows by membership; OLS on w_fan; residual sd ddof 0",
        "fill_c": cal["fill_c"], "fill_n": cal["fill_n"], "p_Pa": p,
        "campaigns": cur,
        "sea_level_reproduction_NOT_LIVE": {"p_Pa": ref["p_Pa"],
                                            "reproduced": ok,
                                            "campaigns": sea},
    }, indent=1), encoding="utf-8")
    print("\nwritten -> results/campaign_error_model.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
