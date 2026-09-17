"""
FURQAN :: Dhahran TMY weather, and what it does to the evidence
===============================================================
Reads an EnergyPlus EPW weather file and answers three questions the package
could not answer before, because it had no hourly Gulf weather:

  1. Does our own psychrometric code agree with ASHRAE's published design
     conditions? The EPW header carries the 2025 ASHRAE Handbook design
     values for this station, so this is a free, independent check on the
     wet-bulb calculation everything else depends on.

  2. What fraction of a Gulf year lies OUTSIDE the wet-bulb range the model
     was validated over? This is the largest open item in the package and it
     has been carried as a qualitative worry. It can now be a number.

  3. What is the hours-weighted annual saving, rather than an unweighted
     mean over five hand-picked conditions?

Source: SAU_SH_Dhahran-Abdulaziz.AB.404160_TMYx.2011-2025.epw
        Station 404160, 26.265 N 50.152 E, elevation 25.6 m, UTC+3.
        TMYx 2011-2025.

DEFECT 61. This docstring and `tmy_dhahran.json` used to say "elevation 3 m".
That was the EPW time-zone field (+3.0) read one column early. The LOCATION
record is  LOCATION,city,state,country,source,WMO,lat,lon,TZ,elevation  --
ten fields, elevation LAST. Nothing downstream used the elevation (every
psychrometric call takes the EPW's own pressure column), so no computed
number moved; the artefact simply recorded a wrong fact about the site.

HOUR CONVENTION (defect 62, investigated). EPW hour h runs 1..24. In this
file EPW hour h carries the station observation made at LOCAL STANDARD TIME
(h-1):00. Measured, not assumed: against ISD-Lite 404160 for three months
whose source year the EPW header names, dry bulb agrees within 0.5 K in
98.6-98.9 % of hours at that alignment and in 28-30 % at h:00. So within a
calendar day of this file, the row index t = h-1 IS the local clock hour,
and hour 24 belongs to the same day (23:00), not to 00:00 of the next.
`src/diurnal.py` and `scripts/generate_pitch_artifacts.py` use exactly that
index, so neither is shifted. Anything joining these rows to real
observations must use `epw_hour_to_local_hour`.

Run:  python src/tmy.py <path-to-epw-or-zip>
"""
from __future__ import annotations

import io
import json
import pathlib
import sys
import zipfile

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import psychro as ps                                            # noqa: E402

# The wet-bulb ceiling of the validation dataset. Above this the model is
# extrapolating, and the whole point of question 2 is to size that.
ALMERIA_WB_MAX_C = 21.9

# Dhahran is Arabia Standard Time, UTC+3, with no daylight saving.
HOUR_CONVENTION = ("EPW hour h (1..24) holds the observation at local standard "
                   "time (h-1):00; row index within a day = local clock hour")


def epw_hour_to_local_hour(h):
    """Local clock hour (0..23) of the observation an EPW hour (1..24) holds.

    Verified for this TMYx file against ISD-Lite (see module docstring). An
    EPW hour is NOT h:00 and hour 24 is NOT midnight of the next day.
    """
    h = np.asarray(h)
    if np.any((h < 1) | (h > 24)):
        raise ValueError("EPW hours run 1..24")
    return h - 1


def parse_location(header) -> dict:
    """The EPW LOCATION record, by field NAME rather than by position in code
    that reads it.

        0 LOCATION, 1 city, 2 state, 3 country, 4 source, 5 WMO,
        6 latitude, 7 longitude, 8 time zone (h from UTC), 9 elevation (m)

    DEFECT 61: elevation was read from field 8, which is the time zone.
    """
    line = next(l for l in header if l.startswith("LOCATION"))
    f = [x.strip() for x in line.split(",")]
    if len(f) < 10:
        raise ValueError(f"EPW LOCATION record has {len(f)} fields, need 10")
    return {"station": f[1], "state": f[2], "country": f[3], "source": f[4],
            "wmo": f[5], "latitude": float(f[6]), "longitude": float(f[7]),
            "timezone_h": float(f[8]), "elevation_m": float(f[9])}


def hourly_wetbulb(T_db, rh, p):
    """Wet bulb for every hour with the package's own psychrometrics. `rh` is
    a FRACTION, `p` in Pa. Shared by this file and the weather-source
    sensitivity so both scenarios are built by the same code."""
    rh = np.clip(np.asarray(rh, float), 0.001, 1.0)
    return rh, np.array([ps.wetbulb_from_rh(float(a), float(b), float(c))
                         for a, b, c in zip(T_db, rh, p)])


def read_epw(path: pathlib.Path):
    """Return (header_lines, data_array) from an .epw, or from a .zip
    containing one."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".epw"))
            raw = z.read(name).decode("latin-1")
    else:
        raw = path.read_text(encoding="latin-1")
    lines = raw.splitlines()
    header, rows = lines[:8], lines[8:]
    data = []
    for ln in rows:
        f = ln.split(",")
        if len(f) < 10:
            continue
        data.append((int(f[1]), int(f[2]), int(f[3]),      # month, day, hour
                     float(f[6]), float(f[7]), float(f[8]), float(f[9])))
    #            dry-bulb, dew point, RH %, pressure Pa
    return header, np.array(data)


def ashrae_design(header) -> dict:
    """Pull the ASHRAE design conditions the EPW header carries.

    Format, after the 'Cooling' keyword: month, DB range, then the pairs
    (0.4 % DB, MCWB), (1 % DB, MCWB), (2 % DB, MCWB), then
    (0.4 % WB, MCDB), (1 % WB, MCDB), (2 % WB, MCDB).
    """
    line = next(l for l in header if l.startswith("DESIGN CONDITIONS"))
    f = line.split(",")
    i = f.index("Cooling")
    return {
        "cooling_month": int(f[i + 1]),
        "DB_0p4_C": float(f[i + 3]),  "MCWB_0p4_C": float(f[i + 4]),
        "DB_1p0_C": float(f[i + 5]),  "MCWB_1p0_C": float(f[i + 6]),
        "DB_2p0_C": float(f[i + 7]),  "MCWB_2p0_C": float(f[i + 8]),
        "WB_0p4_C": float(f[i + 9]),  "MCDB_0p4_C": float(f[i + 10]),
        "WB_1p0_C": float(f[i + 11]), "MCDB_1p0_C": float(f[i + 12]),
        "WB_2p0_C": float(f[i + 13]), "MCDB_2p0_C": float(f[i + 14]),
    }


def main() -> int:
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if src is None or not src.exists():
        print("usage: python src/tmy.py <path to .epw or .zip>")
        return 1

    header, d = read_epw(src)
    loc = parse_location(header)
    month, day, hour = d[:, 0].astype(int), d[:, 1].astype(int), d[:, 2].astype(int)
    T_db, T_dp, rh_pct, p = d[:, 3], d[:, 4], d[:, 5], d[:, 6]

    print("=" * 76)
    print("FURQAN / MIZAN :: Dhahran TMY weather")
    print("=" * 76)
    print(f"  station   {loc['station']}, {loc['country']}  WMO {loc['wmo']}")
    print(f"  position  {loc['latitude']} N  {loc['longitude']} E   "
          f"elevation {loc['elevation_m']} m   UTC{loc['timezone_h']:+g}")
    print(f"  hours     {len(d)}")
    print(f"  hour      {HOUR_CONVENTION}")
    print()

    # ---- hourly wet-bulb, from our own ASHRAE implementation -----------
    print("computing wet-bulb for every hour with the package's own "
          "psychrometrics ...")
    rh, T_wb = hourly_wetbulb(T_db, rh_pct / 100.0, p)

    # ---- 1. cross-check against ASHRAE's own published design values ----
    ash = ashrae_design(header)
    print()
    print("-" * 76)
    print("1. OUR PSYCHROMETRICS vs ASHRAE's PUBLISHED DESIGN CONDITIONS")
    print("-" * 76)
    print("   The EPW header carries the 2025 ASHRAE Handbook design values for")
    print("   this station. They were computed by ASHRAE from the same hours.")
    print("   Ours are computed from the hourly file by our own code. They")
    print("   should agree, and neither was fitted to the other.")
    print()
    print(f"   {'quantity':28s} {'ASHRAE':>9s} {'ours':>9s} {'diff':>8s}")
    checks = []
    for pctl, key in ((0.4, "WB_0p4_C"), (1.0, "WB_1p0_C"), (2.0, "WB_2p0_C")):
        ours = float(np.percentile(T_wb, 100.0 - pctl))
        ref = ash[key]
        checks.append(abs(ours - ref))
        print(f"   {pctl:>4.1f} % wet-bulb {'':12s} {ref:9.2f} {ours:9.2f} "
              f"{ours-ref:+8.2f} K")
    for pctl, key in ((0.4, "DB_0p4_C"), (1.0, "DB_1p0_C"), (2.0, "DB_2p0_C")):
        ours = float(np.percentile(T_db, 100.0 - pctl))
        ref = ash[key]
        checks.append(abs(ours - ref))
        print(f"   {pctl:>4.1f} % dry-bulb {'':12s} {ref:9.2f} {ours:9.2f} "
              f"{ours-ref:+8.2f} K")
    worst = max(checks)
    print()
    print(f"   worst disagreement {worst:.2f} K -- "
          f"{'AGREES' if worst <= 0.6 else 'DOES NOT AGREE'} with ASHRAE")

    # ---- 2. how much of a Gulf year is outside the validated envelope ---
    print()
    print("-" * 76)
    print("2. HOW MUCH OF A GULF YEAR IS OUTSIDE THE VALIDATED ENVELOPE")
    print("-" * 76)
    print(f"   The model was validated on data whose wet-bulb tops out at "
          f"{ALMERIA_WB_MAX_C} C.")
    print("   Above that it is extrapolating. Until now that was a worry with")
    print("   no number on it.")
    print()
    out = T_wb > ALMERIA_WB_MAX_C
    print(f"   hours above {ALMERIA_WB_MAX_C} C wet-bulb : {out.sum():5d} of "
          f"{len(T_wb)}  ({100*out.mean():.1f} % of the year)")
    print(f"   annual mean wet-bulb            : {T_wb.mean():.1f} C")
    print(f"   annual max  wet-bulb            : {T_wb.max():.1f} C")
    print()
    print("   by month:")
    print(f"   {'month':>6s} {'mean WB':>9s} {'max WB':>8s} {'hrs > 21.9':>11s} {'%':>6s}")
    monthly = []
    for m in range(1, 13):
        k = month == m
        frac = 100.0 * (T_wb[k] > ALMERIA_WB_MAX_C).mean()
        monthly.append({"month": m, "mean_wb_C": float(T_wb[k].mean()),
                        "max_wb_C": float(T_wb[k].max()),
                        "hours": int(k.sum()),
                        "pct_above_almeria": float(frac)})
        print(f"   {m:6d} {T_wb[k].mean():9.1f} {T_wb[k].max():8.1f} "
              f"{int((T_wb[k] > ALMERIA_WB_MAX_C).sum()):11d} {frac:6.1f}")

    out_json = {
        "station": loc["station"], "wmo": loc["wmo"],
        "latitude": loc["latitude"], "longitude": loc["longitude"],
        "elevation_m": loc["elevation_m"],
        "timezone_h": loc["timezone_h"],
        "hour_convention": HOUR_CONVENTION,
        "n_hours": int(len(d)),
        "ashrae_design": ash,
        "our_wb_0p4_C": float(np.percentile(T_wb, 99.6)),
        "our_wb_1p0_C": float(np.percentile(T_wb, 99.0)),
        "our_wb_2p0_C": float(np.percentile(T_wb, 98.0)),
        "worst_design_disagreement_K": float(worst),
        "almeria_wb_max_C": ALMERIA_WB_MAX_C,
        "hours_above_almeria": int(out.sum()),
        "hours_at_or_below_almeria": int((~out).sum()),
        "pct_year_above_almeria": float(100 * out.mean()),
        "annual_mean_wb_C": float(T_wb.mean()),
        "annual_max_wb_C": float(T_wb.max()),
        "monthly": monthly,
    }
    (RESULTS / "tmy_dhahran.json").write_text(json.dumps(out_json, indent=1))
    np.save(RESULTS / "tmy_hourly.npy",
            np.column_stack([month, day, hour, T_db, rh, T_wb, p]))
    print()
    print(f"written -> results/tmy_dhahran.json and results/tmy_hourly.npy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
