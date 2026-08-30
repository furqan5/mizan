"""The silica figure: a first-principles wall landing on empirical practice."""
import json, pathlib, warnings
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "results" / "silica_sensitivity.json").read_text())
x = [r["SiO2_mg_L"] for r in d["rows"]]
y = [r["wall_cycles"] for r in d["rows"]]

fig, ax = plt.subplots(figsize=(10, 5.8), dpi=200)

# industry practice band, horizontal
ax.axhspan(3.5, 5.0, color="#f4c95d", alpha=0.40, lw=0, zorder=1)
# Saudi measured silica range, vertical
ax.axvspan(20, 60, color="#5b8fb9", alpha=0.16, lw=0, zorder=1)

ax.plot(x, y, "-o", lw=2.8, ms=9, color="#14425f",
        markerfacecolor="white", markeredgewidth=2.2, zorder=5)

ax.set_xlim(-3, 64)
ax.set_ylim(0, 8.6)
ax.set_xlabel("Silica in makeup water   [mg/L as SiO$_2$]", fontsize=12, labelpad=8)
ax.set_ylabel("Highest safe cycles of concentration", fontsize=12, labelpad=8)
ax.set_title("A limit computed from thermodynamics lands on the industry's rule of thumb",
             fontsize=14, weight="bold", pad=16)

# labels in verified free space: curve descends left->right, so
# bottom-left and top-right are the crowded zones -> use top-left and mid-right
ax.text(1.5, 8.15, "industry practice: 3.5 – 5.0 cycles",
        fontsize=10.5, color="#8a6d1a", weight="bold", va="top")
ax.text(40, 7.6, "Saudi brackish water\n20 – 60 mg/L SiO$_2$",
        ha="center", va="top", fontsize=10, color="#2b5f86", weight="bold")
ax.annotate("Salbukh, Riyadh\nmeasured 26.8 mg/L\n→ wall at 4.9 cycles",
            xy=(26.8, 4.9), xytext=(4.0, 1.7),
            fontsize=10, color="#14425f", weight="bold",
            ha="left", va="center",
            arrowprops=dict(arrowstyle="->", lw=1.8, color="#14425f"))
ax.text(0.5, 6.55, "gypsum binds\n(no silica reported)", fontsize=9.5,
        color="#666", va="center")

ax.grid(axis="y", alpha=0.20, ls=":")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.text(0.5, 0.02,
         "Makeup water measured by Saudi Aramco, Dhahran (Badruzzaman et al. 2022) · silica range from Al-Mutaz & Al-Anezi (2004),\n"
         "King Saud University / Riyadh Water Treatment Project. Silica is prograde — it binds at the COLDEST point in the loop, not the hot skin.",
         ha="center", fontsize=8.6, color="#4a4a4a", linespacing=1.6)
fig.tight_layout(rect=[0, 0.075, 1, 1])
out = ROOT / "figs" / "silica_wall.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("written ->", out)
