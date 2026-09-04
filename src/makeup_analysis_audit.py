"""Is the modelled makeup water self-consistent, and is its sulfate right?

WHY THIS EXISTS
---------------
`ARAMCO_RECLAIMED` carries **SO4 = 566 mg/L**, and sulfate is the single most
load-bearing number in this package: it sets the gypsum wall, which is the
product's central claim, and `value_of_information.py` scores it as worth 10.2 %
of makeup water while being measured by nobody.

A field write-up of the same Saudi Aramco pilot -- same authors, same site,
same eight-month study -- reports the TSE as:

    TDS 1500, Ca 106, Mg 41, SO4 300, HCO3 105, Na 310, Cl 528, TOC 5, PO4 8

That is **300 mg/L sulfate, not 566**. Nearly a factor of two, on the one ion
the thesis rests on.

This does NOT silently replace the water. The two analyses are scored against
two objective tests that need no outside authority -- charge balance and
whether the ions sum to the stated TDS -- and then the gypsum wall is computed
under both so the consequence is visible either way.

Run:  python src/makeup_analysis_audit.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import chemistry as chem  # noqa: E402

EQW = {"Na": 22.990, "K": 39.098, "Ca": 40.078 / 2, "Mg": 24.305 / 2,
       "Cl": 35.453, "SO4": 96.06 / 2, "HCO3": 61.017, "NO3": 62.004}
CATIONS = ("Na", "K", "Ca", "Mg")
ANIONS = ("Cl", "SO4", "HCO3", "NO3")

# As modelled today.
AS_MODELLED = dict(Na=379.0, K=25.0, Ca=94.0, Mg=41.0,
                   Cl=565.0, SO4=566.0, HCO3=70.0, NO3=12.0, TDS=1500.0)

# As reported in the field write-up of the same pilot.
AS_REPORTED = dict(Na=310.0, K=0.0, Ca=106.0, Mg=41.0,
                   Cl=528.0, SO4=300.0, HCO3=105.0, NO3=0.0, TDS=1500.0)


def diagnose(name, w):
    cat = sum(w.get(k, 0.0) / EQW[k] for k in CATIONS)
    an = sum(w.get(k, 0.0) / EQW[k] for k in ANIONS)
    imbalance = (cat - an) / ((cat + an) / 2.0) * 100.0
    ion_sum = sum(w.get(k, 0.0) for k in CATIONS + ANIONS)
    tds_err = (ion_sum - w["TDS"]) / w["TDS"] * 100.0
    print(f"\n{name}")
    print(f"  cations {cat:6.2f} meq/L   anions {an:6.2f} meq/L")
    print(f"  charge imbalance      {imbalance:+7.1f} %   "
          f"({'FAIL, >5 %' if abs(imbalance) > 5 else 'ok'})")
    print(f"  ions sum to           {ion_sum:7.0f} mg/L vs stated TDS {w['TDS']:.0f}")
    print(f"  TDS closure           {tds_err:+7.1f} %   "
          f"({'FAIL, ions exceed TDS' if tds_err > 5 else 'ok'})")
    return imbalance, tds_err


def wall_for(w, label):
    water = chem.balance_sodium(chem.Water(
        name=label, Na=w["Na"], K=w.get("K", 0.0), Ca=w["Ca"], Mg=w["Mg"],
        Cl=w["Cl"], SO4=w["SO4"], HCO3=w["HCO3"], NO3=w.get("NO3", 0.0),
        SiO2=0.0, pH=7.4, TDS=w["TDS"]))
    print(f"\n  {label}: gypsum / calcite saturation at the skin (40 C), pH 8.0")
    wall = None
    for cy in range(3, 15):
        sat = chem.saturation_state(water.concentrate(float(cy)), T_c=40.0)
        gyp, cal = sat["SI_gypsum"], sat["SI_calcite"]
        over = gyp > chem.DEFAULT_LIMITS["SI_gypsum"]
        if over and wall is None:
            wall = cy
        print(f"    {cy:2d} cycles   SI_gypsum {gyp:+.3f}   SI_calcite {cal:+.3f}"
              + ("   <-- gypsum over limit" if over else ""))
        if wall is not None and cy > wall:
            break
    return wall


def main():
    print("=" * 74)
    print("MAKEUP ANALYSIS: is the modelled water self-consistent?")
    print("=" * 74)
    i1, t1 = diagnose("AS MODELLED  (ARAMCO_RECLAIMED, SO4 = 566)", AS_MODELLED)
    i2, t2 = diagnose("AS REPORTED  (field write-up, SO4 = 300)", AS_REPORTED)

    print("\n" + "=" * 74)
    print("CONSEQUENCE FOR THE GYPSUM WALL")
    print("=" * 74)
    w1 = wall_for(AS_MODELLED, "as modelled, SO4 566")
    w2 = wall_for(AS_REPORTED, "as reported, SO4 300")

    print("\n" + "-" * 74)
    print(f"  gypsum wall, SO4 566 : {w1} cycles")
    print(f"  gypsum wall, SO4 300 : {w2} cycles")
    print(f"  charge imbalance     : {i1:+.1f} % modelled vs {i2:+.1f} % reported")
    print(f"  TDS closure          : {t1:+.1f} % modelled vs {t2:+.1f} % reported")
    print("-" * 74)


if __name__ == "__main__":
    main()
