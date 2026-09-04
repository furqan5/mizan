"""Does the gypsum model reproduce the solubility maximum its own comment claims?

chemistry.py line ~353 states:
    gypsum  maximum near 35-40 C, weakly retrograde above it

but log_k_gypsum is a single-enthalpy van 't Hoff, which is monotonic by
construction and cannot produce a maximum. This measures the size of both the
log_k term and the activity term so the two can be compared.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import chemistry as chem  # noqa: E402

print("log_k_gypsum(T) -- solubility product")
print("  T_C     log_k     d(log_k) vs 25 C")
base = chem.log_k_gypsum(25.0)
for T in (15, 25, 35, 40, 50, 60, 70):
    lk = chem.log_k_gypsum(T)
    print(f"  {T:4.0f}   {lk: .5f}   {lk - base:+.5f}")

print("\nMonotonic?  a maximum in SOLUBILITY would show as a maximum in log_k.")
ks = [chem.log_k_gypsum(T) for T in range(10, 81)]
dirs = {(b > a) for a, b in zip(ks, ks[1:])}
print(f"  log_k strictly monotonic over 10-80 C: {len(dirs) == 1}  "
      f"(increasing={list(dirs)[0] if len(dirs) == 1 else 'mixed'})")

# Now the full SI, which is what the gates use, on the actual makeup water.
TSE = chem.balance_sodium(chem.ARAMCO_RECLAIMED)
print("\nFull SI_gypsum on the modelled TSE at 4 cycles:")
print("  T_C    SI_gypsum")
prev = None
for T in (25, 30, 35, 40, 45, 50, 60, 70):
    sat = chem.saturation_state(TSE.concentrate(4.0), T_c=T)
    si = sat["SI_gypsum"]
    arrow = "" if prev is None else ("  up" if si > prev else "  down")
    print(f"  {T:4.0f}   {si: .4f}{arrow}")
    prev = si

print("\nSame, at 6 cycles (where the optimiser actually operates):")
prev = None
for T in (25, 30, 35, 40, 45, 50, 60, 70):
    sat = chem.saturation_state(TSE.concentrate(6.0), T_c=T)
    si = sat["SI_gypsum"]
    arrow = "" if prev is None else ("  up" if si > prev else "  down")
    print(f"  {T:4.0f}   {si: .4f}{arrow}")
    prev = si
