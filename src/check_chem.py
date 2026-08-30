import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from chemistry import *

raw = Water(name="KSA TSE", Ca=106, Mg=41, Na=310, HCO3=105, SO4=300,
            SiO2=15, pH=7.8, TDS=1500)
print("published analysis charge balance : %+.2f %%" % raw.charge_balance_pct())
tse = balance_chloride(raw)
print("after Cl closure                  : %+.2f %% (Cl = %.0f mg/L)"
      % (tse.charge_balance_pct(), tse.Cl))
print()
hdr = "%4s %7s %7s %6s %8s %8s %8s %8s" % (
    "cyc", "TDS", "I", "pH", "SI_cal", "SI_gyp", "SI_sil", "LSI")
print(hdr); print("-" * len(hdr))
for cy in [1, 2, 3, 4, 5, 6, 8, 10, 12]:
    w = tse.concentrate(cy)
    pH = ph_atmospheric_equilibrium(w, 35.0)
    s = saturation_state(w, 35.0, pH=pH)
    print("%4d %7.0f %7.4f %6.2f %8.3f %8.3f %8.3f %8.3f" % (
        cy, w.tds(), s["ionic_strength"], pH, s["SI_calcite"],
        s["SI_gypsum"], s["SI_silica_am"], langelier_index(w, 35.0, pH=pH)))

print()
print("=== HEADLINE: bulk vs condenser skin temperature ===")
print("%8s  %-24s %11s  %s" % ("T_eval", "basis", "max cycles", "binding mineral"))
res = {}
for T, basis in [(32.0, "bulk condenser water"),
                 (35.0, "bulk, hot end"),
                 (40.0, "skin, +5 K film"),
                 (43.0, "skin, +8 K film")]:
    mc = max_cycles_atm(tse, T)
    res[T] = mc
    print("%8.1f  %-24s %11.2f  %s" % (T, basis, mc, binding_mineral_atm(tse, mc, T)))

b, s_ = res[32.0], res[43.0]
print()
print("Bulk-temperature limit  : %.2f cycles" % b)
print("Skin-temperature limit  : %.2f cycles" % s_)
print("Bulk basis overstates the safe limit by %.2f cycles (%.1f%%)"
      % (b - s_, 100.0 * (b - s_) / s_))
print()
w_at_skin = tse.concentrate(s_)
print("At the skin-temperature limit, LSI reads %+.2f -- a number an operator"
      % langelier_index(w_at_skin, 43.0,
                        pH=ph_atmospheric_equilibrium(w_at_skin, 43.0)))
print("would read as heavily scaling, while the binding mineral is actually %s."
      % binding_mineral_atm(tse, s_, 43.0))
