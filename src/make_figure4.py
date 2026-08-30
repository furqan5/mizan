"""Gate V6 figure: the magnesium silicate deposition envelope."""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import chemistry as chem

ROOT = pathlib.Path(__file__).resolve().parents[1]
w = chem.balance_sodium(chem.ARAMCO_RECLAIMED); w.SiO2 = 26.8
conc = w.concentrate(4.0)

T = np.linspace(28, 52, 60)
phs = np.array([chem.ph_saturation_brucite(t, conc) for t in T])

fig, ax = plt.subplots(figsize=(10, 5.8), dpi=200)

# depositing region: above the curve
ax.fill_between(T, phs, 9.8, color="#c0392b", alpha=0.13, lw=0, zorder=1)
ax.fill_between(T, 7.8, phs, color="#2a7f4f", alpha=0.10, lw=0, zorder=1)

# Gulf operating pH band
ax.axhspan(8.5, 9.0, color="#f4c95d", alpha=0.45, lw=0, zorder=2)

ax.plot(T, phs, lw=3.0, color="#14425f", zorder=5)

ax.set_xlim(28, 52)
ax.set_ylim(7.9, 9.75)

# labels, all in verified free space
ax.text(30.0, 9.55, "DEPOSITING\nmagnesium silicate", fontsize=12, weight="bold",
        color="#a33226", va="top", ha="left")
ax.text(30.0, 8.35, "SAFE", fontsize=12, weight="bold",
        color="#1e6b42", va="center", ha="left")
ax.text(51.3, 8.75, "Gulf TSE loops\nrun pH 8.5 – 9.0", fontsize=10,
        weight="bold", color="#8a6d1a", va="center", ha="right")
ax.text(37.5, 8.05, "brucite saturation pH at the condenser skin\n"
        "(retrograde — falls as the skin gets hotter)",
        fontsize=10, color="#14425f", weight="bold", ha="center", va="center")

ax.axvline(46.0, color="#a33226", lw=1.6, ls=":", zorder=4)
ax.text(46.3, 9.28, "above ~46 °C skin the\nwhole operating band deposits",
        fontsize=9.5, color="#a33226", va="center", ha="left")

ax.set_xlabel("Condenser tube skin temperature   [°C]", fontsize=11.5, labelpad=8)
ax.set_ylabel("Bulk pH", fontsize=11.5, labelpad=8)
ax.set_title("The same tower deposits at high load and not at low load — a fixed pH setpoint cannot see this",
             fontsize=13, weight="bold", pad=16)
ax.grid(alpha=0.18, ls=":")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.text(0.5, 0.02,
         "Aramco reclaimed water + 26.8 mg/L silica at 4 cycles · brucite from PHREEQC Mg(OH)$_2$ (log_k −11.18, ΔH −27.1 kcal)\n"
         "Magnesium silicate forms in two steps: brucite precipitates first, then reacts with silica in the boundary layer.",
         ha="center", fontsize=8.6, color="#4a4a4a", linespacing=1.6)
fig.tight_layout(rect=[0, 0.075, 1, 1])
out = ROOT / "figs" / "mg_silicate_envelope.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("written ->", out)
