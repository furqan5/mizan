

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
    ax.legend(loc="upper center", fontsize=base - 2.0, frameon=False, ncol=1)

    ax.annotate("energy leads in the cool half", xy=(wb[1], e[1]),
                xytext=(wb[0] + 0.2, e[1] + 4.2), fontsize=base - 2.0,
                color=RED, weight="bold",
                arrowprops=dict(arrowstyle="-", color=RED, lw=1.0))
    ax.annotate("water leads in the hot half", xy=(wb[6], w[6]),
                xytext=(wb[3] + 0.4, w.max() + 2.4), fontsize=base - 2.0,
                color=TEAL, weight="bold", ha="left",
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=1.0))
    ax.text(wb.mean(), c.min() - 2.4,
            "total cost saving stays between "
            "%.1f %% and %.1f %% all year" % (c.min(), c.max()),
            fontsize=base - 2.0, color=GREEN, weight="bold", ha="center")

    foot = ("Eight equal-hour wet-bulb bins of a Dhahran TMYx year "
            "(2011-2025, station 404160); the controller is run at each bin "
            "centroid and weighted by the hours in that bin."
            "\nPearson correlation between the energy and water reductions "
            "across the bins: r = %+.3f.   Hours-weighted annual means: "
            "%.2f %% power, %.2f %% water, %.2f %% cost."
            % (r, a["annual_energy_pct"], a["annual_water_pct"],
               a["annual_cost_pct"]))

    finish(fig, ax, mode, "seasonal_handoff", footnote=foot)

