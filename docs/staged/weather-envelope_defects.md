# Staged defect entries: weather inputs (60, 61, 62)

Branch `fix/weather-envelope`. These rows are for the main session to paste into
`docs/defect_register.md` at merge. This branch does not edit the register. The
numbers were reserved for this branch: **60, 61, 62**.

**Count impact.** 60 and 61 are defects. 62 was investigated and **nothing was
misaligned**. It is staged so the investigation has a record. If the register
keeps defects strictly to faults, 62 should go in the "not a defect" notes
rather than Part 1, and the found/fixed count rises by **two**, not three.
`tests/test_artefact_consistency.py::test_every_document_agrees_on_how_many_defects_were_found`
checks every document's stated count, so update them all together.

---

## Part 1 rows

| # | Defect | How it showed up | State |
|---|---|---|---|
| 60 | **The envelope split classified whole wet-bulb bins by their centroid, so 266 unvalidated hours were booked as validated** | `annual.py` split the year into eight equal-hour bins of 1,095 h. It marked a whole bin *inside* when its **centroid** wet bulb was ≤ 21.9 °C. Bin 4 had a centroid of 21.38 °C, and **266 of its 1,095 hours were above 21.9 °C**. So defect 48's split reported **3,285 extrapolated hours (37.5 %), a bin count**, where the weather file holds **3,551 (40.5 %)** hour by hour. Those 266 hours' savings were booked to the validated side. `tmy_dhahran.json` had carried the correct 3,551 all along, so two artefacts disagreed on one quantity and nothing compared them. An independent weather cross-check found it on 16–17 Sep 2026 | **Fixed** — 17 Sep 2026. `annual.envelope_bins()` bins the inside hours and the extrapolated hours **separately**. The eight bins are shared 5/3 by hours, every bin is pure, and the run asserts purity. The split now equals the weather file's own counts, 5,209 / 3,551 h. The printed conclusion and `envelope_warning` are derived from the signs instead of typed. The artefact records the SHA-256 of the hourly array it was computed from. Regression: `tests/test_weather_envelope.py` (bins never straddle the edge; the artefact split equals the npy's hour counts and `tmy_dhahran.json`). **Every annual figure moved** (table below). The whole-year numbers moved too, although no weather changed, because moving the bin edges moves the centroids the controller runs at. That bin-resolution error is about a point of annual water saving. **The same centroid rule survives in `src/annual_datacentre.py`**, as a per-bin flag that no aggregate reads. It was not changed there because `src/cdu_hybrid.py`'s frozen, pre-registered experiment rebuilds those bins by the old rule |
| 61 | **`tmy.py` read the EPW time-zone field as the station elevation** | The EPW `LOCATION` record is `…,lat,lon,TZ,elevation`. `tmy.py` took field 8 (TZ = +3.0) as elevation, so `tmy_dhahran.json` and the module docstring said **3 m**. Dhahran 404160 is at **25.6 m**. The cross-check noticed it while using "3 m" to bound a sea-level-pressure correction, so the wrong fact had already propagated one step | **Fixed** — 17 Sep 2026. `tmy.parse_location()` reads the record by field name and refuses a record with fewer than ten fields. It also records `timezone_h`. **No number changed**: nothing read the elevation, and every psychrometric call uses the EPW pressure column. Re-running `tmy.py` left `tmy_hourly.npy` byte-identical (SHA-256 `57efd6ea…4a04c0`) and every other value in `tmy_dhahran.json` unchanged. Regression: `tests/test_weather_envelope.py` |
| 62 | **EPW hour convention: investigated, nothing misaligned** | The cross-check reported that EPW hour *h* holds the station observation at local **(h−1):00**, not h:00. Anything that read hour *h* as h:00 would be shifted by an hour, including the diurnal silica margin, the night/day windows and any join to real observations. **Verified here independently**: against ISD-Lite 404160 for three months whose source year the EPW header names (Apr 2022, Jul 2018, Aug 2019), dry bulb agrees within 0.5 K in **98.6–98.9 %** of hours at (h−1):00, against 28–30 % at h:00 | **Not a defect** — 17 Sep 2026. `diurnal.py` (`pick_summer_day`, the night `t < 6 or t ≥ 21` and day `11 ≤ t < 17` windows) and `scripts/generate_pitch_artifacts.py` both use the row index t = h − 1 within a calendar day as the local clock hour, which is correct under this convention. Hour 24 belongs to the same day (23:00). The Modelica models and the synthetic pitch profiles do not read EPW hours. **Nothing was shifted.** The convention is now stated in `tmy.py`, exposed as `epw_hour_to_local_hour()`, written to `tmy_dhahran.json` as `hour_convention`, used by the weather-source sensitivity to map station climatology onto TMYx rows, and pinned by `tests/test_weather_envelope.py` |

## Supersession table for defect 60

Paste this as the defect's before/after table. `src/audit.py::superseded_from_register`
reads three-column percentage rows from the register, so this table is what
makes the audit flag documents that still quote the old split.

| Annual figure, ratio of totals | before | after |
|---|---|---|
| Water, inside the envelope | −3.31 % | **−3.22 %** |
| Water, extrapolated | 8.23 % | **5.41 %** |
| Energy, inside the envelope | 8.84 % | **8.82 %** |
| Energy, extrapolated | −0.39 % | **+0.95 %** |
| Cost, extrapolated | 2.90 % | **2.75 %** |
| Water, whole year | 2.37 % | **1.31 %** |
| Energy, whole year | 4.52 % | **4.86 %** |
| Cost, whole year | 4.17 % | **4.01 %** |
| Water, mean of ratios | 1.25 % | **0.31 %** |
| Energy, mean of ratios | 5.38 % | **5.69 %** |
| Cost, mean of ratios | 4.48 % | **4.34 %** |
| Share of year extrapolated | 37.5 % | **40.5 %** |
| Share of year inside | 62.5 % | **59.5 %** |

Unchanged: cost inside the envelope, +5.32 %. The hours moved from 5,475 / 3,285
to **5,209 / 3,551**. The energy–water correlation across the bins was −0.836
on the pre-fix artefact and is **−0.714** now. The documents quoting r = −0.66
were already stale before this fix.

**Caution before pasting.** `superseded_from_register` reads only a "before"
cell that is an unsigned percentage. The rows with −3.31 % and −0.39 % are
therefore not tracked, and documents quoting them are caught only by the stale
list in `weather-envelope_doc_updates.md`. `4.17 %` is already a "before" value
in the register (electrical power, 4.17 → 2.86), and a second row makes the
mapping ambiguous. Run `python src/audit.py` after pasting.

## What defect 60 did to the headline

Signs unchanged. Water is negative inside the envelope and positive outside it;
energy is larger inside. **One sign reversed:** the extrapolated energy saving
is now slightly positive (+0.95 %) where it was −0.39 %. So "the energy saving
vanishes outside the envelope" should now read "falls to about one per cent
outside it". The magnitude of the water asymmetry fell by a third (+8.23 → +5.41
outside). Whether the headline survives a change of **weather source** is a
separate, pre-registered question: `docs/weather_source_sensitivity.md`.
