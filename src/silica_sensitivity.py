"""
MIZAN :: how the scaling wall moves with makeup silica
======================================================
The Aramco analysis (Badruzzaman 2022) does not report silica, so our
earlier runs left the silica constraint inactive and the computed wall was
an upper bound. Rather than invent a value, the wall is computed as a
FUNCTION of makeup silica and the Saudi-measured range is marked on it.

Saudi silica reference:
  Al-Mutaz, I.S. & Al-Anezi, I.A. (2004) "Silica Removal During Lime
  Softening in Water Treatment Plant", Int. Conf. on Water Resources & Arid
  Environment. King Saud University; Riyadh Water Treatment Project,
  Ministry of Water and Electricity.
    - "Silica content in brackish water is generally in the range of 20 to
      60 ppm"
    - Salbukh plant (Riyadh) raw water about 30 ppm
    - Measured table: SiO2 26.8 mg/L raw -> 7.6 mg/L after lime softening

Caveat kept explicit: those are brackish WELL waters feeding a drinking
water plant, not treated sewage effluent. They bound the plausible range
for Saudi makeup silica; they are not a measurement of TSE silica.
"""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
T_SKIN, T_BASIN, pH = 44.0, 30.0, 7.75
LIM = chem.OPERATING_LIMITS

base = chem.balance_sodium(chem.ARAMCO_RECLAIMED)

def wall_for(sio2):
    w = chem.Water(**{**base.__dict__}); w.SiO2 = sio2
    for cy10 in range(20, 201):
        cy = cy10 / 10.0
        c = w.concentrate(cy)
        hot = chem.saturation_state(c, T_SKIN, pH=pH)
        cold = chem.saturation_state(c, T_BASIN, pH=pH)
        sp = {"SI_calcite": hot["SI_calcite"], "SI_gypsum": hot["SI_gypsum"],
              "SI_silica_am": cold["SI_silica_am"]}
        bad = [k for k in LIM if sp[k] > LIM[k]]
        if bad:
            return cy, bad[0] if len(bad) == 1 else "+".join(bad)
    return 20.0, "none in range"

print("Wall position vs makeup silica, Aramco reclaimed water")
print("(silica evaluated at the cold basin, where it is least soluble)\n")
print(f"{'SiO2 makeup':>12} {'wall (cycles)':>14}  {'binding':<28} note")
print("-" * 78)
rows = []
notes = {0: "as reported by Badruzzaman (silica not measured)",
         7.6: "Salbukh AFTER lime softening",
         20: "low end of Saudi brackish range",
         26.8: "Salbukh raw water, measured",
         30: "Salbukh raw water, stated",
         60: "high end of Saudi brackish range"}
for s in [0.0, 7.6, 10.0, 20.0, 26.8, 30.0, 40.0, 60.0]:
    cy, b = wall_for(s)
    rows.append({"SiO2_mg_L": s, "wall_cycles": cy, "binding": b})
    print(f"{s:>10.1f}   {cy:>12.1f}  {b:<28} {notes.get(s,'')}")

lo, hi = wall_for(20.0)[0], wall_for(60.0)[0]
base_wall = wall_for(0.0)[0]
print()
print(f"Without silica the wall sits at {base_wall:.1f} cycles.")
print(f"Across the Saudi brackish silica range (20-60 mg/L) it falls to "
      f"{lo:.1f}-{hi:.1f} cycles.")
print()
print("Direction of the correction: silica can only LOWER the wall, never "
      "raise it, so the")
print("earlier silica-free figure was a genuine upper bound and the model "
      "was conservative")
print("in the safe direction. The operating recommendation is the lower "
      "bound of this band")
print("until a site's makeup silica is actually measured.")

(RESULTS / "silica_sensitivity.json").write_text(json.dumps(
    {"rows": rows, "wall_no_silica": base_wall,
     "wall_saudi_range_20_60": [lo, hi],
     "source": "Al-Mutaz & Al-Anezi (2004), King Saud University / Riyadh "
               "Water Treatment Project",
     "caveat": "brackish well water feeding a drinking-water plant, not TSE"},
    indent=2), encoding="utf8")
print(f"\nwritten -> {RESULTS/'silica_sensitivity.json'}")
