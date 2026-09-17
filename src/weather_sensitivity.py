"""
MIZAN :: weather-source sensitivity of the annual study
=======================================================
Pre-registered in docs/staged/weather_source_preregistration.md, committed
before this script was first run. Read that first; this file implements it
and must not be tuned against its own output.

Why. An independent cross-check (16-17 Sep 2026) found that the Dhahran TMYx
file behind every annual number matches station 404160's dry bulb within
0.58 K in every month, but its dew point is up to +8.63 K wetter than the
station climatology and matches no archived report. Which humidity a coastal
plant sees is not settled, so neither source is declared the truth. Headline
claims must hold under both W0 and W1.

  W0  the TMYx year, as `src/annual.py` already scores it (after defect 60)
  W1  the same 8,760 TMYx hours, dry bulb and pressure kept, dew point
      replaced by the ISD-Lite 404160 month x local-hour climatology 2011-2024
  W2  a complete station year, the one with the median hours above 21.9 C
      (descriptive; cannot change a verdict)

Stages
  python src/weather_sensitivity.py --stage build   # data, harness checks
  python src/weather_sensitivity.py --stage run     # controller, verdicts
`build` needs the raw ISD-Lite files: python data/weather/isd_404160/fetch.py
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
ISD = ROOT / "data" / "weather" / "isd_404160"
RAW = ISD / "raw"
LOCAL = RESULTS / "weather_scenarios_local"          # git-ignored arrays
PREREG = ROOT / "docs" / "staged" / "weather_source_preregistration.md"
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import psychro as ps                                            # noqa: E402
import tmy                                                      # noqa: E402

YEARS = list(range(2011, 2025))
UTC_OFFSET_H = 3                     # Arabia Standard Time, no DST
LIMIT = 21.9
ELEVATION_M = 25.6                   # defect 61
# ASHRAE Fundamentals 2017 Ch.1 Eq. (3), standard atmosphere at elevation.
P_STATION_PA = 101325.0 * (1.0 - 2.25577e-5 * ELEVATION_M) ** 5.2559
MIN_OBS_PER_YEAR_CELL = 10
MIN_YEARS_PER_CELL = 7
INTERP_MAX_GAP_H = 3
COMPLETE_YEAR_MIN = 0.85
COMPLETE_MONTH_MIN = 0.60
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


# --------------------------------------------------------------------------
# ISD-Lite
# --------------------------------------------------------------------------
def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_isd_lite(path: pathlib.Path, year: int):
    """Parse one ISD-Lite file. Returns UTC datetime64[h], T, Td (NaN when
    missing). Harness HW4: 12 integer fields per line, year field = file."""
    t_utc, T, Td = [], [], []
    with gzip.open(path, "rt") as fh:
        for n, ln in enumerate(fh, 1):
            f = ln.split()
            if len(f) != 12:
                raise ValueError(f"{path.name}:{n} has {len(f)} fields")
            y, m, d, hh, t, td = (int(x) for x in f[:6])
            if y != year:
                raise ValueError(f"{path.name}:{n} year {y} != {year}")
            t_utc.append(f"{y:04d}-{m:02d}-{d:02d}T{hh:02d}")
            T.append(np.nan if t == -9999 else t / 10.0)
            Td.append(np.nan if td == -9999 else td / 10.0)
    return (np.array(t_utc, dtype="datetime64[h]"), np.array(T), np.array(Td))


def load_station() -> dict:
    """All 2011-2024 observations on LOCAL time, verified against SOURCES."""
    man = json.loads((ISD / "SOURCES.json").read_text(encoding="utf-8"))["files"]
    ts, Ts, Tds = [], [], []
    for ent in man:
        p = RAW / ent["file"]
        if not p.exists():
            raise SystemExit(f"{p} missing -- run data/weather/isd_404160/fetch.py")
        if _sha(p) != ent["sha256"]:
            raise SystemExit(f"{p.name}: SHA-256 does not match SOURCES.json")
        t, T, Td = read_isd_lite(p, ent["year"])
        ts.append(t); Ts.append(T); Tds.append(Td)
    t_local = np.concatenate(ts) + np.timedelta64(UTC_OFFSET_H, "h")
    T, Td = np.concatenate(Ts), np.concatenate(Tds)
    # one observation per local hour; keep the first
    _, first = np.unique(t_local, return_index=True)
    dup = t_local.size - first.size
    first = np.sort(first)
    t_local, T, Td = t_local[first], T[first], Td[first]
    both = np.isfinite(T) & np.isfinite(Td)
    excluded = both & (Td > T + 0.05)
    valid = both & ~excluded
    Y = t_local.astype("datetime64[Y]").astype(int) + 1970
    M = t_local.astype("datetime64[M]").astype(int) % 12 + 1
    H = (t_local - t_local.astype("datetime64[D]")).astype(int)
    return {"t": t_local, "T": T, "Td": Td, "valid": valid, "Y": Y, "M": M,
            "H": H, "n_records": int(sum(x.size for x in ts)),
            "n_duplicate_local_hours": int(dup),
            "n_td_above_t_excluded": int(excluded.sum()),
            "files": [{"file": e["file"], "sha256": e["sha256"]} for e in man]}


def climatology(st: dict, var: str):
    """Month x local-hour mean of `var` over 2011-2024: the mean of per-year
    cell means (each year >= MIN_OBS_PER_YEAR_CELL valid obs), valid when
    >= MIN_YEARS_PER_CELL years qualify. Invalid cells are filled by linear
    interpolation round the 24-hour circle within the month."""
    x, v, Y, M, H = st[var], st["valid"], st["Y"], st["M"], st["H"]
    inyr = (Y >= YEARS[0]) & (Y <= YEARS[-1]) & v
    clim = np.full((12, 24), np.nan)
    nyears = np.zeros((12, 24), int)
    key = (M[inyr] - 1) * 24 * 100 + H[inyr] * 100 + (Y[inyr] - 2000)
    xs = x[inyr]
    uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    sums = np.bincount(inv, weights=xs)
    for k, s, c in zip(uk, sums, cnt):
        if c < MIN_OBS_PER_YEAR_CELL:
            continue
        cell = k // 100
        m, hh = cell // 24, cell % 24
        if np.isnan(clim[m, hh]):
            clim[m, hh] = 0.0
        clim[m, hh] += s / c
        nyears[m, hh] += 1
    clim = np.where(nyears >= MIN_YEARS_PER_CELL, clim / np.maximum(nyears, 1),
                    np.nan)
    filled = np.isnan(clim)
    for m in range(12):
        ok = np.flatnonzero(~filled[m])
        if ok.size < 2:
            raise SystemExit(f"month {m+1}: fewer than 2 valid {var} cells")
        for hh in np.flatnonzero(filled[m]):
            clim[m, hh] = np.interp(hh, np.concatenate([ok - 24, ok, ok + 24]),
                                    np.tile(clim[m, ok], 3))
    return clim, nyears, filled


# --------------------------------------------------------------------------
# psychrometrics
# --------------------------------------------------------------------------
def rh_from_dewpoint(T_db, Td):
    """RH as a FRACTION, pv/pws(T), the definition tmy.py's rh column uses."""
    return ps.sat_vapour_pressure(Td) / ps.sat_vapour_pressure(T_db)


def dewpoint_from_rh(T_db, rh):
    """Vectorised inversion of pws(Td) = rh * pws(T), by bisection."""
    pv = np.asarray(rh) * ps.sat_vapour_pressure(T_db)
    lo, hi = np.full_like(pv, -60.0), np.asarray(T_db, float) + 1e-9
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        up = ps.sat_vapour_pressure(mid) < pv
        lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
    return 0.5 * (lo + hi)


def wetbulb_fast(T_db, rh, p):
    """Vectorised bisection on the SAME ASHRAE Eqs. (20)/(33) psychro.py
    inverts. Used only to rank candidate W2 years; every scenario array is
    built with tmy.hourly_wetbulb, and the two are compared (HW6)."""
    T_db = np.asarray(T_db, float)
    W = ps.humidity_ratio_from_rh(T_db, np.clip(rh, 0.001, 1.0), p)
    lo, hi = np.full_like(T_db, -60.0), T_db.copy()
    sat = ps.humidity_ratio_from_wetbulb(T_db, hi, p) - W < 0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        up = ps.humidity_ratio_from_wetbulb(T_db, mid, p) - W < 0
        lo, hi = np.where(up, mid, lo), np.where(up, hi, mid)
    return np.where(sat, T_db, 0.5 * (lo + hi))


def summarise(h: np.ndarray) -> dict:
    month, T_db, rh, wb = h[:, 0].astype(int), h[:, 3], h[:, 4], h[:, 5]
    td = dewpoint_from_rh(T_db, rh)
    above = wb > LIMIT
    return {
        "hours": int(h.shape[0]),
        "hours_above_21p9": int(above.sum()),
        "pct_above_21p9": float(100.0 * above.mean()),
        "annual_mean_wb_C": float(wb.mean()),
        "wb_0p4_1p0_2p0_C": [float(np.percentile(wb, q)) for q in (99.6, 99.0, 98.0)],
        "monthly_mean_db_C": [float(T_db[month == m].mean()) for m in range(1, 13)],
        "monthly_mean_td_C": [float(td[month == m].mean()) for m in range(1, 13)],
        "monthly_mean_wb_C": [float(wb[month == m].mean()) for m in range(1, 13)],
        "monthly_hours_above_21p9": [int(above[month == m].sum()) for m in range(1, 13)],
    }


# --------------------------------------------------------------------------
# scenarios
# --------------------------------------------------------------------------
def build_w1(h0: np.ndarray, clim_td: np.ndarray):
    month, hour = h0[:, 0].astype(int), h0[:, 2].astype(int)
    T_db, p = h0[:, 3], h0[:, 6]
    k = tmy.epw_hour_to_local_hour(hour)                  # defect 62
    td = clim_td[month - 1, k]
    capped = td > T_db
    td = np.minimum(td, T_db)
    rh, wb = tmy.hourly_wetbulb(T_db, rh_from_dewpoint(T_db, td), p)
    h1 = np.column_stack([h0[:, 0], h0[:, 1], h0[:, 2], T_db, rh, wb, p])
    return h1, {"td_capped_at_db_hours": int(capped.sum())}


def station_year(st: dict, year: int, clim_t, clim_td):
    """A filled 8,760-h local-time year in the tmy_hourly.npy layout, with
    wet bulb from `wetbulb_fast`. Returns (array, info)."""
    start = np.datetime64(f"{year}-01-01T00", "h")
    grid = np.arange(start, np.datetime64(f"{year+1}-01-01T00", "h"),
                     np.timedelta64(1, "h"))
    n = grid.size
    T = np.full(n, np.nan); Td = np.full(n, np.nan)
    sel = st["valid"] & (st["t"] >= grid[0]) & (st["t"] <= grid[-1])
    pos = (st["t"][sel] - start).astype(int)
    T[pos], Td[pos] = st["T"][sel], st["Td"][sel]
    M = grid.astype("datetime64[M]").astype(int) % 12 + 1
    D = (grid.astype("datetime64[D]") - grid.astype("datetime64[M]")).astype(int) + 1
    Hh = (grid - grid.astype("datetime64[D]")).astype(int)
    keep = ~((M == 2) & (D == 29))
    obs = np.isfinite(T)

    cov_year = float(obs[keep].mean())
    cov_month = [float(obs[keep & (M == m)].mean()) for m in range(1, 13)]
    complete = cov_year >= COMPLETE_YEAR_MIN and min(cov_month) >= COMPLETE_MONTH_MIN

    # 1. runs of <= INTERP_MAX_GAP_H missing hours, bounded on both sides
    n_interp = n_own = n_clim = 0
    miss = ~obs
    i = 0
    while i < n:
        if not miss[i]:
            i += 1
            continue
        j = i
        while j < n and miss[j]:
            j += 1
        if i > 0 and j < n and (j - i) <= INTERP_MAX_GAP_H:
            for arr in (T, Td):
                arr[i:j] = np.interp(np.arange(i, j), [i - 1, j], [arr[i - 1], arr[j]])
            n_interp += j - i
        i = j
    # 2. this year's own month x hour mean, else 3. the 2011-2024 climatology
    still = np.flatnonzero(np.isnan(T))
    for idx in still:
        m, hh = M[idx], Hh[idx]
        cell = obs & (M == m) & (Hh == hh)
        if cell.sum() >= MIN_OBS_PER_YEAR_CELL:
            T[idx], Td[idx] = np.nanmean(np.where(cell, T, np.nan)), \
                np.nanmean(np.where(cell, Td, np.nan))
            n_own += 1
        else:
            T[idx], Td[idx] = clim_t[m - 1, hh], clim_td[m - 1, hh]
            n_clim += 1
    capped = Td > T
    Td = np.minimum(Td, T)
    T, Td, M, D, Hh, miss = T[keep], Td[keep], M[keep], D[keep], Hh[keep], miss[keep]
    p = np.full(T.size, P_STATION_PA)
    rh = np.clip(rh_from_dewpoint(T, Td), 0.001, 1.0)
    wb = wetbulb_fast(T, rh, p)
    h = np.column_stack([M, D, Hh + 1, T, rh, wb, p]).astype(float)
    info = {"year": year, "coverage_year": cov_year, "coverage_min_month": min(cov_month),
            "complete": bool(complete), "filled_interp_h": n_interp,
            "filled_own_cell_h": n_own, "filled_climatology_h": n_clim,
            "td_capped_at_db_hours": int(capped.sum()),
            "hours_above_21p9": int((wb > LIMIT).sum())}
    return h, info


def select_median_year(infos):
    cand = sorted((i for i in infos if i["complete"]),
                  key=lambda i: (i["hours_above_21p9"], i["year"]))
    if len(cand) < 3:
        return None
    return cand[(len(cand) - 1) // 2]["year"]


# --------------------------------------------------------------------------
def stage_build() -> int:
    LOCAL.mkdir(parents=True, exist_ok=True)
    st = load_station()
    print(f"ISD-Lite 404160: {st['n_records']} records, "
          f"{st['n_duplicate_local_hours']} duplicate local hours, "
          f"{st['n_td_above_t_excluded']} Td>T excluded, "
          f"{int(st['valid'].sum())} valid (T,Td) hours")
    clim_td, ny_td, fill_td = climatology(st, "Td")
    clim_t, ny_t, fill_t = climatology(st, "T")
    with open(ISD / "dewpoint_climatology_2011_2024.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["month", "local_hour", "mean_dewpoint_C", "n_years_td",
                    "td_cell_interpolated", "mean_drybulb_C", "n_years_t",
                    "t_cell_interpolated"])
        for m in range(12):
            for hh in range(24):
                w.writerow([m + 1, hh, f"{clim_td[m, hh]:.4f}", ny_td[m, hh],
                            int(fill_td[m, hh]), f"{clim_t[m, hh]:.4f}",
                            ny_t[m, hh], int(fill_t[m, hh])])

    checks = {}
    # HW5: climatology monthly means vs the cross-check's ISD monthly means
    xc = [8.57, 8.23, 9.14, 9.91, 10.67, 9.52, 14.74, 19.13, 18.14, 17.34,
          14.39, 10.04]
    mon = clim_td.mean(axis=1)
    checks["HW5_climatology_vs_crosscheck_max_abs_K"] = float(np.max(np.abs(mon - xc)))
    checks["HW5_pass"] = checks["HW5_climatology_vs_crosscheck_max_abs_K"] <= 1.0

    h0 = np.load(RESULTS / "tmy_hourly.npy")
    # HW1: the Td -> RH -> wet-bulb path reproduces W0 from W0's own dew point
    td0 = dewpoint_from_rh(h0[:, 3], h0[:, 4])
    _, wb0 = tmy.hourly_wetbulb(h0[:, 3], rh_from_dewpoint(h0[:, 3], td0), h0[:, 6])
    checks["HW1_w0_roundtrip_max_abs_K"] = float(np.max(np.abs(wb0 - h0[:, 5])))
    checks["HW1_pass"] = checks["HW1_w0_roundtrip_max_abs_K"] <= 1e-6

    h1, w1info = build_w1(h0, clim_td)
    checks["HW2_pass"] = bool(np.array_equal(h1[:, [0, 1, 2, 3, 6]], h0[:, [0, 1, 2, 3, 6]]))
    checks["HW3_pass"] = bool((h1[:, 4] >= 0.001).all() and (h1[:, 4] <= 1.0).all()
                              and (h1[:, 5] <= h1[:, 3] + 1e-9).all())

    infos, years = [], {}
    for y in YEARS:
        hy, info = station_year(st, y, clim_t, clim_td)
        infos.append(info)
        years[y] = hy
    w2_year = select_median_year(infos)
    with open(ISD / "station_years_2011_2024.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        keys = list(infos[0].keys())
        w.writerow(keys)
        for i in infos:
            w.writerow([f"{i[k]:.4f}" if isinstance(i[k], float) else i[k] for k in keys])
    build = {"station": {k: st[k] for k in ("n_records", "n_duplicate_local_hours",
                                            "n_td_above_t_excluded", "files")},
             "station_valid_hours": int(st["valid"].sum()),
             "climatology_td_cells_interpolated": int(fill_td.sum()),
             "climatology_t_cells_interpolated": int(fill_t.sum()),
             "p_station_pa": P_STATION_PA, "station_years": infos,
             "w2_year": w2_year, "checks": checks,
             "W0": summarise(h0), "W1": {**summarise(h1), **w1info}}
    np.save(LOCAL / "W1.npy", h1)
    if w2_year is not None:
        hy = years[w2_year]
        rh, wb = tmy.hourly_wetbulb(hy[:, 3], hy[:, 4], hy[:, 6])
        checks["HW6_fast_vs_canonical_wb_max_abs_K"] = float(np.max(np.abs(wb - hy[:, 5])))
        checks["HW6_pass"] = checks["HW6_fast_vs_canonical_wb_max_abs_K"] <= 1e-4
        hy = hy.copy(); hy[:, 4], hy[:, 5] = rh, wb
        np.save(LOCAL / "W2.npy", hy)
        w2i = next(i for i in infos if i["year"] == w2_year)
        build["W2"] = {**summarise(hy), **w2i}
    for k in ("W1", "W2"):
        f = LOCAL / f"{k}.npy"
        if f.exists():
            import annual
            build[k]["input_hourly_sha256"] = annual.hourly_sha256(np.load(f))
    (LOCAL / "build.json").write_text(json.dumps(build, indent=1))
    print(json.dumps({"checks": checks, "w2_year": w2_year,
                      "climatology_td_cells_interpolated": int(fill_td.sum()),
                      "station_years": [(i["year"], round(i["coverage_year"], 3),
                                         i["complete"], i["hours_above_21p9"])
                                        for i in infos],
                      **{k: {kk: build[k][kk] for kk in ("hours_above_21p9",
                                                         "pct_above_21p9",
                                                         "annual_mean_wb_C")}
                         for k in ("W0", "W1", "W2") if k in build}}, indent=1))
    ok = all(v for k, v in checks.items() if k.endswith("_pass"))
    print("HARNESS", "PASS" if ok else "FAIL")
    return 0 if ok else 1


CLAIMS = {
    "H1_whole_year_energy_positive": lambda r: r["annual_energy_pct_ratio_of_totals"] > 0,
    "H2_whole_year_cost_positive": lambda r: r["annual_cost_pct_ratio_of_totals"] > 0,
    "H3_whole_year_water_positive": lambda r: r["annual_water_pct_ratio_of_totals"] > 0,
    "H4_water_negative_inside_envelope": lambda r: r["by_envelope"]["inside"]["water_pct"] < 0,
    "H5_water_positive_extrapolated": lambda r: r["by_envelope"]["extrapolated"]["water_pct"] > 0,
    "H6_energy_inside_exceeds_extrapolated": lambda r: (
        r["by_envelope"]["inside"]["energy_pct"] > r["by_envelope"]["extrapolated"]["energy_pct"]),
    "H7_energy_positive_inside_envelope": lambda r: r["by_envelope"]["inside"]["energy_pct"] > 0,
    "H8_lead_with_energy": lambda r: (
        r["by_envelope"]["inside"]["energy_pct"] > 0
        and r["by_envelope"]["inside"]["energy_pct"] > r["by_envelope"]["inside"]["water_pct"]),
    "H9_extrapolated_share_35_to_46_pct": lambda r: (
        35.0 <= 100.0 * r["by_envelope"]["extrapolated"]["hours"] / 8760.0 <= 46.0),
    "H10_mean_of_ratios_corrections_opposite_signs": lambda r: (
        (r["annual_energy_pct_ratio_of_totals"] - r["annual_energy_pct"])
        * (r["annual_water_pct_ratio_of_totals"] - r["annual_water_pct"]) < 0),
}
HEADLINE = ("H4_water_negative_inside_envelope", "H5_water_positive_extrapolated",
            "H6_energy_inside_exceeds_extrapolated", "H8_lead_with_energy")


def _claim(fn, r, name=""):
    """True/False, or None (UNDEFINED) when a claim needs an envelope side
    that has no hours in this scenario."""
    sides = r.get("by_envelope", {})
    if (name[:3] in ("H4_", "H5_", "H6_", "H7_", "H8_")
            and any(s.get("hours", 0) == 0 for s in sides.values())):
        return None
    try:
        v = fn(r)
        return bool(v) if v == v else None
    except (KeyError, ZeroDivisionError, TypeError):
        return None


def stage_run() -> int:
    import annual
    build = json.loads((LOCAL / "build.json").read_text())
    if not all(v for k, v in build["checks"].items() if k.endswith("_pass")):
        print("harness checks failed at build; refusing to run")
        return 1
    h0 = np.load(RESULTS / "tmy_hourly.npy")
    w0 = json.loads((RESULTS / "annual_dhahran.json").read_text())
    if w0.get("input_hourly_sha256") != annual.hourly_sha256(h0):
        print("annual_dhahran.json was not computed from tmy_hourly.npy; "
              "re-run src/annual.py first")
        return 1
    results = {"W0": w0}
    for k in ("W1", "W2"):
        f = LOCAL / f"{k}.npy"
        if not f.exists():
            continue
        h = np.load(f)
        assert annual.hourly_sha256(h) == build[k]["input_hourly_sha256"]
        title = ("W1: TMYx dry bulb + ISD 404160 dew-point climatology" if k == "W1"
                 else f"W2: ISD 404160 station year {build['w2_year']}")
        print(f"\n### {k}", flush=True)
        results[k] = annual.run_annual(h, title=title)

    table = {}
    for name, fn in CLAIMS.items():
        vals = {k: _claim(fn, r, name) for k, r in results.items()}
        a, b = vals.get("W0"), vals.get("W1")
        if a is None or b is None:
            verdict = "UNDEFINED"
        elif a and b:
            verdict = "HOLDS"
        elif a or b:
            verdict = "WEATHER-SOURCE-DEPENDENT"
        else:
            verdict = "FAILS"
        w2 = vals.get("W2")
        table[name] = {"W0": a, "W1": b, "W2": w2, "verdict": verdict,
                       "W2_contradicts_verdict": (
                           None if w2 is None or verdict not in ("HOLDS", "FAILS")
                           else (w2 != (verdict == "HOLDS")))}
    headline = all(table[c]["verdict"] == "HOLDS" for c in HEADLINE)

    def brief(r):
        e = r["by_envelope"]
        return {k: r[k] for k in (
            "annual_water_pct_ratio_of_totals", "annual_energy_pct_ratio_of_totals",
            "annual_cost_pct_ratio_of_totals", "annual_water_pct",
            "annual_energy_pct", "annual_cost_pct",
            "fraction_inside_validated_envelope", "hours_above_almeria",
            "unsolved_hours", "v5_gate_unweighted_mean_water_pct",
            "input_hourly_sha256", "n_bins")} | {"by_envelope": e, "bins": r["bins"]}

    prereg_sha = hashlib.sha256(PREREG.read_bytes()).hexdigest() if PREREG.exists() else None
    out = {"preregistration": str(PREREG.relative_to(ROOT)).replace("\\", "/"),
           "preregistration_sha256": prereg_sha,
           "decision_rule": ("No scenario is the truth. A claim HOLDS if true in "
                             "both W0 and W1, is WEATHER-SOURCE-DEPENDENT if true "
                             "in exactly one, FAILS if true in neither. W2 is "
                             "descriptive and cannot change a verdict."),
           "headline_claim": ("water negative inside the validated envelope, "
                              "positive outside it; energy earned inside; lead "
                              "with energy (defect 48)"),
           "headline_survives": headline, "claims": table,
           "construction": {k: v for k, v in build.items() if k not in ("W0", "W1", "W2")},
           "scenarios": {k: {"weather": build.get(k), "annual": brief(r)}
                         for k, r in results.items()},
           "v5_note": ("The V5 gate is an unweighted mean over five fixed design "
                       "conditions and reads no hourly weather, so it is identical "
                       "in every scenario and is not re-scored here.")}
    (RESULTS / "annual_weather_sensitivity.json").write_text(json.dumps(out, indent=1))
    print("\nCLAIMS")
    for name, t in table.items():
        print(f"  {name:48s} W0={t['W0']!s:5s} W1={t['W1']!s:5s} "
              f"W2={t['W2']!s:5s} -> {t['verdict']}")
    print(f"HEADLINE SURVIVES: {headline}")
    print("written -> results/annual_weather_sensitivity.json")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("build", "run"), required=True)
    a = ap.parse_args()
    return stage_build() if a.stage == "build" else stage_run()


if __name__ == "__main__":
    sys.exit(main())
