# Pre-registration: weather-source sensitivity of the annual study

Written 17 Sep 2026 on branch `fix/weather-envelope`, after the defect-60/61/62
fixes (commits `dc28328`, `a6ae483`) and **before** any W1 or W2 quantity was
computed. It is committed together with the code that implements it
(`src/weather_sensitivity.py`, `data/weather/isd_404160/`). That code has not
been run. If a harness check below fails and the code has to be fixed, the fix
and the reason go into `docs/weather_source_sensitivity.md`; nothing in this
file is edited after the run.

## 0. What had been seen before this was written

- **W0, in full.** The defect-60 re-run of `src/annual.py` on the TMYx year
  (ratio of totals): whole year water +1.31 %, energy +4.86 %, cost +4.01 %;
  inside the envelope 5,209 h, water −3.22 %, energy +8.82 %, cost +5.32 %;
  extrapolated 3,551 h, water +5.41 %, energy +0.95 %, cost +2.75 %.
- **The cross-check** (`saudi_tmy_crosscheck.md`, 16–17 Sep 2026): ISD-Lite
  404160 monthly mean dew point by month for 2011–2025; the share of hours with
  wet bulb > 21.9 °C in each complete station year under its block-weighted
  method (16.0–36.4 %, mean 24.7 %; 2015 and 2025 incomplete); Bahrain and
  Dammam dew-point climatologies. So the direction of W1's hours-above count is
  expected (fewer than W0). **What those hours are worth to the controller has
  not been computed for any station humidity.** That is what this tests.
- Nothing else. No ISD file has been parsed in this repository, no climatology
  built and no station year assembled.

## 1. Scenarios

| | dry bulb | humidity | pressure | purpose |
|---|---|---|---|---|
| **W0** | TMYx | TMYx | TMYx | the repository's weather, after defect 60 |
| **W1** | TMYx, same 8,760 hours | ISD 404160 dew point, month × local-hour climatology 2011–2024 | TMYx | isolates the humidity source |
| **W2** | ISD 404160, one complete year | ISD, same year | standard atmosphere at 25.6 m | a real station year; descriptive only |

W2 changes dry bulb too, and therefore the load model, so it is **not** a
humidity isolation. It cannot change a verdict (§4).

## 2. Construction, fixed now

### 2.1 Data

- NCEI ISD-Lite, USAF 404160 / WBAN 99999, years 2011–2024, one file per year,
  URLs and SHA-256 in `data/weather/isd_404160/SOURCES.json`. The hashes are the
  ones the cross-check recorded when it retrieved the files. Any mismatch stops
  the run.
- **Storage decision: commit the script, the hashes and derived aggregates only,
  not the raw `.gz` files.** The files are small and public, but they are
  non-U.S. observations that NCEI redistributes from WMO exchange. NCEI's ISD
  documentation carries a WMO Resolution 40 notice that lets the originating
  country restrict commercial re-export, and this is a commercial venture's
  public repository. [J: a precaution, not a legal finding.] The committed
  aggregates, `dewpoint_climatology_2011_2024.csv` and
  `station_years_2011_2024.csv`, reproduce W1 exactly. W2 needs the raw files,
  which `fetch.py` re-downloads and hash-verifies into the git-ignored `raw/`.
- Parsing: 12 integer fields per line; T = field 5 / 10, Td = field 6 / 10;
  −9999 = missing. Times are UTC and are shifted +3 h to Arabia Standard Time
  (no DST) before assigning year, month and hour. Duplicate local hours keep the
  first record. An hour is **valid** when T and Td are both present and
  Td ≤ T + 0.05 K.

### 2.2 W1

1. **Climatology.** For each (month, local hour) cell and each year 2011–2024,
   take the year-cell mean of Td if the cell has ≥ 10 valid hours. The cell
   climatology is the unweighted mean of those year-cell means, so each year
   counts equally. It is valid if ≥ 7 years qualify.
2. **Gaps.** An invalid cell is filled by linear interpolation around the
   24-hour circle, from the nearest valid hours of the same month. The number of
   filled cells is reported. A month with fewer than 2 valid cells stops the
   run.
3. **Mapping (defect 62).** TMYx row (month m, EPW hour h) takes
   Td = climatology[m, h − 1].
4. Td is capped at the row's TMYx dry bulb (RH ≤ 1). The capped hours are
   counted.
5. RH = pws(Td) / pws(T_db) as a **fraction**, with
   `psychro.sat_vapour_pressure`. Wet bulb comes from
   `tmy.hourly_wetbulb(T_db, RH, p_TMYx)`, the function that builds W0.

### 2.3 W2

1. For each local calendar year 2011–2024, place valid hours on an 8,760-h
   local grid, dropping 29 Feb.
2. **Complete** means valid hours ≥ 85 % of the year and ≥ 60 % of every
   calendar month, counted before filling.
3. **Gaps**, filling T and Td on the same hours:
   - runs of ≤ 3 missing hours bounded on both sides are filled by linear
     interpolation;
   - remaining hours take that year's own (month, local hour) mean if the cell
     has ≥ 10 valid hours;
   - otherwise they take the 2011–2024 climatology cell (§2.2 rule, applied to T
     and Td).

   Td is then capped at T. The count filled by each method is reported.
4. Pressure is the ASHRAE standard atmosphere at 25.6 m, 101,325 ×
   (1 − 2.25577×10⁻⁵ × 25.6)^5.2559 Pa. The station's sea-level pressure is
   missing in most records, and the TMYx pressure belongs to other years.
5. **Selection.** Count hours with wet bulb > 21.9 °C in each complete year's
   filled series. Sort ascending by (count, year) and take element
   (n − 1) // 2, the lower middle for even n. If fewer than 3 years are
   complete, W2 is reported as not constructible. For ranking, wet bulb comes
   from a vectorised bisection on the same ASHRAE equations. The chosen year is
   rebuilt with `tmy.hourly_wetbulb` before it is scored.

### 2.4 Harness checks. All must pass before any W1/W2 result is interpreted.

- **HW1.** W0's wet bulb, reconstructed through the W1 path (dew point from W0's
  RH, then RH, then wet bulb), matches `tmy_hourly.npy` to ≤ 1×10⁻⁶ K. This
  catches RH fraction/percent and Pa/kPa errors.
- **HW2.** W1's month, day, hour, dry-bulb and pressure columns are identical to
  W0's.
- **HW3.** W1 RH lies in [0.001, 1] and wet bulb ≤ dry bulb in every hour.
- **HW4.** Every ISD line has 12 integer fields, its year matches the file, and
  every SHA-256 matches.
- **HW5.** The climatology's monthly means (the mean of 24 cells) are within
  1.0 K of the cross-check's ISD monthly means (2011–2025, block method) in
  every month. This catches ×10, wrong-column and UTC errors, not bias.
- **HW6.** For the chosen W2 year, the bisection wet bulb matches
  `tmy.hourly_wetbulb` to ≤ 1×10⁻⁴ K.

## 3. What is run and reported

Each scenario is scored **once** by `annual.run_annual()` at commit `a6ae483`
behaviour: eight equal-hour bins cut at 21.9 °C, the same load model, grids,
baseline and tariffs. W0 is taken from `results/annual_dhahran.json`, after
checking that its recorded input hash equals the current `tmy_hourly.npy`.

Reported per scenario, in `results/annual_weather_sensitivity.json` and
`docs/weather_source_sensitivity.md`:

- hours with wet bulb > 21.9 °C, counted hourly, and as a share of the year;
- the inside/extrapolated split in hours;
- annual water, energy and cost savings as **ratios of totals** (the repository
  convention), for the whole year, inside and extrapolated;
- the means of ratios, and unsolved hours;
- annual mean wet bulb, the 0.4/1/2 % wet bulbs, and monthly mean dry bulb, dew
  point and wet bulb;
- the V5 gate figure. V5 is an unweighted mean over five fixed design conditions
  and reads no hourly weather, so it is identical in every scenario. It is
  reported and **not re-scored**.

## 4. Claims and the decision rule

**No scenario is declared the truth.** Each claim is evaluated as a strict
inequality on W0 and on W1:

| id | claim |
|---|---|
| H1 | whole-year energy saving > 0 |
| H2 | whole-year cost saving > 0 |
| H3 | whole-year water saving > 0 |
| H4 | water saving **inside** the validated envelope < 0 |
| H5 | water saving on **extrapolated** hours > 0 |
| H6 | energy saving inside > energy saving extrapolated |
| H7 | energy saving inside > 0 |
| H8 | "lead with energy": energy inside > 0 **and** energy inside > water inside |
| H9 | extrapolated share of the year within 35–46 % ("two fifths", the band `audit.py` enforces) |
| H10 | the mean-of-ratios corrections for energy and water have opposite signs |

- **HOLDS**: true in both W0 and W1. It may be stated without qualification
  from weather source, quoting the W0–W1 range rather than one number.
- **WEATHER-SOURCE-DEPENDENT**: true in exactly one. It must be stated as such,
  with both values.
- **FAILS**: true in neither.
- **UNDEFINED**: a side has no hours. Reported, not interpreted.

W2 is printed beside each verdict. If it contradicts a HOLDS or FAILS verdict,
the contradiction is flagged, but it does not change the verdict.

**The handoff headline**, *"water −3.31 % inside the envelope / +8.23 % outside,
lead with energy"*, **survives** only if H4, H5, H6 and H8 all HOLD. If it
survives, it survives with the W0–W1 magnitudes and not with −3.31 / +8.23,
which defect 60 already superseded.

## 5. Known limitations, declared in advance

- A month × hour climatology has no day-to-day humidity variance, so W1's
  wet-bulb distribution is narrower than any real year. W2 exists to show
  whether that matters.
- The station record may itself be dry-biased. The cross-check found a 12 K
  range in July mean dew point across years. W1 is not a claim that the station
  is right.
- Eight centroid bins carry a resolution error. Defect 60 moved the whole-year
  water saving by 1.06 points with no change of weather. Differences between
  scenarios smaller than that are not interpreted as physics.
