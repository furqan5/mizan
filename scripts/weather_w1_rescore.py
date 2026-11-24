"""
MIZAN :: the W1 weather scenario re-scored without the raw ISD-Lite files
=========================================================================
`src/weather_sensitivity.py --stage build` needs the raw ISD-Lite 404160
files, which are not on this laptop. W1 itself needs only two inputs: the
TMYx hourly array and the month x local-hour dew-point climatology, and the
climatology is committed (data/weather/isd_404160/
dewpoint_climatology_2011_2024.csv). This rebuilds W1 from those two through
the registered `weather_sensitivity.build_w1` and scores it with the
registered `annual.run_annual`. Nothing else is touched.

The one difference from the registered build is that the committed CSV
holds the climatology at four decimals (0.0001 K), so the rebuilt array is
not byte-identical to the one the 17 September run scored. Whether that
matters is settled empirically, by the rule in
docs/staged/plant_scale_site_pressure_addendum_20261124.md section 3: on the
sea-level fill law the rebuilt W1 must reproduce the stored W1 whole-year
and per-envelope water and energy figures to 0.01 points, or it is not used.

Run:     python scripts/weather_w1_rescore.py
Writes:  results/annual_weather_w1_rescore.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "src"))

import annual                                                   # noqa: E402
import weather_sensitivity as ws                                # noqa: E402

CLIM = ws.ISD / "dewpoint_climatology_2011_2024.csv"
ADDENDUM = ROOT / "docs" / "staged" / "plant_scale_site_pressure_addendum_20261124.md"
TOL_PTS = 0.01
COMPARED = ("annual_water_pct_ratio_of_totals", "annual_energy_pct_ratio_of_totals",
            "annual_cost_pct_ratio_of_totals")


def load_climatology() -> np.ndarray:
    clim = np.full((12, 24), np.nan)
    with open(CLIM, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            clim[int(r["month"]) - 1, int(r["local_hour"])] = float(r["mean_dewpoint_C"])
    if np.isnan(clim).any():
        raise SystemExit(f"{CLIM} does not fill all 12 x 24 cells")
    return clim


def envelope_figures(r: dict) -> dict:
    out = {k: r[k] for k in COMPARED}
    for name, e in r["by_envelope"].items():
        for k, v in e.items():
            if isinstance(v, (int, float)) and k.endswith("_pct"):
                out[f"{name}:{k}"] = v
    return out


def main() -> int:
    cal = json.loads((RESULTS / "calibration.json").read_text(encoding="utf-8"))
    h0 = np.load(RESULTS / "tmy_hourly.npy")
    h1, info = ws.build_w1(h0, load_climatology())

    stored_all = json.loads((RESULTS / "annual_weather_sensitivity.json").read_text(encoding="utf-8"))
    stored = stored_all["scenarios"]["W1"]
    print(f"fill law c {cal['fill_c']:.4f}, n {cal['fill_n']:.4f}")
    print(f"rebuilt W1 sha256 {annual.hourly_sha256(h1)[:16]}..., stored "
          f"{stored['weather']['input_hourly_sha256'][:16]}..., "
          f"Td capped at T_db in {info['td_capped_at_db_hours']} h "
          f"(stored {stored['weather'].get('td_capped_at_db_hours')})")

    r = annual.run_annual(h1, title="W1 rebuilt from the committed climatology")
    now, before = envelope_figures(r), envelope_figures(stored["annual"])
    deltas = {k: now[k] - before[k] for k in now if k in before}
    worst = max(abs(v) for v in deltas.values())

    out = {
        "what": ("W1 (TMYx dry bulb and pressure, ISD 404160 dew-point climatology "
                 "2011-2024) rebuilt from the committed climatology CSV and scored "
                 "by annual.run_annual on the fill law in results/calibration.json"),
        "addendum": str(ADDENDUM.relative_to(ROOT)).replace("\\", "/"),
        "addendum_sha256": (hashlib.sha256(ADDENDUM.read_bytes()).hexdigest()
                            if ADDENDUM.exists() else None),
        "climatology_csv_sha256": hashlib.sha256(CLIM.read_bytes()).hexdigest(),
        "input_hourly_sha256": annual.hourly_sha256(h1),
        "stored_w1_input_hourly_sha256": stored["weather"]["input_hourly_sha256"],
        "td_capped_at_db_hours": info["td_capped_at_db_hours"],
        "fill_c": cal["fill_c"], "fill_n": cal["fill_n"],
        "annual": {k: r[k] for k in (
            "annual_water_pct_ratio_of_totals", "annual_energy_pct_ratio_of_totals",
            "annual_cost_pct_ratio_of_totals", "fraction_inside_validated_envelope",
            "hours_above_almeria", "unsolved_hours", "n_bins")}
                  | {"by_envelope": r["by_envelope"], "bins": r["bins"]},
        "against_stored_w1_pts": deltas,
        "max_abs_difference_from_stored_pts": worst,
        "reproduces_stored_within_0p01": worst <= TOL_PTS,
        "note": ("Under the sea-level law 'reproduces_stored_within_0p01' is the "
                 "addendum's validity test for the rebuild. Under the site-pressure "
                 "law the differences are the effect of the fill law."),
    }
    (RESULTS / "annual_weather_w1_rescore.json").write_text(json.dumps(out, indent=1),
                                                            encoding="utf-8")
    print(f"\nlargest difference from the stored W1 figures: {worst:.4f} points")
    for k, v in deltas.items():
        print(f"   {k:60s} {before[k]:+8.3f} -> {now[k]:+8.3f}  ({v:+.4f})")
    print("written -> results/annual_weather_w1_rescore.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
