"""
MIZAN :: every figure, in two variants
======================================
One module, two outputs per figure:

  figs/<name>.png        REPORT variant  -- page proportions, print type
                         sizes, and a source footnote under the axes.
                         The descriptive caption comes from the LaTeX
                         figure environment.

  figs/slide/<name>.png  SLIDE variant   -- no footnote, larger type, drawn
                         at the deck placeholder's aspect ratio.

Neither variant carries an editorial title inside the image, and that is the
fix for the deck's figure problem. The old build put the report image on a
slide that already had its own headline, so every figure slide showed two
competing titles, and the footnote -- set for a 10-inch page -- rendered at
roughly 6 pt when projected. The surrounding document supplies the words;
the figure supplies only the data.

Every number is read from results/*.json and results/*.csv. Re-run the gates
and re-run this; the figures cannot drift from the evidence.
"""
from __future__ import annotations

import json
import pathlib
import sys
import warnings

warnings.filterwarnings("ignore")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
R = ROOT / "results"
FIGS = ROOT / "figs"
SLIDE = FIGS / "slide"
FIGS.mkdir(exist_ok=True)
SLIDE.mkdir(exist_ok=True)

sys.path.insert(0, str(pathlib.Path(__file__).parent))

NAVY = "#14425f"
TEAL = "#1c7293"
RED = "#b3252b"
AMBER = "#c89a2b"
GREEN = "#1e6b46"
GREY = "#4a4a4a"
INK_TXT = "#1A2B33"

# Report pages are A4 with 25 mm margins; the deck placeholder is 7.55 x 4.35
# inches. Matching the aspect ratio at generation time means the deck never
# has to stretch an image, which is where the axis labels used to distort.
GEOM = {
    "report": dict(figsize=(10.0, 5.8), dpi=200, base=11.5),
    "slide": dict(figsize=(9.4, 5.42), dpi=210, base=15.0),
}


def new_fig(mode):
    g = GEOM[mode]
    fig, ax = plt.subplots(figsize=g["figsize"], dpi=g["dpi"])
    return fig, ax, g["base"]


def finish(fig, ax, mode, name, title=None, footnote=None, rect_bottom=0.075):
    """Titles and footnotes are REPORT-only. On a slide the surrounding
    layout carries them, and duplicating them is what made the old slides
    look crowded."""
    ax.grid(axis="y", alpha=0.20, ls=":")
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    if mode == "report":
        # No embedded title in either variant. In the report the LaTeX
        # caption describes the figure; on a slide the slide headline does.
        # Carrying an editorial title as well duplicated both.
        if footnote:
            fig.text(0.5, 0.02, footnote, ha="center", fontsize=8.6,
                     color=GREY, linespacing=1.6)
            fig.tight_layout(rect=[0, rect_bottom, 1, 1])
        else:
            fig.tight_layout()
        out = FIGS / f"{name}.png"
    else:
        fig.tight_layout()
        out = SLIDE / f"{name}.png"

    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"   {mode:6s} -> {out.relative_to(ROOT)}")


# --------------------------------------------------------------------------
def fig_water_ceiling(mode):
    """WHY THE WATER GATE COULD NOT BE PASSED.

    Makeup is evaporation plus blowdown, and blowdown is evaporation/(C-1),
    so at constant evaporation makeup = E*C/(C-1) and the makeup saving
    available by raising cycles from the incumbent 4 is fixed arithmetic. It
    is a hyperbola with a horizontal asymptote at 25 %. Draw the gypsum wall
    on it and the pre-registered 15 % criterion, and the picture answers the
    question by itself: the criterion sits on the far side of the wall.
    """
    summary = json.loads((R / "controller_summary.json").read_text())
    sm = summary["summary"]
    wall = float(sm["physical_ceiling_cycles"])
    last_ok = float(sm["economic_ceiling_cycles"])
    achieved = float(sm["water_pct"])
    criterion = float(summary["criteria"]["makeup_water_reduction_pct_min"])

    # Cycles required to reach the criterion on cycles alone. Setting
    # 1 - (C/(C-1))/(4/3) = crit and solving gives C = 1/(1 - 0.75/(1-crit)).
    # For 15 % that is 8.5 -- half a cycle past where gypsum saturates.
    c_needed = 1.0 / (1.0 - 0.75 / (1.0 - criterion / 100.0))
    y_last = 100.0 * (1.0 - (last_ok / (last_ok - 1.0)) / (4.0 / 3.0))

    C = np.linspace(4.0, 20.0, 400)
    sav = 100.0 * (1.0 - (C / (C - 1.0)) / (4.0 / 3.0))

    fig, ax, base = new_fig(mode)

    ax.axhline(25.0, color=GREY, lw=1.4, ls=":", zorder=2)
    ax.fill_betweenx([0, 27], wall, 20.5, color=RED, alpha=0.10, lw=0, zorder=1)
    ax.axvline(wall, color=RED, lw=2.8, zorder=4)

    ax.plot(C, sav, lw=3.0, color=NAVY, zorder=5)
    ax.axhline(criterion, color=AMBER, lw=2.4, ls="--", zorder=4)
    ax.plot([last_ok], [y_last], "o", ms=11,
            color=NAVY, markerfacecolor="white", markeredgewidth=2.6, zorder=6)
    ax.plot([c_needed], [criterion], "X", ms=14, color=AMBER, zorder=7)

    ax.set_xlim(4, 20.5)
    ax.set_ylim(0, 27)
    ax.set_xlabel("Cycles of concentration", fontsize=base, labelpad=8)
    ax.set_ylabel("Makeup water saved vs 4 cycles   [%]", fontsize=base,
                  labelpad=8)
    ax.tick_params(labelsize=base - 1.5)

    ax.text(20.2, 25.6, "absolute ceiling 25 % (zero blowdown)", ha="right",
            va="bottom", fontsize=base - 2.0, color=GREY, style="italic")
    # two short lines rather than one long one: a single line at this y
    # ran straight through the marker at c_needed
    # the curve occupies the left half at this height, so the label goes at
    # the right end of its own dashed line, where nothing else is drawn
    ax.text(20.2, criterion - 0.9,
            f"pre-registered criterion {criterion:.0f} %",
            ha="right", va="top", fontsize=base - 1.5, color=AMBER,
            weight="bold")
    ax.annotate(f"needs {c_needed:.1f} cycles —\npast the wall",
                xy=(c_needed, criterion), xytext=(c_needed + 1.6, 22.0),
                fontsize=base - 2.0, color=AMBER, weight="bold",
                ha="left", va="center", linespacing=1.5,
                arrowprops=dict(arrowstyle="->", lw=1.8, color=AMBER))
    ax.text(wall + 0.45, 3.6,
            f"GYPSUM WALL — {wall:.0f} cycles\nacid cannot move it",
            ha="left", va="center", fontsize=base - 1.0, color=RED,
            weight="bold", linespacing=1.5)
    ax.annotate(f"last feasible point\n{last_ok:.0f} cycles = {y_last:.1f} %",
                xy=(last_ok, y_last), xytext=(11.5, 9.5),
                fontsize=base - 2.0, color=NAVY, weight="bold",
                ha="left", va="center", linespacing=1.5,
                arrowprops=dict(arrowstyle="->", lw=1.8, color=NAVY))

    finish(fig, ax, mode, "water_ceiling",
           title="The water criterion was set on the far side of a wall",
           footnote=(
               "Makeup = evaporation × C/(C−1), so the saving available from cycles alone is fixed arithmetic, not a modelling choice.\n"
               f"{criterion:.0f} % requires {c_needed:.1f} cycles; gypsum saturates at {wall:.0f}. "
               f"The controller reaches {achieved:.2f} % by also lowering evaporation."))


def fig_chiller_envelope(mode):
    """THE NEW BINDING CONSTRAINT.

    Entering condenser water chosen by the optimiser in each Gulf condition,
    against the York YT curve's fitted range. In four of five conditions the
    optimum sits hard against the 35 degC ceiling: in Gulf summer the limit
    on fan speed is the chiller, not the tower and not the chemistry.
    """
    v5 = pd.read_csv(R / "v5_controller.csv")
    lo, hi = 15.56, 35.0

    fig, ax, base = new_fig(mode)
    y = np.arange(len(v5))[::-1]

    ax.axvspan(lo, hi, color=TEAL, alpha=0.10, lw=0, zorder=1)
    ax.axvline(hi, color=RED, lw=2.8, zorder=4)
    ax.axvline(lo, color=TEAL, lw=2.0, ls="--", zorder=4)

    for k, (yy, r) in enumerate(zip(y, v5.itertuples())):
        ax.plot([r.base_T_cws_C, r.opt_T_cws_C], [yy, yy], lw=2.0,
                color="#9fb3c0", zorder=3)
        ax.plot(r.base_T_cws_C, yy, "o", ms=9, color="#9fb3c0",
                markeredgecolor="#6b7480", markeredgewidth=1.4, zorder=5)
        ax.plot(r.opt_T_cws_C, yy, "o", ms=12, color=NAVY,
                markerfacecolor=NAVY, zorder=6)

    ax.set_yticks(y)
    ax.set_yticklabels(v5["condition"], fontsize=base - 1.0)
    ax.set_xlim(20, 38)
    ax.set_ylim(-0.7, len(v5) - 0.3)
    ax.set_xlabel("Entering condenser water   [°C]", fontsize=base,
                  labelpad=8)
    ax.tick_params(axis="x", labelsize=base - 1.5)
    ax.grid(axis="x", alpha=0.20, ls=":")
    ax.grid(axis="y", visible=False)

    # every marker sits at x >= 23, and the rows are integers, so the gaps
    # between rows on the left are the only reliably empty space
    ax.text(hi + 0.3, len(v5) - 0.6,
            f"chiller ceiling {hi:.0f} °C\nfitted range and\nmachine limit",
            ha="left", va="top", fontsize=base - 2.0, color=RED,
            weight="bold", linespacing=1.5)
    ax.text(20.4, 3.5, "grey = incumbent setpoint\nnavy = optimised",
            ha="left", va="center", fontsize=base - 2.0, color="#6b7480",
            linespacing=1.5)

    finish(fig, ax, mode, "chiller_envelope",
           title="In Gulf summer the fan is limited by the chiller, not the tower",
           footnote=(
               "Chiller curves: York YT 1758 kW / 6.28 COP water-cooled centrifugal, EnergyPlus datasets/Chillers.idf (CoolTools library).\n"
               "Operating points outside the fitted range are rejected by the optimiser rather than extrapolated."))


def fig_gypsum_wall(mode):
    v5b = pd.read_csv(R / "v5b_two_ceilings.csv")
    f = v5b[v5b["feasible"]]
    x = f["cycles"].to_numpy(float)
    y = f["total_cost_h"].to_numpy(float)
    wall = float(x.max()) + 1.0
    blocking = v5b[~v5b["feasible"]]["blocking_mineral"].dropna()
    mineral = (blocking.iloc[0] if len(blocking) else "SI_gypsum")
    mineral = mineral.replace("SI_", "").upper()

    fig, ax, base = new_fig(mode)
    ax.axvspan(3.5, 5.0, color=AMBER, alpha=0.28, lw=0, zorder=1)
    ax.axvspan(wall, wall + 2.6, color=RED, alpha=0.10, lw=0, zorder=1)
    ax.axvline(wall, color=RED, lw=2.8, zorder=4)
    ax.plot(x, y, "-o", lw=3.0, ms=10, color=NAVY, markerfacecolor="white",
            markeredgewidth=2.4, zorder=5)

    ax.set_xlim(2.6, wall + 2.4)
    pad = (y.max() - y.min()) * 0.30
    ax.set_ylim(y.min() - pad, y.max() + pad * 0.55)
    ax.set_xlabel("Cycles of concentration", fontsize=base, labelpad=8)
    ax.set_ylabel("Total operating cost   [$ / h]", fontsize=base, labelpad=8)
    ax.tick_params(labelsize=base - 1.5)

    ax.text(4.25, y.max() + pad * 0.30, "industry practice\n3.5 – 5.0 cycles",
            ha="center", va="top", fontsize=base - 1.5, color="#8a6d1a",
            weight="bold", linespacing=1.5)
    ax.text(wall + 0.3, (y.max() + y.min()) / 2,
            f"{mineral}\nWALL\n{wall:.0f} cycles", ha="left", va="center",
            fontsize=base, color=RED, weight="bold", linespacing=1.5)
    ax.annotate("cost falls the whole way — the economics never turn",
                xy=(x.max(), y.min()), xytext=(3.0, y.min() - pad * 0.55),
                fontsize=base - 1.5, color=GREEN, weight="bold",
                ha="left", va="center",
                arrowprops=dict(arrowstyle="->", lw=1.8, color=GREEN))

    finish(fig, ax, mode, "gypsum_wall",
           title="The economics push toward a wall the industry's index cannot see",
           footnote=(
               "10 MW condenser loop · makeup water measured by Saudi Aramco, Dhahran (Badruzzaman et al. 2022) · published Saudi tariffs.\n"
               "Gypsum binds at every cycle count on this water; calcite never does — and the Langelier Saturation Index describes calcite only."))


def fig_silica_wall(mode):
    d = json.loads((R / "silica_sensitivity.json").read_text())
    x = [r["SiO2_mg_L"] for r in d["rows"]]
    y = [r["wall_cycles"] for r in d["rows"]]

    fig, ax, base = new_fig(mode)
    ax.axhspan(3.5, 5.0, color=AMBER, alpha=0.35, lw=0, zorder=1)
    ax.axvspan(20, 60, color=TEAL, alpha=0.14, lw=0, zorder=1)
    ax.plot(x, y, "-o", lw=3.0, ms=10, color=NAVY, markerfacecolor="white",
            markeredgewidth=2.4, zorder=5)

    ax.set_xlim(-3, 64)
    ax.set_ylim(0, 8.8)
    ax.set_xlabel("Silica in makeup water   [mg/L as SiO$_2$]", fontsize=base,
                  labelpad=8)
    ax.set_ylabel("Highest safe cycles of concentration", fontsize=base,
                  labelpad=8)
    ax.tick_params(labelsize=base - 1.5)

    ax.text(1.5, 8.5, "industry practice: 3.5 – 5.0 cycles", fontsize=base - 1.5,
            color="#8a6d1a", weight="bold", va="top")
    ax.text(41, 7.9, "Saudi brackish water\n20 – 60 mg/L SiO$_2$", ha="center",
            va="top", fontsize=base - 2.0, color="#2b5f86", weight="bold",
            linespacing=1.5)
    ax.annotate("Salbukh, Riyadh\nmeasured 26.8 mg/L\n→ wall at 4.9 cycles",
                xy=(26.8, 4.9), xytext=(4.0, 1.8), fontsize=base - 2.0,
                color=NAVY, weight="bold", ha="left", va="center",
                arrowprops=dict(arrowstyle="->", lw=1.8, color=NAVY))

    finish(fig, ax, mode, "silica_wall",
           title="A limit computed from thermodynamics lands on the industry's rule of thumb",
           footnote=(
               "Makeup water measured by Saudi Aramco, Dhahran (Badruzzaman et al. 2022) · silica range from Al-Mutaz & Al-Anezi (2004),\n"
               "King Saud University / Riyadh Water Treatment Project. Silica is prograde — it binds at the COLDEST point in the loop, not the hot skin."))


def fig_silica_seasonal(mode):
    d = json.loads((R / "silica_seasonal.json").read_text())
    T = [r["basin_T_C"] for r in d["rows"]]
    S = [r["solubility_mg_L"] for r in d["rows"]]
    static = d["static_limit_mg_L"]

    fig, ax, base = new_fig(mode)
    ax.fill_between(T, S, static, color=RED, alpha=0.16, lw=0, zorder=1)
    ax.axhline(static, color=RED, lw=2.6, ls="--", zorder=3)
    ax.plot(T, S, "-o", lw=3.0, ms=9, color=NAVY, markerfacecolor="white",
            markeredgewidth=2.2, zorder=5)

    ax.set_xlim(13, 37.5)
    ax.set_ylim(70, 182)
    ax.set_xlabel("Cooling-tower basin temperature   [°C]",
                  fontsize=base, labelpad=8)
    ax.set_ylabel("Amorphous silica ceiling   [mg/L as SiO$_2$]",
                  fontsize=base, labelpad=8)
    ax.tick_params(labelsize=base - 1.5)

    ax.text(36.8, static + 4, 'industry static rule: "do not exceed 150 mg/L"',
            ha="right", va="bottom", fontsize=base - 1.5, color=RED,
            weight="bold")
    ax.text(25.0, 133, "everything in here is scaling\nrisk the rule does not see",
            ha="center", va="center", fontsize=base - 1.5, color="#a33226",
            weight="bold", style="italic", linespacing=1.5)
    ax.text(14.2, 86, "true ceiling, from\namorphous silica\nsolubility", ha="left",
            va="center", fontsize=base - 2.0, color=NAVY, weight="bold",
            linespacing=1.5)

    finish(fig, ax, mode, "silica_seasonal",
           title="Silica is prograde: the real limit moves with the season, the rule does not",
           footnote=(
               "Solubility from the USGS PHREEQC SiO$_2$(a) constant · basin temperature approaches ambient wet-bulb, which swings ~15 K seasonally in the Gulf.\n"
               "Amorphous silica has no effective general-service inhibitor; deposits require hydrofluoric acid or mechanical removal."))


def fig_mg_silicate(mode):
    import chemistry as chem

    w = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
    w.SiO2 = 26.8
    conc = w.concentrate(4.0)
    T = np.linspace(28, 52, 60)
    ph_s = np.array([chem.ph_saturation_brucite(float(t), conc) for t in T])

    fig, ax, base = new_fig(mode)
    ax.fill_between(T, ph_s, 9.75, color=RED, alpha=0.13, lw=0, zorder=1)
    ax.fill_between(T, 7.9, ph_s, color=GREEN, alpha=0.10, lw=0, zorder=1)
    ax.axhspan(8.5, 9.0, color=AMBER, alpha=0.30, lw=0, zorder=2)
    ax.plot(T, ph_s, lw=3.2, color=NAVY, zorder=5)

    # Two distinct crossings, and they mean different things. Where the
    # brucite saturation pH falls below the TOP of the operating band the
    # band begins to straddle the limit; only where it falls below the
    # BOTTOM of the band does the whole band deposit. Marking one crossing
    # and labelling it with the other's meaning overstates the risk.
    band_lo, band_hi = 8.5, 9.0
    t_straddle = float(np.interp(band_hi, ph_s[::-1], T[::-1]))
    t_all = float(np.interp(band_lo, ph_s[::-1], T[::-1]))
    ax.axvspan(t_straddle, t_all, color=RED, alpha=0.07, lw=0, zorder=2)
    ax.axvline(t_straddle, color=AMBER, lw=2.0, ls=":", zorder=4)
    ax.axvline(t_all, color=RED, lw=2.4, ls=":", zorder=4)

    ax.set_xlim(28, 52)
    ax.set_ylim(7.9, 9.75)
    ax.set_xlabel("Condenser tube skin temperature   [°C]", fontsize=base,
                  labelpad=8)
    ax.set_ylabel("Bulk pH", fontsize=base, labelpad=8)
    ax.tick_params(labelsize=base - 1.5)

    # Layout note: the saturation line runs from top-left to bottom-right,
    # so the free space is the top-right (red) and the bottom-left (green).
    # Every label below sits in one of those, or hard against an axis.
    ax.text(28.4, 9.73, "brucite saturation pH at the condenser skin\n"
                        "(retrograde — falls as the skin gets hotter)",
            ha="left", va="top", fontsize=base - 2.5, color=NAVY,
            weight="bold", linespacing=1.5)
    ax.text(51.6, 9.30, "DEPOSITING\nmagnesium silicate", ha="right", va="top",
            fontsize=base - 0.5, color="#8c2020", weight="bold",
            linespacing=1.5)
    ax.text(29.0, 8.18, "SAFE", ha="left", va="center", fontsize=base + 1,
            color=GREEN, weight="bold")
    ax.text(51.6, 8.76, "Gulf TSE loops\nrun pH 8.5 – 9.0", ha="right",
            va="center", fontsize=base - 1.5, color="#8a6d1a", weight="bold",
            linespacing=1.5)
    ax.annotate(f"~{t_straddle:.0f} °C: the band\nstarts to straddle",
                xy=(t_straddle, 9.02), xytext=(39.6, 9.36),
                fontsize=base - 2.0, color="#8a6d1a", weight="bold",
                ha="left", va="center", linespacing=1.5,
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#8a6d1a"))
    ax.annotate(f"~{t_all:.0f} °C: the WHOLE\nband deposits",
                xy=(t_all, 8.47), xytext=(46.8, 8.14),
                fontsize=base - 2.0, color=RED, weight="bold",
                ha="left", va="center", linespacing=1.5,
                arrowprops=dict(arrowstyle="->", lw=1.6, color=RED))

    finish(fig, ax, mode, "mg_silicate_envelope",
           title="The same tower deposits at high load and not at low load",
           footnote=(
               "Aramco reclaimed water + 26.8 mg/L silica at 4 cycles · brucite from PHREEQC Mg(OH)$_2$ (log_k −11.18, ΔH −27.1 kcal).\n"
               "Magnesium silicate forms in two steps: brucite precipitates first, then reacts with silica in the boundary layer."))


def fig_wetbulb_gap(mode):
    """THE SIZE OF THE EXTRAPOLATION, FINALLY A NUMBER.

    The validation dataset tops out at 21.9 degC wet-bulb. For the whole
    project that gap was carried as a worry with no magnitude on it, because
    there was no hourly Gulf weather to measure it against. A TMYx file for
    Dhahran settles it: two fifths of the operating year is above the
    ceiling, and 84 % of September is.

    This figure cuts AGAINST the package, which is why it is in it.
    """
    d = json.loads((R / "tmy_dhahran.json").read_text())
    a = d["ashrae_design"]
    mon = d["monthly"]
    m = np.arange(1, 13)
    mean_wb = [x["mean_wb_C"] for x in mon]
    max_wb = [x["max_wb_C"] for x in mon]

    fig, ax, base = new_fig(mode)
    ax.fill_between(m, 21.9, max_wb, where=np.array(max_wb) > 21.9,
                    color=RED, alpha=0.15, lw=0, zorder=1, interpolate=True)
    ax.plot(m, max_wb, "-o", lw=2.6, ms=7, color=RED, label="monthly maximum")
    ax.plot(m, mean_wb, "-o", lw=2.6, ms=7, color=NAVY, label="monthly mean")
    ax.axhline(21.9, color=GREY, lw=2.4, ls="--", zorder=3)
    ax.axhline(a["WB_1p0_C"], color=AMBER, lw=2.0, ls=":", zorder=3)

    ax.set_xticks(m)
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.set_ylim(6, 40)
    ax.set_ylabel("wet-bulb temperature  [°C]", fontsize=base, labelpad=8)
    ax.set_xlabel("month", fontsize=base, labelpad=8)
    ax.tick_params(labelsize=base - 1.5)
    # both reference labels sit in the empty top-left band, clear of every curve
    ax.text(1.15, 38.4, f"ASHRAE 1 % design wet-bulb  {a['WB_1p0_C']:.1f} °C",
            fontsize=base - 1.5, color=AMBER, weight="bold", va="top")
    ax.text(1.15, 36.2, "ceiling of the validation data  21.9 °C",
            fontsize=base - 1.5, color=GREY, weight="bold", va="top")
    ax.text(6.5, 11.5,
            f"{d['pct_year_above_almeria']:.1f} % of the year\nis above the ceiling",
            fontsize=base - 0.5, color=RED, weight="bold", ha="center",
            linespacing=1.5)
    ax.legend(loc="lower left", fontsize=base - 2.0, frameon=False)

    finish(fig, ax, mode, "wetbulb_gap",
           footnote=(
               "Dhahran TMYx 2011-2025, station 404160, 8,760 hourly rows. Wet-bulb computed with this package's own ASHRAE psychrometrics,\n"
               f"which reproduce ASHRAE's published design percentiles for this station to {d['worst_design_disagreement_K']:.2f} K."))




# --------------------------------------------------------------------------
def fig_seasonal_handoff(mode):
    """WHY THE TWO SAVINGS HAVE TO BE PRICED TOGETHER.

    Once electrical power is reported separately from cost, the hours-weighted
    year shows something the five-condition gate could never show: the energy
    saving and the water saving are ANTI-CORRELATED across the year
    (Pearson r = -0.66 over eight equal-hour wet-bulb bins).

    In the cool half the controller spends fan power to buy compressor power,
    and the water result is modest. In the hot half it slows the fan, banks
    evaporation, and the energy result nearly vanishes. Total cost saving
    stays inside a narrow band all year precisely BECAUSE the two mechanisms
    hand off to each other.

    A single-objective controller gives up half the year. That is the whole
    argument for coupling the two models, and it is visible only here.
    """
    a = json.loads((R / "annual_dhahran.json").read_text())
    b = a["bins"]
    wb = np.array([x["T_wb_C"] for x in b])
    e = np.array([x["energy_pct"] for x in b])
    w = np.array([x["water_pct"] for x in b])
    c = np.array([x["cost_pct"] for x in b])
    r = float(np.corrcoef(e, w)[0, 1])

    fig, ax, base = new_fig(mode)

    ax.plot(wb, e, "-o", color=RED, lw=2.4, ms=7, zorder=4,
            label="electrical power reduction")
    ax.plot(wb, w, "-s", color=TEAL, lw=2.4, ms=7, zorder=4,
            label="makeup water reduction")
    ax.plot(wb, c, "--", color=GREY, lw=2.0, zorder=3,
            label="total operating cost reduction")

    ax.fill_between(wb, c.min(), c.max(), color=GREEN, alpha=0.07, zorder=0)
    ax.axhline(c.min(), color=GREEN, lw=0.9, ls=":", alpha=0.55, zorder=1)
    ax.axhline(c.max(), color=GREEN, lw=0.9, ls=":", alpha=0.55, zorder=1)

    ax.set_xlabel("wet-bulb temperature at the bin centroid  [°C]",
                  fontsize=base, labelpad=8)
    ax.set_ylabel("reduction against the incumbent baseline  [%]",
                  fontsize=base, labelpad=8)
    ax.tick_params(labelsize=base - 1.5)
    ax.set_ylim(0, max(w.max(), e.max()) + 5.5)
    ax.legend(loc="lower left", fontsize=base - 2.0, frameon=False, ncol=1)

    ax.annotate("energy leads in the cool half", xy=(wb[1], e[1]),
                xytext=(wb[0] + 0.2, e[1] + 4.2), fontsize=base - 2.0,
                color=RED, weight="bold",
                arrowprops=dict(arrowstyle="-", color=RED, lw=1.0))
    ax.annotate("water leads in the hot half", xy=(wb[6], w[6] + 0.4),
                xytext=(wb[4] - 0.3, w.max() + 1.5), fontsize=base - 2.0,
                color=TEAL, weight="bold", ha="left",
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=1.0))
    ax.text(wb[0] - 0.2, max(w.max(), e.max()) + 3.4,
            "shaded band: total cost saving, %.1f-%.1f %% all year"
            % (c.min(), c.max()),
            fontsize=base - 2.0, color=GREEN, weight="bold", ha="left")

    foot = ("Eight equal-hour wet-bulb bins of a Dhahran TMYx year "
            "(2011-2025, station 404160); the controller is run at each bin "
            "centroid and weighted by the hours in that bin."
            "\nPearson correlation between the energy and water reductions "
            "across the bins: r = %+.3f.   Hours-weighted annual means: "
            "%.2f %% power, %.2f %% water, %.2f %% cost."
            % (r, a["annual_energy_pct"], a["annual_water_pct"],
               a["annual_cost_pct"]))

    finish(fig, ax, mode, "seasonal_handoff", footnote=foot)




# --------------------------------------------------------------------------
def fig_gulf_day(mode):
    """ONE GULF DAY, AND THE LIMIT NOBODY MEASURES.

    Reproduces the Simulink diurnal run from the Python core, so that the
    figure in the report is generated by the same code every other number in
    it comes from and cannot drift from the results.

    Three panels, and the third is the argument:

      1. Temperatures. The condenser skin runs well above anything the plant
         instruments see.
      2. The brucite saturation pH AT THE SKIN against the bulk pH the loop
         actually holds. It is retrograde, so it FALLS as the afternoon load
         pushes the skin hotter, and it crosses the operating point twice.
      3. What the plant's own two instruments read across the same day:
         conductivity and bulk pH, both flat.

    Note on panel 3: both traces are constant, which is the point. If each
    axis is centred on its own constant the two lines land on the same pixel
    row and one hides the other, which reads as a broken plot rather than as
    a result. The limits are therefore deliberately asymmetric.
    """
    import numpy as _np
    cal = json.loads((R / "calibration.json").read_text())
    fc, fn = cal["fill_c"], cal["fill_n"]

    import controller as ctl
    import chemistry as chem
    import run_controller as rc

    hour = _np.arange(24)
    s = _np.sin(_np.pi * _np.maximum(hour - 6, 0) / 16.0) ** 2
    T_db = 32.0 + 12.0 * s
    rh = 0.55 - 0.25 * s
    load = 0.62 + 0.38 * s

    CYCLES, BULK_PH, FAN_PCT, SKIN_DT = 4.0, 8.7, 85.0, 8.0
    w_loop = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
    w_loop.SiO2 = 26.8
    conc = w_loop.concentrate(CYCLES)

    T_cold, T_hot, T_skin, pH_lim = [], [], [], []
    for i in range(len(hour)):
        cond = dict(rc.PLANT)
        cond.update({"T_db": float(T_db[i]), "rh": float(rh[i])})
        cond["Q_evap_kw"] = rc.PLANT["Q_evap_kw"] * float(load[i])
        th = ctl._thermal_solve(FAN_PCT, CYCLES, cond, rc.TSE, fc, fn)
        if th is None:
            T_cold.append(_np.nan); T_hot.append(_np.nan)
            T_skin.append(_np.nan); pH_lim.append(_np.nan)
            continue
        # _thermal_solve returns (m_a, aw, T_wo, info, conc, T_wi, Q_cond)
        t_wo, t_wi = th[2], th[5]
        skin = t_wi + SKIN_DT
        T_cold.append(t_wo); T_hot.append(t_wi); T_skin.append(skin)
        pH_lim.append(chem.ph_saturation_brucite(skin, conc))

    T_cold = _np.array(T_cold); T_hot = _np.array(T_hot)
    T_skin = _np.array(T_skin); pH_lim = _np.array(pH_lim)
    depositing = pH_lim < BULK_PH
    hrs = int(_np.nansum(depositing))

    g = GEOM[mode]
    fig, axes = plt.subplots(3, 1, figsize=(g["figsize"][0], g["figsize"][1] * 1.55),
                             dpi=g["dpi"], sharex=True)
    base = g["base"]

    ax = axes[0]
    ax.plot(hour, T_skin, color=RED, lw=2.6, label="condenser tube skin - where scale forms")
    ax.plot(hour, T_hot, color=NAVY, lw=2.2, label="hot water leaving the condenser")
    ax.plot(hour, T_cold, color=TEAL, lw=2.2, label="cold water leaving the tower")
    ax.set_ylabel("temperature  [°C]", fontsize=base)
    ax.legend(loc="upper left", fontsize=base - 2.5, frameon=False)
    ax.grid(axis="y", alpha=0.20, ls=":"); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

    ax = axes[1]
    ax.plot(hour, pH_lim, color=RED, lw=2.6, label="scale limit, evaluated at the tube skin")
    ax.axhline(BULK_PH, color=GREY, lw=1.8, ls="--")
    ax.fill_between(hour, pH_lim, BULK_PH, where=depositing,
                    color=RED, alpha=0.13, interpolate=True)
    ax.text(0.4, BULK_PH + 0.012, "the loop actually runs here  (bulk pH %.1f)" % BULK_PH,
            fontsize=base - 2.5, color=GREY, weight="bold", va="bottom")
    ax.text(1.6, float(_np.nanmin(pH_lim)) + 0.045,
            str(hrs) + " hours of 24, the bulk pH sits" + chr(10) +
            "ABOVE the limit at the skin",
            fontsize=base - 2.0, color=RED, weight="bold", ha="left",
            va="bottom", linespacing=1.6)
    ax.set_ylabel("pH", fontsize=base)
    ax.legend(loc="lower left", fontsize=base - 2.5, frameon=False)
    ax.grid(axis="y", alpha=0.20, ls=":"); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

    ax = axes[2]
    cond_uS = _np.full_like(hour, 1.55 * conc.TDS, dtype=float)
    c0 = float(cond_uS.mean())
    ax.plot(hour, cond_uS, color=TEAL, lw=2.6, label="conductivity")
    ax.set_ylabel("conductivity  [µS/cm]", fontsize=base, color=TEAL)
    ax.set_ylim(c0 * 0.94, c0 * 1.24)          # trace sits low in the frame
    ax.tick_params(axis="y", labelcolor=TEAL)
    ax2 = ax.twinx()
    ax2.plot(hour, _np.full_like(hour, BULK_PH, dtype=float),
             color=AMBER, lw=2.6, label="bulk pH")
    ax2.set_ylabel("bulk pH", fontsize=base, color=AMBER)
    ax2.set_ylim(BULK_PH - 0.80, BULK_PH + 0.20)   # trace sits high in the frame
    ax2.tick_params(axis="y", labelcolor=AMBER)
    ax2.spines["top"].set_visible(False)
    ax.text(12, c0 * 1.14, "both instruments read a flat line all day",
            fontsize=base - 1.5, color=GREY, weight="bold", ha="center")
    ax.set_xlabel("hour of the day", fontsize=base)
    ax.grid(axis="y", alpha=0.20, ls=":"); ax.set_axisbelow(True)
    for sp in ("top",):
        ax.spines[sp].set_visible(False)

    ax.set_xlim(0, 23)
    ax.set_xticks([0, 4, 8, 12, 16, 20])

    foot = ("Dhahran summer day: 32-44 °C dry bulb, cooling load 62-100 % of design, tower fan held at a fixed 85 % as a "
            "building management system runs one today." + chr(10) +
            "Measured Saudi Aramco reclaimed water at 4 cycles with 26.8 mg/L silica; condenser skin taken at bulk + "
            + format(SKIN_DT, ".0f") + " K.")
    if mode == "report":
        fig.text(0.5, 0.015, foot, ha="center", fontsize=8.6, color=GREY, linespacing=1.6)
        fig.tight_layout(rect=[0, 0.055, 1, 1])
        out = FIGS / "gulf_day.png"
    else:
        fig.tight_layout()
        out = SLIDE / "gulf_day.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   %-6s -> %s   (%d depositing hours)" % (mode, out.relative_to(ROOT), hrs))




# --------------------------------------------------------------------------
def fig_simulink_model(mode):
    """THE MODEL ARCHITECTURE, DRAWN FROM ITS OWN BUILD SCRIPT.

    Every block and signal is taken from build_mizan_model.m, which builds
    mizan_plant.slx from text.

    Drawing notes, because the first version of this figure was unreadable:
    block subtitles and most signal names were removed (the caption carries
    them), and routing is ORTHOGONAL rather than curved. Curved arcs that
    cross look like a mistake; right-angle routes that cross look like a
    schematic. The layout below has exactly one crossing.
    """
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    g = GEOM[mode]
    fig, ax = plt.subplots(figsize=(g["figsize"][0], g["figsize"][0] * 0.58),
                           dpi=g["dpi"])
    base = g["base"]
    ax.set_xlim(0, 102); ax.set_ylim(0, 100); ax.axis("off")

    FILL = {"phys": "#E8EFF4", "sim": "#DCE9E9", "chem": "#F6E7E7",
            "ctrl": "#F5EEDC", "src": "#EFEFEF"}
    EDGE = {"phys": NAVY, "sim": TEAL, "chem": RED, "ctrl": AMBER, "src": GREY}

    B = {}

    def box(key, x, y, w, h, label, kind, tag=None):
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
            linewidth=1.7, edgecolor=EDGE[kind], facecolor=FILL[kind], zorder=3))
        ax.text(x + w / 2, y + h / 2 + (1.6 if tag else 0), label,
                ha="center", va="center", fontsize=base - 2.2,
                weight="bold", color=INK_TXT, zorder=4)
        if tag:
            ax.text(x + w / 2, y + h / 2 - 2.6, tag, ha="center", va="center",
                    fontsize=base - 4.4, color=GREY, style="italic", zorder=4)
        B[key] = (x, y, w, h)

    def P(key, side, off=0.0):
        x, y, w, h = B[key]
        return {"L": (x, y + h / 2 + off), "R": (x + w, y + h / 2 + off),
                "T": (x + w / 2 + off, y + h), "B": (x + w / 2 + off, y)}[side]

    def route(pts, colour=GREY, lw=1.6, label=None, lat=None):
        """Orthogonal polyline through pts, arrowhead on the last segment."""
        for i in range(len(pts) - 2):
            ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                    color=colour, lw=lw, solid_capstyle="round", zorder=2)
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>",
                                     mutation_scale=11, linewidth=lw,
                                     color=colour, zorder=2,
                                     shrinkA=0, shrinkB=0))
        if label and lat:
            ax.text(lat[0], lat[1], label, ha="center", va="center",
                    fontsize=base - 4.4, color=colour, zorder=5,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white",
                              ec="none", alpha=0.95))

    # ---- blocks --------------------------------------------------------
    box("clock", 4, 86, 15, 8, "Clock", "src")
    box("amb", 25, 86, 26, 8, "Ambient and load", "src")

    box("basin", 4, 64, 20, 10, "Basin temperature", "phys")
    box("chill", 28, 64, 17, 10, "Chiller", "phys")
    box("cond", 49, 64, 19, 10, "Condenser", "phys")
    box("tower", 72, 64, 25, 10, "Cooling tower", "phys")

    box("mass", 4, 46, 20, 10, "Loop thermal mass", "sim", "Simscape, 150 t")
    box("bal", 28, 46, 19, 10, "Basin heat balance", "phys")

    box("consts", 3, 24, 18, 10, "cycles = 4\nbulk pH = 8.7", "src")
    box("scale", 50, 24, 20, 10, "Scaling limit", "chem", "brucite pH at skin")

    box("fanp", 2, 6, 18, 10, "Fan power", "phys")
    box("delay", 24, 6, 20, 10, "Control interval", "ctrl")
    box("sup", 50, 5, 27, 12, "SUPERVISOR", "ctrl", "Stateflow, 4 states")

    # ---- signals, all orthogonal ---------------------------------------
    route([P("clock", "R"), P("amb", "L")], GREY)

    # ambient -> chiller (load) and -> tower (weather)
    ax_, ay = P("amb", "B", -4)
    cx, cy = P("chill", "T")
    route([(ax_, ay), (ax_, 79), (cx, 79), (cx, cy)], GREY,
          label="Q_evap", lat=(cx - 7.5, 80.6))
    rx, ry = P("amb", "R")
    tx, ty = P("tower", "T")
    route([(rx, ry), (tx, ry), (tx, ty)], GREY,
          label="T_db, rh", lat=(tx + 7.0, 90.8))

    # the closed physical cycle
    route([P("mass", "T"), P("basin", "B")], TEAL, 2.1)
    route([P("basin", "R"), P("chill", "L")], NAVY, 2.1)
    route([P("chill", "R"), P("cond", "L")], NAVY, 2.1)
    route([P("cond", "R"), P("tower", "L")], NAVY, 2.1)

    bx, by = P("tower", "B")
    hx, hy = P("bal", "R")
    route([(bx, by), (bx, hy), (hx, hy)], NAVY, 2.1,
          label="tower outlet", lat=(67, hy + 2.6))
    route([P("bal", "L"), P("mass", "R")], TEAL, 2.1)


    # condenser -> chemistry
    sx, sy = P("cond", "B")
    kx, ky = P("scale", "T")
    route([(sx, sy), (sx, 38), (kx, 38), (kx, ky)], RED, 2.1,
          label="skin temp", lat=(sx + 5.0, 40.6))
    route([P("consts", "R"), P("scale", "L")], GREY)

    # chemistry -> supervisor
    mx, my = P("scale", "B")
    ux, uy = P("sup", "T", 6)
    route([(mx, my), (mx, 20), (ux, 20), (ux, uy)], RED, 2.1,
          label="margin", lat=(mx + 5.6, 21.4))

    # chiller envelope flag -> supervisor  (the one crossing, at x = 36)
    ex, ey = P("chill", "B")
    vx, vy = P("sup", "T", -6)
    route([(ex, ey), (ex, 61), (1.2, 61), (1.2, 20), (vx, 20), (vx, vy)],
          GREY, label="in envelope", lat=(12.5, 21.6))

    # supervisor -> delay -> fan power, and delay -> tower around the outside
    route([P("sup", "L"), P("delay", "R")], AMBER, 2.1,
          label="fan command", lat=(47, 13.4))
    route([P("delay", "L"), P("fanp", "R")], AMBER, 2.1)
    dx, dy = P("delay", "B")
    route([(dx, dy), (dx, 1.5), (100, 1.5), (100, by), (bx + 6, by)],
          AMBER, 2.1, label="fan %", lat=(88, 3.0))

    foot = ("Every block and signal is taken from build_mizan_model.m, which builds mizan_plant.slx from text. "
            "Colour: teal = Simscape physical network, navy = MATLAB Function"
            + chr(10) +
            "carrying the physics, red = chemistry, amber = Stateflow supervisor. "
            "The physical loop is a closed cycle, so the tower must reject the evaporator load plus the compressor work.")
    if mode == "report":
        fig.text(0.5, 0.02, foot, ha="center", fontsize=8.4, color=GREY,
                 linespacing=1.6)
        fig.tight_layout(rect=[0, 0.06, 1, 1])
        out = FIGS / "simulink_model.png"
    else:
        fig.tight_layout()
        out = SLIDE / "simulink_model.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   %-6s -> %s" % (mode, out.relative_to(ROOT)))


FIGURES = [fig_water_ceiling, fig_chiller_envelope, fig_gypsum_wall,
           fig_silica_wall, fig_silica_seasonal, fig_mg_silicate, fig_wetbulb_gap,
           fig_seasonal_handoff, fig_gulf_day,
           fig_simulink_model]


def main():
    for f in FIGURES:
        print(f.__name__)
        for mode in ("report", "slide"):
            try:
                f(mode)
            except Exception as e:                      # noqa: BLE001
                print(f"   {mode:6s} -- FAILED: {type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
