"""The seasonal silica ceiling: the industry's static rule is non-conservative."""
import json, pathlib, warnings
warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parents[1]
d = json.loads((ROOT / "results" / "silica_seasonal.json").read_text())
T = [r["basin_T_C"] for r in d["rows"]]
S = [r["solubility_mg_L"] for r in d["rows"]]
static = d["static_limit_mg_L"]

fig, ax = plt.subplots(figsize=(10, 5.8), dpi=200)

# the unsafe zone: between the true ceiling and the static rule
ax.fill_between(T, S, static, color="#c0392b", alpha=0.16, lw=0, zorder=1)

ax.axhline(static, color="#c0392b", lw=2.6, ls="--", zorder=3)
ax.plot(T, S, "-o", lw=2.9, ms=9, color="#14425f",
        markerfacecolor="white", markeredgewidth=2.2, zorder=5)

ax.set_xlim(13, 37.5)
ax.set_ylim(70, 178)

# labels, all in verified free space
ax.text(36.8, static + 5, 'industry static rule: "do not exceed 150 mg/L"',
        ha="right", va="bottom", fontsize=10.5, color="#c0392b", weight="bold")
ax.text(24.5, 133, "everything in here is\nscaling risk the rule does not see",
        ha="center", va="center", fontsize=10.5, color="#a33226",
        weight="bold", style="italic")
ax.text(14.2, 86, "true ceiling, from\namorphous silica\nsolubility",
        ha="left", va="center", fontsize=10, color="#14425f", weight="bold")
ax.annotate("winter basin\n37 % non-conservative", xy=(15, 95), xytext=(19.5, 76),
            fontsize=9.5, color="#14425f", ha="center", va="center",
            arrowprops=dict(arrowstyle="->", lw=1.6, color="#14425f"))

ax.set_xlabel("Cooling-tower basin temperature   [°C]  —  tracks ambient wet-bulb",
              fontsize=11.5, labelpad=8)
ax.set_ylabel("Amorphous silica ceiling   [mg/L as SiO$_2$]", fontsize=11.5, labelpad=8)
ax.set_title("Silica is prograde: the real limit moves with the season, the rule does not",
             fontsize=14, weight="bold", pad=16)
ax.grid(axis="y", alpha=0.20, ls=":")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.text(0.5, 0.02,
         "Solubility from the USGS PHREEQC SiO$_2$(a) constant · basin temperature approaches ambient wet-bulb, which swings ~15 K seasonally in the Gulf.\n"
         "Amorphous silica has no effective general-service inhibitor; deposits require hydrofluoric acid or mechanical removal.",
         ha="center", fontsize=8.6, color="#4a4a4a", linespacing=1.6)
fig.tight_layout(rect=[0, 0.075, 1, 1])
out = ROOT / "figs" / "silica_seasonal.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("written ->", out)
