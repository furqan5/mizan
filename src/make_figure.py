"""Discovery figure. Layout is planned explicitly so nothing overlaps.

The curve descends left to right, so the free regions are bottom-left and
top-right. Every annotation is placed in one of those, or outside the data
range entirely. No legend: there is one series and the y-axis names it.
"""
import json, pathlib, warnings
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
R = ROOT / "results"
d = pd.read_csv(R / "v5b_two_ceilings.csv")
cs = json.loads((R / "controller_summary.json").read_text())["summary"]
f = d[d.feasible]
phys = cs["physical_ceiling_cycles"]

ymin, ymax = f.total_cost_h.min(), f.total_cost_h.max()
span = ymax - ymin
lo = ymin - 0.30 * span
hi = ymax + 0.18 * span
xlo, xhi = 2.5, 9.6
wall_x = phys - 0.5

fig, ax = plt.subplots(figsize=(10, 5.8), dpi=200)

# --- bands first, so the curve draws on top -------------------------------
ax.axvspan(3.5, 5.0, color="#f4c95d", alpha=0.35, lw=0, zorder=1)
ax.axvspan(wall_x, xhi, color="#c0392b", alpha=0.15, lw=0, zorder=1)
ax.axvline(wall_x, color="#c0392b", lw=3.0, zorder=2)

# --- the data -------------------------------------------------------------
ax.plot(f.cycles, f.total_cost_h, "-o", lw=2.8, ms=9, color="#14425f",
        markerfacecolor="white", markeredgewidth=2.2, zorder=5)

# --- annotations, each in verified free space -----------------------------
# top strip, above all data: band labels
ax.text(4.25, ymax + 0.115 * span, "industry practice\n3.5 – 5.0 cycles",
        ha="center", va="center", fontsize=10, color="#8a6d1a", weight="bold")

# right band, vertically centred: the wall. Curve never enters x > 7.
ax.text((wall_x + xhi) / 2, ymin + 0.62 * span, "GYPSUM\nWALL",
        ha="center", va="center", fontsize=17, weight="bold", color="#c0392b")
ax.text((wall_x + xhi) / 2, ymin + 0.30 * span,
        "acid cannot\nmove this", ha="center", va="center",
        fontsize=10.5, color="#c0392b", style="italic")

# bottom-left, below the curve: the direction of the economics
# strictly below the curve minimum, so nothing crosses the data
arrow_y = ymin - 0.09 * span
ax.annotate("", xy=(7.05, arrow_y), xytext=(3.05, arrow_y),
            arrowprops=dict(arrowstyle="-|>", lw=2.6, color="#1e7a4d"))
ax.text(5.05, ymin - 0.20 * span,
        "cost falls the whole way — the economics never turn",
        ha="center", va="center", fontsize=10.5, color="#1e7a4d", weight="bold")

ax.set_xlim(xlo, xhi)
ax.set_ylim(lo, hi)
ax.set_xticks([3, 4, 5, 6, 7, 8, 9])
ax.set_xlabel("Cycles of concentration", fontsize=12, labelpad=8)
ax.set_ylabel("Total operating cost   [$ / h]", fontsize=12, labelpad=8)
ax.set_title("The economics push toward a wall the industry's index cannot see",
             fontsize=14.5, weight="bold", pad=16)
ax.grid(axis="y", alpha=0.20, ls=":")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.text(0.5, 0.02,
         "10 MW condenser loop · makeup water measured by Saudi Aramco, Dhahran (Badruzzaman et al. 2022) · published Saudi tariffs\n"
         "Gypsum binds at every cycle count on this water; calcite never does — and the Langelier Saturation Index describes calcite only.",
         ha="center", fontsize=8.6, color="#4a4a4a", linespacing=1.6)
fig.tight_layout(rect=[0, 0.075, 1, 1])
out = ROOT / "figs" / "gypsum_wall.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("written ->", out)
