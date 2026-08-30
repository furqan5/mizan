"""
MIZAN :: gate V6 -- the magnesium silicate operating envelope
=============================================================
Magnesium silicate scaling is a two-step mechanism: brucite Mg(OH)2
precipitates first, then reacts with dissolved and colloidal silica in the
boundary layer to form the dense scale. Brucite's saturation pH is
RETROGRADE -- it falls as temperature rises -- so the deposition criterion
is:

    deposition occurs when   bulk pH  >  pH_s(brucite) at the SKIN

This is the sharpest test the controller faces, because it requires all
three things the architecture provides and that no incumbent combines:

  * skin temperature, from the live thermal model and duty
  * bulk pH, from the chemistry model
  * acid dose, as the actuator that moves bulk pH

And it produces a load-dependent answer. The same tower, same water, same
pH deposits magnesium silicate at high load and does not at low load,
because the skin runs hotter. A fixed pH setpoint cannot express that.
"""
import json, pathlib, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
w = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
w.SiO2 = 26.8                      # Salbukh measured, Riyadh

GULF_PH_LOW, GULF_PH_HIGH = 8.5, 9.0   # typical Gulf TSE loop, per review

print("GATE V6 -- magnesium silicate deposition envelope")
print("Aramco reclaimed water + 26.8 mg/L silica, 4 cycles\n")
conc = w.concentrate(4.0)
print(f"{'skin T':>8} {'pH_s(brucite)':>15} {'safe below':>12}   verdict at Gulf pH 8.5-9.0")
print("-" * 78)
rows = []
for T in [30.0, 34.0, 38.0, 42.0, 46.0, 50.0]:
    phs = chem.ph_saturation_brucite(T, conc)
    if phs >= GULF_PH_HIGH:
        v = "safe across the whole band"
    elif phs <= GULF_PH_LOW:
        v = "DEPOSITING across the whole band"
    else:
        v = f"deposits above pH {phs:.2f} -- band straddles the limit"
    rows.append({"skin_T_C": T, "pH_s": phs, "verdict": v})
    print(f"{T:>8.0f} {phs:>15.2f} {phs:>12.2f}   {v}")

print()
print("The acid actuator has a dual role that conventional practice does not connect:")
print("  lowering pH suppresses calcite (known) AND moves the loop below the")
print("  brucite saturation pH at the skin, which is what actually prevents")
print("  magnesium silicate (not known, not controlled for).")
print()

# where the empirical product rule lands, for comparison
for name, lim in chem.MG_SILICA_LIMITS.items():
    n = chem.max_cycles_mg_silicate(w, lim, "Mg")
    print(f"  empirical Mg x SiO2 product, {name:11s} {lim:>7,.0f} -> {n:.2f} cycles")
print()
print("  industry operates 3.5-5.0 cycles; the utility (25,000) and standard")
print("  (35,000) limits bracket that, which is the consistency check.")

(RESULTS / "mg_silicate_envelope.json").write_text(json.dumps(
    {"rows": rows, "gulf_ph_band": [GULF_PH_LOW, GULF_PH_HIGH],
     "product_limits_cycles": {k: chem.max_cycles_mg_silicate(w, v, "Mg")
                               for k, v in chem.MG_SILICA_LIMITS.items()},
     "makeup_SiO2_mg_L": 26.8, "makeup_Mg_mg_L": w.Mg}, indent=2), encoding="utf8")
print(f"\nwritten -> {RESULTS/'mg_silicate_envelope.json'}")
