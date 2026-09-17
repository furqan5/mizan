# Weather-source sensitivity of the annual study

17 Sep 2026, branch `fix/weather-envelope`. Pre-registered in
`docs/staged/weather_source_preregistration.md` (commit `d62b18b`) before any
W1 or W2 number existed. Each scenario was run once, after that commit, by
`python src/weather_sensitivity.py --stage build` and then `--stage run`. The
harness passed on the first build, and no code was changed between the
pre-registration and the run.

Outputs:

- `results/annual_weather_sensitivity.json`
- `results/weather_sensitivity_run.log`
- `data/weather/isd_404160/dewpoint_climatology_2011_2024.csv`
- `data/weather/isd_404160/station_years_2011_2024.csv`

## Verdicts

**No scenario is the truth.** A claim HOLDS only if it is true under both the
TMYx humidity (W0) and the Dhahran station humidity (W1).

| id | claim | W0 | W1 | W2 | verdict |
|---|---|:-:|:-:|:-:|---|
| H1 | whole-year energy saving > 0 | yes | yes | yes | **HOLDS** |
| H2 | whole-year cost saving > 0 | yes | yes | yes | **HOLDS** |
| H3 | whole-year **water** saving > 0 | yes | **no** | no | **WEATHER-SOURCE-DEPENDENT** |
| H4 | water saving inside the validated envelope < 0 | yes | yes | yes | **HOLDS** |
| H5 | water saving on extrapolated hours > 0 | yes | yes | yes | **HOLDS** |
| H6 | energy saving larger inside than extrapolated | yes | yes | yes | **HOLDS** |
| H7 | energy saving inside the envelope > 0 | yes | yes | yes | **HOLDS** |
| H8 | lead with energy (energy inside > 0 and > water inside) | yes | yes | yes | **HOLDS** |
| H9 | "two fifths of the year is extrapolated" (35–46 %) | yes | **no** | no | **WEATHER-SOURCE-DEPENDENT** |
| H10 | mean-of-ratios corrections have opposite signs | yes | yes* | yes | **HOLDS** |

\*Only nominally. Under W1 the water correction is positive but rounds to
+0.00 points.

**The defect-48 headline survives in sign and not in size.** The claim is:
*water negative inside the envelope, positive outside it; energy earned inside;
lead with energy.* H4, H5, H6 and H8 all hold. The −3.31 % / +8.23 % figures do
not survive. Defect 60 superseded them before any change of weather source
(corrected on TMYx to −3.22 % / +5.41 %). Across the two humidity sources the
water saving is **−3.22 to −4.77 %** inside the envelope and **+1.91 to
+5.41 %** outside it.

**The positive annual water saving does not survive.** It is +1.31 % on TMYx
humidity and **−2.64 %** on station humidity, where the controller uses more
makeup water over the year than the baseline. The median complete station year,
2021, gives −0.74 %. This 3.95-point swing between W0 and W1 is larger than the
1.06-point bin-resolution error declared in advance, so it is a result and not
noise.

## The table

All savings are ratios of annual totals against the fixed baseline (4 cycles,
pH 7.8, 32 °C condenser water) unless marked. Positive means a saving.

| | **W0** TMYx | **W1** TMYx dry bulb + station dew point | **W2** station year 2021 |
|---|---:|---:|---:|
| hours with wet bulb > 21.9 °C | 3,551 (40.5 %) | 2,130 (24.3 %) | 2,166 (24.7 %) |
| hours inside / extrapolated | 5,209 / 3,551 | 6,630 / 2,130 | 6,594 / 2,166 |
| annual mean wet bulb | 19.93 °C | 18.12 °C | 18.42 °C |
| 0.4 / 1 / 2 % wet bulb | 31.34 / 30.45 / 29.69 °C | 25.48 / 25.21 / 24.96 °C | 30.42 / 29.76 / 29.04 °C |
| **whole year** water | **+1.31 %** | **−2.64 %** | −0.74 % |
| whole year energy | +4.86 % | +6.54 % | +5.33 % |
| whole year cost | +4.01 % | +3.85 % | +3.67 % |
| **inside** water | −3.22 % | −4.77 % | −4.82 % |
| inside energy | +8.82 % | +9.10 % | +8.08 % |
| inside cost | +5.32 % | +4.96 % | +4.197 %† |
| **extrapolated** water | +5.41 % | +1.91 % | +8.41 % |
| extrapolated energy | +0.95 % | +0.59 % | −1.07 % |
| extrapolated cost | +2.75 % | +1.32 % | +2.46 % |
| means of ratios: water / energy / cost | 0.31 / 5.69 / 4.34 % | −2.64 / 7.14 / 4.33 % | −1.23 / 5.98 / 4.00 % |
| unsolved hours | 0 | 0 | 0 |
| V5 gate (five fixed conditions, reads no weather) | 4.38 % | 4.38 % | 4.38 % |

†Written to three decimals because the two-decimal form collides with a superseded register figure that `src/audit.py` scans for.

V5 is identical by construction and was not re-scored. It still fails
against 15 %.

### How the scenarios were built, and the checks they passed

- **Station data.** ISD-Lite 404160, 2011–2024: 116,330 records and 115,632
  valid (T, Td) hours, all SHA-256-verified against `SOURCES.json`. There were
  no duplicate local hours and no Td > T exclusions. The UTC times were shifted
  +3 h.
- **W1.** The dew-point climatology has 12 × 24 cells, and all of them met the
  "≥ 10 obs in ≥ 7 years" rule, so none was interpolated. Td was capped at the
  TMYx dry bulb in 27 hours. The dry bulb, pressure and calendar columns are
  byte-identical to W0.
- **W2.** 13 of 14 years were complete. 2015 failed, with one month at 8.5 %
  coverage. Hours above 21.9 °C by complete year:

  | year | hours above 21.9 °C |
  |---|---:|
  | 2013 | 1,407 |
  | 2014 | 1,585 |
  | 2016 | 1,647 |
  | 2018 | 1,976 |
  | 2020 | 1,995 |
  | 2019 | 2,051 |
  | **2021** | **2,166** |
  | 2023 | 2,211 |
  | 2017 | 2,275 |
  | 2022 | 2,447 |
  | 2024 | 2,478 |
  | 2011 | 2,699 |
  | 2012 | 3,217 |

  That is 16.1–36.7 % of the year. The median year is 2021. It had 97.8 %
  coverage; 73 h were filled by interpolation, 121 h from its own month × hour
  cells and 0 h from climatology. **The TMYx year's 3,551 h is above every
  complete station year.**
- **Harness checks:**
  - HW1: W0 rebuilt through the dew-point path, 2.6 × 10⁻¹³ K.
  - HW2: pass. HW3: pass.
  - HW4: 14/14 hashes, 12 fields per line.
  - HW5: climatology monthly means within 0.26 K of the cross-check's.
  - HW6: bisection vs canonical wet bulb, 2.5 × 10⁻⁹ K.

### Two things the table shows that the verdicts do not

1. **W1 has no humid tail.** A month × hour climatology averages humid spells
   away, so W1's 0.4 % wet bulb is 25.5 °C, against ASHRAE's 31.4 °C.
   Pre-registered, W2 was the guard against that. W2 has the tail (30.4 °C) and
   still gives the same verdict as W1 on every claim. So the W1 result is not an
   artefact of averaging. W2 does move two magnitudes: extrapolated water
   +8.41 % and extrapolated energy −1.07 %. Its hottest bin is the one that
   earns water.
2. **Station humidity helps validation and hurts water.** It moves about 1,400
   hours from outside the envelope to inside it, and inside is exactly where the
   controller trades water for energy. So the share of the year the model has
   been validated for rises from 59.5 % to 75.7 %, while the annual water result
   turns negative. The "extrapolation" caveat shrinks, and the water case gets
   worse, not better.

## What it means for the pitch

- **Energy, and cost, are robust to the humidity source.** The whole-year energy
  saving is +4.86 to +6.54 %. The saving inside the validated envelope is +8.82
  to +9.10 %, and cost is +3.85 to +4.01 %. These may be stated without a
  weather qualifier, subject to every other caveat the package carries. **Lead
  with energy** survives, and it is now better supported than when it was
  chosen.
- **Do not quote a positive annual water saving.** Its sign depends on which
  humidity a Dhahran plant is assumed to breathe, and that is unresolved: the
  island station at Bahrain is as wet as TMYx, and Dammam KFIA is drier than
  Dhahran. The honest sentence is: *"annual makeup water is between −2.6 % and
  +1.3 % depending on the humidity record, so on this water the controller is
  roughly water-neutral while it saves energy."*
- **The defect-48 split survives in sign and not in size.** Quote it as a range,
  never as −3.31 / +8.23. *"Water is 3–5 % worse inside the validated envelope
  and 2–5 % better outside it."* The energy saving outside the envelope is about
  zero (−1.1 to +1.0 % across the three scenarios), which is no longer "the
  exact reverse" of a negative number.
- **"Two fifths of a Dhahran year is extrapolated" is a property of the TMYx
  file.** On station humidity it is a quarter: 24.3 % in W1, and 16.1–36.7 %
  across complete station years. Say *"a quarter to two fifths, depending on
  the humidity record"*. The KFUPM wind-tunnel argument still stands, on a
  smaller base.
- **What a pilot should measure first is cheap.** Humidity at the tower inlet
  now decides the sign of the water result. A logged wet bulb at the plant costs
  almost nothing next to the chemistry instruments in
  `docs/instrumentation_spec.md`, and it settles which of W0 and W1 the site
  actually lives in.

## Limits

- Station humidity may be dry-biased. The 16–17 Sep cross-check reports July
  mean dew point ranging 9.62–21.99 °C across 2011–2025. The Bahrain and Dammam
  comparisons above are also that cross-check's, not this run's. W1 does not
  claim the station is right.
- Eight centroid bins carry a resolution error of about 1 point of annual water.
- The load model is dry-bulb-driven, so W2 changes load as well as humidity.
- One plant, one water and one tariff set. Nothing here re-validates the
  evaporation model; V2 still fails.
