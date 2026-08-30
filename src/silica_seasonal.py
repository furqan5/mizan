"""
MIZAN :: the silica limit is not a constant, and industry treats it as one
=========================================================================
Gemini's literature sweep surfaced the decisive sentence: commercial water
treatment practice "usually defaults to setting a static bulk-water
concentration limit (e.g. do not exceed 150 mg/L) REGARDLESS of transient
basin temperatures."

Amorphous silica is prograde -- solubility RISES with temperature. A Gulf
tower basin sits near the ambient wet-bulb, which swings roughly 15 K
between winter and summer. So the true silica ceiling moves with the
season, and a static rule is wrong in both directions:

  cold months -> real solubility is LOWER than the static rule assumes
                 -> the plant is scaling while its rule says it is safe
  hot months  -> real solubility is HIGHER than the static rule assumes
                 -> the plant is blowing down water it did not need to

That is the headroom, and it is not a claim about running past a wall. It
is a claim that the wall moves and nobody tracks it.

Second lever, also from the sweep: a polymaleic silica dispersant
(Acumer 5000 class) is documented to raise the workable silica ceiling from
about 150 to about 250 mg/L in operating towers.
"""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
MW_SIO2 = 60.084

def solubility_mg_L(T_c):
    """Amorphous silica solubility [mg/L as SiO2] at temperature T_c,
    from the PHREEQC SiO2(a) constant used throughout the model."""
    return 10.0 ** chem.log_k_silica_am(T_c) * MW_SIO2 * 1000.0

STATIC_LIMIT = 150.0        # the industry's fixed rule [C]
DISPERSANT_LIMIT = 250.0    # Acumer 5000 class, documented ceiling [C]
MAKEUP_SIO2 = 26.8          # Salbukh measured, Riyadh [C]

print("Amorphous silica solubility vs tower-basin temperature")
print("(basin sits near ambient wet-bulb, so this is the seasonal swing)\n")
print(f"{'basin T':>9} {'solubility':>12} {'max COC at':>12}   {'vs static 150 mg/L rule'}")
print(f"{'[degC]':>9} {'[mg/L]':>12} {'26.8 mg/L':>12}")
print("-" * 74)
rows = []
seasons = {15.0: "Gulf winter night", 20.0: "winter day",
           25.0: "shoulder", 30.0: "summer", 35.0: "summer peak"}
for T in [15.0, 20.0, 25.0, 30.0, 35.0]:
    s = solubility_mg_L(T)
    coc = s / MAKEUP_SIO2
    delta = 100.0 * (s - STATIC_LIMIT) / STATIC_LIMIT
    verdict = ("static rule UNSAFE by %.0f%%" % -delta) if delta < 0 else \
              ("static rule leaves %.0f%% on the table" % delta)
    rows.append({"basin_T_C": T, "solubility_mg_L": s, "max_COC": coc,
                 "pct_vs_static": delta, "season": seasons[T]})
    print(f"{T:>9.0f} {s:>12.0f} {coc:>12.1f}   {verdict}")

s15, s35 = solubility_mg_L(15.0), solubility_mg_L(35.0)
print()
print(f"Seasonal swing in the true ceiling: {s15:.0f} -> {s35:.0f} mg/L, "
      f"a factor of {s35/s15:.2f}.")
print(f"In cycles at {MAKEUP_SIO2:.1f} mg/L makeup: "
      f"{s15/MAKEUP_SIO2:.1f} -> {s35/MAKEUP_SIO2:.1f} COC.")
print()
print("With a documented silica dispersant (Acumer 5000 class, ceiling "
      f"{DISPERSANT_LIMIT:.0f} mg/L):")
print(f"   max COC rises to {DISPERSANT_LIMIT/MAKEUP_SIO2:.1f} at "
      f"{MAKEUP_SIO2:.1f} mg/L makeup silica,")
print(f"   versus {STATIC_LIMIT/MAKEUP_SIO2:.1f} on the uninhibited static "
      "rule -- a real, purchasable increment.")
print()
print("The two levers compose. Knowing the ceiling moves seasonally tells "
      "you WHEN you can")
print("safely run high; the dispersant raises HOW high. Neither is "
      "available to a fixed")
print("conductivity setpoint, and neither is visible to an index that "
      "describes calcite.")

(RESULTS / "silica_seasonal.json").write_text(json.dumps(
    {"rows": rows, "static_limit_mg_L": STATIC_LIMIT,
     "dispersant_limit_mg_L": DISPERSANT_LIMIT,
     "makeup_sio2_mg_L": MAKEUP_SIO2,
     "swing_factor_15_to_35C": s35 / s15}, indent=2), encoding="utf8")
print(f"\nwritten -> {RESULTS/'silica_seasonal.json'}")
